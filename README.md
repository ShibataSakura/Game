# Arcade Racer

A lightweight top-down kart racer inspired by arcade classics. Select your driver, race a computer opponent, and pick up power-ups to swing the race in your favor.

## Features
- Four colorful characters to choose from, each represented by a unique kart.
- Single player race against an AI opponent that follows the track and competes for victory.
- Oval circuit with grass runoff, track boundaries, and lap tracking.
- Power-up crates that grant temporary boost or slow effects for dynamic gameplay.
- HUD showing lap counter, speed, and current status effects.

## Requirements
- Python 3.10+
- [Pygame](https://www.pygame.org/)

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Controls
- **Up / W**: Accelerate
- **Down / S**: Brake / Reverse
- **Left / A**: Turn left
- **Right / D**: Turn right
- **Enter / Space**: Confirm selections, continue
- **Esc**: Quit during result screen

## Running the Game

```bash
python racing_game.py
```

Select a racer, then complete three laps before the rival kart to win. Collect boost power-ups to speed ahead or slow power-ups to hinder both racers.
