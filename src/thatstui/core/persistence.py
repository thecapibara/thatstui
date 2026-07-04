"""Save / load game state to JSON files in the user config directory.

Uses ``platformdirs.user_config_dir("thatstui")`` as the base path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir


def save_dir() -> Path:
    """Return the ``<config>/thatstui/saves/`` directory, creating it if needed."""
    p = Path(user_config_dir("thatstui")) / "saves"
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_state(game_id: str) -> dict[str, Any] | None:
    """Load saved state for *game_id*.

    Returns the deserialised dict, or ``None`` if no save exists or the
    file is corrupt.
    """
    path = save_dir() / f"{game_id}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def save_state(game_id: str, data: dict[str, Any]) -> None:
    """Persist *data* to the save file for *game_id*."""
    path = save_dir() / f"{game_id}.json"
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
