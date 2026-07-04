"""Fractal Tree Visualizer with wind sway, growth animation, and multiple tree types.

Uses rich.text.Text for rendering to avoid escaping bugs with backslashes.
"""

import math
import random
from typing import Final
from rich.text import Text


class FractalTree:
    """A recursive fractal tree rendering with wind sway and falling particles."""

    name: Final[str] = "Fractal Tree"

    def __init__(self) -> None:
        self.WIDTH = 60
        self.HEIGHT = 20
        self._last_dt = 0.0
        
        # 0: Sakura, 1: Apple, 2: Oak, 3: Pine
        self.tree_type = 0
        self.growth = 0.0
        self.particles: list[dict] = []
        self.resize(60, 20)

    def resize(self, width: int, height: int) -> None:
        self.WIDTH = max(20, width)
        self.HEIGHT = max(8, height)
        self.particles = []

    def handle_key(self, key: str) -> None:
        """Switch tree type when 1, 2, 3 or 4 is pressed."""
        if key in ("1", "num_1"):
            if self.tree_type != 0:
                self.tree_type = 0
                self.growth = 0.0
        elif key in ("2", "num_2"):
            if self.tree_type != 1:
                self.tree_type = 1
                self.growth = 0.0
        elif key in ("3", "num_3"):
            if self.tree_type != 2:
                self.tree_type = 2
                self.growth = 0.0
        elif key in ("4", "num_4"):
            if self.tree_type != 3:
                self.tree_type = 3
                self.growth = 0.0

    def frame(self, dt_total: float) -> Text:
        dt = dt_total - self._last_dt
        self._last_dt = dt_total

        # Update growth factor (fully grown in 1.2 seconds)
        if self.growth < 1.0:
            self.growth = min(1.0, self.growth + dt / 1.2)

        W, H = self.WIDTH, self.HEIGHT
        grid = [[" " for _ in range(W)] for _ in range(H)]
        color_grid: list[list[str | None]] = [[None for _ in range(W)] for _ in range(H)]

        # Ground / Grass
        for x in range(W):
            grid[H - 1][x] = "░"
            color_grid[H - 1][x] = "green" if self.tree_type != 2 else "yellow"

        # Calculate wind sway using a sine wave
        sway = math.sin(dt_total * 1.8) * 0.07

        # Draw recursive tree
        # Initial branch length based on height
        initial_length = float(H) * 0.28 * self.growth
        x_start = float(W // 2)
        y_start = float(H - 2)
        max_depth = 5 if self.tree_type != 3 else 6

        # Draw a thicker trunk base to make it look sturdy and realistic
        trunk_base_y = int(y_start)
        for ty in range(trunk_base_y - 2, trunk_base_y + 1):
            if 0 <= ty < H - 1:
                # Triple width trunk base
                for tx in [int(x_start) - 1, int(x_start), int(x_start) + 1]:
                    if 0 <= tx < W:
                        grid[ty][tx] = "┃" if tx == int(x_start) else "│"
                        color_grid[ty][tx] = "yellow"

        # Draw the tree structure recursively
        leaf_coords: list[tuple[float, float]] = []
        self._draw_branch(grid, color_grid, x_start, y_start - 2, initial_length, 0.0, max_depth, max_depth, sway, leaf_coords)

        # Spawn new falling particles at leaf tips occasionally
        if self.growth >= 0.8 and leaf_coords:
            for lx, ly in leaf_coords:
                if random.random() < 0.02:  # small chance per leaf tip
                    if self.tree_type == 0:
                        char = random.choice(["*", "o", "."])
                        color = "magenta"
                    elif self.tree_type == 1:
                        char = random.choice(["@", "o"]) if random.random() < 0.25 else "o"
                        color = "red" if char == "@" else "green"
                    elif self.tree_type == 2:
                        char = random.choice(["*", "o"])
                        color = random.choice(["yellow", "red"])  # Orange is mapped to yellow/red
                    else:  # Pine (falling pine cones or snow)
                        char = "*" if random.random() < 0.85 else "%"
                        color = "white" if char == "*" else "yellow"

                    self.particles.append({
                        "x": lx,
                        "y": ly,
                        "vx": random.uniform(-0.8, 0.8),
                        "vy": random.uniform(1.5, 3.0),
                        "char": char,
                        "color": color,
                        "sway_offset": random.uniform(0, 10)
                    })

        # Update and draw particles
        next_particles = []
        for p in self.particles:
            p["x"] += p["vx"] * dt + math.sin(dt_total * 2.5 + p["sway_offset"]) * 0.08
            p["y"] += p["vy"] * dt
            
            px, py = int(round(p["x"])), int(p["y"])
            if 0 <= px < W and 0 <= py < H - 1:
                # Only overwrite empty spaces to avoid drawing over branches
                if grid[py][px] == " ":
                    grid[py][px] = p["char"]
                    color_grid[py][px] = p["color"]
                next_particles.append(p)
        self.particles = next_particles

        # Build lines using rich.text.Text to avoid any markup escaping bugs
        text = Text()
        for y in range(H):
            line_str = "".join(grid[y])
            line = Text(line_str)
            
            # Apply styles to color segments
            current_color = None
            start_x = -1
            for x in range(W):
                color = color_grid[y][x]
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

        # Overlay the top menu selection bar directly onto row 0
        names = ["Sakura", "Apple Tree", "Autumn Oak", "Pine"]
        names_uk = ["Сакура", "Яблуня", "Осінній дуб", "Сосна"]
        
        top_bar = Text()
        for idx in range(4):
            label = f"{names[idx]}/{names_uk[idx]}"
            if idx == self.tree_type:
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
            
        # Replace the first line of Text with centered_top_bar
        # Text object contains lines split by '\n', we can slice or build it cleanly.
        # But even simpler: let's build the final text object by prepending the centered top bar!
        # First we remove the first line of 'text'.
        lines_text = text.split("\n")
        lines_text[0] = centered_top_bar
        
        final_text = Text()
        for i, line in enumerate(lines_text):
            final_text.append(line)
            if i < len(lines_text) - 1:
                final_text.append("\n")

        return final_text

    def _draw_branch(
        self,
        grid: list[list[str]],
        color_grid: list[list[str | None]],
        x: float,
        y: float,
        length: float,
        angle: float,
        depth: int,
        max_depth: int,
        sway: float,
        leaf_coords: list[tuple[float, float]]
    ) -> None:
        if depth == 0 or length < 1.0:
            lx, ly = int(round(x)), int(round(y))
            W, H = self.WIDTH, self.HEIGHT
            if 0 <= lx < W and 0 <= ly < H - 1:
                leaf_coords.append((x, y))
                if self.tree_type == 0:  # Sakura (magenta/pink)
                    grid[ly][lx] = "*" if random.random() < 0.4 else "o"
                    color_grid[ly][lx] = "magenta"
                elif self.tree_type == 1:  # Apple Tree (green with red apples)
                    if random.random() < 0.25:
                        grid[ly][lx] = "@"
                        color_grid[ly][lx] = "red"
                    else:
                        grid[ly][lx] = "o"
                        color_grid[ly][lx] = "green"
                elif self.tree_type == 2:  # Autumn Oak (red/yellow)
                    grid[ly][lx] = "*"
                    color_grid[ly][lx] = random.choice(["yellow", "red"])
                elif self.tree_type == 3:  # Pine (green needles)
                    grid[ly][lx] = "▲" if random.random() < 0.5 else "*"
                    color_grid[ly][lx] = "green"
            return

        # End point calculation
        x_end = x + length * math.sin(angle)
        y_end = y - length * math.cos(angle)

        x1, y1 = int(round(x)), int(round(y))
        x2, y2 = int(round(x_end)), int(round(y_end))

        # Set branch colors (yellow is brown-ish, green for pine)
        if self.tree_type == 3:  # Pine
            color = "green" if depth < max_depth - 1 else "yellow"
        else:
            color = "yellow" if depth < max_depth - 1 else "white"

        self._draw_line(grid, color_grid, x1, y1, x2, y2, ("─", "│", "/", "\\"), color)

        # Recurse with wind sway (tips sway more than base)
        branch_sway = sway * (max_depth - depth + 1) * 0.1

        # Use narrower split angles to make branches more vertical
        # This aligns better with tall terminal characters and looks much smoother
        if self.tree_type == 3:  # Pine symmetric side branching
            self._draw_branch(grid, color_grid, x_end, y_end, length * 0.72, angle + branch_sway, depth - 1, max_depth, sway, leaf_coords)
            self._draw_branch(grid, color_grid, x_end, y_end, length * 0.42, angle - 0.75 + branch_sway, depth - 1, max_depth, sway, leaf_coords)
            self._draw_branch(grid, color_grid, x_end, y_end, length * 0.42, angle + 0.75 + branch_sway, depth - 1, max_depth, sway, leaf_coords)
        else:  # Standard split branching
            num_branches = 3 if self.tree_type == 2 else 2
            if num_branches == 2:
                self._draw_branch(grid, color_grid, x_end, y_end, length * 0.76, angle - 0.28 + branch_sway, depth - 1, max_depth, sway, leaf_coords)
                self._draw_branch(grid, color_grid, x_end, y_end, length * 0.76, angle + 0.28 + branch_sway, depth - 1, max_depth, sway, leaf_coords)
            else:  # Oak split
                self._draw_branch(grid, color_grid, x_end, y_end, length * 0.72, angle - 0.38 + branch_sway, depth - 1, max_depth, sway, leaf_coords)
                self._draw_branch(grid, color_grid, x_end, y_end, length * 0.65, angle + branch_sway, depth - 1, max_depth, sway, leaf_coords)
                self._draw_branch(grid, color_grid, x_end, y_end, length * 0.72, angle + 0.38 + branch_sway, depth - 1, max_depth, sway, leaf_coords)

    def _draw_line(
        self,
        grid: list[list[str]],
        color_grid: list[list[str | None]],
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        char_set: tuple[str, str, str, str],
        color: str
    ) -> None:
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        # Character selection based on slope
        if dx > 2 * dy:
            ch = char_set[0]
        elif dy > 2 * dx:
            ch = char_set[1]
        elif (sx > 0 and sy < 0) or (sx < 0 and sy > 0):
            ch = char_set[2]
        else:
            ch = char_set[3]

        x, y = x1, y1
        W, H = self.WIDTH, self.HEIGHT
        while True:
            if 0 <= x < W and 0 <= y < H - 1:
                grid[y][x] = ch
                color_grid[y][x] = color
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
