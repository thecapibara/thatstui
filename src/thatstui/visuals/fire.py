"""Doom Fire Visualizer with interactive wind and intensity controls."""

import random
from typing import Final


from rich.text import Text


class FireShow:
    """A terminal fire animation using the classic Doom Fire propagation algorithm."""

    name: Final[str] = "Fire Show"

    # Color palette (HEX colors from dark/cool to white hot)
    PALETTE: Final[list[tuple[str, str]]] = [
        # (character, color_tag)
        (" ", ""),                # 0
        (".", "blue"),           # 1
        (".", "#3c1145"),        # 2
        (".", "#4a0f3d"),        # 3
        (",", "#670b32"),        # 4
        (",", "#800827"),        # 5
        ("*", "#9c0b1d"),        # 6
        ("*", "#b61917"),        # 7
        ("o", "#cb2c1a"),        # 8
        ("o", "#de441d"),        # 9
        ("x", "#ed5b21"),        # 10
        ("x", "#f87523"),        # 11
        ("%", "#ff9024"),        # 12
        ("%", "#ffa927"),        # 13
        ("#", "#ffc227"),        # 14
        ("#", "#ffdb27"),        # 15
        ("▓", "#fff23a"),        # 16
        ("█", "#ffffff"),        # 17
    ]

    def __init__(self) -> None:
        self.WIDTH = 60
        self.HEIGHT = 20
        self._last_dt = 0.0
        
        # 0: Calm, 1: Wind Left, 2: Wind Right, 3: Wildfire
        self.mode = 0
        self.fire_grid: list[list[int]] = []
        self.resize(60, 20)

    def resize(self, width: int, height: int) -> None:
        self.WIDTH = max(20, width)
        self.HEIGHT = max(8, height)
        
        # Initialize grid with 0 (empty fire)
        self.fire_grid = [[0 for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]
        
        # Set bottom row to maximum heat (len(PALETTE) - 1)
        max_heat = len(self.PALETTE) - 1
        for x in range(self.WIDTH):
            self.fire_grid[self.HEIGHT - 1][x] = max_heat

    def handle_key(self, key: str) -> None:
        """Switch fire modes."""
        if key in ("1", "num_1"):
            self.mode = 0
        elif key in ("2", "num_2"):
            self.mode = 1
        elif key in ("3", "num_3"):
            self.mode = 2
        elif key in ("4", "num_4"):
            self.mode = 3

    def frame(self, dt_total: float) -> Text:
        # Limit frame rate / compute updates
        self._spread_fire()

        W, H = self.WIDTH, self.HEIGHT
        text = Text()

        # Render rows (excluding the bottom permanent heat source)
        for y in range(H - 1):
            row_chars = []
            row_colors = []
            for x in range(W):
                heat = self.fire_grid[y][x]
                char, color = self.PALETTE[heat]
                row_chars.append(char)
                row_colors.append(color if color else None)
                
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
            text.append("\n")

        # Add the bottom heat source row styled in pure white-hot
        bottom_row = Text("█" * W, style="#ffffff")
        text.append(bottom_row)

        # Center top menu selection
        modes = ["Calm", "Wind Left", "Wind Right", "Wildfire"]
        modes_uk = ["Штиль", "Вітер вліво", "Вітер вправо", "Буря"]
        
        top_bar = Text()
        for idx in range(4):
            label = f"{modes[idx]}/{modes_uk[idx]}"
            if idx == self.mode:
                top_bar.append(f"▶ {label} ◀", style="bold yellow")
            else:
                top_bar.append(f"{idx+1}: {label}", style="dim")
            if idx < 3:
                top_bar.append("  |  ", style="dim")
                
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

    def _spread_fire(self) -> None:
        W, H = self.WIDTH, self.HEIGHT
        max_heat = len(self.PALETTE) - 1

        # Adjust bottom row heat dynamically for wildfire turbulence
        if self.mode == 3:  # Wildfire turbulence
            for x in range(W):
                self.fire_grid[H - 1][x] = random.choice([max_heat, max_heat - 1, max_heat - 2])
        else:
            for x in range(W):
                self.fire_grid[H - 1][x] = max_heat

        # Propagate heat upwards
        for y in range(1, H):
            for x in range(W):
                heat = self.fire_grid[y][x]
                if heat == 0:
                    self.fire_grid[y - 1][x] = 0
                else:
                    # Decay and horizontal shift parameters based on mode
                    if self.mode == 0:    # Calm: small random sway
                        decay = random.randint(0, 2)
                        shift = decay - 1  # -1, 0, 1
                    elif self.mode == 1:  # Wind Left
                        decay = random.randint(0, 2)
                        shift = -decay     # shift left
                    elif self.mode == 2:  # Wind Right
                        decay = random.randint(0, 2)
                        shift = decay      # shift right
                    else:                 # Wildfire: faster decay and higher chaos
                        decay = random.randint(0, 3)
                        shift = random.randint(-2, 2)

                    # Compute target coordinate
                    dst_x = (x + shift + W) % W
                    dst_y = y - 1
                    
                    # Compute new heat value
                    loss = decay & 1
                    if self.mode == 3 and random.random() < 0.2:
                        loss += 1  # additional decay for flame height variation in wildfire
                        
                    new_heat = max(0, heat - loss)
                    self.fire_grid[dst_y][dst_x] = new_heat
