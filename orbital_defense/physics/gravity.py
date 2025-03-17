"""
Gravitational physics calculations for the Orbital Defense game.

This module implements gravitational force calculations and orbital mechanics
using Newton's law of universal gravitation.
"""

from typing import List, Tuple
import math
from .vector import Vector2D

# Gravitational constant (scaled for game purposes)
G = 6.67430e-2  # Modified for gameplay balance

class GravitationalBody:
    """Represents an object with mass that exerts gravitational force."""
    
    def __init__(self, position: Vector2D, mass: float, radius: float):
        """
        Initialize a gravitational body.
        
        Args:
            position (Vector2D): Position vector of the body
            mass (float): Mass of the body in kg
            radius (float): Radius of the body in meters
        """
        self.position = Vector2D(float(position.x), float(position.y))  # Create new Vector2D to avoid modifying original
        self.mass = float(mass)
        self.radius = float(radius)
        self.velocity = Vector2D(0.0, 0.0)  # Initialize with float values
        self.acceleration = Vector2D(0.0, 0.0)  # Initialize with float values
    
    def gravitational_force(self, other: 'GravitationalBody') -> Vector2D:
        """
        Calculate gravitational force exerted on another body.
        
        Args:
            other (GravitationalBody): The other body to calculate force with
        
        Returns:
            Vector2D: Force vector pointing from this body to the other
        """
        # Calculate distance vector
        r = Vector2D(
            float(other.position.x) - float(self.position.x),
            float(other.position.y) - float(self.position.y)
        )
        distance = float(r.magnitude)
        
        # Avoid division by zero and unrealistic forces at very small distances
        if distance < (self.radius + other.radius):
            return Vector2D(0.0, 0.0)
        
        # Calculate force magnitude using Newton's law of gravitation
        force_magnitude = float(G * (self.mass * other.mass) / (distance * distance))
        
        # Return force vector in direction of other body
        normalized = Vector2D(float(r.x) / distance, float(r.y) / distance)
        return Vector2D(
            float(normalized.x) * force_magnitude,
            float(normalized.y) * force_magnitude
        )
    
    def orbital_velocity(self, center: 'GravitationalBody', clockwise: bool = True) -> Vector2D:
        """
        Calculate the velocity needed for circular orbit around another body.
        
        Args:
            center (GravitationalBody): The body to orbit around
            clockwise (bool): Direction of orbit
        
        Returns:
            Vector2D: Velocity vector for circular orbit
        """
        # Calculate distance vector
        r = Vector2D(
            float(self.position.x) - float(center.position.x),
            float(self.position.y) - float(center.position.y)
        )
        distance = float(r.magnitude)
        
        # Calculate orbital speed using vis-viva equation for circular orbit
        speed = float(math.sqrt(G * center.mass / distance))
        
        # Get perpendicular direction for orbital velocity
        if clockwise:
            return Vector2D(
                float(-r.y) * speed / distance,
                float(r.x) * speed / distance
            )
        else:
            return Vector2D(
                float(r.y) * speed / distance,
                float(-r.x) * speed / distance
            )
    
    def update_position(self, dt: float):
        """
        Update position based on velocity and acceleration.
        
        Args:
            dt (float): Time step in seconds
        """
        # Verlet integration for more accurate orbital motion
        half_dt_squared = 0.5 * dt * dt
        
        # Calculate acceleration term
        acc_x = float(self.acceleration.x) * half_dt_squared
        acc_y = float(self.acceleration.y) * half_dt_squared
        
        # Calculate velocity term
        vel_x = float(self.velocity.x) * dt
        vel_y = float(self.velocity.y) * dt
        
        # Update position
        self.position = Vector2D(
            float(self.position.x) + vel_x + acc_x,
            float(self.position.y) + vel_y + acc_y
        )
        
        # Update velocity
        self.velocity = Vector2D(
            float(self.velocity.x) + float(self.acceleration.x) * dt,
            float(self.velocity.y) + float(self.acceleration.y) * dt
        )
    
    def apply_force(self, force: Vector2D):
        """
        Apply a force to this body, updating its acceleration.
        
        Args:
            force (Vector2D): Force vector to apply
        """
        # F = ma -> a = F/m
        self.acceleration = Vector2D(
            float(force.x) / float(self.mass),
            float(force.y) / float(self.mass)
        )

class GravitySimulator:
    """Manages gravitational interactions between multiple bodies."""
    
    def __init__(self):
        """Initialize an empty gravity simulator."""
        self.bodies: List[GravitationalBody] = []
    
    def add_body(self, body: GravitationalBody):
        """Add a body to the simulation."""
        self.bodies.append(body)
    
    def remove_body(self, body: GravitationalBody):
        """Remove a body from the simulation."""
        if body in self.bodies:
            self.bodies.remove(body)
    
    def calculate_net_force(self, body: GravitationalBody) -> Vector2D:
        """
        Calculate net gravitational force on a body from all other bodies.
        
        Args:
            body (GravitationalBody): Body to calculate forces for
        
        Returns:
            Vector2D: Net force vector
        """
        net_x = 0.0
        net_y = 0.0
        
        for other in self.bodies:
            if other is not body:  # Don't calculate force with self
                force = other.gravitational_force(body)
                net_x += force.x
                net_y += force.y
                
        return Vector2D(net_x, net_y)
    
    def step(self, dt: float):
        """
        Advance the simulation by one time step.
        
        Args:
            dt (float): Time step in seconds
        """
        # Calculate and apply forces
        for body in self.bodies:
            force = self.calculate_net_force(body)
            body.apply_force(force)
        
        # Update positions
        for body in self.bodies:
            body.update_position(dt) 