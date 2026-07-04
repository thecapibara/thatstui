"""Hub launcher, generic game screen, and animation screen.

HubApp         — main menu with two sections (Games / Visuals), arrow
                  navigation, language toggle (L), aggregate stats.
GameScreen     — generic screen driving any ``Game``.
AnimationScreen — runs a pure looping animation (matrix, starfield, ...).
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from thatstui.core import i18n
from thatstui.core.engine import GameEngine
from thatstui.core.persistence import load_state
from thatstui.games import GAMES
from thatstui.visuals import VISUALS

_TICK_INTERVAL = 0.1
_SAVE_EVERY_TICKS = max(1, round(5.0 / _TICK_INTERVAL))


# ═══════════════════════════════════════════════════════════════════════
# Hub
# ═══════════════════════════════════════════════════════════════════════

class HubApp(App):
    """Main launcher — Games + Visuals sections, arrow navigation."""

    CSS = """
    Screen {
        background: $surface;
        align-horizontal: center;
        align-vertical: middle;
    }
    #hero {
        align-horizontal: center;
        align-vertical: middle;
        width: 100%;
        height: auto;
        padding: 0 0 1 0;
    }
    #title {
        text-style: bold;
        color: $accent;
        content-align: center middle;
        text-align: center;
        padding: 0;
    }
    #subtitle {
        padding: 0;
        content-align: center middle;
        text-align: center;
        text-style: dim italic;
        color: $text-muted;
    }
    #author {
        padding: 0 0 1 0;
        content-align: center middle;
        text-align: center;
        text-style: dim;
        color: $text-muted;
    }
    #lang-indicator {
        padding: 0 0 1 0;
        content-align: center middle;
        text-align: center;
        color: $warning;
        text-style: bold;
    }
    #stats-container {
        width: 100%;
        height: auto;
        align-horizontal: center;
    }
    #stats {
        padding: 0 1;
        content-align: center middle;
        text-align: center;
        text-style: bold;
        color: $success;
        border: round $accent;
        width: 70%;
        min-width: 50;
        height: auto;
        margin: 0 0 1 0;
    }
    #menu-container {
        width: 100%;
        height: auto;
        align-horizontal: center;
    }
    #menu {
        align-horizontal: center;
        align-vertical: middle;
        width: 60%;
        min-width: 44;
        height: auto;
        padding: 0 2;
    }
    .section-header {
        text-style: bold;
        color: $primary;
        padding: 1 0 0 0;
        text-align: center;
        content-align: center middle;
    }
    .section-divider {
        color: $accent;
        text-style: dim;
        text-align: center;
        padding: 0 0 0 0;
        height: 1;
    }
    .menu-item {
        padding: 0 2;
        height: 1;
        text-align: center;
        content-align: center middle;
    }
    .menu-item-selected {
        padding: 0 2;
        height: 1;
        text-style: bold;
        color: $text;
        background: $accent 30%;
        text-align: center;
        content-align: center middle;
        border-left: thick $accent;
        border-right: thick $accent;
    }
    #hint {
        padding: 1 0 0 0;
        content-align: center middle;
        text-align: center;
        text-style: dim;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("й", "quit", "Quit"),
        ("l", "toggle_language", "Language"),
        ("д", "toggle_language", "Language"),
        ("up", "cursor_up", "Up"),
        ("down", "cursor_down", "Down"),
        ("enter", "select", "Select"),
    ]

    def __init__(self) -> None:
        super().__init__()
        # Combined menu: list of (kind, id, name_en, name_uk)
        self._items: list[tuple[str, str, str, str]] = []
        self._cursor = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="hero"):
            yield Static(i18n.tr("title"), id="title")
            yield Static(i18n.tr("subtitle"), id="subtitle")
            yield Static("by JustGL", id="author")
            yield Static("", id="lang-indicator")
            with Vertical(id="stats-container"):
                yield Static("", id="stats")
        with Vertical(id="menu-container"):
            yield Vertical(id="menu")
        yield Static("", id="hint")

    def on_mount(self) -> None:
        self._build_items()
        self._build_menu_widgets()
        self._update_menu()
        self.set_interval(1.0, self._refresh_live)

    def _build_items(self) -> None:
        """Build the flat list of menu entries (games then visuals)."""
        self._items = []
        for gid, name, _emoji, _fac in GAMES:
            self._items.append(("game", gid, name, name))
        for vid, name_en, name_uk, _kind, _fac in VISUALS:
            self._items.append(("visual", vid, name_en, name_uk))
        self._cursor = 0

    def _build_menu_widgets(self) -> None:
        """Create the Static widgets ONCE. No re-mounting later."""
        from textual.widgets import Static as _S
        menu = self.query_one("#menu", Vertical)
        widgets = []
        # Games section header + divider
        widgets.append(_S("", id="header-games", classes="section-header"))
        widgets.append(_S("──────────────", classes="section-divider"))
        game_count = len(GAMES)
        for i, (kind, _id, _ne, _nu) in enumerate(self._items):
            if i == game_count:
                widgets.append(_S("", id="header-visuals", classes="section-header"))
                widgets.append(_S("──────────────", classes="section-divider"))
            widgets.append(_S("", id=f"item-{i}", classes="menu-item"))
        menu.mount(*widgets)

    def _update_menu(self) -> None:
        """Update text + classes of existing widgets (no mount/unmount)."""
        lang = i18n.current()
        try:
            self.query_one("#header-games", Static).update(i18n.tr("section_games"))
            self.query_one("#header-visuals", Static).update(i18n.tr("section_visuals"))
        except Exception:
            pass
        game_count = len(GAMES)
        for i, (kind, _id, name_en, name_uk) in enumerate(self._items):
            label = name_uk if lang == "uk" else name_en
            try:
                w = self.query_one(f"#item-{i}", Static)
                w.update(f"  {label}")
                selected = i == self._cursor
                w.remove_class("menu-item", "menu-item-selected")
                w.add_class("menu-item-selected" if selected else "menu-item")
            except Exception:
                pass
        self._refresh_live()

    def _refresh_live(self) -> None:
        # Language indicator
        lang = i18n.current()
        lang_name = i18n.tr("lang_uk" if lang == "uk" else "lang_en")
        try:
            self.query_one("#lang-indicator", Static).update(
                f"🌐 {i18n.tr('language')}: [bold]{lang_name}[/]  (L)"
            )
        except Exception:
            pass
        # Stats
        total_time = 0.0
        total_upgrades = 0
        for game_id, _n, _e, factory in GAMES:
            data = load_state(game_id)
            if data and data.get("stats"):
                s = data["stats"]
                total_time += s.get("playtime_seconds", 0.0)
                total_upgrades += s.get("upgrades_bought", 0)
        try:
            self.query_one("#stats", Static).update(
                f"⏱  {i18n.tr('total_playtime')}: [bold]{_fmt_time(total_time)}[/]"
                f"   •   ⬆  {i18n.tr('upgrades_bought')}: [bold]{total_upgrades}[/]"
            )
        except Exception:
            pass
        # Hint
        try:
            self.query_one("#hint", Static).update(i18n.tr("hint_nav"))
        except Exception:
            pass

    # ── navigation ────────────────────────────────────────────────────

    def action_cursor_up(self) -> None:
        if self._items:
            self._cursor = (self._cursor - 1) % len(self._items)
            self._update_menu()

    def action_cursor_down(self) -> None:
        if self._items:
            self._cursor = (self._cursor + 1) % len(self._items)
            self._update_menu()

    def action_select(self) -> None:
        if not self._items:
            return
        kind, item_id, _n_en, _n_uk = self._items[self._cursor]
        if kind == "game":
            if item_id == "tamagotchi":
                from thatstui.visuals.tamagotchi import TamagotchiScreen
                self.push_screen(TamagotchiScreen())
            else:
                self.push_screen(GameScreen(item_id))
        else:
            info = None
            from thatstui.visuals import get_visual_info

            info = get_visual_info(item_id)
            if info is None:
                return
            _vid, name_en, name_uk, vkind, factory = info
            lang = i18n.current()
            display_name = name_uk if lang == "uk" else name_en
            if vkind == "pet":
                self.push_screen(factory())
            else:
                self.push_screen(AnimationScreen(factory(), display_name))

    def action_toggle_language(self) -> None:
        i18n.toggle()
        self._update_menu()

    def action_quit(self) -> None:
        self.exit()


# ═══════════════════════════════════════════════════════════════════════
# Generic Game Screen
# ═══════════════════════════════════════════════════════════════════════

class GameScreen(Screen):
    """Generic Textual screen driving any ``Game``."""

    CSS = """
    Screen { background: $surface; }
    #game-area { height: 100%; }
    #grid-container { width: 2fr; height: 100%; align: center middle; }
    #grid { width: auto; padding: 1; border: heavy $primary; color: $text; }
    #sidebar { width: 36; height: 100%; border: heavy $accent; padding: 1; background: $panel; }
    #stats-panel { height: auto; margin-bottom: 1; color: $text; }
    #upgrades-panel { height: auto; margin-bottom: 1; color: $success; }
    #controls-hint { height: auto; text-style: dim; color: $text-muted; }
    #offline-summary { height: auto; text-style: italic; color: $warning; border: dashed $warning; padding: 0 1; }
    """

    BINDINGS = [
        ("p", "toggle_pause", "Pause"),
        ("з", "toggle_pause", "Pause"),
        ("]", "speed_up", "Faster"),
        ("ї", "speed_up", "Faster"),
        ("[", "speed_down", "Slower"),
        ("х", "speed_down", "Slower"),
        ("escape", "back_to_hub", "Back"),
        ("r", "reset_game", "Reset"),
        ("к", "reset_game", "Reset"),
        ("enter", "noop", ""),
        ("1", "buy_0", "Buy 1"),
        ("2", "buy_1", "Buy 2"),
        ("3", "buy_2", "Buy 3"),
        ("4", "buy_3", "Buy 4"),
        ("5", "buy_4", "Buy 5"),
        ("6", "buy_5", "Buy 6"),
        ("7", "buy_6", "Buy 7"),
        ("8", "buy_7", "Buy 8"),
        ("9", "buy_8", "Buy 9"),
    ]

    def __init__(self, game_id: str) -> None:
        super().__init__()
        self.game_id = game_id
        self.engine: GameEngine | None = None
        self._tick_counter = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="game-area"):
            with Vertical(id="grid-container"):
                yield Static("", id="grid")
            with Vertical(id="sidebar"):
                yield Static("", id="stats-panel")
                yield Static("", id="upgrades-panel")
                yield Static("", id="controls-hint")
        yield Static("", id="offline-summary")

    def on_mount(self) -> None:
        from thatstui.games import get_game_info

        info = get_game_info(self.game_id)
        if info is None:
            self.app.pop_screen()
            return
        _id, name, emoji, factory = info
        self.title = f"{emoji} {name}"
        self.engine = GameEngine.load(self.game_id, factory)
        self.engine.game.lang = i18n.current()
        self.set_interval(_TICK_INTERVAL, self._tick)
        self._refresh_ui()
        if self.engine.offline_summary:
            self.query_one("#offline-summary", Static).update(
                f"⏰ {i18n.tr('offline_earnings')}: {self.engine.offline_summary}"
            )

    def _tick(self) -> None:
        if self.engine is None:
            return
        self.engine.tick_game(_TICK_INTERVAL)
        self._tick_counter += 1
        if self._tick_counter % _SAVE_EVERY_TICKS == 0:
            self.engine.save_now()
        self._refresh_ui()

    def _refresh_ui(self) -> None:
        if self.engine is None:
            return
        game = self.engine.game
        self.query_one("#grid", Static).update(game.render_grid())  # type: ignore[attr-defined]
        status_lines = game.status_lines()
        state = i18n.tr("paused") if game.paused else i18n.tr("running")
        state_color = "red" if game.paused else "green"
        stats_text = (
            f"[bold cyan]{i18n.tr('speed')}:[/] ×{game.speed}  "
            f"[bold {state_color}]{'⏸ ' + state if game.paused else '▶ ' + state}[/]\n"
            + "\n".join(status_lines)
        )
        self.query_one("#stats-panel", Static).update(stats_text)
        upgrades_text = f"[bold underline]{i18n.tr('upgrades')}[/]"
        for i, up in enumerate(game.upgrades()):
            upgrades_text += f"\n[bold yellow]{i + 1}.[/] {up.name}: {up.cost:.1f}"
        self.query_one("#upgrades-panel", Static).update(upgrades_text)
        self.query_one("#controls-hint", Static).update(
            f"[bold]p[/] {i18n.tr('pause_hint')}  "
            f"[bold][ ][/] / [bold]][/] "
            f"{i18n.tr('speed_hint')}:×{game.speed}  [bold]1-9[/] {i18n.tr('buy_hint')}  "
            f"[bold]R[/] reset  "
            f"[bold]Esc[/] {i18n.tr('back_hint')}"
        )

    def action_toggle_pause(self) -> None:
        if self.engine:
            self.engine.game.paused = not self.engine.game.paused
            self._refresh_ui()

    def action_speed_up(self) -> None:
        if self.engine:
            speeds = [1, 2, 5, 10]
            cur = self.engine.game.speed
            idx = speeds.index(cur) if cur in speeds else 0
            self.engine.game.speed = speeds[(idx + 1) % len(speeds)]
            self._refresh_ui()

    def action_speed_down(self) -> None:
        if self.engine:
            speeds = [1, 2, 5, 10]
            cur = self.engine.game.speed
            idx = speeds.index(cur) if cur in speeds else 0
            self.engine.game.speed = speeds[(idx - 1) % len(speeds)]
            self._refresh_ui()

    def action_back_to_hub(self) -> None:
        if self.engine:
            self.engine.save_now()
        self.app.pop_screen()

    def action_reset_game(self) -> None:
        """Reset the current game to a fresh state (deletes save)."""
        if self.engine is None:
            return
        from thatstui.games import get_game_info
        from thatstui.core.persistence import save_state
        import os
        game_id = self.game_id
        info = get_game_info(game_id)
        if info is None:
            return
        _id, _name, _emoji, factory = info
        # Delete the save file
        try:
            from thatstui.core.persistence import save_dir
            save_file = save_dir() / f"{game_id}.json"
            if save_file.exists():
                save_file.unlink()
        except Exception:
            pass
        # Re-create a fresh game
        self.engine.game = factory(None)
        self.engine.game.lang = i18n.current()
        self.engine.save_now()
        self._refresh_ui()

    def action_noop(self) -> None:
        """Swallow Enter key so it doesn't propagate to the hub."""
        pass

    def _buy(self, idx: int) -> None:
        if self.engine is None:
            return
        ups = self.engine.game.upgrades()
        if idx < len(ups):
            self.engine.game.buy_upgrade(ups[idx].id)
            self._refresh_ui()

    def action_buy_0(self) -> None:
        self._buy(0)

    def action_buy_1(self) -> None:
        self._buy(1)

    def action_buy_2(self) -> None:
        self._buy(2)

    def action_buy_3(self) -> None:
        self._buy(3)

    def action_buy_4(self) -> None:
        self._buy(4)

    def action_buy_5(self) -> None:
        self._buy(5)

    def action_buy_6(self) -> None:
        self._buy(6)

    def action_buy_7(self) -> None:
        self._buy(7)

    def action_buy_8(self) -> None:
        self._buy(8)

    def on_unmount(self) -> None:
        if self.engine:
            self.engine.save_now()


# ═══════════════════════════════════════════════════════════════════════
# Animation Screen (pure looping visuals)
# ═══════════════════════════════════════════════════════════════════════

class AnimationScreen(Screen):
    """Runs a pure looping animation. The animation object exposes
    ``frame(dt_total: float) -> str`` returning a rich-markup string."""

    CSS = """
    Screen { background: $surface; }
    #anim {
        width: 100%;
        height: 1fr;
        content-align: center middle;
        text-align: center;
        padding: 1;
        color: $text;
        text-wrap: nowrap;
        overflow: hidden hidden;
    }
    #anim-hint { height: auto; text-style: dim; color: $text-muted; text-align: center; }
    """

    BINDINGS = [("escape", "back", "Back"), ("enter", "noop", "")]

    def __init__(self, animation, display_name: str = "") -> None:
        super().__init__()
        self.animation = animation
        self._display_name = display_name or getattr(animation, "name", "Animation")
        self._t = 0.0
        self._sized = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="anim")
        yield Static(i18n.tr("back_hint") + " (Esc)", id="anim-hint")
        yield Footer()

    def on_mount(self) -> None:
        self.title = self._display_name
        self.set_interval(_TICK_INTERVAL, self._tick)
        self._tick()

    def on_resize(self, event) -> None:  # type: ignore[no-untyped-def]
        """Re-adapt animation when terminal is resized (e.g. tiling WM)."""
        self._adapt_size(event.size.width, event.size.height)

    def on_key(self, event) -> None:  # type: ignore[no-untyped-def]
        """Forward key events to the active animation if supported."""
        if hasattr(self.animation, "handle_key"):
            self.animation.handle_key(event.key)

    def _adapt_size(self, cols: int | None = None, rows: int | None = None) -> None:
        """Resize the animation to fit the current terminal area."""
        try:
            # Use app terminal size (more reliable than screen.size early on)
            if cols is None or rows is None:
                try:
                    cols, rows = self.app.size
                except Exception:
                    cols, rows = self.size.width, self.size.height
            
            # #anim has padding: 1, which reduces content width by 2 and height by 2.
            # Header is 1 line, Footer is 1 line, hint is 1 line.
            # So the content area of #anim is:
            w = cols - 2
            h = rows - 5
            
            # If the animation draws borders/headers inside itself (like Snake),
            # it needs extra space: 2 columns for borders, 3 rows for headers/borders.
            if getattr(self.animation, "name", "") == "Snake":
                w -= 2
                h -= 3
                
            if w > 0 and h > 0:
                if hasattr(self.animation, "resize"):
                    self.animation.resize(max(20, w), max(8, h))
                self._sized = True
        except Exception:
            pass

    def _tick(self) -> None:
        # Defer size adaptation until the screen has real dimensions.
        if not self._sized:
            self._adapt_size()
        self._t += _TICK_INTERVAL
        frame = self.animation.frame(self._t)
        self.query_one("#anim", Static).update(frame)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_noop(self) -> None:
        """Swallow Enter key so it doesn't propagate to the hub."""
        pass


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    if s < 86400:
        return f"{s // 3600}h {(s % 3600) // 60}m"
    return f"{s // 86400}d {(s % 86400) // 3600}h"


def main() -> None:
    HubApp().run()


if __name__ == "__main__":
    main()