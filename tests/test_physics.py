"""
Tests for the physics engine components.
"""

import math
import pytest
from orbital_defense.physics.vector import Vector2D
from orbital_defense.physics.gravity import GravitationalBody, GravitySimulator
from orbital_defense.physics.motion import Projectile, ProjectileMotion

def test_vector_operations():
    """Test basic vector operations."""
    v1 = Vector2D(3, 4)
    v2 = Vector2D(1, 2)
    
    # Test addition
    v3 = v1 + v2
    assert v3.x == 4
    assert v3.y == 6
    
    # Test scalar multiplication
    v4 = v1 * 2
    assert v4.x == 6
    assert v4.y == 8
    
    # Test magnitude
    assert v1.magnitude == 5.0
    
    # Test normalization
    v_norm = v1.normalize()
    assert math.isclose(v_norm.magnitude, 1.0, rel_tol=1e-9)
    
    # Test dot product
    assert v1.dot(v2) == 11.0
    
    # Test angle
    v5 = Vector2D(1, 0)
    assert v5.angle == 0.0
    v6 = Vector2D(0, 1)
    assert math.isclose(v6.angle, math.pi/2, rel_tol=1e-9)

def test_gravitational_force():
    """Test gravitational force calculations."""
    body1 = GravitationalBody(Vector2D(0, 0), 1000.0, 1.0)
    body2 = GravitationalBody(Vector2D(10, 0), 100.0, 1.0)
    
    force = body1.gravitational_force(body2)
    
    # Force should point from body1 to body2 (positive x direction)
    assert force.x > 0
    assert math.isclose(force.y, 0.0, abs_tol=1e-9)
    
    # Test inverse square law
    body3 = GravitationalBody(Vector2D(20, 0), 100.0, 1.0)
    force2 = body1.gravitational_force(body3)
    
    # Force should be 1/4 at double the distance
    assert math.isclose(force.magnitude / force2.magnitude, 4.0, rel_tol=1e-9)

def test_orbital_velocity():
    """Test orbital velocity calculations."""
    # Create a central body and orbiting body
    center = GravitationalBody(Vector2D(0, 0), 1e6, 10.0)  # Large central mass
    orbiter = GravitationalBody(Vector2D(100, 0), 100.0, 1.0)
    
    # Calculate orbital velocity for circular orbit
    v_orbit = orbiter.orbital_velocity(center)
    
    # Verify velocity is perpendicular to position vector
    pos_to_center = center.position - orbiter.position
    assert math.isclose(v_orbit.dot(pos_to_center), 0.0, abs_tol=1e-9)

def test_projectile_motion():
    """Test projectile motion with gravity."""
    sim = GravitySimulator()
    motion = ProjectileMotion(sim)
    
    # Add a planet
    planet = GravitationalBody(Vector2D(0, 0), 1e6, 10.0)
    sim.add_body(planet)
    
    # Launch a projectile straight up
    start_pos = Vector2D(0, 20)  # Start above planet surface
    angle = math.pi/2  # Straight up
    speed = 10.0
    mass = 1.0
    
    trajectory = motion.predict_trajectory(
        start_pos,
        angle,
        speed,
        mass,
        steps=100,
        dt=0.1
    )
    
    # Projectile should eventually fall back down
    assert len(trajectory) == 100
    assert trajectory[-1].y < trajectory[0].y

def test_collision_detection():
    """Test collision detection between bodies."""
    body1 = GravitationalBody(Vector2D(0, 0), 100.0, 5.0)
    body2 = GravitationalBody(Vector2D(7, 0), 100.0, 3.0)
    
    # Bodies should collide when distance <= sum of radii
    sim = GravitySimulator()
    motion = ProjectileMotion(sim)
    
    assert motion.check_collision(body1, body2)  # 7 <= 5 + 3
    
    # Move body2 just out of range
    body2.position = Vector2D(8.1, 0)
    assert not motion.check_collision(body1, body2)  # 8.1 > 5 + 3 