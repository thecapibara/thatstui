# 🎮 thatstui

> **A terminal idle-games and visual animations suite**
> 
> *Developed by JustGL*

`thatstui` is a collection of incremental, idle, and simulation games playable entirely in your terminal. It features stateful games, smooth visuals, customizable settings, and persistent offline progress.

---

## 🚀 Features

- **Multi-Game Suite**: 7 incremental/idle games and 5 smooth visualizers.
- **Stateful Tamagotchi**: A living ASCII pet that accumulates Care Points (CP) and can be upgraded to survive long offline periods.
- **Offline catch-up**: Calculations run in bulk when you return to your games.
- **Cross-platform**: Native installation support for Linux, macOS, and Windows.
- **Language support**: Play in English or Ukrainian.

---

## 🕹️ Games & Visuals

### 🎮 Games
- 🐜 **Ant Colony**: Build and manage an ant empire.
- ⛏️ **Deep Mine**: Direct workers to extract resources from the depths.
- 🌲 **Forest**: Grow and harvest trees in a simulated woodland.
- 🏭 **Factory**: Build production lines and automate manufacturing.
- 🚀 **Space Colony**: Manage population, life support, and rocket launches.
- ⚔️ **Idle Hero**: Upgrade stats and defeat monsters automatically.
- 📈 **Stock Market**: Buy and sell shares to maximize profits.
- 🐾 **Tamagotchi**: Care for your pet (Pixel), earn **Care Points (CP)**, and purchase upgrades:
  - **Auto-Feeder**: Slower hunger decay.
  - **Medkit**: Extreme health loss reduction when starving or dirty.
  - **Cozy Bed**: Slower awake energy decay.
  - **Toys**: Slower happiness decay.

### 🎨 Visuals
- 🌧️ **Matrix Rain**: Classic green digital rain effect.
- 🌌 **Starfield**: Smooth 3D space travel particle simulation.
- 🐠 **Fish Tank**: A living virtual aquarium.
- 🌊 **Plasma Waves**: Coloured math-generated sine wave plasma.
- 🐍 **Snake**: Autonomous self-playing snake AI.

---

## 💻 Installation

Choose the installation method for your operating system:

### 🐧 Linux & 🍏 macOS (curl + bash)
Install directly using our setup script:
```bash
curl -fsSL https://raw.githubusercontent.com/thecapibara/thatstui/main/install.sh | bash
```

### 🪟 Windows (PowerShell)
Run this command in PowerShell (as Administrator if needed):
```powershell
iwr -useb https://raw.githubusercontent.com/thecapibara/thatstui/main/install.ps1 | iex
```

### 📦 Manual Installation
If you have cloned the repository locally:
```bash
# Via pipx (recommended)
pipx install .

# Or via pip
pip install --user .
```

---

## ⌨️ General Controls

| Key | Action |
| --- | --- |
| `↑` / `↓` | Navigate menu / options |
| `Enter` | Select / Launch |
| `L` | Toggle language (English / Українська) |
| `Esc` | Go back to main hub / Save state |
| `Q` | Quit app |

### 🐾 Tamagotchi Controls
- `f` — Feed (+Hunger, +CP)
- `p` — Play (+Happiness, -Energy, +CP)
- `c` — Clean (+Cleanliness, +CP)
- `s` — Toggle sleep (recovers Energy)
- `u` — Open/Close Upgrades Shop (buy upgrades using keys `1`, `2`, `3`, `4`)

---

## 🛠️ Local Development

To run and edit the project locally:

1. Clone this repository:
   ```bash
   git clone https://github.com/thecapibara/thatstui.git
   cd thatstui
   ```
2. Set up virtual environment and install in editable mode:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
3. Run the development build:
   ```bash
   thatstui
   ```
