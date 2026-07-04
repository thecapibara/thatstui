"""Starfield animation — 3D starfield with perspective projection.

Each star has a 3D-ish position (x, y, z).  The z-coordinate decreases over
time (star moves toward the viewer).  Perspective projection maps each star
onto a 60×20 terminal grid.  Closer stars are brighter/larger.
"""

from __future__ import annotations

import random
from typing import List, Tuple


class Starfield:
    """Pure looping 3D starfield animation.

    Call ``frame(dt_total)`` each tick to get a Rich-markup string that can
    be displayed in a textual ``Static`` widget.
    """

    name = "Starfield"

    WIDTH = 60
    HEIGHT = 20

    def __init__(self, n_stars: int = 80) -> None:
        self.focal_length = 3.0
        self.z_far = 30.0
        self.z_near = 0.5
        self.respawn_threshold = 0.5
        self.stars: List[Tuple[float, float, float, float, float]] = []
        self._n_stars = n_stars
        self.resize(self.WIDTH, self.HEIGHT)

    def resize(self, width: int, height: int) -> None:
        """Adapt to a new grid size."""
        self.WIDTH = max(20, width)
        self.HEIGHT = max(8, height)
        self.cx = self.WIDTH // 2
        self.cy = self.HEIGHT // 2
        self.stars = [self._create_star(0.0) for _ in range(self._n_stars)]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _create_star(current_time: float) -> Tuple[float, float, float, float, float]:
        """Return a star tuple ``(x, y, initial_z, birth_time, speed)``."""
        x = random.uniform(-30.0, 30.0)
        y = random.uniform(-9.0, 9.0)
        initial_z = random.uniform(5.0, 30.0)
        speed = random.uniform(3.0, 8.0)
        return (x, y, initial_z, current_time, speed)

    @staticmethod
    def _markup_for_z(z: float) -> str:
        """Rich-markup string for a star at depth *z* (smaller = closer)."""
        if z < 5.0:
            return "[bold white]\u25cf[/]"       # ●
        if z < 15.0:
            return "[white]\u2022[/]"             # •
        return "[dim white].[/]"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def frame(self, dt_total: float) -> str:
        """Return a ``\\n``-separated string (WIDTH × HEIGHT) with current
        star positions.

        *dt_total* is the total elapsed time (seconds) since the animation
        started — used to advance each star's depth.
        """
        # grid[sy][sx] = smallest z (closest star) at that cell, or None
        grid: List[List[float | None]] = [
            [None for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)
        ]

        for i, (x, y, init_z, birth_time, speed) in enumerate(self.stars):
            z = init_z - speed * (dt_total - birth_time)

            if z < self.respawn_threshold:
                # star has passed the viewer — respawn at far depth
                self.stars[i] = self._create_star(dt_total)
                x, y, init_z, birth_time, speed = self.stars[i]
                z = init_z

            # Perspective projection  (guard against division by zero)
            z_safe = max(0.01, z)
            sx = int(round(self.cx + (x * self.focal_length) / z_safe))
            sy = int(round(self.cy + (y * self.focal_length) / z_safe))

            if 0 <= sx < self.WIDTH and 0 <= sy < self.HEIGHT:
                # Keep the closest (smallest z) star in this cell
                current = grid[sy][sx]
                if current is None or z < current:
                    grid[sy][sx] = z

        # ── build output string ──────────────────────────────────────
        lines: List[str] = []
        for sy in range(self.HEIGHT):
            row: List[str] = []
            for sx in range(self.WIDTH):
                z_val = grid[sy][sx]
                if z_val is not None:
                    row.append(self._markup_for_z(z_val))
                else:
                    row.append(" ")
            lines.append("".join(row))

        return "\n".join(lines)
