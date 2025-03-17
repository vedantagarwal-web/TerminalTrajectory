"""
Motion physics for the Orbital Defense game.

This module handles projectile motion calculations, taking into account
gravitational effects from multiple bodies.
"""

from typing import List, Optional, Tuple
import math
from dataclasses import dataclass
from .vector import Vector2D
from .gravity import GravitationalBody, GravitySimulator

@dataclass
class TrajectoryPoint:
    """A point along a trajectory with position and velocity."""
    position: Vector2D
    velocity: Vector2D
    time: float

class Projectile(GravitationalBody):
    """A projectile that follows physical motion laws."""
    
    def __init__(
        self,
        position: Vector2D,
        velocity: Vector2D,
        mass: float = 1.0,
        radius: float = 0.5
    ):
        """
        Initialize a projectile.
        
        Args:
            position (Vector2D): Initial position
            velocity (Vector2D): Initial velocity
            mass (float): Mass of the projectile
            radius (float): Radius of the projectile
        """
        super().__init__(position, mass, radius)
        self.velocity = velocity
        self.trajectory: List[TrajectoryPoint] = []
        self.record_trajectory = True
    
    def update_position(self, dt: float):
        """
        Update position and record trajectory point if enabled.
        
        Args:
            dt (float): Time step
        """
        # Store current velocity before update
        current_velocity = Vector2D(self.velocity.x, self.velocity.y)
        
        # Update position using parent class method
        super().update_position(dt)
        
        if self.record_trajectory:
            self.trajectory.append(
                TrajectoryPoint(
                    position=Vector2D(self.position.x, self.position.y),
                    velocity=current_velocity,
                    time=len(self.trajectory) * dt
                )
            )

class ProjectileMotion:
    """Handles projectile motion calculations with gravity."""
    
    def __init__(self, gravity_sim: GravitySimulator):
        """
        Initialize projectile motion calculator.
        
        Args:
            gravity_sim (GravitySimulator): Gravity simulator instance
        """
        self.gravity_sim = gravity_sim
        self.projectiles: List[Projectile] = []
    
    def launch_projectile(
        self,
        position: Vector2D,
        angle: float,
        speed: float,
        mass: float = 1.0,
        radius: float = 0.5
    ) -> Projectile:
        """
        Launch a new projectile.
        
        Args:
            position (Vector2D): Launch position
            angle (float): Launch angle in radians
            speed (float): Initial speed
            mass (float): Projectile mass
            radius (float): Projectile radius
        
        Returns:
            Projectile: The launched projectile
        """
        velocity = Vector2D.from_polar(speed, angle)
        projectile = Projectile(position, velocity, mass, radius)
        self.projectiles.append(projectile)
        self.gravity_sim.add_body(projectile)
        return projectile
    
    def remove_projectile(self, projectile: Projectile):
        """
        Remove a projectile from simulation.
        
        Args:
            projectile (Projectile): Projectile to remove
        """
        if projectile in self.projectiles:
            self.projectiles.remove(projectile)
            self.gravity_sim.remove_body(projectile)
    
    def predict_trajectory(
        self,
        start_pos: Vector2D,
        angle: float,
        speed: float,
        mass: float,
        steps: int = 100,
        dt: float = 0.1
    ) -> List[Vector2D]:
        """
        Predict trajectory without actually launching projectile.
        
        Args:
            start_pos (Vector2D): Starting position
            angle (float): Launch angle in radians
            speed (float): Initial speed
            mass (float): Projectile mass
            steps (int): Number of prediction steps
            dt (float): Time step for prediction
        
        Returns:
            List[Vector2D]: List of predicted positions
        """
        # Create temporary projectile for prediction
        velocity = Vector2D.from_polar(speed, angle)
        projectile = Projectile(
            Vector2D(start_pos.x, start_pos.y),  # Create new Vector2D to avoid modifying original
            Vector2D(velocity.x, velocity.y),     # Create new Vector2D to avoid modifying original
            mass,
            0.5  # Default radius for prediction
        )
        
        # Add to simulator temporarily
        self.gravity_sim.add_body(projectile)
        
        # Predict positions
        positions = []
        for _ in range(steps):
            positions.append(Vector2D(projectile.position.x, projectile.position.y))
            force = self.gravity_sim.calculate_net_force(projectile)
            projectile.apply_force(force)
            projectile.update_position(dt)
            
        # Remove temporary projectile
        self.gravity_sim.remove_body(projectile)
        
        return positions
    
    def check_collision(
        self,
        projectile: Projectile,
        target: GravitationalBody
    ) -> bool:
        """
        Check if projectile collides with target.
        
        Args:
            projectile (Projectile): Projectile to check
            target (GravitationalBody): Target to check collision with
        
        Returns:
            bool: True if collision occurs
        """
        dx = projectile.position.x - target.position.x
        dy = projectile.position.y - target.position.y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance <= (projectile.radius + target.radius)
    
    def export_trajectory_data(self, projectile: Projectile) -> List[dict]:
        """
        Export trajectory data for analysis.
        
        Args:
            projectile (Projectile): Projectile to export data for
        
        Returns:
            List[dict]: List of trajectory data points
        """
        return [
            {
                'time': point.time,
                'x': point.position.x,
                'y': point.position.y,
                'vx': point.velocity.x,
                'vy': point.velocity.y,
                'speed': math.sqrt(point.velocity.x * point.velocity.x + point.velocity.y * point.velocity.y),
                'angle': math.atan2(point.velocity.y, point.velocity.x)
            }
            for point in projectile.trajectory
        ] 