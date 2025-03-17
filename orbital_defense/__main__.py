"""
Main entry point for Orbital Defense game.
"""

import os
import sys
from pathlib import Path
from .game.controller import GameController

def main():
    """Run the Orbital Defense game."""
    # Get the path to the config file
    config_path = Path(__file__).parent / 'config' / 'physics_params.yaml'
    
    if not config_path.exists():
        print("Error: Could not find physics configuration file.")
        sys.exit(1)
    
    try:
        # Create and run game controller
        game = GameController(str(config_path))
        game.run()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 