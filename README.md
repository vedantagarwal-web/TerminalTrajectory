# 🚀 Orbital Defense

[![Physics Nerd Approved](https://img.shields.io/badge/Physics%20Nerd-Approved%20⚛️-blue)](#)

A physics-accurate CLI space shooter where you defend your planet against incoming threats using real orbital mechanics and gravitational physics!

## 🎮 Game Overview

In Orbital Defense, you command a planetary defense station tasked with protecting your world from incoming threats. Unlike traditional space shooters, this game incorporates real physics principles including:

- Gravitational fields and orbital mechanics
- Relativistic projectile motion
- Conservation of momentum and energy
- Multi-body gravitational interactions

The game features:
- Visual trajectory prediction to help aiming
- Multiple weapon types with different physics properties
- Enemy behavior with basic AI for ship navigation
- Score tracking and increasing difficulty
- Advanced collision detection system

## 🔬 Physics Concepts

The game implements several key physics concepts:

1. **Gravitational Force**: \[ F_g = G\frac{m_1m_2}{r^2} \]
2. **Orbital Velocity**: \[ v = \sqrt{\frac{GM}{r}} \]
3. **Projectile Motion**: \[ \begin{cases} x = x_0 + v_0\cos(\theta)t \\ y = y_0 + v_0\sin(\theta)t - \frac{1}{2}gt^2 \end{cases} \]
4. **Conservation of Energy**: \[ E = \frac{1}{2}mv^2 - \frac{GMm}{r} \]

## 🎯 Game Controls

- `[Space]` - Fire selected weapon
- `[←/→]` or `[A/D]` - Adjust firing angle
- `[↑/↓]` or `[W/S]` - Adjust power/velocity
- `[1-3]` - Select different weapons
- `[Q]` or `[Esc]` - Quit game
- `[P]` - Pause/Resume game
- `[X]` indicators show predicted enemy positions

## 🎲 Gameplay Tips

- Watch the trajectory line to see where your shots will go
- The planet's gravity will curve your shots - use this to your advantage
- Different weapons have different masses and speeds, affecting how gravity influences them
- Lead indicators (X marks) show where enemies are likely to be
- The game gets progressively more difficult, so destroy enemies quickly
- If an enemy hits the planet, it's game over!

## 🛠️ Installation

1. Ensure Python 3.8+ is installed
2. Clone this repository
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the game:
   ```bash
   python -m orbital_defense
   ```

## 🧪 Running Tests

```bash
pytest tests/
```

## 📐 Project Structure

```
orbital_defense/
├── physics/
│   ├── vector.py       # Vector operations
│   ├── gravity.py      # Gravitational calculations
│   └── motion.py       # Projectile and orbital motion
├── game/
│   ├── entities.py     # Game objects (station, enemies, weapons)
│   ├── renderer.py     # ASCII visualization
│   └── controller.py   # Game logic and input handling
├── config/
│   └── physics_params.yaml  # Adjustable physics parameters
└── tests/
    ├── test_physics.py
    └── test_game.py
```

## 🧩 Key Components

### Physics System

The physics system provides realistic gravity simulation through:
- Vector-based calculations for position, velocity, and acceleration
- N-body gravitational simulation between all game objects
- Predictive trajectory calculation for aiming

### Game Controller

The game controller manages:
- Input handling and key mapping
- Game state updates and physics simulation steps
- Collision detection and scoring
- Enemy spawning and difficulty progression

### ASCII Renderer

The renderer provides a clean terminal visualization with:
- 2D character buffer for drawing game elements
- Different character styles for various game objects
- Trajectory visualization with varying symbols for distance
- Enemy lead indicators for aiming assistance
- UI elements for weapon status, score, and controls

## 🔧 Development Decisions

1. **Vector Operations**: Custom vector class for precise physics calculations
2. **Time Steps**: Fixed time step with sleep control for consistent game speed
3. **Collision Detection**: Enhanced collision detection with adjustable collision radius
4. **User Experience**: Visual aids like trajectory prediction and lead indicators
5. **Keyboard Handling**: Multi-key tracking for smooth, responsive controls

## 🎓 Educational Value

This game serves as an interactive way to learn about:
- Orbital mechanics and space physics
- Numerical integration methods
- Vector mathematics
- Conservation laws in physics
- Game development patterns in Python

## 🚀 Future Enhancements

Potential areas for expansion:
- More enemy types with varied behaviors
- Additional weapon types with special physics properties
- Power-ups and upgrades for the defense station
- Multiple levels with different gravitational scenarios
- Graphical mode with PyGame or other visualization libraries

## 📊 Data Analysis

The replay system exports trajectory data in CSV format with columns:
- Time
- Position (x, y)
- Velocity (vx, vy)
- Acceleration (ax, ay)
- Forces (Fx, Fy)

Perfect for physics students to analyze real orbital mechanics! 