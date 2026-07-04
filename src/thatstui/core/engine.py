"""GameEngine — drives save/load, offline catch-up, and the tick loop.

The engine is the bridge between the pure ``Game`` logic and the Textual
screen.  It handles persistence, offline-earnings computation, and
provides the ``tick_game`` helper called by the screen's interval.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from thatstui.core.game import Game
from thatstui.core.persistence import load_state, save_state

_MAX_OFFLINE_SECONDS = 7 * 24 * 3600  # 7 days
_CATCHUP_CHUNK = 3600  # 1 hour chunks
_MAX_CATCHUP_ITERATIONS = 10000


class GameEngine:
    """Binds a ``Game`` instance to its persistence and tick loop."""

    def __init__(self, game: Game, game_id: str) -> None:
        self.game = game
        self.game_id = game_id
        self.offline_summary: str = ""
        self._last_save_time: float = 0.0

    # ── factory / load ────────────────────────────────────────────────

    @classmethod
    def load(
        cls,
        game_id: str,
        factory: Callable[[dict[str, Any] | None], Game],
    ) -> GameEngine:
        """Load a saved game or create a fresh one, running offline catch-up.

        *factory* receives either the saved dict (to reconstruct state)
        or ``None`` (to create a fresh game).
        """
        data = load_state(game_id)
        if data is not None:
            game = factory(data)
            engine = cls(game, game_id)
            engine._run_offline_catchup()
        else:
            engine = cls(factory(None), game_id)
        return engine

    # ── offline catch-up ─────────────────────────────────────────────

    def _run_offline_catchup(self) -> None:
        """Simulate elapsed time since last save."""
        now = time.time()
        elapsed = min(now - self.game.last_saved, _MAX_OFFLINE_SECONDS)
        if elapsed <= 0:
            return

        # Snapshot status before catch-up
        before = list(self.game.status_lines())

        remaining = elapsed
        iterations = 0
        while remaining > 0 and iterations < _MAX_CATCHUP_ITERATIONS:
            dt = min(_CATCHUP_CHUNK, remaining)
            self.game.tick(dt)
            remaining -= dt
            iterations += 1

        after = list(self.game.status_lines())
        diffs = [f"{b} → {a}" for b, a in zip(before, after) if b != a]
        prefix = f"⏰ Offline ({elapsed:.1f}s"
        if diffs:
            self.offline_summary = f"{prefix}): " + "; ".join(diffs)
        else:
            self.offline_summary = f"{prefix}): no change"

    # ── tick helper (called by screen interval) ──────────────────────

    def tick_game(self, dt: float) -> None:
        """Advance game time by *dt* real seconds.

        Respects pause and speed multiplier.  Also accumulates
        ``playtime_seconds`` on the game's stats.
        """
        if not self.game.paused:
            effective_dt = dt * self.game.speed
            self.game.tick(effective_dt)
            self.game.stats.playtime_seconds += effective_dt

    # ── save ──────────────────────────────────────────────────────────

    def save_now(self) -> None:
        """Immediately write game state to disk."""
        self.game.last_saved = time.time()
        data = self.game.to_dict()
        data["last_saved"] = self.game.last_saved
        data["paused"] = self.game.paused
        data["speed"] = self.game.speed
        data["stats"] = {
            "playtime_seconds": self.game.stats.playtime_seconds,
            "upgrades_bought": self.game.stats.upgrades_bought,
        }
        save_state(self.game_id, data)
