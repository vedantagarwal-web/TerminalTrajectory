"""
Game controller for Orbital Defense.

This module handles game logic, input processing, and game state management.
It implements a physics-based space defense game where players must protect
a central planet from incoming enemy ships and asteroids.

The game uses realistic orbital mechanics and gravitational physics to create
challenging and engaging gameplay. Players control a defense station that orbits
the planet and can fire projectiles at enemies.

Key features:
- Physics-based gameplay with realistic gravity
- Multiple weapon types with different properties
- Trajectory prediction system
- Enemy collision detection and constraint system
- Score tracking and game state management
"""

import sys
import time
import math
import yaml
import random
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
from pynput import keyboard

from ..physics.vector import Vector2D
from ..physics.gravity import GravitationalBody, GravitySimulator
from ..physics.motion import ProjectileMotion, Projectile
from .entities import WeaponType, DefenseStation, Enemy, Asteroid, EnemyShip
from .renderer import AsciiRenderer

class GameController:
    """
    Main game controller class.
    
    This class manages the entire game state, including physics simulation,
    input handling, collision detection, and rendering. It serves as the primary
    interface between the player and the game systems.
    
    Attributes:
        width (int): Screen width in characters
        height (int): Screen height in characters
        config (dict): Configuration parameters loaded from YAML
        gravity_sim (GravitySimulator): Physics simulator for gravitational effects
        planet (GravitationalBody): The central planet to defend
        motion (ProjectileMotion): Controller for projectile physics
        weapons (Dict[str, WeaponType]): Available weapon types
        station (DefenseStation): Player's defense station
        score (int): Current game score
        game_over (bool): Flag indicating if the game is over
        paused (bool): Flag indicating if the game is paused
        projectiles (List[Projectile]): Active projectiles
        enemies (List[Enemy]): Active enemies
        predicted_trajectory (List[Vector2D]): Points in predicted projectile path
        aim_point (Vector2D): Visual indicator for aim direction
        dt (float): Time step for physics simulation
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the game controller.
        
        Args:
            config_path (str): Path to physics configuration file (YAML)
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Set up screen dimensions (80x24 is standard terminal size)
        self.width = 80
        self.height = 24
        
        # Override enemy spawn distance to be visible on screen
        self.config['enemies']['spawn_distance'] = 18.0
        
        # Game start flag
        self.waiting_for_start = False
        
        # Initialize physics
        self.gravity_sim = GravitySimulator()
        
        # Initialize planet (center of screen)
        planet_config = self.config['planet']
        self.planet = GravitationalBody(
            Vector2D(self.width / 2, self.height / 2),
            planet_config['mass'],
            3.0  # Reduced size for terminal visibility
        )
        self.gravity_sim.add_body(self.planet)
        
        # Setup physics motion controller
        self.motion = ProjectileMotion(self.gravity_sim)
        
        # Initialize weapons
        self.weapons = {
            name: WeaponType(
                name=name,
                mass=weapon['mass'],
                radius=weapon['radius'],
                max_speed=weapon['max_speed'] * 2.0,  # Double speed for better playability
                cooldown=weapon['cooldown'] * 0.5,  # Half cooldown for better playability
                guidance_strength=weapon.get('guidance_strength', 0.0)
            )
            for name, weapon in self.config['projectiles']['types'].items()
        }
        
        # Create defense station
        station_config = self.config['defense_station']
        orbit_height = 4.0  # Distance from planet surface
        station_pos = Vector2D(
            self.planet.position.x,
            self.planet.position.y + self.planet.radius + orbit_height
        )
        self.station = DefenseStation(
            station_pos,
            station_config['mass'],
            1.0,  # Reduced size for terminal visibility
            self.weapons
        )
        
        # Initialize game state
        self.score = 0
        self.game_over = False
        self.paused = False
        self.projectiles = []
        self.enemies = []
        self.predicted_trajectory = []
        self.aim_point = None
        
        # Initialize renderer
        self.renderer = AsciiRenderer(self.width, self.height)
        
        # Set up keyboard listener
        self.key_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
            suppress=False,  # Don't suppress key events
            win32_event_filter=None  # Capture all keys
        )
        self.key_listener.start()
        
        # Track pressed keys
        self.pressed_keys = set()
        
        # Game timing
        self.dt = 0.05  # 50ms per frame (~20 FPS)
        self.enemy_spawn_timer = 0
        self.difficulty = 0
    
    def _on_key_press(self, key):
        """
        Handle key press events from the keyboard listener.
        
        This method processes key press events and updates the game state accordingly.
        Keys can trigger immediate actions (fire weapon, change weapon) or be tracked
        for continuous input handling (movement).
        
        Args:
            key: The key event from pynput
        """
        try:
            # If waiting for start, check for space key to start the game
            if self.waiting_for_start:
                # Check for space key
                if (hasattr(key, 'name') and key.name.lower() == 'space') or \
                   (hasattr(key, 'char') and key.char == ' '):
                    self.waiting_for_start = False
                return
                
            # Handle special keys (arrows, etc.)
            if hasattr(key, 'name'):
                key_name = key.name.lower()
                self.pressed_keys.add(key_name)
                
                # Handle direct actions
                if key_name == 'space':
                    self._fire_weapon()
                elif key_name in ['1', '2', '3']:
                    weapon_index = int(key_name) - 1
                    if weapon_index < len(self.weapons):
                        weapon_name = list(self.weapons.keys())[weapon_index]
                        self.station.current_weapon = weapon_name
                elif key_name == 'esc':
                    self.game_over = True
                elif key_name == 'p':
                    self.paused = not self.paused
            
            # Handle regular keys (characters)
            elif hasattr(key, 'char'):
                key_char = key.char.lower() if key.char else None
                if key_char:
                    self.pressed_keys.add(key_char)
                    
                    # Handle direct actions
                    if key_char == ' ':
                        self._fire_weapon()
                    elif key_char in ['1', '2', '3']:
                        weapon_index = int(key_char) - 1
                        if weapon_index < len(self.weapons):
                            weapon_name = list(self.weapons.keys())[weapon_index]
                            self.station.current_weapon = weapon_name
                    elif key_char == 'p':
                        self.paused = not self.paused
                    elif key_char == 'q':
                        self.game_over = True
        except Exception as e:
            print(f"Error handling key press: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_key_release(self, key):
        """
        Handle key release events from the keyboard listener.
        
        This method removes released keys from the set of pressed keys
        to ensure continuous input (like movement) stops appropriately.
        
        Args:
            key: The key event from pynput
        """
        try:
            if hasattr(key, 'name'):
                self.pressed_keys.discard(key.name.lower())
            elif hasattr(key, 'char') and key.char:
                self.pressed_keys.discard(key.char.lower())
        except Exception as e:
            print(f"Error handling key release: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_input(self):
        """
        Process keyboard input for continuous actions.
        
        This method handles continuous input actions like rotating the
        station and adjusting weapon power, based on which keys are
        currently pressed.
        """
        # Handle continuous inputs
        # Left/Right: rotate station
        if any(k in self.pressed_keys for k in ['left', 'a']):
            self.station.angle = (self.station.angle + 0.2) % (2 * math.pi)
        if any(k in self.pressed_keys for k in ['right', 'd']):
            self.station.angle = (self.station.angle - 0.2) % (2 * math.pi)
        
        # Up/Down: adjust power
        if any(k in self.pressed_keys for k in ['up', 'w']):
            self.station.power = min(100, self.station.power + 5)
        if any(k in self.pressed_keys for k in ['down', 's']):
            self.station.power = max(0, self.station.power - 5)
    
    def _fire_weapon(self):
        """
        Fire the currently selected weapon.
        
        This method creates and launches a projectile based on the
        station's current weapon, position, angle, and power.
        The projectile is affected by physics and gravity.
        """
        params = self.station.fire()
        if params:
            # Make projectiles faster and larger for easier hits
            params['speed'] *= 5.0  # Increased to 5x for faster projectiles
            params['radius'] *= 4.0  # Increased to 4x for much larger projectiles
            
            # Create the projectile with enhanced parameters
            projectile = self.motion.launch_projectile(
                params['position'],
                params['angle'],
                params['speed'],
                params['mass'],
                params['radius']
            )
            self.projectiles.append(projectile)
            
            # Add visual feedback - update trajectory immediately after firing
            self._update_trajectory()
    
    def _spawn_enemy(self):
        """
        Spawn a new enemy with physics properties.
        
        This method creates either an asteroid or enemy ship at a random
        position around the planet. The enemy is given a velocity that
        directs it toward the planet, making it a threat that the player
        must destroy.
        """
        # Calculate spawn position (random angle, fixed distance)
        angle = random.uniform(0, 2 * math.pi)
        distance = min(18.0, self.config['enemies']['spawn_distance'])
        x = self.planet.position.x + distance * math.cos(angle)
        y = self.planet.position.y + distance * math.sin(angle)
        spawn_pos = Vector2D(x, y)
        
        # Determine enemy type
        enemy_type = random.choices(
            ['asteroid', 'ship'],
            weights=[0.7, 0.3]  # 70% asteroids, 30% ships
        )[0]
        
        # Create enemy with appropriate parameters
        if enemy_type == 'asteroid':
            mass = random.uniform(
                self.config['enemies']['asteroid']['min_mass'],
                self.config['enemies']['asteroid']['max_mass']
            )
            enemy = Asteroid(
                spawn_pos,
                mass,
                3.0,  # Increased from 2.0 for better visibility
                self.config['enemies']['asteroid']['points']
            )
        else:  # ship
            ship_config = {
                'ai': self.config['enemies']['ship']['ai'],
                'planet_mass': self.planet.mass,
                'speed_multiplier': 0.2  # Reduced further for better control
            }
            enemy = EnemyShip(
                spawn_pos,
                self.config['enemies']['ship']['mass'],
                3.0,  # Increased from 2.0 for better visibility
                ship_config,
                self.config['enemies']['ship']['points']
            )
        
        # Calculate velocity - very slow direct path to planet
        direction = Vector2D(
            self.planet.position.x - spawn_pos.x,
            self.planet.position.y - spawn_pos.y
        ).normalize()
        
        # Set direct velocity toward planet (extremely slow)
        enemy.velocity = Vector2D(
            direction.x * 0.1,  # Reduced further for better control
            direction.y * 0.1
        )
        
        # Add to game state
        self.enemies.append(enemy)
        self.gravity_sim.add_body(enemy)
        
        # Update spawn timer - slower spawning
        self.enemy_spawn_timer = max(5.0, 8.0 - self.difficulty)  # Increased from 3.0-6.0
    
    def update(self):
        """
        Update the game state for one time step.
        
        This method updates all aspects of the game state, including:
        - Weapon cooldowns
        - Enemy spawning
        - Physics simulation
        - Enemy constraints (keeping them on screen)
        - Collision detection
        - Off-screen object cleanup
        - Trajectory prediction
        - Game difficulty
        
        It is called once per frame in the game loop.
        """
        if self.paused:
            return
        
        # Update cooldowns
        for weapon in self.station.cooldowns:
            if self.station.cooldowns[weapon] > 0:
                self.station.cooldowns[weapon] -= self.dt
        
        # Update enemy spawn timer
        if self.enemy_spawn_timer > 0:
            self.enemy_spawn_timer -= self.dt
        else:
            self._spawn_enemy()
        
        # Update physics (gravity simulation)
        self.gravity_sim.step(self.dt)
        
        # Keep enemies inside visible bounds
        self._constrain_enemies()
        
        # Check collisions
        self._check_collisions()
        
        # Remove off-screen objects (only projectiles, not enemies)
        self._cleanup_off_screen()
        
        # Update trajectory prediction
        self._update_trajectory()
        
        # Update difficulty
        self.difficulty += 0.0005
    
    def _constrain_enemies(self):
        """
        Keep enemies within the visible area by redirecting their velocity.
        
        This method checks each enemy's position against the screen boundaries.
        If an enemy is outside the visible area, it is moved back within bounds
        and its velocity is modified to direct it back toward the planet.
        This ensures enemies don't escape the play area and always pose a threat.
        """
        margin = 5  # Buffer from screen edge
        
        for enemy in self.enemies:
            x, y = enemy.position.x, enemy.position.y
            modified = False
            
            # Check horizontal bounds
            if x < margin:
                enemy.position.x = margin
                enemy.velocity.x = abs(enemy.velocity.x) * 0.5  # Bounce back to center
                modified = True
            elif x > self.width - margin:
                enemy.position.x = self.width - margin
                enemy.velocity.x = -abs(enemy.velocity.x) * 0.5  # Bounce back to center
                modified = True
                
            # Check vertical bounds
            if y < margin:
                enemy.position.y = margin
                enemy.velocity.y = abs(enemy.velocity.y) * 0.5  # Bounce back to center
                modified = True
            elif y > self.height - margin:
                enemy.position.y = self.height - margin
                enemy.velocity.y = -abs(enemy.velocity.y) * 0.5  # Bounce back to center
                modified = True
                
            # If enemy was outside bounds, redirect it toward the planet
            if modified:
                # Get direction to planet
                direction = Vector2D(
                    self.planet.position.x - enemy.position.x,
                    self.planet.position.y - enemy.position.y
                ).normalize()
                
                # Add a small velocity component toward the planet
                enemy.velocity.x += direction.x * 0.05
                enemy.velocity.y += direction.y * 0.05
                
                # Limit velocity magnitude to prevent excessive speed
                vel_magnitude = math.sqrt(enemy.velocity.x**2 + enemy.velocity.y**2)
                if vel_magnitude > 0.3:
                    enemy.velocity.x *= 0.3 / vel_magnitude
                    enemy.velocity.y *= 0.3 / vel_magnitude
    
    def _check_collisions(self):
        """
        Check and handle collisions between game objects.
        
        This method checks for:
        1. Collisions between projectiles and enemies (scoring points)
        2. Collisions between enemies and the planet (game over)
        
        When a collision is detected, appropriate actions are taken
        (removing objects, increasing score, ending the game).
        """
        # Check projectile-enemy collisions with improved detection
        for proj in self.projectiles[:]:
            for enemy in self.enemies[:]:
                # Enhanced collision detection - larger detection radius
                if self._enhanced_collision_check(proj, enemy):
                    # Handle collision
                    enemy.is_destroyed = True
                    self.score += enemy.points
                    
                    # Debug print for collision
                    print(f"Hit! +{enemy.points} points (Score: {self.score})")
                    
                    # Remove objects from physics simulation
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
                        self.motion.remove_projectile(proj)
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                        self.gravity_sim.remove_body(enemy)
                    
                    # Break inner loop since projectile is destroyed
                    break
        
        # Check enemy-planet collisions
        for enemy in self.enemies[:]:
            if self._check_collision(enemy, self.planet):
                self.game_over = True
                break
    
    def _enhanced_collision_check(self, obj1, obj2):
        """
        Enhanced collision detection with a larger detection radius.
        
        This method provides more forgiving collision detection by using
        a radius larger than the actual object sizes. This makes it easier
        for players to hit enemies.
        
        Args:
            obj1: First physics object
            obj2: Second physics object
            
        Returns:
            bool: True if objects are colliding, False otherwise
        """
        # Calculate distance between centers
        dx = obj1.position.x - obj2.position.x
        dy = obj1.position.y - obj2.position.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Use enhanced collision radius (1.5x sum of radii)
        collision_radius = (obj1.radius + obj2.radius) * 1.5
        
        # Check if distance is less than enhanced collision radius
        is_collision = distance < collision_radius
        
        return is_collision
    
    def _check_collision(self, obj1, obj2):
        """
        Standard collision detection based on object radii.
        
        Args:
            obj1: First physics object
            obj2: Second physics object
            
        Returns:
            bool: True if objects are colliding, False otherwise
        """
        # Calculate distance between centers
        dx = obj1.position.x - obj2.position.x
        dy = obj1.position.y - obj2.position.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Check if distance is less than sum of radii
        return distance < (obj1.radius + obj2.radius)
    
    def _cleanup_off_screen(self):
        """
        Remove projectiles that have left the visible area.
        
        This method checks each projectile's position against screen boundaries
        and removes any that have gone too far off-screen. This prevents
        memory leaks from projectiles that will never return to the play area.
        """
        margin = 20  # Allow objects to go slightly off-screen
        
        # Clean up projectiles only (enemies are constrained separately)
        for proj in self.projectiles[:]:
            x, y = proj.position.x, proj.position.y
            if (x < -margin or x > self.width + margin or
                y < -margin or y > self.height + margin):
                self.motion.remove_projectile(proj)
                self.projectiles.remove(proj)
    
    def _update_trajectory(self):
        """
        Update the predicted trajectory for the current weapon.
        
        This method calculates and stores a series of points that predict
        where a fired projectile would travel. This helps the player aim
        by visualizing the path that accounts for gravity and other physics.
        """
        if self.station.can_fire():
            weapon = self.weapons[self.station.current_weapon]
            speed = (self.station.power / 100.0) * weapon.max_speed * 3.0  # Match the 3x speed boost
            
            # Create more trajectory points for better visibility
            self.predicted_trajectory = self.motion.predict_trajectory(
                Vector2D(self.station.position.x, self.station.position.y),
                self.station.angle,
                speed,
                weapon.mass,
                steps=30,  # Increased from 15 for more visible trajectory path
                dt=0.05  # Smaller time step for more detailed trajectory
            )
            
            # Add aim indicator - show where you're aiming
            aim_x = self.station.position.x + math.cos(self.station.angle) * 3
            aim_y = self.station.position.y + math.sin(self.station.angle) * 3
            self.aim_point = Vector2D(aim_x, aim_y)
        else:
            self.predicted_trajectory = []
            self.aim_point = None
    
    def render(self):
        """
        Render the current game state to the terminal.
        
        This method uses the AsciiRenderer to draw all game elements, including:
        - Planet
        - Defense station
        - Projectiles
        - Enemies
        - Trajectory prediction
        - User interface elements
        """
        # Clear screen
        print("\033c", end="", flush=True)
        
        # Use the renderer to draw the game with physics objects
        self.renderer.render(
            self.planet.position,
            self.planet.radius,
            self.station,
            [p.position for p in self.projectiles],
            self.enemies,
            self.predicted_trajectory,
            self.score,
            self.aim_point
        )
        
        # Show controls
        help_text = "← → Aim | ↑ ↓ Power | 1-3: Weapons | SPACE: Fire | P: Pause | Q: Quit"
        print(help_text)
    
    def run(self):
        """
        Main game loop.
        
        This method contains the primary game loop that:
        1. Displays instructions at the start
        2. Waits for the player to start the game
        3. Runs the game logic in a loop until game over
        4. Displays the final score
        5. Cleans up resources
        
        The loop handles input, updates the game state, and renders each frame,
        while also managing frame timing to maintain a consistent frame rate.
        """
        try:
            # Display game instructions
            print("\033c", end="", flush=True)  # Clear screen
            print("ORBITAL DEFENSE - Game Instructions:")
            print("-----------------------------------")
            print("- Arrow keys or WASD: Aim and adjust firing power")
            print("- 1, 2, 3: Select different weapons")
            print("- Space: Fire weapon")
            print("- P: Pause game")
            print("- Q: Quit game")
            print("\nGAMEPLAY TIPS:")
            print("- Watch the trajectory line to see where your shots will go")
            print("- Enemies with an 'X' marker show their predicted position")
            print("- The planet's gravity will curve your shots - use this to your advantage!")
            print("- Different weapons have different speeds and masses - experiment!")
            print("\nDefend the planet from incoming enemy ships and asteroids.")
            print("Use the physics of gravity to curve your shots and hit enemies.")
            print("\nPress SPACE to start...")
            
            # Wait for space key press to start
            self.waiting_for_start = True
            while self.waiting_for_start:
                time.sleep(0.1)  # Short sleep to prevent CPU hogging
                
            # Clear screen once at the beginning
            print("\033c", end="", flush=True)
            
            # Spawn initial enemies
            self._spawn_enemy()
            
            # Initialize trajectory on game start
            self._update_trajectory()
            
            # Main game loop
            last_frame_time = time.time()
            frame_count = 0
            fps = 0
            fps_update_time = time.time()
            
            while not self.game_over:
                # Calculate frame time
                current_time = time.time()
                frame_delta = current_time - last_frame_time
                
                # Handle input
                self.handle_input()
                
                # Update trajectory prediction regularly to provide feedback during aiming
                if frame_count % 3 == 0:  # Update every 3 frames
                    self._update_trajectory()
                
                # Update game state
                self.update()
                
                # Render frame
                self.render()
                
                # Calculate FPS
                frame_count += 1
                if current_time - fps_update_time >= 1.0:
                    fps = frame_count / (current_time - fps_update_time)
                    frame_count = 0
                    fps_update_time = current_time
                
                # Display FPS in top right
                print(f"\033[1;{self.width-10}HFPS: {fps:.1f}", end="", flush=True)
                
                # Control frame rate
                sleep_time = max(0, self.dt - frame_delta)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Update timing
                last_frame_time = time.time()
            
            # Game over screen
            print("\033c", end="", flush=True)  # Clear screen
            print(f"GAME OVER! Final Score: {self.score}")
            print("\nPress any key to exit...")
            input()
        
        except KeyboardInterrupt:
            print("\nGame terminated by user.")
        finally:
            # Clean up keyboard listener
            self.key_listener.stop() 