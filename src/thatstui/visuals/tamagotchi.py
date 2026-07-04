"""Tamagotchi — a stateful idle pet living in your terminal.

A textual ``Screen`` subclass that renders an ASCII pet.  The pet's
stats decay over time, respond to key-based care actions, and persist
to disk via ``thatstui.core.persistence``.  Offline catch-up decays
stats in bulk when you return.
"""

from __future__ import annotations

import time
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

from thatstui.core.i18n import tr
from thatstui.core.persistence import load_state, save_state

# ── helpers ─────────────────────────────────────────────────────────────

_TICK = 0.1               # interval between decay steps (seconds)
_SAVE_EVERY_TICKS = 50    # every 50 ticks ≈ 5 s
_MAX_CATCHUP_CHUNK = 3600.0  # process at most 1 h per chunk
_MAX_CATCHUP_ITERS = 10000
_MAX_CATCHUP_SECONDS = 7 * 24 * 3600  # cap at 1 week
_AUTO_REVIVE_DELAY = 30.0  # seconds before dead pet auto-revives


def _fmt_age(seconds: float) -> str:
    """Format seconds into a human-readable age string."""
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    if s < 86400:
        return f"{s // 3600}h {(s % 3600) // 60}m"
    return f"{s // 86400}d {(s % 86400) // 3600}h"


def _stat_bar(value: float, color: str, label: str) -> str:
    """Return a rich-markup stat bar (10 chars wide)."""
    filled = max(0, min(10, round(value / 100 * 10)))
    empty = 10 - filled
    return f"{label}: [bold {color}]{'█' * filled}{'░' * empty}[/] {value:.0f}"


def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


# ═══════════════════════════════════════════════════════════════════════
# Tamagotchi Screen
# ═══════════════════════════════════════════════════════════════════════


class TamagotchiScreen(Screen):
    """An idle pet that lives, decays, and responds to care actions.

    State is persisted to disk via ``thatstui.core.persistence`` with
    ``game_id = "tamagotchi"``.
    """

    game_id = "tamagotchi"

    DEFAULT_STATE: dict[str, Any] = {
        "hunger": 50.0,
        "happiness": 50.0,
        "energy": 50.0,
        "cleanliness": 50.0,
        "age": 0.0,
        "health": 100.0,
        "asleep": False,
        "pet_name": "Pixel",
        "last_saved": 0.0,
        "points": 0.0,
        "upg_feed": 0,
        "upg_health": 0,
        "upg_energy": 0,
        "upg_happy": 0,
    }

    BINDINGS = [
        Binding("f", "feed", tr("feed")),
        Binding("а", "feed", tr("feed"), show=False),
        Binding("p", "play", tr("play")),
        Binding("з", "play", tr("play"), show=False),
        Binding("c", "clean", tr("clean")),
        Binding("с", "clean", tr("clean"), show=False),
        Binding("s", "toggle_sleep", tr("sleep")),
        Binding("і", "toggle_sleep", tr("sleep"), show=False),
        Binding("u", "toggle_shop", tr("upgrades")),
        Binding("г", "toggle_shop", tr("upgrades"), show=False),
        Binding("1", "buy_1", "Buy 1", show=False),
        Binding("2", "buy_2", "Buy 2", show=False),
        Binding("3", "buy_3", "Buy 3", show=False),
        Binding("4", "buy_4", "Buy 4", show=False),
        Binding("escape", "back_to_hub", tr("back")),
        Binding("enter", "noop", "", show=False),
    ]

    CSS = """
    Screen {
        background: $surface;
    }
    #tamagotchi-display {
        width: 100%;
        height: 100%;
        align: center middle;
        text-align: center;
        padding: 1 2;
        color: $text;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.state: dict[str, Any] = dict(self.DEFAULT_STATE)
        self._tick_counter = 0
        self._death_time: float | None = None
        self._offline_message: str = ""
        self.show_shop = False

    # ── lifecycle ─────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static("", id="tamagotchi-display")

    def on_mount(self) -> None:
        self.title = "🐾 Tamagotchi"
        self._load_or_init()
        self._offline_catchup()
        self.set_interval(_TICK, self._tick)
        self._refresh_ui()

    def on_unmount(self) -> None:
        self._save_now()

    # ── state persistence ─────────────────────────────────────────────

    def _load_or_init(self) -> None:
        saved = load_state(self.game_id)
        if saved is not None:
            self.state.update(saved)
        for k, v in self.DEFAULT_STATE.items():
            self.state.setdefault(k, v)

    def _save_now(self) -> None:
        self.state["last_saved"] = time.time()
        save_state(self.game_id, self.state)

    # ── offline catch-up ─────────────────────────────────────────────

    def _offline_catchup(self) -> None:
        now = time.time()
        last_saved = self.state.get("last_saved", 0.0)
        if last_saved <= 0:
            self.state["last_saved"] = now
            return

        elapsed = min(now - last_saved, _MAX_CATCHUP_SECONDS)
        if elapsed < 1.0:
            return

        remaining = elapsed
        iters = 0
        while remaining > 0 and iters < _MAX_CATCHUP_ITERS:
            dt = min(remaining, _MAX_CATCHUP_CHUNK)
            self._apply_decay(dt)
            remaining -= dt
            iters += 1

        self.state["last_saved"] = now

        # Show offline summary once
        self._offline_message = (
            f"[bold yellow]⏰ Offline for {_fmt_age(elapsed)}[/]\n"
            f"[italic]Your pet missed you — stats have changed![/]"
        )

    # ── decay logic ───────────────────────────────────────────────────

    def _apply_decay(self, dt: float) -> None:
        """Apply autonomous decay/ageing for ``dt`` seconds."""
        s = self.state

        # Dead pets don't decay
        if s.get("health", 0) <= 0:
            return

        asleep = s.get("asleep", False)
        upg_feed = s.get("upg_feed", 0)
        upg_happy = s.get("upg_happy", 0)
        upg_energy = s.get("upg_energy", 0)
        upg_health = s.get("upg_health", 0)

        # Energy decay (Cozy Bed upgrade reduces awake energy loss)
        if asleep:
            s["energy"] = _clamp(s["energy"] + 0.1 * dt)
        else:
            energy_decay = (0.04 / (1.0 + 0.5 * upg_energy)) * dt
            s["energy"] = _clamp(s["energy"] - energy_decay)

        # Hunger decay (Auto-Feeder upgrade reduces hunger accumulation)
        hunger_decay = (0.05 / (1.0 + 1.0 * upg_feed)) * dt
        s["hunger"] = _clamp(s["hunger"] + hunger_decay)

        # Happiness decay (Toys upgrade reduces sadness rate)
        happy_decay = (0.03 / (1.0 + 0.5 * upg_happy)) * dt
        s["happiness"] = _clamp(s["happiness"] - happy_decay)

        s["cleanliness"] = _clamp(s["cleanliness"] - 0.02 * dt)
        s["age"] += dt

        # Health (Medkit upgrade reduces health loss when starving/dirty)
        if s["hunger"] >= 100 or s["cleanliness"] <= 0:
            health_decay = (0.05 / (1.0 + 2.0 * upg_health)) * dt
            s["health"] = _clamp(s["health"] - health_decay)
        elif (
            s["hunger"] < 80
            and s["cleanliness"] > 20
            and s["energy"] > 20
            and s["happiness"] > 20
        ):
            s["health"] = _clamp(s["health"] + 0.01 * dt)

        # Points accumulation (only when alive and healthy)
        if s["health"] > 50:
            s["points"] = s.get("points", 0.0) + 0.1 * dt

        # Re-check after health update
        if s["health"] <= 0 and self._death_time is None:
            self._death_time = time.time()

    # ── tick loop ─────────────────────────────────────────────────────

    def _tick(self) -> None:
        s = self.state
        now = time.time()

        # Auto-revive after 30 s of death
        if s.get("health", 0) <= 0 and self._death_time is not None:
            if now - self._death_time >= _AUTO_REVIVE_DELAY:
                # Reset to default stats (keep name, last_saved, points, and upgrades!)
                name = s.get("pet_name", "Pixel")
                saved_ts = s.get("last_saved", now)
                points = s.get("points", 0.0)
                upgrades = {
                    "upg_feed": s.get("upg_feed", 0),
                    "upg_health": s.get("upg_health", 0),
                    "upg_energy": s.get("upg_energy", 0),
                    "upg_happy": s.get("upg_happy", 0),
                }
                for k, v in self.DEFAULT_STATE.items():
                    s[k] = v
                s["pet_name"] = name
                s["last_saved"] = saved_ts
                s["points"] = points
                s.update(upgrades)
                self._death_time = None
                self._offline_message = "[bold green]✨ Your pet has revived![/]"

        self._apply_decay(_TICK)
        self._tick_counter += 1

        if self._tick_counter % _SAVE_EVERY_TICKS == 0:
            self._save_now()

        self._refresh_ui()

    # ── rendering ─────────────────────────────────────────────────────

    def _refresh_ui(self) -> None:
        try:
            display = self.query_one("#tamagotchi-display", Static)
            display.update(self._build_display())
            # Clear one-shot messages after first display
            self._offline_message = ""
        except Exception:
            pass  # Not mounted yet — safe to ignore

    def _build_display(self) -> str:
        s = self.state
        health = s.get("health", 100)
        hunger = s.get("hunger", 50)
        happiness = s.get("happiness", 50)
        energy = s.get("energy", 50)
        cleanliness = s.get("cleanliness", 50)
        asleep = s.get("asleep", False)
        pet_name = s.get("pet_name", "Pixel")
        age = s.get("age", 0)
        dead = health <= 0

        # ── expression ────────────────────────────────────────────────
        if dead:
            face = "(✖_✖)"
            face_color = "dim red"
            mood = tr("Dead")
        elif asleep:
            face = "(︶.︶)"
            face_color = "magenta"
            mood = tr("Sleeping")
        elif hunger >= 80:
            face = "(╥_╥)"
            face_color = "yellow"
            mood = tr("Hungry!")
        elif health < 30:
            face = "(×_×)"
            face_color = "red"
            mood = tr("Sick")
        elif happiness < 30:
            face = "(╥_╥)"
            face_color = "yellow"
            mood = tr("Sad")
        elif happiness >= 60 and hunger < 40 and energy >= 40:
            face = "(◕‿◕)"
            face_color = "green"
            mood = tr("Happy!")
        else:
            face = "(•‿•)"
            face_color = "cyan"
            mood = tr("Content")

        # ── pet art ───────────────────────────────────────────────────
        if dead:
            pet_lines = [
                "      ,___,",
                f"     [bold {face_color}] {face} [/]",
                f"     [bold {face_color}]  |  |  [/]",
                f"     [bold {face_color}]  |  |  [/]",
                f"     [bold {face_color}] (____) [/]",
                f"     [dim]✖ Revives in {max(0, int(_AUTO_REVIVE_DELAY - (time.time() - (self._death_time or 0))))}s[/]",
            ]
        elif asleep:
            pet_lines = [
                "       [dim italic]zZz[/]",
                "     [dim italic] zZz[/]",
                "      ,___,",
                f"     [bold {face_color}] {face} [/]",
                f"     [bold {face_color}]  |  |  [/]",
                f"     [bold {face_color}]  |  |  [/]",
                f"     [bold {face_color}] (____) [/]",
            ]
        else:
            pet_lines = [
                "      ,___,",
                f"     [bold {face_color}] {face} [/]",
                f"     [bold {face_color}]  |  |  [/]",
                f"     [bold {face_color}]  |  |  [/]",
                f"     [bold {face_color}] (____) [/]",
            ]

        # ── assemble output ───────────────────────────────────────────
        age_str = _fmt_age(age)
        body = "\n".join(pet_lines)

        if self.show_shop:
            cost_feed = self._upgrade_cost("feed")
            cost_health = self._upgrade_cost("health")
            cost_energy = self._upgrade_cost("energy")
            cost_happy = self._upgrade_cost("happy")

            shop_text = "\n".join([
                f"[bold yellow]💰 {tr('points')}: {int(s.get('points', 0))}[/]",
                "",
                f"[bold]1[/] {tr('upg_feed')}: Lvl {s.get('upg_feed', 0)} ({tr('cost')}: {cost_feed} CP)",
                f"   [dim]{tr('desc_feed')}[/]",
                f"[bold]2[/] {tr('upg_health')}: Lvl {s.get('upg_health', 0)} ({tr('cost')}: {cost_health} CP)",
                f"   [dim]{tr('desc_health')}[/]",
                f"[bold]3[/] {tr('upg_energy')}: Lvl {s.get('upg_energy', 0)} ({tr('cost')}: {cost_energy} CP)",
                f"   [dim]{tr('desc_energy')}[/]",
                f"[bold]4[/] {tr('upg_happy')}: Lvl {s.get('upg_happy', 0)} ({tr('cost')}: {cost_happy} CP)",
                f"   [dim]{tr('desc_happy')}[/]",
            ])

            controls = (
                f"[bold]u[/] {tr('back')}  "
                f"[bold]Esc[/] {tr('back')}"
            )

            lines = [
                "",
                f"[bold]🐾 {pet_name}[/]  │  {tr('upg_shop')}",
                "",
                body,
                "",
                shop_text,
                "",
                controls,
            ]
        else:
            stats = "\n".join([
                _stat_bar(hunger, "red", f" {tr('Hunger')}"),
                _stat_bar(happiness, "green", f" {tr('Happiness')}"),
                _stat_bar(energy, "yellow", f" {tr('Energy')}"),
                _stat_bar(cleanliness, "cyan", f" {tr('Cleanliness')}"),
                _stat_bar(health, "green" if health > 50 else "red", f" {tr('Health')}"),
                "",
                f"💰 {tr('points')}: [bold yellow]{int(s.get('points', 0))}[/]"
            ])

            controls = (
                f"[dim][bold]f[/] {tr('feed')}  "
                f"[bold]p[/] {tr('play')}  "
                f"[bold]c[/] {tr('clean')}  "
                f"[bold]s[/] {tr('sleep')}  "
                f"[bold]u[/] {tr('upgrades')}  "
                f"[bold]Esc[/] {tr('back')}[/]"
            )

            lines = [
                "",
                f"[bold]🐾 {pet_name}[/]  │  {tr('Age')}: {age_str}",
                "",
                body,
                "",
                stats,
                "",
                f"[italic]{mood}[/]",
                "",
                controls,
            ]

        # Offline / event messages (show at top for a while)
        if self._offline_message:
            lines.insert(0, self._offline_message)

        return "\n".join(lines)

    # ── actions (key bindings) ────────────────────────────────────────

    def action_feed(self) -> None:
        """Feed the pet — reduces hunger, boosts happiness, grants points."""
        s = self.state
        if s.get("health", 0) <= 0:
            return
        old_hunger = s["hunger"]
        s["hunger"] = _clamp(s["hunger"] - 30)
        s["happiness"] = min(100.0, s["happiness"] + 5)
        if old_hunger > 0:
            s["points"] = s.get("points", 0.0) + 15
        self._refresh_ui()

    def action_play(self) -> None:
        """Play with the pet — boosts happiness, costs energy, makes hungrier, grants points."""
        s = self.state
        if s.get("health", 0) <= 0:
            return
        old_happy = s["happiness"]
        old_energy = s["energy"]
        s["happiness"] = min(100.0, s["happiness"] + 25)
        s["energy"] = max(0.0, s["energy"] - 15)
        s["hunger"] = min(100.0, s["hunger"] + 10)
        if old_happy < 100 and old_energy >= 15:
            s["points"] = s.get("points", 0.0) + 20
        self._refresh_ui()

    def action_clean(self) -> None:
        """Clean the pet — resets cleanliness, small happiness boost, grants points."""
        s = self.state
        if s.get("health", 0) <= 0:
            return
        old_clean = s["cleanliness"]
        s["cleanliness"] = 100.0
        s["happiness"] = min(100.0, s["happiness"] + 5)
        if old_clean < 100:
            s["points"] = s.get("points", 0.0) + 15
        self._refresh_ui()

    def action_toggle_sleep(self) -> None:
        """Toggle sleep mode — when asleep, energy recovers."""
        self.state["asleep"] = not self.state["asleep"]
        self._refresh_ui()

    def action_toggle_shop(self) -> None:
        """Toggle the upgrades shop display."""
        self.show_shop = not self.show_shop
        self._refresh_ui()

    def _upgrade_cost(self, category: str) -> int:
        s = self.state
        lvl = s.get(f"upg_{category}", 0)
        bases = {
            "feed": 50,
            "health": 80,
            "energy": 40,
            "happy": 40,
        }
        return bases.get(category, 50) * (2 ** lvl)

    def _buy_upgrade(self, category: str) -> None:
        if not self.show_shop:
            return
        s = self.state
        cost = self._upgrade_cost(category)
        points = s.get("points", 0.0)
        if points >= cost:
            s["points"] = points - cost
            key = f"upg_{category}"
            s[key] = s.get(key, 0) + 1
            self._save_now()
            self._refresh_ui()

    def action_buy_1(self) -> None:
        self._buy_upgrade("feed")

    def action_buy_2(self) -> None:
        self._buy_upgrade("health")

    def action_buy_3(self) -> None:
        self._buy_upgrade("energy")

    def action_buy_4(self) -> None:
        self._buy_upgrade("happy")

    def action_back_to_hub(self) -> None:
        """Save and return to the hub."""
        self._save_now()
        self.app.pop_screen()

    def action_noop(self) -> None:
        """Swallow Enter key so it doesn't propagate to the hub."""
        pass
