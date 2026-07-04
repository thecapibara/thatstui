"""Games registry.

Each entry: (game_id, name, emoji, factory_callable)
where factory(data: dict | None) -> Game
"""

from __future__ import annotations

from typing import Callable

from thatstui.core.game import Game

GameFactory = Callable[[dict | None], Game]

GAMES: list[tuple[str, str, str, GameFactory]] = [
    ("tamagotchi", "Tamagotchi", "🐾", lambda d: None),  # Launches via custom Screen subclass
    ("ant_colony", "Ant Colony", "🐜", lambda d: _import("ant_colony", "AntColony", d)),
    ("deep_mine", "Deep Mine", "⛏️", lambda d: _import("deep_mine", "DeepMine", d)),
    ("forest", "Forest", "🌲", lambda d: _import("forest", "Forest", d)),
    ("factory", "Factory", "🏭", lambda d: _import("factory", "Factory", d)),
    ("space_colony", "Space Colony", "🚀", lambda d: _import("space_colony", "SpaceColony", d)),
    ("idle_hero", "Idle Hero", "⚔️", lambda d: _import("idle_hero", "IdleHero", d)),
    ("stock_market", "Stock Market", "📈", lambda d: _import("stock_market", "StockMarket", d)),
]


def _import(module: str, cls: str, data: dict | None) -> Game:
    """Lazy import to avoid circular dependencies on module load."""
    import importlib

    mod = importlib.import_module(f"thatstui.games.{module}")
    return getattr(mod, cls)(data)


def get_game_info(game_id: str) -> tuple[str, str, str, GameFactory] | None:
    """Look up a game by its id."""
    for g in GAMES:
        if g[0] == game_id:
            return g
    return None