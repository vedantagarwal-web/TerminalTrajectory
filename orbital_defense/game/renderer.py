"""
ASCII renderer for Orbital Defense.

This module handles the ASCII-based visualization of the game state,
including the planet, defense station, projectiles, and enemies.
"""

import math
from typing import List, Dict, Tuple
from rich.console import Console
from rich.style import Style
from ..physics.vector import Vector2D
from .entities import DefenseStation, Enemy, Asteroid, EnemyShip

class AsciiRenderer:
    """Renders game state using ASCII characters."""
    
    def __init__(self, width: int, height: int):
        """
        Initialize the renderer.
        
        Args:
            width (int): Screen width in characters
            height (int): Screen height in characters
        """
        self.width = width
        self.height = height
        self.console = Console()
        
        # Character mappings for different entities
        self.chars = {
            'empty': ' ',
            'planet': 'O',
            'station': '^',
            'projectile': '*',
            'asteroid': '#',
            'ship': '@',
            'explosion': 'X',
            'trajectory': '.'
        }
        
        # Initialize screen buffer
        self.buffer = [[self.chars['empty'] for _ in range(width)]
                      for _ in range(height)]
    
    def clear_buffer(self):
        """Clear the screen buffer."""
        for y in range(self.height):
            for x in range(self.width):
                self.buffer[y][x] = self.chars['empty']
    
    def world_to_screen(self, position: Vector2D) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            position (Vector2D): World position
        
        Returns:
            Tuple[int, int]: Screen coordinates (x, y)
        """
        x = int(position.x)
        y = self.height - 1 - int(position.y)  # Invert y-axis for terminal
        
        # Ensure coordinates are within bounds
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        return x, y
    
    def draw_circle(self, center: Vector2D, radius: float, char: str):
        """
        Draw a circle in ASCII.
        
        Args:
            center (Vector2D): Center position
            radius (float): Circle radius
            char (str): Character to use
        """
        cx, cy = self.world_to_screen(center)
        
        # Draw circle using simple algorithm
        for dx in range(-int(radius), int(radius) + 1):
            for dy in range(-int(radius), int(radius) + 1):
                if dx*dx + dy*dy <= radius*radius:
                    screen_x, screen_y = cx + dx, cy + dy
                    if (0 <= screen_x < self.width and
                        0 <= screen_y < self.height):
                        self.buffer[screen_y][screen_x] = char
    
    def draw_trajectory(self, points: List[Vector2D]):
        """
        Draw a predicted trajectory.
        
        Args:
            points (List[Vector2D]): List of trajectory points
        """
        for point in points:
            x, y = self.world_to_screen(point)
            if 0 <= x < self.width and 0 <= y < self.height:
                self.buffer[y][x] = self.chars['trajectory']
    
    def draw_ui(self, station: DefenseStation, score: int):
        """
        Draw game UI elements.
        
        Args:
            station (DefenseStation): Player's defense station
            score (int): Current score
        """
        # Draw weapon info
        weapon = station.weapons[station.current_weapon]
        weapon_info = f"Weapon: {weapon.name} | Power: {station.power:3.0f}% | Angle: {math.degrees(station.angle):3.0f}°"
        self._draw_text(1, 1, weapon_info)
        
        # Draw cooldown bar
        cooldown = station.cooldowns[station.current_weapon]
        if cooldown > 0:
            bar_width = 20
            filled = int((1 - cooldown / weapon.cooldown) * bar_width)
            cooldown_bar = f"[{'=' * filled}{' ' * (bar_width - filled)}]"
            self._draw_text(1, 2, cooldown_bar)
        
        # Draw score
        score_text = f"Score: {score}"
        self._draw_text(self.width - len(score_text) - 1, 1, score_text)
    
    def _draw_text(self, x: int, y: int, text: str):
        """Draw text at specified position."""
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
        score: int
    ):
        """
        Render the complete game state.
        
        Args:
            planet_pos (Vector2D): Planet position
            planet_radius (float): Planet radius
            station (DefenseStation): Defense station
            projectiles (List[Vector2D]): Active projectiles
            enemies (List[Enemy]): Active enemies
            trajectory (List[Vector2D]): Predicted trajectory
            score (int): Current score
        """
        # Clear screen and buffer
        print("\033[2J\033[H", end="", flush=True)  # ANSI escape code to clear screen and move cursor to home
        self.clear_buffer()
        
        # Draw border first
        for x in range(self.width):
            self.buffer[0][x] = '-'
            self.buffer[self.height-1][x] = '-'
        for y in range(self.height):
            self.buffer[y][0] = '|'
            self.buffer[y][self.width-1] = '|'
        
        # Draw trajectory (background)
        if trajectory:
            self.draw_trajectory(trajectory)
        
        # Draw planet (using a consistent size)
        cx, cy = self.world_to_screen(planet_pos)
        
        # Draw planet body (using a fixed size for better visibility)
        for dx in range(-2, 3):  # Fixed size of 5x5
            for dy in range(-2, 3):
                screen_x, screen_y = cx + dx, cy + dy
                if (0 <= screen_x < self.width and
                    0 <= screen_y < self.height):
                    self.buffer[screen_y][screen_x] = self.chars['planet']
        
        # Draw station
        x, y = self.world_to_screen(station.position)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = self.chars['station']
        
        # Draw projectiles
        for proj in projectiles:
            x, y = self.world_to_screen(proj)
            if 0 <= x < self.width and 0 <= y < self.height:
                self.buffer[y][x] = self.chars['projectile']
        
        # Draw enemies
        for enemy in enemies:
            x, y = self.world_to_screen(enemy.position)
            if 0 <= x < self.width and 0 <= y < self.height:
                char = (self.chars['asteroid'] if isinstance(enemy, Asteroid)
                       else self.chars['ship'])
                self.buffer[y][x] = char
        
        # Draw UI
        self.draw_ui(station, score)
        
        # Render to console (single frame)
        for y in range(self.height):
            print(''.join(self.buffer[y]), flush=True) 