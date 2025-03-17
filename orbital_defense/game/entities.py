"""
Game entities for Orbital Defense.

This module defines the game objects that interact in the Orbital Defense game,
including the defense station, enemies, and other interactive elements.
"""

from typing import List, Optional, Dict
import math
import random
from dataclasses import dataclass
from ..physics.vector import Vector2D
from ..physics.gravity import GravitationalBody

@dataclass
class WeaponType:
    """Configuration for a weapon type."""
    name: str
    mass: float
    radius: float
    max_speed: float
    cooldown: float
    guidance_strength: float = 0.0

class DefenseStation(GravitationalBody):
    """The player-controlled defense station."""
    
    def __init__(
        self,
        position: Vector2D,
        mass: float,
        radius: float,
        weapons: Dict[str, WeaponType]
    ):
        """
        Initialize the defense station.
        
        Args:
            position (Vector2D): Initial position
            mass (float): Station mass
            radius (float): Station radius
            weapons (Dict[str, WeaponType]): Available weapons
        """
        super().__init__(position, mass, radius)
        self.weapons = weapons
        self.current_weapon = list(weapons.keys())[0]
        self.angle = 0.0  # Firing angle in radians
        self.power = 50.0  # Firing power (percentage)
        self.cooldowns = {name: 0.0 for name in weapons.keys()}
    
    def update_cooldowns(self, dt: float):
        """Update weapon cooldown timers."""
        for weapon in self.cooldowns:
            self.cooldowns[weapon] = max(0.0, self.cooldowns[weapon] - dt)
    
    def can_fire(self) -> bool:
        """Check if current weapon can be fired."""
        return self.cooldowns[self.current_weapon] <= 0.0
    
    def fire(self) -> Optional[Dict]:
        """
        Attempt to fire current weapon.
        
        Returns:
            Optional[Dict]: Projectile parameters if can fire, None otherwise
        """
        if not self.can_fire():
            return None
            
        weapon = self.weapons[self.current_weapon]
        self.cooldowns[self.current_weapon] = weapon.cooldown
        
        speed = (self.power / 100.0) * weapon.max_speed
        
        return {
            'position': Vector2D(self.position.x, self.position.y),
            'angle': self.angle,
            'speed': speed,
            'mass': weapon.mass,
            'radius': weapon.radius,
            'guidance_strength': weapon.guidance_strength
        }

class Enemy(GravitationalBody):
    """Base class for enemy objects."""
    
    def __init__(
        self,
        position: Vector2D,
        velocity: Vector2D,
        mass: float,
        radius: float,
        points: int
    ):
        """
        Initialize an enemy.
        
        Args:
            position (Vector2D): Initial position
            velocity (Vector2D): Initial velocity
            mass (float): Enemy mass
            radius (float): Enemy radius
            points (int): Points awarded for destruction
        """
        super().__init__(position, mass, radius)
        self.velocity = velocity
        self.points = points
        self.is_destroyed = False

class Asteroid(GravitationalBody):
    """An asteroid that can be destroyed for points."""
    
    def __init__(
        self,
        position: Vector2D,
        mass: float,
        radius: float,
        points: int = 100
    ):
        """
        Initialize an asteroid.
        
        Args:
            position (Vector2D): Initial position
            mass (float): Asteroid mass
            radius (float): Asteroid radius
            points (int): Points awarded for destruction
        """
        super().__init__(position, mass, radius)
        self.points = points

class EnemyShip(Enemy):
    """An AI-controlled enemy ship."""
    
    def __init__(
        self,
        position: Vector2D,
        mass: float,
        radius: float,
        config: Dict = None,
        points: int = 200
    ):
        """
        Initialize an enemy ship.
        
        Args:
            position (Vector2D): Initial position
            mass (float): Ship mass
            radius (float): Ship radius
            config (Dict): Ship configuration
            points (int): Points awarded for destruction
        """
        super().__init__(position, Vector2D(0, 0), mass, radius, points)
        self.config = config or {}
        self.last_ai_update = 0.0
        self.target = None
        self.state = 'approach'  # approach, orbit, attack
    
    def update_ai(self, current_time: float, planet_pos: Vector2D):
        """
        Update AI behavior.
        
        Args:
            current_time (float): Current game time
            planet_pos (Vector2D): Planet position
        """
        # Check if it's time to update AI
        if current_time - self.last_ai_update < self.config['ai']['update_interval']:
            return
        
        self.last_ai_update = current_time
        
        # Calculate distance to planet
        distance = self.position.distance_to(planet_pos)
        
        # Update state based on distance
        if distance < self.config['ai']['orbit_distance']:
            self.state = 'orbit'
        elif distance < self.config['ai']['approach_distance']:
            self.state = 'approach'
        else:
            self.state = 'approach'
        
        # Calculate desired velocity based on state
        if self.state == 'approach':
            # Move towards planet
            direction = planet_pos - self.position
            direction = direction.normalize()
            desired_velocity = direction * self.config['ai']['max_speed']
        else:  # orbit
            # Calculate orbital velocity
            desired_velocity = self.orbital_velocity(
                GravitationalBody(planet_pos, self.config['planet_mass'], 0),
                clockwise=False
            )
        
        # Apply force to reach desired velocity
        current_velocity = self.velocity
        velocity_diff = desired_velocity - current_velocity
        force = velocity_diff * self.mass / self.config['ai']['update_interval']
        self.apply_force(force) 