"""Fractal Tree Visualizer with wind sway, growth animation, and multiple tree types.

Uses rich.text.Text for rendering to avoid escaping bugs with backslashes.
Features a lush, full canopy and a tapered trunk for a natural look.
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

        # Tapered trunk parameters
        x_start = float(W // 2)
        y_start = float(H - 2)
        trunk_height = max(3, int(H * 0.22))
        
        # Draw tapered trunk (sturdy at the bottom, tapering upwards)
        trunk_top_y = int(y_start) - trunk_height
        for ty in range(trunk_top_y, int(y_start) + 1):
            if 0 <= ty < H - 1:
                # Width depends on height to create a taper
                dist_from_bottom = int(y_start) - ty
                if dist_from_bottom <= 1:
                    # Very bottom: 5 characters wide
                    cols = [int(x_start) - 2, int(x_start) - 1, int(x_start), int(x_start) + 1, int(x_start) + 2]
                elif dist_from_bottom <= 3:
                    # Middle trunk: 3 characters wide
                    cols = [int(x_start) - 1, int(x_start), int(x_start) + 1]
                else:
                    # Upper trunk: 1 character wide
                    cols = [int(x_start)]

                for tx in cols:
                    if 0 <= tx < W:
                        grid[ty][tx] = "┃" if tx == int(x_start) else "│"
                        color_grid[ty][tx] = "yellow"

        # Draw the tree structure recursively starting from the top of the trunk
        initial_length = float(H - trunk_height - 3) * self.growth
        leaf_coords: list[tuple[float, float]] = []
        max_depth = 5 if self.tree_type != 3 else 6
        
        # We start the recursion
        self._draw_branch(grid, color_grid, x_start, float(trunk_top_y), initial_length, 0.0, max_depth, max_depth, sway, leaf_coords)

        # Spawn new falling particles at leaf tips occasionally
        if self.growth >= 0.8 and leaf_coords:
            for lx, ly in leaf_coords:
                if random.random() < 0.025:  # small chance per leaf tip
                    if self.tree_type == 0:
                        char = random.choice(["*", "o", "."])
                        color = "magenta"
                    elif self.tree_type == 1:
                        char = random.choice(["@", "o"]) if random.random() < 0.25 else "o"
                        color = "red" if char == "@" else "green"
                    elif self.tree_type == 2:
                        char = random.choice(["*", "o"])
                        color = random.choice(["yellow", "red"])
                    else:  # Pine
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

        # Build lines using rich.text.Text
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
        # Draw leaves not just at depth == 0, but as a cluster for a full, lush canopy!
        if depth <= 2:
            lx, ly = int(round(x)), int(round(y))
            leaf_coords.append((x, y))
            
            # Spawn a lush cluster of leaves around the branch end
            # More leaves at the outer tips (depth 0 has most leaves)
            num_leaves = 3 if depth == 2 else (5 if depth == 1 else 7)
            W, H = self.WIDTH, self.HEIGHT
            
            for _ in range(num_leaves):
                # Spread radius
                rx = int(round(x + random.uniform(-1.8, 1.8)))
                ry = int(round(y + random.uniform(-1.2, 1.2)))
                
                if 0 <= rx < W and 0 <= ry < H - 1:
                    # Do not overwrite the trunk/wood branches
                    if grid[ry][rx] == " " or grid[ry][rx] in ("*", "o", "."):
                        if self.tree_type == 0:  # Sakura (magenta/pink)
                            grid[ry][rx] = "*" if random.random() < 0.4 else "o"
                            color_grid[ry][rx] = "magenta"
                        elif self.tree_type == 1:  # Apple Tree (green with red apples)
                            if random.random() < 0.22:
                                grid[ry][rx] = "@"
                                color_grid[ry][rx] = "red"
                            else:
                                grid[ry][rx] = "o"
                                color_grid[ry][rx] = "green"
                        elif self.tree_type == 2:  # Autumn Oak (red/yellow/orange)
                            grid[ry][rx] = "*" if random.random() < 0.6 else "o"
                            color_grid[ry][rx] = random.choice(["yellow", "red"])
                        elif self.tree_type == 3:  # Pine (green needles)
                            grid[ry][rx] = "▲" if random.random() < 0.6 else "*"
                            color_grid[ry][rx] = "green"
            
            if depth == 0:
                return

        # End point calculation
        x_end = x + length * math.sin(angle)
        y_end = y - length * math.cos(angle)

        x1, y1 = int(round(x)), int(round(y))
        x2, y2 = int(round(x_end)), int(round(y_end))

        # Set branch colors (thicker main branches, yellow is brown-ish, green for pine)
        if self.tree_type == 3:  # Pine
            color = "green" if depth < max_depth - 1 else "yellow"
        else:
            color = "yellow" if depth < max_depth - 1 else "white"

        # Draw branch line
        self._draw_line(grid, color_grid, x1, y1, x2, y2, ("─", "│", "/", "\\"), color)

        # Recurse with wind sway
        branch_sway = sway * (max_depth - depth + 1) * 0.08

        # Branching parameters
        if self.tree_type == 3:  # Pine symmetric side branching
            self._draw_branch(grid, color_grid, x_end, y_end, length * 0.72, angle + branch_sway, depth - 1, max_depth, sway, leaf_coords)
            self._draw_branch(grid, color_grid, x_end, y_end, length * 0.42, angle - 0.72 + branch_sway, depth - 1, max_depth, sway, leaf_coords)
            self._draw_branch(grid, color_grid, x_end, y_end, length * 0.42, angle + 0.72 + branch_sway, depth - 1, max_depth, sway, leaf_coords)
        else:  # Standard split branching
            num_branches = 3 if self.tree_type == 2 else 2
            if num_branches == 2:
                # Wide first split, narrower subsequent splits
                split_angle = 0.38 if depth == max_depth else 0.26
                self._draw_branch(grid, color_grid, x_end, y_end, length * 0.76, angle - split_angle + branch_sway, depth - 1, max_depth, sway, leaf_coords)
                self._draw_branch(grid, color_grid, x_end, y_end, length * 0.76, angle + split_angle + branch_sway, depth - 1, max_depth, sway, leaf_coords)
            else:  # Oak split into 3 limbs
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
                # Do not draw over thicker trunk
                if grid[y][x] not in ("┃", "│"):
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
