"""
Game entities for Orbital Defense.

This module defines the game objects that interact in the Orbital Defense game,
including the defense station, enemies, and other interactive elements.

The entities in this module extend the physics objects defined in the physics module,
adding game-specific properties and behaviors. Each entity type has specific properties
and behaviors that define how it interacts with the game world:

- Defense Station: Player-controlled entity that can aim and fire weapons
- Asteroid: Simple enemy that follows gravitational physics
- Enemy Ship: AI-controlled ship that can navigate toward the planet

All entities interact through physics simulations, particularly gravitational forces.
"""

from typing import List, Optional, Dict
import math
import random
from dataclasses import dataclass
from ..physics.vector import Vector2D
from ..physics.gravity import GravitationalBody

@dataclass
class WeaponType:
    """
    Configuration for a weapon type.
    
    This dataclass defines the properties of a weapon that can be fired
    by the defense station. Different weapons have different masses, speeds,
    and cooldown times, providing gameplay variety.
    
    Attributes:
        name (str): Weapon name/identifier
        mass (float): Projectile mass (affects gravitational interactions)
        radius (float): Visual/collision radius of projectile
        max_speed (float): Maximum projectile speed at 100% power
        cooldown (float): Time in seconds before weapon can be fired again
        guidance_strength (float): Strength of homing capability (0 = none)
    """
    name: str
    mass: float
    radius: float
    max_speed: float
    cooldown: float
    guidance_strength: float = 0.0

class DefenseStation(GravitationalBody):
    """
    The player-controlled defense station.
    
    The defense station orbits the planet and can fire projectiles to destroy
    incoming enemies. It has multiple weapon types and can adjust firing angle
    and power. The station extends GravitationalBody to participate in the
    physics simulation.
    
    Attributes:
        weapons (Dict[str, WeaponType]): Available weapon types
        current_weapon (str): Currently selected weapon name
        angle (float): Firing angle in radians (0 = right, π/2 = up)
        power (float): Firing power as percentage (0-100%)
        cooldowns (Dict[str, float]): Remaining cooldown time for each weapon
    """
    
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
            position (Vector2D): Initial position vector
            mass (float): Station mass for physics calculations
            radius (float): Station radius for collisions and rendering
            weapons (Dict[str, WeaponType]): Available weapons dictionary
        """
        super().__init__(position, mass, radius)
        self.weapons = weapons
        self.current_weapon = list(weapons.keys())[0]
        self.angle = 0.0  # Firing angle in radians
        self.power = 50.0  # Firing power (percentage)
        self.cooldowns = {name: 0.0 for name in weapons.keys()}
    
    def update_cooldowns(self, dt: float):
        """
        Update weapon cooldown timers.
        
        Decreases all weapon cooldowns by the elapsed time.
        
        Args:
            dt (float): Time step in seconds
        """
        for weapon in self.cooldowns:
            self.cooldowns[weapon] = max(0.0, self.cooldowns[weapon] - dt)
    
    def can_fire(self) -> bool:
        """
        Check if current weapon can be fired.
        
        Returns:
            bool: True if weapon is ready to fire, False otherwise
        """
        return self.cooldowns[self.current_weapon] <= 0.0
    
    def fire(self) -> Optional[Dict]:
        """
        Attempt to fire current weapon.
        
        If the current weapon is ready (not in cooldown), this method will
        reset the cooldown and return parameters for creating a projectile.
        The projectile's speed is based on the current power setting.
        
        Returns:
            Optional[Dict]: Dictionary with projectile parameters if weapon
                           can be fired, None otherwise
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
    """
    Base class for enemy objects.
    
    This class extends GravitationalBody to add enemy-specific properties 
    like point value and destruction state. All enemy types inherit from
    this class and add their own specialized behaviors.
    
    Attributes:
        velocity (Vector2D): Current velocity vector
        points (int): Points awarded to player when destroyed
        is_destroyed (bool): Flag indicating if enemy has been destroyed
    """
    
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
            position (Vector2D): Initial position vector
            velocity (Vector2D): Initial velocity vector
            mass (float): Enemy mass for physics calculations
            radius (float): Enemy radius for collisions and rendering
            points (int): Points awarded for destruction
        """
        super().__init__(position, mass, radius)
        self.velocity = velocity
        self.points = points
        self.is_destroyed = False

class Asteroid(GravitationalBody):
    """
    An asteroid that can be destroyed for points.
    
    Asteroids are simple enemies that move according to physics rules.
    They are affected by gravity and can collide with other objects.
    
    Attributes:
        points (int): Points awarded when asteroid is destroyed
    """
    
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
            position (Vector2D): Initial position vector
            mass (float): Asteroid mass for physics calculations
            radius (float): Asteroid radius for collisions and rendering
            points (int): Points awarded for destruction (default: 100)
        """
        super().__init__(position, mass, radius)
        self.points = points

class EnemyShip(Enemy):
    """
    An AI-controlled enemy ship.
    
    Enemy ships are more advanced enemies that use AI to navigate toward
    the planet. They can adjust their trajectory and have different behavioral
    states based on their distance to the planet.
    
    Attributes:
        config (Dict): Configuration parameters for AI behavior
        last_ai_update (float): Time of last AI update
        target (Optional): Current target (if any)
        state (str): Current behavioral state (approach, orbit, attack)
    """
    
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
            position (Vector2D): Initial position vector
            mass (float): Ship mass for physics calculations
            radius (float): Ship radius for collisions and rendering
            config (Dict): Ship AI configuration parameters
            points (int): Points awarded for destruction (default: 200)
        """
        super().__init__(position, Vector2D(0, 0), mass, radius, points)
        self.config = config or {}
        self.last_ai_update = 0.0
        self.target = None
        self.state = 'approach'  # approach, orbit, attack
    
    def update_ai(self, current_time: float, planet_pos: Vector2D):
        """
        Update AI behavior based on current game state.
        
        This method implements the ship's AI logic, determining how it
        should move based on its distance to the planet. The ship can be
        in different states (approach, orbit) which affect its movement.
        
        The AI only updates at intervals defined in the configuration to
        prevent excessive CPU usage.
        
        Args:
            current_time (float): Current game time in seconds
            planet_pos (Vector2D): Current planet position vector
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