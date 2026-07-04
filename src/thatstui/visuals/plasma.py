"""Plasma Waves – smooth flowing plasma effect with coloured sine waves."""

from __future__ import annotations

import math
from typing import Any


class Plasma:
    """Smooth plasma animation using overlapping sine waves.

    Instantiated once; call ``frame(dt_total)`` repeatedly to get
    successive frames as rich-markup strings.
    """

    name = "Plasma Waves"

    def __init__(self, width: int = 80, height: int = 22) -> None:
        self.resize(width, height)

    def resize(self, width: int, height: int) -> None:
        """Store grid dimensions (minimum 20×8) and cache the distance matrix."""
        self.width = max(20, width)
        self.height = max(8, height)
        cx = (self.width - 1) / 2.0
        cy = (self.height - 1) / 2.0
        # Precompute and cache the distances from center for each grid point
        self._dist_matrix = [
            [math.sqrt((x - cx) ** 2 + (y - cy) ** 2) for x in range(self.width)]
            for y in range(self.height)
        ]

    # ------------------------------------------------------------------

    def frame(self, dt_total: float) -> str:
        """Return a *height* × *width* grid of the current plasma frame.

        Rich markup wraps each character individually.
        Optimized by precomputing trigonometric terms and using static styles.
        """
        w = self.width
        h = self.height

        # Precompute the sine values for terms depending only on x, y, and x + y
        sin_x = [math.sin(x * 0.10 + dt_total * 1.5) for x in range(w)]
        sin_y = [math.sin(y * 0.15 + dt_total * 1.2) for y in range(h)]
        sin_xy = [math.sin(xy * 0.08 + dt_total * 0.9) for xy in range(w + h)]

        # Precompute the time-dependent term in the distance sine
        dt_term = dt_total * 2.0

        # Pre-styled representations for the 5 levels (space -> full block)
        # • 0: [blue] [/]
        # • 1: [cyan]░[/]
        # • 2: [green]▒[/]
        # • 3: [yellow]▓[/]
        # • 4: [bold red]█[/]
        STYLED_CHARS = (
            "[blue] [/]",
            "[cyan]░[/]",
            "[green]▒[/]",
            "[yellow]▓[/]",
            "[bold red]█[/]"
        )

        lines: list[str] = []
        for y in range(h):
            row: list[str] = []
            val_y = sin_y[y]
            dist_row = self._dist_matrix[y]
            for x in range(w):
                v = (
                    sin_x[x]
                    + val_y
                    + sin_xy[x + y]
                    + math.sin(dist_row[x] * 0.10 - dt_term)
                )
                # Map v ∈ [-4, 4] → level 0..4
                t = (v + 4.0) * 0.125  # Divide by 8.0
                if t < 0.0:
                    t = 0.0
                elif t > 1.0:
                    t = 1.0
                level = int(t * 4.0)  # 0 to 4
                row.append(STYLED_CHARS[level])
            lines.append("".join(row))

        return "\n".join(lines)
