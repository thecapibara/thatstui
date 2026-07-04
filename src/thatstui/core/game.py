"""Game base class (abstract), Upgrade and GameStats dataclasses.

This is the contract all games must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Upgrade:
    """A purchasable upgrade for an idle game."""

    id: str
    name: str
    description: str
    cost: float
    # Cost multiplier per level if repeatable; 1.15 = 15% increase per level
    cost_scale: float = 1.15
    repeatable: bool = True
    max_level: int = 0  # 0 = unlimited


@dataclass
class GameStats:
    """Aggregate statistics tracked for a game session."""

    playtime_seconds: float = 0.0
    upgrades_bought: int = 0


class Game(ABC):
    """Abstract base class for all idle games.

    Game subclasses implement pure game logic (no Textual dependencies).
    The engine and screens handle the UI, persistence, and tick loop.

    Every subclass MUST set class-level attributes:
        game_id: str   — unique identifier (e.g. "ant_colony")
        name: str      — human-readable name
        emoji: str     — theme emoji (e.g. "🐜")
    """

    game_id: str = ""
    name: str = ""
    emoji: str = ""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.stats = GameStats()
        self.paused = False
        self.speed = 1
        self.last_saved: float = 0.0  # unix timestamp of last save
        self.lang: str = "en"  # current UI language ("en" or "uk")
        if data is not None:
            self.from_dict(data)

    # ── required overrides ────────────────────────────────────────────

    @abstractmethod
    def tick(self, dt: float) -> None:
        """Advance game state by *dt* seconds of game-time.

        *dt* has already been multiplied by the speed multiplier by the
        engine, so subclasses should treat it as plain game-time seconds.
        """

    @abstractmethod
    def upgrades(self) -> list[Upgrade]:
        """Return currently available upgrades with their computed cost.

        Apply cost scaling by current level.  Exclude upgrades that have
        reached their ``max_level``.
        """

    @abstractmethod
    def buy_upgrade(self, upgrade_id: str) -> bool:
        """Attempt to purchase *upgrade_id*.

        Deduct cost from the game's currency if affordable, apply the
        effect, increment ``stats.upgrades_bought``, and return True.
        Return False if the upgrade is unavailable or not affordable.
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict representing the full state.

        Must include: last_saved, paused, speed, stats, and all game-
        specific fields needed to restore state via ``from_dict``.
        """

    @abstractmethod
    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore full state from *data* (output of ``to_dict``).

        Must restore: last_saved, paused, speed, stats, and all game-
        specific fields.
        """

    # ── optional overrides ────────────────────────────────────────────

    def status_lines(self) -> list[str]:
        """Short text lines shown in the hub menu for this game.

        Override to provide live-ish status (e.g. "Population: 42").
        """
        return []

    # ── convenience ───────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"<{type(self).__name__} game_id={self.game_id!r}>"
