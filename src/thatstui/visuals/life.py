"""Game of Life Visualizer with color heatmap, age tracking, fade-out glow trails, and presets."""

import random
from typing import Final


from rich.text import Text


class GameOfLife:
    """Conway's Game of Life simulation with neon trails and pattern presets."""

    name: Final[str] = "Game of Life"

    def __init__(self) -> None:
        self.WIDTH = 60
        self.HEIGHT = 20
        self._last_dt = 0.0
        self._update_timer = 0.0
        
        # Presets: 0: Random, 1: Glider Gun, 2: Pulsar Oscillators
        self.preset = 0
        
        self.cells: list[list[bool]] = []
        self.age: list[list[int]] = []
        self.glow: list[list[int]] = []
        self.resize(60, 20)

    def resize(self, width: int, height: int) -> None:
        self.WIDTH = max(20, width)
        self.HEIGHT = max(8, height)
        self._load_preset()

    def handle_key(self, key: str) -> None:
        """Switch presets or reset."""
        if key in ("1", "num_1"):
            if self.preset != 0:
                self.preset = 0
                self._load_preset()
        elif key in ("2", "num_2"):
            if self.preset != 1:
                self.preset = 1
                self._load_preset()
        elif key in ("3", "num_3"):
            if self.preset != 2:
                self.preset = 2
                self._load_preset()
        elif key in ("4", "num_4", "r", "к"):
            # Force reset current preset
            self._load_preset()

    def _load_preset(self) -> None:
        W, H = self.WIDTH, self.HEIGHT
        self.cells = [[False for _ in range(W)] for _ in range(H)]
        self.age = [[0 for _ in range(W)] for _ in range(H)]
        self.glow = [[0 for _ in range(W)] for _ in range(H)]

        if self.preset == 0:
            # Random seeding
            for y in range(H):
                for x in range(W):
                    if random.random() < 0.22:
                        self.cells[y][x] = True
                        self.age[y][x] = 1
                        self.glow[y][x] = 4

        elif self.preset == 1:
            # Gosper Glider Gun
            gun_pattern = [
                (5, 1), (5, 2), (6, 1), (6, 2),
                (5, 11), (6, 11), (7, 11),
                (4, 12), (8, 12),
                (3, 13), (9, 13),
                (3, 14), (9, 14),
                (6, 15),
                (4, 16), (8, 16),
                (5, 17), (6, 17), (7, 17),
                (6, 18),
                (3, 21), (4, 21), (5, 21),
                (3, 22), (4, 22), (5, 22),
                (2, 23), (6, 23),
                (1, 25), (2, 25), (6, 25), (7, 25),
                (3, 35), (4, 35), (3, 36), (4, 36)
            ]
            # Center the gun if possible
            start_y = max(1, H // 2 - 6)
            start_x = max(1, W // 2 - 20)
            for dy, dx in gun_pattern:
                y, x = start_y + dy, start_x + dx
                if 0 <= y < H and 0 <= x < W:
                    self.cells[y][x] = True
                    self.age[y][x] = 1
                    self.glow[y][x] = 4

        elif self.preset == 2:
            # Pulsar Oscillators
            cx, cy = W // 2, H // 2
            offsets = []
            for idx in [2, 3, 4]:
                for idy in [1, 6]:
                    offsets.extend([
                        (idx, idy), (-idx, idy), (idx, -idy), (-idx, -idy),
                        (idy, idx), (idy, -idx), (-idy, idx), (-idy, -idx)
                    ])
            for dy, dx in offsets:
                y, x = cy + dy, cx + dx
                if 0 <= y < H and 0 <= x < W:
                    self.cells[y][x] = True
                    self.age[y][x] = 1
                    self.glow[y][x] = 4

    def frame(self, dt_total: float) -> Text:
        dt = dt_total - self._last_dt
        self._last_dt = dt_total

        # Run simulation updates every 0.12 seconds
        self._update_timer += dt
        if self._update_timer >= 0.12:
            self._update_timer = 0.0
            self._tick_game_of_life()

        W, H = self.WIDTH, self.HEIGHT
        text = Text()

        for y in range(H):
            row_chars = []
            row_colors = []
            for x in range(W):
                # Determine character and color based on state
                is_alive = self.cells[y][x]
                cell_age = self.age[y][x]
                cell_glow = self.glow[y][x]

                if is_alive:
                    if cell_age == 1:
                        char, color = "*", "#ffffff"  # Newborn: bright white
                    elif cell_age < 5:
                        char, color = "o", "#00ffff"  # Young: neon cyan
                    else:
                        char, color = "█", "#00ff66"  # Mature: neon green
                else:
                    if cell_glow == 4:
                        char, color = "x", "#ff00ff"  # Fade 1: magenta
                    elif cell_glow == 3:
                        char, color = "+", "#880088"  # Fade 2: dark purple
                    elif cell_glow == 2:
                        char, color = ".", "#660022"  # Fade 3: deep red/brown
                    elif cell_glow == 1:
                        char, color = ".", "#2b0011"  # Fade 4: dim tail
                    else:
                        char, color = " ", None

                row_chars.append(char)
                row_colors.append(color)

            line = Text("".join(row_chars))
            
            # Apply styles to segments
            current_color = None
            start_x = -1
            for x in range(W):
                color = row_colors[x]
                if color != current_color:
                    if current_color is not None and start_x != -1:
                        line.stylize(current_color, start_x, x)
                    current_color = color
                    start_x = x if color is not None else -1
            if current_color is not None and start_x != -1:
                line.stylize(current_color, start_x, W)
                
            text.append(line)
            if y < H - 1:
                text.append("\n")

        # Add top bar menu
        presets = ["Random", "Gosper Gun", "Pulsar Oscillators"]
        presets_uk = ["Хаос", "Планерна гармата", "Осцилятори"]
        
        top_bar = Text()
        for idx in range(3):
            label = f"{presets[idx]}/{presets_uk[idx]}"
            if idx == self.preset:
                top_bar.append(f"▶ {label} ◀", style="bold yellow")
            else:
                top_bar.append(f"{idx+1}: {label}", style="dim")
            top_bar.append("  |  ", style="dim")
        top_bar.append("4/R: Reset/Скидання", style="dim")
        
        # Center the top bar on the first row
        padding = (W - len(top_bar)) // 2
        if padding > 0:
            centered_top_bar = Text(" " * padding) + top_bar + Text(" " * padding)
        else:
            centered_top_bar = top_bar

        lines_text = text.split("\n")
        lines_text[0] = centered_top_bar
        
        final_text = Text()
        for i, line in enumerate(lines_text):
            final_text.append(line)
            if i < len(lines_text) - 1:
                final_text.append("\n")

        return final_text

    def _tick_game_of_life(self) -> None:
        W, H = self.WIDTH, self.HEIGHT
        next_cells = [[False for _ in range(W)] for _ in range(H)]
        
        # Conway rules
        for y in range(H):
            for x in range(W):
                # Count neighbors wrapping around edges
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        ny = (y + dy + H) % H
                        nx = (x + dx + W) % W
                        if self.cells[ny][nx]:
                            neighbors += 1

                is_alive = self.cells[y][x]
                if is_alive:
                    if neighbors in (2, 3):
                        next_cells[y][x] = True
                        self.age[y][x] += 1
                        self.glow[y][x] = 4
                    else:
                        next_cells[y][x] = False
                        self.age[y][x] = 0
                else:
                    if neighbors == 3:
                        next_cells[y][x] = True
                        self.age[y][x] = 1
                        self.glow[y][x] = 4
                    else:
                        next_cells[y][x] = False
                        self.age[y][x] = 0
                        self.glow[y][x] = max(0, self.glow[y][x] - 1)

        self.cells = next_cells
