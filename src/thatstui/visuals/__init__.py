"""Visuals registry — terminal animations and the Tamagotchi pet.

Each entry: (visual_id, name_en, name_uk, kind, factory)
  kind "anim": factory() -> Animation object with ``frame(dt_total) -> str``
  kind "pet":  factory() -> textual Screen subclass (stateful)
"""

from __future__ import annotations

from typing import Any, Callable

VisualFactory = Callable[[], Any]

VISUALS: list[tuple[str, str, str, str, VisualFactory]] = [
    ("matrix", "Matrix Rain", "Матриця", "anim", lambda: _anim("matrix", "MatrixRain")),
    ("starfield", "Starfield", "Зоряне поле", "anim", lambda: _anim("starfield", "Starfield")),
    ("fish_tank", "Fish Tank", "Акваріум", "anim", lambda: _anim("fish_tank", "FishTank")),
    ("plasma", "Plasma Waves", "Плазма", "anim", lambda: _anim("plasma", "Plasma")),
    ("snake", "Snake", "Змійка", "anim", lambda: _anim("snake", "Snake")),
]


def _screen(module: str, cls: str):
    """Return an INSTANCE of a textual Screen subclass."""
    import importlib

    mod = importlib.import_module(f"thatstui.visuals.{module}")
    return getattr(mod, cls)()


def _anim(module: str, cls: str):
    import importlib

    mod = importlib.import_module(f"thatstui.visuals.{module}")
    return getattr(mod, cls)()


def get_visual_info(visual_id: str) -> tuple[str, str, str, str, VisualFactory] | None:
    for v in VISUALS:
        if v[0] == visual_id:
            return v
    return None