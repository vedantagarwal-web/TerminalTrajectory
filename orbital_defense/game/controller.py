"""
Game controller for Orbital Defense.

This module handles game logic, input processing, and game state management.
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
from .entities import (
    WeaponType, DefenseStation, Enemy,
    Asteroid, EnemyShip
)
from .renderer import AsciiRenderer

class GameController:
    """Main game controller class."""
    
    def __init__(self, config_path: str):
        """
        Initialize the game controller.
        
        Args:
            config_path (str): Path to physics configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize screen dimensions
        self.width = 80  # Terminal-friendly width
        self.height = 24  # Terminal-friendly height
        
        # Initialize physics
        self.gravity_sim = GravitySimulator()
        self.motion = ProjectileMotion(self.gravity_sim)
        
        # Create planet
        planet_config = self.config['planet']
        self.planet = GravitationalBody(
            Vector2D(self.width / 2, self.height / 2),  # Center of screen
            planet_config['mass'],
            3.0  # Smaller radius for terminal display
        )
        self.gravity_sim.add_body(self.planet)
        
        # Initialize weapons
        self.weapons = {
            name: WeaponType(
                name=name,
                mass=weapon['mass'],
                radius=weapon['radius'],
                max_speed=weapon['max_speed'],
                cooldown=weapon['cooldown'],
                guidance_strength=weapon.get('guidance_strength', 0.0)
            )
            for name, weapon in self.config['projectiles']['types'].items()
        }
        
        # Create defense station
        station_config = self.config['defense_station']
        orbit_height = 2.0  # Smaller orbit for terminal display
        station_pos = Vector2D(
            self.planet.position.x,
            self.planet.position.y + self.planet.radius + orbit_height
        )
        self.station = DefenseStation(
            station_pos,
            station_config['mass'],
            0.5,  # Smaller radius for terminal display
            self.weapons
        )
        
        # Initialize game state
        self.score = 0
        self.projectiles: List[Projectile] = []
        self.enemies: List[Enemy] = []
        self.predicted_trajectory: List[Vector2D] = []
        self.paused = False
        self.game_over = False
        
        # Initialize renderer
        self.renderer = AsciiRenderer(self.width, self.height)
        
        # Timing
        self.dt = self.config['simulation']['time_step']
        self.last_spawn = 0
        self.spawn_interval = 2.0  # seconds
        
        # Set up keyboard listener
        self.key_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
            suppress=False  # Don't suppress key events
        )
        self.key_listener.start()
        
        # Track pressed keys
        self.pressed_keys = set()
        
        # Enemy spawning variables
        self.difficulty = 0.1
        self.spawn_timer = max(0.5, self.config['enemies']['spawn_interval'] - self.difficulty)
    
    def _on_key_press(self, key):
        """Handle key press events."""
        try:
            # Handle special keys
            if hasattr(key, 'name'):
                key_name = key.name
                self.pressed_keys.add(key_name)
                
                # Handle weapon selection
                if key_name in [str(i) for i in range(1, len(self.weapons) + 1)]:
                    weapon_index = int(key_name) - 1
                    weapon_name = list(self.weapons.keys())[weapon_index]
                    self.station.current_weapon = weapon_name
                
                # Handle other actions
                elif key_name == 'space':
                    self._fire_weapon()
                elif key_name == 'esc':
                    self.game_over = True
                    return False  # Stop listener
                elif key_name == 'p':
                    self.paused = not self.paused
                elif key_name == 'r':
                    self._save_replay()
            
            # Handle regular keys
            elif hasattr(key, 'char'):
                key_char = key.char
                self.pressed_keys.add(key_char)
                
                # Handle weapon selection
                if key_char in [str(i) for i in range(1, len(self.weapons) + 1)]:
                    weapon_index = int(key_char) - 1
                    weapon_name = list(self.weapons.keys())[weapon_index]
                    self.station.current_weapon = weapon_name
                
                # Handle other actions
                elif key_char == ' ':
                    self._fire_weapon()
                elif key_char == 'p':
                    self.paused = not self.paused
                elif key_char == 'r':
                    self._save_replay()
        except Exception as e:
            print(f"Error handling key press: {e}")
    
    def _on_key_release(self, key):
        """Handle key release events."""
        try:
            if hasattr(key, 'name'):
                self.pressed_keys.discard(key.name)
            elif hasattr(key, 'char'):
                self.pressed_keys.discard(key.char)
        except Exception as e:
            print(f"Error handling key release: {e}")
    
    def handle_input(self):
        """Process keyboard input."""
        # Handle continuous inputs
        if 'left' in self.pressed_keys:
            self.station.angle = (self.station.angle + 0.1) % (2 * math.pi)
        if 'right' in self.pressed_keys:
            self.station.angle = (self.station.angle - 0.1) % (2 * math.pi)
        if 'up' in self.pressed_keys:
            self.station.power = min(100.0, self.station.power + 2.0)
        if 'down' in self.pressed_keys:
            self.station.power = max(0.0, self.station.power - 2.0)
    
    def _fire_weapon(self):
        """Handle weapon firing."""
        params = self.station.fire()
        if params:
            projectile = self.motion.launch_projectile(
                params['position'],
                params['angle'],
                params['speed'],
                params['mass'],
                params['radius']
            )
            self.projectiles.append(projectile)
    
    def _spawn_enemy(self):
        """Spawn a new enemy based on game difficulty."""
        # Calculate spawn position (random angle, fixed distance)
        angle = random.uniform(0, 2 * math.pi)
        distance = self.config['enemies']['spawn_distance']
        x = self.planet.position.x + distance * math.cos(angle)
        y = self.planet.position.y + distance * math.sin(angle)
        spawn_pos = Vector2D(x, y)
        
        # Choose enemy type based on difficulty
        # As difficulty increases, more ships spawn
        ship_weight = min(0.3 + self.difficulty * 0.1, 0.7)  # Max 70% ships
        enemy_type = random.choices(
            ['asteroid', 'ship'],
            weights=[1 - ship_weight, ship_weight]
        )[0]
        
        # Create enemy with appropriate parameters
        if enemy_type == 'asteroid':
            # Asteroids get slightly larger with difficulty
            mass_multiplier = 1.0 + self.difficulty * 0.2
            mass = random.uniform(
                self.config['enemies']['asteroid']['min_mass'] * mass_multiplier,
                self.config['enemies']['asteroid']['max_mass'] * mass_multiplier
            )
            enemy = Asteroid(
                spawn_pos,
                mass,
                self.config['enemies']['asteroid']['radius'],
                self.config['enemies']['asteroid']['points']
            )
        else:  # ship
            # Ships get faster with difficulty
            ship_config = {
                'ai': self.config['enemies']['ship']['ai'],
                'planet_mass': self.planet.mass,
                'speed_multiplier': 1.0 + self.difficulty * 0.3  # Up to 30% faster
            }
            enemy = EnemyShip(
                spawn_pos,
                self.config['enemies']['ship']['mass'],
                self.config['enemies']['ship']['radius'],
                ship_config,
                self.config['enemies']['ship']['points']
            )
        
        # Calculate initial velocity for orbit
        enemy.velocity = enemy.orbital_velocity(self.planet, clockwise=False)
        
        # Add to game state
        self.enemies.append(enemy)
        self.gravity_sim.add_body(enemy)
        
        # Update difficulty (slower increase)
        self.difficulty += 0.05  # Reduced from 0.1
        self.spawn_timer = max(0.5, self.config['enemies']['spawn_interval'] - self.difficulty)
    
    def update(self):
        """Update game state."""
        if self.paused:
            return
        
        # Update cooldowns
        for weapon in self.station.cooldowns:
            if self.station.cooldowns[weapon] > 0:
                self.station.cooldowns[weapon] -= self.dt
        
        # Update spawn timer
        if self.spawn_timer > 0:
            self.spawn_timer -= self.dt
        else:
            self._spawn_enemy()
        
        # Update enemy AI
        current_time = time.time()
        for enemy in self.enemies:
            if isinstance(enemy, EnemyShip):
                enemy.update_ai(current_time, self.planet.position)
        
        # Update physics
        self.gravity_sim.step(self.dt)
        
        # Check collisions
        self._check_collisions()
        
        # Remove off-screen objects
        self._cleanup_off_screen()
        
        # Update trajectory prediction
        self._update_trajectory()
    
    def _check_collisions(self):
        """Check and handle collisions between objects."""
        # Check projectile-enemy collisions
        for proj in self.projectiles[:]:
            for enemy in self.enemies[:]:
                if self.motion.check_collision(proj, enemy):
                    # Handle collision
                    enemy.is_destroyed = True
                    self.score += enemy.points
                    
                    # Remove objects from physics simulation
                    self.motion.remove_projectile(proj)
                    self.gravity_sim.remove_body(enemy)
                    
                    # Remove from game state
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                    
                    # Break inner loop since projectile is destroyed
                    break
        
        # Check enemy-planet collisions
        for enemy in self.enemies[:]:
            if self.motion.check_collision(enemy, self.planet):
                self.game_over = True
                break  # No need to check other enemies
    
    def _cleanup_off_screen(self):
        """Remove objects that have left the game area."""
        margin = 50  # Allow objects to go slightly off-screen
        
        # Clean up projectiles
        for proj in self.projectiles[:]:
            x, y = proj.position.x, proj.position.y
            if (x < -margin or x > self.width + margin or
                y < -margin or y > self.height + margin):
                self.motion.remove_projectile(proj)
                self.projectiles.remove(proj)
        
        # Clean up enemies
        for enemy in self.enemies[:]:
            x, y = enemy.position.x, enemy.position.y
            if (x < -margin or x > self.width + margin or
                y < -margin or y > self.height + margin):
                self.gravity_sim.remove_body(enemy)
                self.enemies.remove(enemy)
    
    def _update_trajectory(self):
        """Update predicted projectile trajectory."""
        if self.station.can_fire():
            weapon = self.weapons[self.station.current_weapon]
            speed = (self.station.power / 100.0) * weapon.max_speed
            self.predicted_trajectory = self.motion.predict_trajectory(
                Vector2D(self.station.position.x, self.station.position.y),
                self.station.angle,
                speed,
                weapon.mass,
                steps=self.config['simulation']['max_prediction_steps'],
                dt=self.config['simulation']['prediction_interval']
            )
        else:
            self.predicted_trajectory = []
    
    def _save_replay(self):
        """Save trajectory data to CSV file."""
        all_data = []
        for i, proj in enumerate(self.projectiles):
            data = self.motion.export_trajectory_data(proj)
            for point in data:
                point['projectile_id'] = i
            all_data.extend(data)
        
        if all_data:
            df = pd.DataFrame(all_data)
            df.to_csv('trajectory_replay.csv', index=False)
    
    def render(self):
        """Render the current game state."""
        self.renderer.render(
            self.planet.position,
            self.planet.radius,
            self.station,
            [p.position for p in self.projectiles],
            self.enemies,
            self.predicted_trajectory,
            self.score
        )
    
    def run(self):
        """Main game loop."""
        try:
            last_frame_time = time.time()
            frame_count = 0
            last_fps_time = time.time()
            
            while not self.game_over:
                current_time = time.time()
                frame_delta = current_time - last_frame_time
                
                # Handle input
                self.handle_input()
                
                # Update game state
                self.update()
                
                # Render frame
                self.render()
                
                # Control frame rate
                sleep_time = max(0, self.dt - frame_delta)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Update timing
                last_frame_time = time.time()
                frame_count += 1
                
                # Calculate and display FPS every second
                if current_time - last_fps_time >= 1.0:
                    fps = frame_count / (current_time - last_fps_time)
                    print(f"\033[K\033[1;1HFPS: {fps:.1f}", end="", flush=True)
                    frame_count = 0
                    last_fps_time = current_time
        
        except KeyboardInterrupt:
            print("\nGame terminated by user.")
        finally:
            # Clean up keyboard listener
            self.key_listener.stop() 