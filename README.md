# 🎲 LUDO GAME — Built with Pygame

A fully functional, visually stunning Ludo board game built entirely in Python using Pygame. Features smooth animations, bot AI, local multiplayer, and a premium dark-themed UI — all rendered programmatically with zero external assets.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.1+-green?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

### 🎮 Two Game Modes
| Mode | Description |
|------|-------------|
| 🤖 **Play vs Bots** | Choose your color, remaining slots filled by smart AI bots |
| 👥 **Play With Friends** | 2-4 players on the same device with custom name entry |

### 🧠 Smart Bot AI
- **Priority-based decision engine** with scored moves:
  - 🔴 **Kill opponent** (score: 100) — Land on enemy tokens
  - 🔓 **Unlock from base** (score: 75) — Release tokens on rolling 6
  - 🏃 **Advance closest to home** (score: 50+) — Push tokens forward
  - 🛡️ **Safety awareness** (bonus: +25) — Prefer safe squares
- Animated "Thinking..." indicator with realistic delay

### ✨ Smooth Animations
- **Token movement** — Lerp-based gliding between cells
- **Dice roll** — Spinning 3D-like animation with easing
- **Captures** — Burst particle explosion effect
- **Home entry** — Golden glow pulse + particles
- **Turn transitions** — Color-coded banner slides from top
- **Idle tokens** — Subtle sinusoidal bob animation
- **Menu background** — Floating colored orbs

### 🎨 Premium UI Design
- Dark navy theme (`#0D1B2A`)
- Neon glow animated title
- Glassmorphism-style buttons and panels
- Crisp colored zones with gradient home columns
- Safe squares marked with ⭐ star icons
- Player HUD with animated active border pulse
- Dice rendered with pip dots (not emoji)
- Turn history log (last 5 moves)

### 📋 Standard Ludo Rules
- Roll **6** to unlock a token from base
- Roll **6** → bonus roll (max 3 consecutive)
- **3 consecutive 6s** → last moved token sent back to base
- Landing on opponent → capture (send to base)
- **Safe squares** protect tokens from capture
- **Stacked tokens** (2+ same color on cell) are safe
- **Exact roll** needed to enter home
- First player to get all 4 tokens home wins!

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/SampathSriramoju/LUDO-GAME-USING-PYGAME.git
cd LUDO-GAME-USING-PYGAME

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

> **Note:** If `pygame` fails to build from source, try `pip install pygame-ce` (community edition with pre-built wheels).

---

## 🗂️ Project Structure

```
LUDO-GAME-USING-PYGAME/
├── main.py              # Game controller & state machine
├── board.py             # Board rendering & coordinate system
├── game_token.py        # Token & Player classes
├── game_bot.py          # Bot AI with priority scoring
├── game_ui.py           # UI components (menus, HUD, buttons)
├── game_animations.py   # Animation system (particles, dice, effects)
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

### Architecture

```
┌─────────────────────────────────────────────┐
│                  main.py                     │
│         (Game Controller / State Machine)    │
│                                              │
│   MENU → SELECT/FRIENDS → GAME → WIN_SCREEN │
├──────────┬───────────┬───────────┬───────────┤
│ board.py │game_token │ game_bot  │ game_ui   │
│ (Board & │ (Token &  │ (Bot AI)  │ (UI       │
│  Coords) │  Player)  │           │Components)│
├──────────┴───────────┴───────────┴───────────┤
│              game_animations.py               │
│    (Particles, Dice, Lerp, Effects, Banner)   │
└───────────────────────────────────────────────┘
```

---

## 🎮 How to Play

### Main Menu
- Click **"🤖 Play vs Bots"** for single-player against AI
- Click **"👥 Play With Friends"** for local multiplayer

### Play vs Bots
1. Select number of players (2–4)
2. Choose your color (Red, Green, Yellow, or Blue)
3. Remaining slots are auto-assigned to Bot players
4. Click **Start Game**

### Play With Friends
1. Select number of players (2–4)
2. Enter each player's name (max 12 characters)
3. Colors are pre-assigned per slot
4. Click **Start Game**
5. Pass the device between turns (2-second turn banner)

### In-Game
- Click **"🎲 Roll Dice"** on your turn
- If multiple tokens can move, **click the token** you want to move
- Tokens with valid moves are highlighted with a pulsing ring
- Watch the HUD panel for turn history and player stats

---

## ⚙️ Technical Details

| Spec | Value |
|------|-------|
| Resolution | 1100 × 750 (windowed) |
| Frame Rate | 60 FPS with delta-time |
| Board Grid | 15 × 15 cells |
| Main Path | 52 cells (clockwise loop) |
| Home Column | 6 cells per color |
| External Assets | **None** — everything drawn with code |

---

## 🎨 Color Palette

| Element | Color | Hex |
|---------|-------|-----|
| Background | Deep Navy | `#0D1B2A` |
| Red Zone | Crimson | `#E63946` |
| Green Zone | Teal | `#2A9D8F` |
| Yellow Zone | Gold | `#E9C46A` |
| Blue Zone | Steel | `#457B9D` |

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest features
- 🔀 Submit pull requests

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👨‍💻 Author

**Sampath Sriramoju**

- GitHub: [@SampathSriramoju](https://github.com/SampathSriramoju)

---

*Built with ❤️ and Python*
