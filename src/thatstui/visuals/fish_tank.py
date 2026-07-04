"""Fish Tank — looping aquarium animation for thatstui."""

from __future__ import annotations

import math
import random
from typing import Final


class FishTank:
    """A fish tank terminal animation with fish, bubbles, seaweed, and sand.

    Rendered by AnimationScreen in hub.py calling frame(dt_total) every 0.2 s.
    The returned string supports rich markup (colour tags) and is passed to a
    textual ``Static`` widget.
    """

    name: Final[str] = "Fish Tank"

    WIDTH: int = 60
    HEIGHT: int = 20

    FISH_COLORS: Final[list[str]] = [
        "cyan",
        "yellow",
        "magenta",
        "green",
        "red",
        "blue",
        "white",
    ]

    def __init__(self) -> None:
        self._last_dt: float = 0.0
        self.resize(60, 20)

    def resize(self, width: int, height: int) -> None:
        """Rebuild entities for a new grid size."""
        self.WIDTH = max(20, width)
        self.HEIGHT = max(8, height)
        # ---- fish -----------------------------------------------------------
        self.fish: list[dict] = []
        for _ in range(8):
            direction = random.choice([-1, 1])
            species = "><>" if direction == 1 else "<><"
            self.fish.append({
                "x": random.uniform(0, self.WIDTH - 3),
                "y": random.uniform(1, self.HEIGHT - 4),
                "direction": direction,
                "speed": random.uniform(8, 20),
                "color": random.choice(self.FISH_COLORS),
                "species": species,
            })
        # ---- bubbles --------------------------------------------------------
        self.bubbles: list[dict] = []
        for _ in range(15):
            self.bubbles.append({
                "x": random.uniform(0, self.WIDTH),
                "y": random.uniform(1, self.HEIGHT - 3),
                "rise_speed": random.uniform(3, 8),
            })
        # ---- seaweed stalks -------------------------------------------------
        self.seaweed: list[dict] = []
        spread = max(1, self.WIDTH // 8)
        for i in range(7):
            self.seaweed.append({
                "x": 4 + i * spread,
                "height": random.randint(4, 8),
            })

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def frame(self, dt_total: float) -> str:
        """Return a full aquarium frame as a single multi-line string.

        Parameters
        ----------
        dt_total:
            Total elapsed time in seconds (used for sway animation and to
            compute per-frame delta for movement).
        """
        dt = dt_total - self._last_dt
        self._last_dt = dt_total

        W, H = self.WIDTH, self.HEIGHT

        # ---- build plain-character grid ------------------------------------
        grid = [[" " for _ in range(W)] for _ in range(H)]

        self._draw_surface(grid)
        self._draw_sand(grid)
        self._draw_seaweed(grid, dt_total)
        self._update_bubbles(grid, dt)
        fish_spans = self._update_fish(grid, dt)

        # ---- apply rich markup (fish colours) ------------------------------
        lines: list[str] = []
        for y in range(H):
            raw = "".join(grid[y])
            spans = sorted(
                (s for s in fish_spans if s[0] == y),
                key=lambda s: s[1],
                reverse=True,
            )
            for _, x_start, x_end, colour in spans:
                raw = f"{raw[:x_start]}[{colour}]{raw[x_start:x_end]}[/]{raw[x_end:]}"
            lines.append(raw)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _draw_surface(grid: list[list[str]]) -> None:
        """Water surface — row 0."""
        for x in range(len(grid[0])):
            grid[0][x] = "~"

    @staticmethod
    def _draw_sand(grid: list[list[str]]) -> None:
        """Sand bottom — last three rows."""
        W, H = len(grid[0]), len(grid)
        for y in range(H - 3, H):
            for x in range(W):
                grid[y][x] = "░"

    def _draw_seaweed(self, grid: list[list[str]], dt_total: float) -> None:
        """Swaying seaweed anchored on the sand."""
        W, H = len(grid[0]), len(grid)
        for sw in self.seaweed:
            sway = math.sin(dt_total * 1.5 + sw["x"] * 0.3)
            for i in range(sw["height"]):
                y = H - 4 - i  # grow up from sand
                if y < 1:
                    break
                # tip sways more than base
                offset = int(sway * (i / sw["height"]) * 1.5)
                col = sw["x"] + offset
                if 0 <= col < W:
                    ch = "▓" if i == 0 else "│"
                    grid[y][col] = ch

    def _update_bubbles(self, grid: list[list[str]], dt: float) -> None:
        """Rise bubbles; respawn when they pop at the surface."""
        W, H = len(grid[0]), len(grid)
        for b in self.bubbles:
            b["y"] -= b["rise_speed"] * dt
            if b["y"] < 1:
                b["y"] = float(H - 3)
                b["x"] = random.uniform(0, W)
            bx, by = int(b["x"]), int(b["y"])
            if 0 <= bx < W and 0 <= by < H:
                if grid[by][bx] == " ":
                    grid[by][bx] = "o"

    def _update_fish(
        self,
        grid: list[list[str]],
        dt: float,
    ) -> list[tuple[int, int, int, str]]:
        """Move fish, bounce off walls, record colour spans.

        Returns a list of ``(y, x_start, x_end, colour)`` tuples for
        post-processing into rich markup.
        """
        W, H = len(grid[0]), len(grid)
        spans: list[tuple[int, int, int, str]] = []

        for f in self.fish:
            f["x"] += f["direction"] * f["speed"] * dt
            species_len = len(f["species"])

            # bounce off walls
            if f["x"] < 0:
                f["x"] = 0.0
                f["direction"] = 1
                f["species"] = "><>"
            elif f["x"] > W - species_len:
                f["x"] = float(W - species_len)
                f["direction"] = -1
                f["species"] = "<><"

            fx, fy = int(round(f["x"])), int(f["y"])
            for i, ch in enumerate(f["species"]):
                col = fx + i
                if 0 <= col < W and 0 <= fy < H:
                    grid[fy][col] = ch

            spans.append((fy, fx, fx + species_len, f["color"]))

        return spans
