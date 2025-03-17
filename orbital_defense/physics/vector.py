"""
Vector operations for 2D space physics calculations.

This module provides a Vector2D class that implements all necessary vector operations
for physics calculations in the Orbital Defense game.
"""

import math
from typing import Union, Tuple, List
import numpy as np

class Vector2D:
    """A 2D vector class with physics-oriented operations."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        """
        Initialize a 2D vector.
        
        Args:
            x (float): x-component of the vector
            y (float): y-component of the vector
        """
        self.x = float(x)
        self.y = float(y)
    
    def __repr__(self) -> str:
        return f"Vector2D(x={float(self.x):.3f}, y={float(self.y):.3f})"
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        """Vector addition."""
        return Vector2D(float(self.x) + float(other.x), float(self.y) + float(other.y))
    
    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        """Vector subtraction."""
        return Vector2D(float(self.x) - float(other.x), float(self.y) - float(other.y))
    
    def __mul__(self, scalar: float) -> 'Vector2D':
        """Scalar multiplication."""
        return Vector2D(float(self.x) * float(scalar), float(self.y) * float(scalar))
    
    def __rmul__(self, scalar: float) -> 'Vector2D':
        """Reverse scalar multiplication."""
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2D':
        """Scalar division."""
        if scalar == 0:
            raise ValueError("Cannot divide vector by zero")
        return Vector2D(float(self.x) / float(scalar), float(self.y) / float(scalar))
    
    @property
    def magnitude(self) -> float:
        """Calculate the magnitude (length) of the vector."""
        return math.sqrt(float(self.x) * float(self.x) + float(self.y) * float(self.y))
    
    @property
    def angle(self) -> float:
        """Calculate the angle in radians from the positive x-axis."""
        return math.atan2(self.y, self.x)
    
    def normalize(self) -> 'Vector2D':
        """Return a normalized unit vector."""
        mag = float(self.magnitude)
        if mag == 0:
            return Vector2D(0.0, 0.0)
        return Vector2D(float(self.x) / mag, float(self.y) / mag)
    
    def dot(self, other: 'Vector2D') -> float:
        """Calculate dot product with another vector."""
        return float(self.x) * float(other.x) + float(self.y) * float(other.y)
    
    def cross_magnitude(self, other: 'Vector2D') -> float:
        """Calculate the magnitude of the cross product with another vector."""
        return float(self.x) * float(other.y) - float(self.y) * float(other.x)
    
    def rotate(self, angle: float) -> 'Vector2D':
        """
        Rotate the vector by a given angle in radians.
        
        Args:
            angle (float): Rotation angle in radians
        
        Returns:
            Vector2D: New rotated vector
        """
        cos_a = float(math.cos(angle))
        sin_a = float(math.sin(angle))
        return Vector2D(
            float(self.x) * cos_a - float(self.y) * sin_a,
            float(self.x) * sin_a + float(self.y) * cos_a
        )
    
    @classmethod
    def from_polar(cls, magnitude: float, angle: float) -> 'Vector2D':
        """
        Create a vector from polar coordinates.
        
        Args:
            magnitude (float): Length of the vector
            angle (float): Angle in radians from positive x-axis
        
        Returns:
            Vector2D: New vector from polar coordinates
        """
        return cls(
            float(magnitude) * float(math.cos(angle)),
            float(magnitude) * float(math.sin(angle))
        )
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert vector to tuple representation."""
        return (float(self.x), float(self.y))
    
    def to_numpy(self) -> np.ndarray:
        """Convert vector to numpy array."""
        return np.array([float(self.x), float(self.y)])
    
    def distance_to(self, other: 'Vector2D') -> float:
        """Calculate Euclidean distance to another vector."""
        dx = float(self.x) - float(other.x)
        dy = float(self.y) - float(other.y)
        return math.sqrt(dx * dx + dy * dy)
    
    def project_onto(self, other: 'Vector2D') -> 'Vector2D':
        """
        Project this vector onto another vector.
        
        Args:
            other (Vector2D): Vector to project onto
        
        Returns:
            Vector2D: Projection of this vector onto other vector
        """
        # Calculate dot product
        dot_product = float(self.dot(other))
        
        # Calculate magnitude squared of other vector
        other_mag_squared = float(other.x) * float(other.x) + float(other.y) * float(other.y)
        
        if other_mag_squared == 0:
            return Vector2D(0.0, 0.0)
            
        # Calculate projection
        scale = dot_product / other_mag_squared
        return Vector2D(
            float(other.x) * scale,
            float(other.y) * scale
        ) 