"""Internationalisation — minimal EN/UK string store.

Persists the chosen language to the user config dir alongside saves.
Games and the hub look up strings via :func:`tr`.
"""

from __future__ import annotations

import json
from pathlib import Path

from thatstui.core.persistence import save_dir

_LANG_FILE = save_dir().parent / "settings.json"

SUPPORTED = ("en", "uk")

_current = "en"

# ── common UI strings (hub + game screen) ─────────────────────────────
_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "title": "thatstui — terminal idle games",
        "subtitle": "a living terminal — let it grow",
        "section_games": "Games",
        "section_visuals": "Visuals",
        "hint_launch": "Press 1-7 to launch a game  •  Q to quit",
        "hint_nav": "↑↓ navigate  Enter select  L language  Q quit",
        "total_playtime": "Total playtime",
        "upgrades_bought": "Upgrades bought",
        "speed": "Speed",
        "paused": "PAUSED",
        "running": "Running",
        "upgrades": "Upgrades",
        "buy_hint": "1-9 buy",
        "pause_hint": "p pause",
        "speed_hint": "speed",
        "back_hint": "Esc back",
        "back": "Back",
        "quit": "Quit",
        "language": "Language",
        "lang_en": "English",
        "lang_uk": "Українська",
        "offline_earnings": "Offline earnings",
        "select_language": "Select language",
        "feed": "Feed",
        "play": "Play",
        "clean": "Clean",
        "sleep": "Sleep",
        "upg_shop": "Upgrades Shop",
        "upg_feed": "Auto-Feeder",
        "upg_health": "Medkit",
        "upg_energy": "Cozy Bed",
        "upg_happy": "Toys",
        "cost": "Cost",
        "desc_feed": "Slower hunger decay",
        "desc_health": "Slower health loss",
        "desc_energy": "Slower energy decay",
        "desc_happy": "Slower happiness decay",
        "points": "Care Points",
        "Age": "Age",
        "Hunger": "Hunger",
        "Happiness": "Happiness",
        "Energy": "Energy",
        "Cleanliness": "Cleanliness",
        "Health": "Health",
        "Dead": "Dead",
        "Sleeping": "Sleeping",
        "Hungry!": "Hungry!",
        "Sick": "Sick",
        "Sad": "Sad",
        "Happy!": "Happy!",
        "Content": "Content",
    },
    "uk": {
        "title": "thatstui — термінальні ігри",
        "subtitle": "живий термінал — нехай росте",
        "section_games": "Ігри",
        "section_visuals": "Візуали",
        "hint_launch": "Натисни 1-7 щоб запустити гру  •  Q — вихід",
        "hint_nav": "↑↓ вибір  Enter — запустити  L — мова  Q — вихід",
        "total_playtime": "Загальний час",
        "upgrades_bought": "Куплено апгрейдів",
        "speed": "Швидкість",
        "paused": "ПАУЗА",
        "running": "Працює",
        "upgrades": "Апгрейди",
        "buy_hint": "1-9 купити",
        "pause_hint": "p пауза",
        "speed_hint": "швидк.",
        "back_hint": "Esc назад",
        "back": "Назад",
        "quit": "Вихід",
        "language": "Мова",
        "lang_en": "English",
        "lang_uk": "Українська",
        "offline_earnings": "Офлайн-дохід",
        "select_language": "Оберіть мову",
        "feed": "Годувати",
        "play": "Грати",
        "clean": "Чистити",
        "sleep": "Сон",
        "upg_shop": "Магазин покращень",
        "upg_feed": "Автогодівниця",
        "upg_health": "Аптечка",
        "upg_energy": "Тепле ліжко",
        "upg_happy": "Іграшки",
        "cost": "Ціна",
        "desc_feed": "Повільніше хоче їсти",
        "desc_health": "Повільніше втрачає здоров'я",
        "desc_energy": "Повільніше втрачає енергію",
        "desc_happy": "Повільніше сумує",
        "points": "Очки турботи",
        "Age": "Вік",
        "Hunger": "Голод",
        "Happiness": "Щастя",
        "Energy": "Енергія",
        "Cleanliness": "Чистота",
        "Health": "Здоров'я",
        "Dead": "Помер",
        "Sleeping": "Спить",
        "Hungry!": "Голодний!",
        "Sick": "Хворий",
        "Sad": "Сумний",
        "Happy!": "Щасливий!",
        "Content": "Задоволений",
    },
}


def current() -> str:
    return _current


def set_language(lang: str) -> None:
    global _current
    if lang in SUPPORTED:
        _current = lang
        _persist()


def toggle() -> str:
    set_language("uk" if _current == "en" else "en")
    return _current


def tr(key: str) -> str:
    return _STRINGS.get(_current, _STRINGS["en"]).get(key, key)


def load() -> None:
    global _current
    try:
        if _LANG_FILE.exists():
            data = json.loads(_LANG_FILE.read_text("utf-8"))
            lang = data.get("language", "en")
            if lang in SUPPORTED:
                _current = lang
    except Exception:
        pass


def _persist() -> None:
    try:
        _LANG_FILE.parent.mkdir(parents=True, exist_ok=True)
        _LANG_FILE.write_text(
            json.dumps({"language": _current}, ensure_ascii=False), "utf-8"
        )
    except Exception:
        pass


# Load persisted language on import.
load()