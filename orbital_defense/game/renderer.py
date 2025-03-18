"""
ASCII renderer for Orbital Defense.

This module handles the ASCII-based visualization of the game state,
including the planet, defense station, projectiles, and enemies.

It provides a simple but effective terminal-based visualization system that
represents game objects using ASCII characters in a 2D grid. The renderer
handles coordinate transformations, buffer management, and specialized
drawing functions for various game elements.

Key features:
- 2D ASCII visualization in terminal
- Visual trajectory prediction
- Lead indicators for moving targets
- UI elements for game state information
- Dynamic character selection for different entity types
"""

import math
from typing import List, Dict, Tuple
from rich.console import Console
from rich.style import Style
from ..physics.vector import Vector2D
from .entities import DefenseStation, Enemy, Asteroid, EnemyShip

class AsciiRenderer:
    """
    Renders game state using ASCII characters in a terminal.
    
    This class manages a 2D buffer of characters that represent the game world,
    provides methods for drawing various game elements, and handles the display
    of the buffer to the terminal.
    
    Attributes:
        width (int): Width of the screen buffer in characters
        height (int): Height of the screen buffer in characters
        console (Console): Rich library console for styled output
        chars (Dict[str, str]): Mapping of entity types to ASCII characters
        buffer (List[List[str]]): 2D buffer representing the screen
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize the ASCII renderer.
        
        Args:
            width (int): Screen width in characters
            height (int): Screen height in characters
        """
        self.width = width
        self.height = height
        self.console = Console()
        
        # Define character mappings for different entities
        self.chars = {
            'empty': ' ',         # Empty space
            'planet': 'O',        # Planet
            'station': '^',       # Defense station
            'projectile': '*',    # Projectile
            'trajectory': '+',    # Trajectory point
            'asteroid': 'A',      # Asteroid
            'ship': 'S'           # Enemy ship
        }
        
        # Initialize screen buffer
        self.buffer = [[' ' for _ in range(width)] for _ in range(height)]
    
    def clear_buffer(self):
        """
        Clear the screen buffer.
        
        Resets all cells in the buffer to the empty character.
        This should be called at the beginning of each render cycle.
        """
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = self.chars['empty']
    
    def world_to_screen(self, position: Vector2D) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.
        
        The game world uses floating-point coordinates, but the screen
        buffer uses integer indices. This method handles the conversion
        and ensures coordinates are within the screen boundaries.
        
        Args:
            position (Vector2D): World position with floating-point coordinates
        
        Returns:
            Tuple[int, int]: Screen coordinates (x, y) as integers
        """
        # Direct mapping from world to screen coordinates
        x = int(position.x)
        y = int(position.y)
        
        # Ensure coordinates are within bounds
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        return x, y
    
    def draw_circle(self, center_x: int, center_y: int, radius: float, char: str):
        """
        Draw a circle in ASCII.
        
        Uses a simple distance-based algorithm to determine which cells
        should be filled to represent a circle.
        
        Args:
            center_x (int): Center x position on screen
            center_y (int): Center y position on screen
            radius (float): Circle radius in screen units
            char (str): Character to use for drawing the circle
        """
        # Draw circle using simple algorithm
        for dx in range(-int(radius), int(radius) + 1):
            for dy in range(-int(radius), int(radius) + 1):
                if dx*dx + dy*dy <= radius*radius:
                    screen_x, screen_y = center_x + dx, center_y + dy
                    if (0 <= screen_x < self.width and
                        0 <= screen_y < self.height):
                        self.buffer[screen_y][screen_x] = char
    
    def draw_trajectory(self, points: List[Vector2D]):
        """
        Draw a predicted trajectory path.
        
        Places trajectory markers at each point in the provided list.
        This helps players visualize the expected path of projectiles.
        
        Args:
            points (List[Vector2D]): List of trajectory points in world coordinates
        """
        for point in points:
            x, y = self.world_to_screen(point)
            if 0 <= x < self.width and 0 <= y < self.height:
                self.buffer[y][x] = self.chars['trajectory']
    
    def draw_ui(self, station: DefenseStation, score: int):
        """
        Draw game UI elements like weapon info, cooldowns, and score.
        
        This method adds text-based UI elements to the top of the screen
        to provide the player with important game state information.
        
        Args:
            station (DefenseStation): Player's defense station with weapon info
            score (int): Current player score
        """
        # Draw weapon info
        weapon = station.weapons[station.current_weapon]
        weapon_text = f"Weapon: {station.current_weapon} | Power: {int(station.power)}%"
        self._draw_text(1, 1, weapon_text)
        
        # Draw weapon cooldown if active
        if station.cooldowns[station.current_weapon] > 0:
            cooldown = station.cooldowns[station.current_weapon]
            cooldown_text = f"Cooldown: {cooldown:.1f}s"
            self._draw_text(1, 2, cooldown_text)
        else:
            ready_text = "READY TO FIRE!"
            self._draw_text(1, 2, ready_text)
        
        # Draw angle information
        angle_degrees = int((station.angle * 180 / math.pi) % 360)
        angle_text = f"Angle: {angle_degrees}°"
        self._draw_text(self.width - len(angle_text) - 20, 2, angle_text)
        
        # Draw score
        score_text = f"Score: {score}"
        self._draw_text(self.width - len(score_text) - 1, 1, score_text)
    
    def draw_lead_indicator(self, enemy_pos, enemy_vel, projectile_speed):
        """
        Draw a lead indicator showing where to aim for moving targets.
        
        This helper feature predicts an enemy's future position based
        on its current velocity, helping the player aim more accurately.
        
        Args:
            enemy_pos (Vector2D): Enemy's current position
            enemy_vel (Vector2D): Enemy's current velocity vector
            projectile_speed (float): Average speed of fired projectiles
        """
        # Simple prediction - assume enemy continues at current velocity
        # This is oversimplified but helps with aiming
        time_step = 1.0  # 1 second prediction
        predicted_x = enemy_pos.x + enemy_vel.x * time_step
        predicted_y = enemy_pos.y + enemy_vel.y * time_step
        
        # Convert to screen coordinates
        x, y = self.world_to_screen(Vector2D(predicted_x, predicted_y))
        
        # Draw aim point
        if 0 <= x < self.width and 0 <= y < self.height:
            # Use an X to mark the predicted position
            self.buffer[y][x] = 'X'
    
    def _draw_text(self, x: int, y: int, text: str):
        """
        Draw text at specified position in the buffer.
        
        Args:
            x (int): Starting x position
            y (int): Y position (row)
            text (str): Text to draw
        """
        for i, char in enumerate(text):
            if 0 <= x + i < self.width and 0 <= y < self.height:
                self.buffer[y][x + i] = char
    
    def render(
        self,
        planet_pos: Vector2D,
        planet_radius: float,
        station: DefenseStation,
        projectiles: List[Vector2D],
        enemies: List[Enemy],
        trajectory: List[Vector2D],
        score: int,
        aim_point: Vector2D = None
    ):
        """
        Render the complete game state to the terminal.
        
        This is the main rendering method that orchestrates the drawing of
        all game elements and UI components. It clears the screen, populates
        the buffer with all visual elements, and then outputs the complete
        frame to the terminal.
        
        The rendering process follows a layered approach, with background
        elements drawn first and foreground elements drawn later.
        
        Args:
            planet_pos (Vector2D): Planet position
            planet_radius (float): Planet radius
            station (DefenseStation): Defense station object
            projectiles (List[Vector2D]): List of projectile positions
            enemies (List[Enemy]): List of enemy objects
            trajectory (List[Vector2D]): Predicted trajectory points
            score (int): Current score
            aim_point (Vector2D, optional): Current aim direction indicator
        """
        # Clear screen and buffer
        print("\033c", end="", flush=True)
        self.clear_buffer()
        
        # Draw border
        for x in range(self.width):
            self.buffer[0][x] = '-'
            self.buffer[self.height-1][x] = '-'
        for y in range(self.height):
            self.buffer[y][0] = '|'
            self.buffer[y][self.width-1] = '|'
        
        # Draw trajectory path (background) - make it more prominent
        if trajectory:
            # Use different characters for start, middle and end of trajectory
            for i, point in enumerate(trajectory):
                x, y = self.world_to_screen(point)
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Use different characters based on position in trajectory
                    if i < len(trajectory) // 3:
                        # Beginning of trajectory - use dots
                        self.buffer[y][x] = '.'
                    elif i < 2 * len(trajectory) // 3:
                        # Middle of trajectory - use plus signs
                        self.buffer[y][x] = '+'
                    else:
                        # End of trajectory - use asterisks
                        self.buffer[y][x] = '*'
        
        # Draw aim indicator if available
        if aim_point:
            aim_x, aim_y = self.world_to_screen(aim_point)
            if 0 <= aim_x < self.width and 0 <= aim_y < self.height:
                self.buffer[aim_y][aim_x] = '>'  # Arrow pointing where you're aiming
        
        # Draw planet
        planet_x, planet_y = self.world_to_screen(planet_pos)
        self.draw_circle(planet_x, planet_y, planet_radius, self.chars['planet'])
        
        # Draw defense station
        station_x, station_y = self.world_to_screen(station.position)
        if 0 <= station_x < self.width and 0 <= station_y < self.height:
            self.buffer[station_y][station_x] = self.chars['station']
        
        # Draw projectiles
        for proj_pos in projectiles:
            x, y = self.world_to_screen(proj_pos)
            if 0 <= x < self.width and 0 <= y < self.height:
                self.buffer[y][x] = self.chars['projectile']
        
        # Calculate average projectile speed for lead indicators
        weapon = station.weapons[station.current_weapon]
        avg_projectile_speed = (station.power / 100.0) * weapon.max_speed * 4.0
        
        # Draw enemies with labels and lead indicators
        for i, enemy in enumerate(enemies):
            # Draw lead indicator for each enemy
            self.draw_lead_indicator(enemy.position, enemy.velocity, avg_projectile_speed)
            
            # Draw the enemy
            x, y = self.world_to_screen(enemy.position)
            if 0 <= x < self.width and 0 <= y < self.height:
                char = self.chars['asteroid'] if isinstance(enemy, Asteroid) else self.chars['ship']
                self.buffer[y][x] = char
                
                # Add a number label near the enemy
                if 0 <= x+1 < self.width and 0 <= y < self.height:
                    self.buffer[y][x+1] = str((i % 9) + 1)
        
        # Draw UI
        self.draw_ui(station, score)
        
        # Render buffer to screen
        for row in self.buffer:
            print(''.join(row))
        
        # Show controls
        help_text = "← → Aim | ↑ ↓ Power | 1-3: Weapons | SPACE: Fire | P: Pause | Q: Quit"
        print(help_text) 