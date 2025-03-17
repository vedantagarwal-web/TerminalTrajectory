# 🚀 Orbital Defense

[![Physics Nerd Approved](https://img.shields.io/badge/Physics%20Nerd-Approved%20⚛️-blue)](#)

A physics-accurate CLI space shooter where you defend your planet against incoming threats using real orbital mechanics and gravitational physics!

## 🎮 Game Overview

In Orbital Defense, you command a planetary defense station tasked with protecting your world from incoming threats. Unlike traditional space shooters, this game incorporates real physics principles including:

- Gravitational fields and orbital mechanics
- Relativistic projectile motion
- Conservation of momentum and energy
- Multi-body gravitational interactions

## 🔬 Physics Concepts

The game implements several key physics concepts:

1. **Gravitational Force**: \[ F_g = G\frac{m_1m_2}{r^2} \]
2. **Orbital Velocity**: \[ v = \sqrt{\frac{GM}{r}} \]
3. **Projectile Motion**: \[ \begin{cases} x = x_0 + v_0\cos(\theta)t \\ y = y_0 + v_0\sin(\theta)t - \frac{1}{2}gt^2 \end{cases} \]
4. **Conservation of Energy**: \[ E = \frac{1}{2}mv^2 - \frac{GMm}{r} \]

## 🎯 Game Controls

- `[Space]` - Fire selected weapon
- `[←/→]` - Adjust firing angle
- `[↑/↓]` - Adjust power/velocity
- `[1-4]` - Select different weapons
- `[Q]` - Quit game
- `[P]` - Pause/View current trajectories
- `[R]` - Save replay to CSV

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
│   ├── entities.py     # Game objects (ships, projectiles)
│   ├── renderer.py     # ASCII visualization
│   └── controller.py   # Game logic and input handling
├── config/
│   └── physics_params.yaml  # Adjustable physics parameters
└── tests/
    ├── test_physics.py
    └── test_game.py
```

## 🔧 Development Decisions

1. **Vector Operations**: Custom vector class for precise physics calculations
2. **Time Steps**: Variable time step with fixed upper limit for stable physics
3. **Collision Detection**: Spatial partitioning for efficient collision checks
4. **Visualization**: ASCII-based with optional trajectory plotting

## 🎓 Educational Value

This game serves as an interactive way to learn about:
- Orbital mechanics and space physics
- Numerical integration methods
- Vector mathematics
- Conservation laws in physics

## 📊 Data Analysis

The replay system exports trajectory data in CSV format with columns:
- Time
- Position (x, y)
- Velocity (vx, vy)
- Acceleration (ax, ay)
- Forces (Fx, Fy)

Perfect for physics students to analyze real orbital mechanics! 