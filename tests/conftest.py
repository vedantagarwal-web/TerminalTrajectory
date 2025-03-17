"""
Pytest configuration for Orbital Defense tests.
"""

import pytest
from orbital_defense.physics.vector import Vector2D
from orbital_defense.physics.gravity import GravitationalBody

@pytest.fixture
def basic_vectors():
    """Create basic test vectors."""
    return {
        'zero': Vector2D(0, 0),
        'unit_x': Vector2D(1, 0),
        'unit_y': Vector2D(0, 1),
        'diagonal': Vector2D(3, 4),
    }

@pytest.fixture
def basic_bodies():
    """Create basic gravitational bodies for testing."""
    return {
        'planet': GravitationalBody(Vector2D(0, 0), 1e6, 10.0),
        'satellite': GravitationalBody(Vector2D(100, 0), 100.0, 1.0),
        'asteroid': GravitationalBody(Vector2D(-50, 50), 1000.0, 5.0),
    } 