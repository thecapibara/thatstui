"""Self-playing Snake — the snake moves autonomously, collects apples, grows,
and uses a simple greedy AI to avoid walls and itself."""

from __future__ import annotations

import random
from typing import List, Tuple


class Snake:
    """Autonomous self-playing snake animation.

    No user input needed — the snake moves on its own, chasing apples
    while avoiding walls and its own tail.
    """

    name = "Snake"

    MOVE_INTERVAL: float = 0.15  # seconds between game ticks

    def __init__(self, width: int = 70, height: int = 20) -> None:
        self._last_dt: float = 0.0
        self.resize(width, height)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def resize(self, width: int, height: int) -> None:
        """Configure the playfield and reset the game state."""
        self.width = max(20, width)
        self.height = max(8, height)
        # Snake body: list of (x, y) positions, head first (index 0)
        cx = self.width // 2
        cy = self.height // 2
        self.snake: List[Tuple[int, int]] = [
            (cx - i, cy) for i in range(4)
        ]
        self.direction: Tuple[int, int] = (1, 0)  # heading right
        self.score: int = 0
        self._move_accumulator: float = 0.0
        self._last_dt = 0.0
        self._spawn_apple()

    def frame(self, dt_total: float) -> str:
        """Return a Rich-markup string of the current snake frame.

        Parameters
        ----------
        dt_total:
            Total elapsed time in seconds since the animation started.
            Used to compute delta for smooth, frame-rate-independent
            movement.
        """
        # Delta time (guard against time jumps)
        dt = dt_total - self._last_dt
        self._last_dt = dt_total
        if dt < 0:
            dt = 0.0

        # Accumulate time and advance game ticks
        self._move_accumulator += dt
        while self._move_accumulator >= self.MOVE_INTERVAL:
            self._move_accumulator -= self.MOVE_INTERVAL
            self._tick()

        W, H = self.width, self.height

        # ---- build the character grid ------------------------------------
        grid = [[" " for _ in range(W)] for _ in range(H)]

        # Apple
        ax, ay = self.apple
        grid[ay][ax] = "[bold red]●[/]"

        # Snake body (tail to head so head overwrites apple if needed)
        for i, (sx, sy) in enumerate(self.snake):
            if i == 0:
                grid[sy][sx] = "[bold green]█[/]"
            else:
                grid[sy][sx] = "[green]█[/]"

        # ---- assemble output lines ---------------------------------------
        total_w = W + 2  # inner width + left & right borders

        # Header (centered)
        plain = f"🐍 Snake  |  Score: {self.score}  |  Length: {len(self.snake)}"
        rich_header = (
            f"[bold]🐍 Snake[/]  |  Score: [yellow]{self.score}[/]  |  "
            f"Length: {len(self.snake)}"
        )
        # Note: 🐍 counts as 1 character in len() but takes 2 terminal columns.
        plain_len = len(plain) + 1
        pad = max(0, total_w - plain_len)
        left_pad = pad // 2
        right_pad = pad - left_pad
        header_line = " " * left_pad + rich_header + " " * right_pad

        # Borders
        top_border = "[dim]┌[/]" + "[dim]─[/]" * W + "[dim]┐[/]"
        bottom_border = "[dim]└[/]" + "[dim]─[/]" * W + "[dim]┘[/]"
        border_l = "[dim]│[/]"
        border_r = "[dim]│[/]"

        rows: list[str] = [header_line, top_border]
        for y in range(H):
            row = "".join(grid[y])
            rows.append(border_l + row + border_r)
        rows.append(bottom_border)

        return "\n".join(rows)

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _spawn_apple(self) -> None:
        """Place the apple on a random empty cell."""
        occupied = set(self.snake)
        empty = [
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (x, y) not in occupied
        ]
        if empty:
            self.apple = random.choice(empty)
        else:
            self.apple = (0, 0)  # board full — fallback (unlikely)

    def _ai_direction(self) -> Tuple[int, int]:
        """Greedy safe direction toward the apple.

        Returns a direction ``(dx, dy)`` that avoids walls and the
        snake's own body.  Prefers the direction that minimises
        Manhattan distance to the apple.  Falls back to any safe
        direction, or finally the current direction (which will
        cause a collision + reset).
        """
        head = self.snake[0]
        rev = (-self.direction[0], -self.direction[1])

        candidates: List[Tuple[float, Tuple[int, int]]] = []

        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            if (dx, dy) == rev:
                continue  # can't reverse
            nx, ny = head[0] + dx, head[1] + dy

            # Wall check
            if not (0 <= nx < self.width and 0 <= ny < self.height):
                continue

            # Self check — tail will move away, so exclude it
            if (nx, ny) in self.snake[:-1]:
                continue

            dist = abs(nx - self.apple[0]) + abs(ny - self.apple[1])
            candidates.append((dist, (dx, dy)))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]

        # Totally stuck — keep current direction (will crash → reset)
        return self.direction

    def _tick(self) -> None:
        """Advance the game by one discrete step."""
        head = self.snake[0]
        dx, dy = self._ai_direction()
        new_head = (head[0] + dx, head[1] + dy)
        nx, ny = new_head

        # Wall collision
        if not (0 <= nx < self.width and 0 <= ny < self.height):
            self._reset()
            return

        eating = new_head == self.apple

        # Self collision (adjust body check for growth)
        if eating:
            if new_head in self.snake:        # tail stays
                self._reset()
                return
        else:
            if new_head in self.snake[:-1]:   # tail moves away
                self._reset()
                return

        # Commit the move
        self.direction = (dx, dy)
        self.snake.insert(0, new_head)

        if eating:
            self.score += 1
            self._spawn_apple()
        else:
            self.snake.pop()

    def _reset(self) -> None:
        """Reset the snake to its initial state after a collision."""
        cx = self.width // 2
        cy = self.height // 2
        self.snake = [(cx - i, cy) for i in range(4)]
        self.direction = (1, 0)
        self.score = 0
        self._spawn_apple()
