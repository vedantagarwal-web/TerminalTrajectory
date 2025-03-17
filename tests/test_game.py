"""
Tests for game mechanics and entities.
"""

import math
import pytest
from orbital_defense.physics.vector import Vector2D
from orbital_defense.game.entities import (
    WeaponType, DefenseStation, Enemy,
    Asteroid, EnemyShip
)

@pytest.fixture
def weapon_types():
    """Create test weapon types."""
    return {
        'test_weapon': WeaponType(
            name='test_weapon',
            mass=1.0,
            radius=0.5,
            max_speed=100.0,
            cooldown=1.0
        ),
        'guided_weapon': WeaponType(
            name='guided_weapon',
            mass=2.0,
            radius=0.8,
            max_speed=80.0,
            cooldown=2.0,
            guidance_strength=0.5
        )
    }

def test_defense_station(weapon_types):
    """Test defense station functionality."""
    station = DefenseStation(
        Vector2D(0, 0),
        1000.0,
        5.0,
        weapon_types
    )
    
    # Test initial state
    assert station.current_weapon == 'test_weapon'
    assert station.angle == 0.0
    assert station.power == 50.0
    assert all(cd == 0.0 for cd in station.cooldowns.values())
    
    # Test weapon firing
    params = station.fire()
    assert params is not None
    assert params['mass'] == weapon_types['test_weapon'].mass
    assert params['speed'] == weapon_types['test_weapon'].max_speed * 0.5
    
    # Test cooldown
    assert station.cooldowns['test_weapon'] == weapon_types['test_weapon'].cooldown
    assert not station.can_fire()
    
    # Test cooldown update
    station.update_cooldowns(0.5)
    assert station.cooldowns['test_weapon'] == 0.5
    
    # Test weapon switching
    station.current_weapon = 'guided_weapon'
    assert station.current_weapon == 'guided_weapon'
    assert station.can_fire()  # Different weapon should have separate cooldown

def test_asteroid_generation():
    """Test random asteroid generation."""
    bounds = (800, 600)
    params = {
        'min_mass': 10.0,
        'max_mass': 50.0,
        'min_radius': 2.0,
        'max_radius': 5.0,
        'min_speed': 20.0,
        'max_speed': 40.0,
        'points': 100
    }
    planet_pos = Vector2D(400, 300)
    
    asteroid = Asteroid.random(bounds, params, planet_pos)
    
    # Test that asteroid is generated within bounds
    assert 0 <= asteroid.position.x <= bounds[0]
    assert 0 <= asteroid.position.y <= bounds[1]
    
    # Test that parameters are within specified ranges
    assert params['min_mass'] <= asteroid.mass <= params['max_mass']
    assert params['min_radius'] <= asteroid.radius <= params['max_radius']
    assert params['points'] == asteroid.points
    
    # Test that velocity is non-zero
    assert asteroid.velocity.magnitude > 0

def test_enemy_ship_behavior():
    """Test enemy ship AI behavior."""
    # Create a ship targeting the origin
    ship = EnemyShip(
        position=Vector2D(100, 100),
        velocity=Vector2D(0, 0),
        mass=30.0,
        radius=3.0,
        points=200,
        target=Vector2D(0, 0)
    )
    
    # Test initial state
    assert not ship.is_destroyed
    assert ship.points == 200
    
    # Test that ship moves towards target
    ship.update(0.1)
    
    # Velocity should point towards target
    to_target = Vector2D(0, 0) - ship.position
    vel_direction = ship.velocity.normalize()
    target_direction = to_target.normalize()
    
    # Dot product should be close to 1 (vectors pointing in same direction)
    assert vel_direction.dot(target_direction) > 0.9

def test_collision_scoring():
    """Test scoring system for enemy destruction."""
    enemy = Enemy(
        position=Vector2D(0, 0),
        velocity=Vector2D(1, 0),
        mass=10.0,
        radius=2.0,
        points=100
    )
    
    assert enemy.points == 100
    assert not enemy.is_destroyed
    
    # Simulate destruction
    enemy.is_destroyed = True
    assert enemy.is_destroyed 