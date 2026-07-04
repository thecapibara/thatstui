"""Matrix Rain – falling green characters (the classic Matrix effect)."""

from __future__ import annotations

import random
from typing import Any


class MatrixRain:
    """Falling green characters – the classic Matrix rain effect.

    Instantiated once; call ``frame(dt_total)`` repeatedly to get
    successive frames as rich-markup strings.
    """

    name = "Matrix Rain"

    def __init__(self, width: int = 60, height: int = 20) -> None:
        self._char_pool: list[str] = (
            [chr(0x30A0 + i) for i in range(96)]  # katakana block
            + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            + list("!@#$%^&*()_+-=[]{}|;:',.<>?/")
        )
        self.resize(width, height)

    def resize(self, width: int, height: int) -> None:
        """Rebuild columns for a new grid size."""
        self.width = max(10, width)
        self.height = max(6, height)
        self.columns = []
        for _ in range(self.width):
            length = random.randint(8, 18)
            trail_chars = [random.choice(self._char_pool) for _ in range(length + 4)]
            self.columns.append({
                "offset": random.random() * (self.height + length),
                "speed": 2.0 + random.random() * 4.0,
                "length": length,
                "chars": trail_chars,
            })

    # ------------------------------------------------------------------
    def frame(self, dt_total: float) -> str:
        """Return a *height* × *width* grid of the current frame.

        Rich markup:
          • ``[bold white]<char>[/]`` → head (brightest character)
          • ``[green]<char>[/]``      → trail (fading green)
          • `` ``                     → empty cell
        """
        lines: list[str] = []
        for r in range(self.height):
            row_chars: list[str] = []
            for c in range(self.width):
                col = self.columns[c]
                cycle = self.height + col["length"]
                raw = (dt_total * col["speed"] + col["offset"]) % cycle
                head_y = int(raw)

                # Head off-screen → column in its reset phase
                if head_y >= self.height:
                    row_chars.append(" ")
                    continue

                trail_top = head_y - col["length"] + 1
                if trail_top <= r <= head_y:
                    idx = r - trail_top
                    ch = col["chars"][idx % len(col["chars"])]
                    if r == head_y:
                        row_chars.append(f"[bold white]{ch}[/]")
                    else:
                        row_chars.append(f"[green]{ch}[/]")
                else:
                    row_chars.append(" ")
            lines.append("".join(row_chars))
        return "\n".join(lines)
