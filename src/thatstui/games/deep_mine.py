"""Deep Mine — a vertical digging idle game.

⛏️ Dig deeper, find ores, smelt bars, and sell for gold.
Upgrade your miners and equipment to reach ever-greater depths.
"""

from __future__ import annotations

import math
import random
from typing import Any

from thatstui.core.game import Game, GameStats, Upgrade


# ── upgrade definitions (base config) ─────────────────────────────────

_UPGRADE_DEFS: dict[str, Upgrade] = {
    "more_miners": Upgrade(
        id="more_miners",
        name="More Miners",
        description="Hire an additional miner (+1)",
        cost=15,
        cost_scale=1.15,
        repeatable=True,
    ),
    "dig_speed": Upgrade(
        id="dig_speed",
        name="Dig Speed",
        description="Miners dig 20% faster per level",
        cost=25,
        cost_scale=1.15,
        repeatable=True,
    ),
    "reinforced_elevator": Upgrade(
        id="reinforced_elevator",
        name="Reinforced Elevator",
        description="Reduce depth slowdown by 50% per level",
        cost=50,
        cost_scale=1.15,
        repeatable=True,
    ),
    "smelter": Upgrade(
        id="smelter",
        name="Smelter Upgrade",
        description="Smelt ore 0.2 ore/s faster per level",
        cost=80,
        cost_scale=1.15,
        repeatable=True,
    ),
    "auto_sell": Upgrade(
        id="auto_sell",
        name="Auto-Sell",
        description="Bars sell at 25% premium automatically",
        cost=200,
        repeatable=False,
        max_level=1,
    ),
    "ore_scanner": Upgrade(
        id="ore_scanner",
        name="Ore Scanner",
        description="Reveal richer veins — double ore yield",
        cost=150,
        repeatable=False,
        max_level=1,
    ),
}

# ── translation strings ──────────────────────────────────────────────

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Upgrades
        "more_miners_name": "More Miners",
        "more_miners_desc": "Hire an additional miner (+1)",
        "dig_speed_name": "Dig Speed",
        "dig_speed_desc": "Miners dig 20% faster per level",
        "reinforced_elevator_name": "Reinforced Elevator",
        "reinforced_elevator_desc": "Reduce depth slowdown by 50% per level",
        "smelter_name": "Smelter Upgrade",
        "smelter_desc": "Smelt ore 0.2 ore/s faster per level",
        "auto_sell_name": "Auto-Sell",
        "auto_sell_desc": "Bars sell at 25% premium automatically",
        "ore_scanner_name": "Ore Scanner",
        "ore_scanner_desc": "Reveal richer veins — double ore yield",
        # Status lines
        "status_gold": "💰 [green]{:.1f}g[/]",
        "status_depth": "⛏️ Depth: [cyan]{:.0f}m[/]",
        "status_miners": "👷 Miners: [yellow]{}[/]",
        # Grid
        "grid_header": "[bold]⛏️ Deep Mine[/]  |  Depth: [cyan]{:.0f}m[/]  |  💰 [green]{:.1f}[/]",
        "legend": "[yellow]m[/] miner  [white]I[/] iron  [yellow]C[/] copper  [cyan]S[/] silver  [bold yellow]G[/] gold  [magenta]X[/] crystal",
    },
    "uk": {
        "more_miners_name": "Більше шахтарів",
        "more_miners_desc": "Найняти додаткового шахтаря (+1)",
        "dig_speed_name": "Швидкість копання",
        "dig_speed_desc": "Шахтарі копають на 20% швидше за рівень",
        "reinforced_elevator_name": "Підсилений ліфт",
        "reinforced_elevator_desc": "Зменшити сповільнення глибини на 50% за рівень",
        "smelter_name": "Покращення плавильні",
        "smelter_desc": "Переплавляти на 0.2 руди/с швидше за рівень",
        "auto_sell_name": "Авто-продаж",
        "auto_sell_desc": "Зливки продаються з 25% премією автоматично",
        "ore_scanner_name": "Сканер руди",
        "ore_scanner_desc": "Виявляє багатші жили — подвоює видобуток руди",
        # Status lines
        "status_gold": "💰 [green]{:.1f}зл[/]",
        "status_depth": "⛏️ Глибина: [cyan]{:.0f}м[/]",
        "status_miners": "👷 Шахтарі: [yellow]{}[/]",
        # Grid
        "grid_header": "[bold]⛏️ Глибока Шахта[/]  |  Глибина: [cyan]{:.0f}м[/]  |  💰 [green]{:.1f}[/]",
        "legend": "[yellow]m[/] шахтар  [white]I[/] залізо  [yellow]C[/] мідь  [cyan]S[/] срібло  [bold yellow]G[/] золото  [magenta]X[/] кристал",
    },
}

# ── ore tier definitions ─────────────────────────────────────────────
# Each tier: name, display symbol, upper depth bound, gold value per bar,
#            ore-yield rate (ore per meter dug)

ORE_TIERS: list[dict[str, Any]] = [
    {"name": "iron",      "symbol": "I", "depth_max": 50,   "value": 1.0,  "rate": 0.50},
    {"name": "copper",    "symbol": "C", "depth_max": 120,  "value": 2.0,  "rate": 0.40},
    {"name": "silver",    "symbol": "S", "depth_max": 250,  "value": 5.0,  "rate": 0.30},
    {"name": "gold_ore",  "symbol": "G", "depth_max": 500,  "value": 10.0, "rate": 0.20},
    {"name": "crystal",   "symbol": "X", "depth_max": 1e12, "value": 25.0, "rate": 0.15},
]

# ── rendering constants ──────────────────────────────────────────────

GRID_WIDTH = 46
GRID_HEIGHT = 18
VIEWPORT_ROWS = GRID_HEIGHT - 1  # 17 rows for the mine cross-section
MAX_VIEW_DEPTH = 340.0  # show 0-340 m in the viewport
METERS_PER_ROW = MAX_VIEW_DEPTH / VIEWPORT_ROWS  # 20 m per row


# ── helpers ───────────────────────────────────────────────────────────

def _hash_seed(row: int, col: int, phase: int) -> int:
    """Deterministic pseudo-random hash for stable ore vein placement."""
    return (row * 9973 + col * 7919 + phase * 6271) & 0x7FFFFFFF


# ── game class ────────────────────────────────────────────────────────

class DeepMine(Game):
    """Deep Mine idle game."""

    game_id = "deep_mine"
    name = "Deep Mine"
    emoji = "⛏️"

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        # Set these BEFORE super().__init__ because from_dict depends on them
        self.gold: float = 0.0
        self.depth: float = 0.0
        self.miners: int = 3
        self.dig_speed: float = 1.0  # m/s per miner at surface
        self.elevator_level: int = 1
        self.smelter_level: int = 1
        self.smelter_queue: float = 0.0  # raw ore awaiting smelting
        self.auto_sell: bool = False
        self.ore_scanner: bool = False
        self.upgrade_levels: dict[str, int] = {}
        self.ore_inventory: dict[str, float] = {}  # accumulated by tier name
        self._time: float = 0.0  # for rendering animation (not persisted)

        super().__init__(data)

        if data is None:
            # Fresh-game setup
            self.gold = 8.0
            self.miners = 3
            self.dig_speed = 1.0
            self.elevator_level = 1
            self.smelter_level = 1

    # ── helpers ───────────────────────────────────────────────────────

    def _tr(self, key: str) -> str:
        """Look up a translated string for the current language."""
        lang_dict = _STRINGS.get(self.lang, _STRINGS["en"])
        return lang_dict.get(key, _STRINGS["en"].get(key, key))

    def _slowdown(self) -> float:
        """Depth-based speed factor (1.0 at surface, drops off with depth).

        Each elevator level mitigates the penalty by 50%-points per level.
        """
        mitigation = 1.0 + self.elevator_level * 0.5
        return 1.0 / (1.0 + self.depth * 0.002 / mitigation)

    def _dig_rate(self) -> float:
        """Total digging rate in m/s for the current state."""
        return self.miners * self.dig_speed * self._slowdown()

    def _current_ore_tier(self) -> dict[str, Any] | None:
        """Return the ore tier active at the current depth."""
        for tier in ORE_TIERS:
            if self.depth < tier["depth_max"]:
                return tier
        return ORE_TIERS[-1]

    def _ore_yield_rate(self) -> float:
        """Ore collected per meter dug at the current depth."""
        tier = self._current_ore_tier()
        if tier is None:
            return 0.0
        rate = tier["rate"]
        if self.ore_scanner:
            rate *= 2.0
        return rate

    def _smelter_throughput(self) -> float:
        """Max ore the smelter can process per second."""
        return self.smelter_level * 0.2

    # ── tick ──────────────────────────────────────────────────────────

    def tick(self, dt: float) -> None:
        """Advance the mine by *dt* game-seconds.

        Digging depth is subdivided into 1-second chunks for accuracy of
        the depth-dependent slowdown factor.  Resource production (ore
        accumulation, smelting) scales linearly over the full *dt*.
        """
        self._time += dt

        # -- digging & ore accumulation --
        remaining = dt
        chunk = 1.0
        total_depth_gain = 0.0

        while remaining > 0:
            step = chunk if remaining >= chunk else remaining
            rate = self._dig_rate()
            depth_gain = rate * step

            # Mine ore for this sub-step (before depth changes)
            tier = self._current_ore_tier()
            if tier is not None and depth_gain > 0:
                ore_per_meter = tier["rate"]
                if self.ore_scanner:
                    ore_per_meter *= 2.0
                ore_mined = depth_gain * ore_per_meter
                tier_name = tier["name"]
                self.ore_inventory[tier_name] = (
                    self.ore_inventory.get(tier_name, 0.0) + ore_mined
                )
                self.smelter_queue += ore_mined

            self.depth += depth_gain
            total_depth_gain += depth_gain
            remaining -= step

        # -- smelting --
        throughput = self._smelter_throughput() * dt
        if throughput > 0.0 and self.smelter_queue > 0.0:
            smelted = throughput if throughput <= self.smelter_queue else self.smelter_queue
            self.smelter_queue -= smelted

            # Determine value from current depth's tier
            tier = self._current_ore_tier()
            if tier is not None:
                value = tier["value"]
                if self.auto_sell:
                    value *= 1.25
                self.gold += smelted * value

    # ── upgrades ──────────────────────────────────────────────────────

    def upgrades(self) -> list[Upgrade]:
        """Return currently available upgrades with cost scaled by level."""
        result: list[Upgrade] = []
        for defn in _UPGRADE_DEFS.values():
            level = self.upgrade_levels.get(defn.id, 0)
            if defn.max_level > 0 and level >= defn.max_level:
                continue  # maxed out
            cost = defn.cost * (defn.cost_scale ** level)
            result.append(
                Upgrade(
                    id=defn.id,
                    name=self._tr(f"{defn.id}_name"),
                    description=self._tr(f"{defn.id}_desc"),
                    cost=cost,
                    cost_scale=defn.cost_scale,
                    repeatable=defn.repeatable,
                    max_level=defn.max_level,
                )
            )
        return result

    def buy_upgrade(self, upgrade_id: str) -> bool:
        """Purchase an upgrade if affordable."""
        current = self.upgrades()
        upgrade = next((u for u in current if u.id == upgrade_id), None)
        if upgrade is None:
            return False
        if self.gold < upgrade.cost:
            return False

        self.gold -= upgrade.cost
        level = self.upgrade_levels.get(upgrade_id, 0) + 1
        self.upgrade_levels[upgrade_id] = level
        self.stats.upgrades_bought += 1

        # Apply effects
        if upgrade_id == "more_miners":
            self.miners += 1
        elif upgrade_id == "dig_speed":
            self.dig_speed = 1.0 + level * 0.2
        elif upgrade_id == "reinforced_elevator":
            self.elevator_level = level
        elif upgrade_id == "smelter":
            self.smelter_level = level
        elif upgrade_id == "auto_sell":
            self.auto_sell = True
        elif upgrade_id == "ore_scanner":
            self.ore_scanner = True

        return True

    # ── serialisation ─────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_saved": self.last_saved,
            "paused": self.paused,
            "speed": self.speed,
            "stats": {
                "playtime_seconds": self.stats.playtime_seconds,
                "upgrades_bought": self.stats.upgrades_bought,
            },
            "gold": self.gold,
            "depth": self.depth,
            "miners": self.miners,
            "dig_speed": self.dig_speed,
            "elevator_level": self.elevator_level,
            "smelter_level": self.smelter_level,
            "smelter_queue": self.smelter_queue,
            "auto_sell": self.auto_sell,
            "ore_scanner": self.ore_scanner,
            "upgrade_levels": dict(self.upgrade_levels),
            "ore_inventory": dict(self.ore_inventory),
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        self.last_saved = data.get("last_saved", 0.0)
        self.paused = data.get("paused", False)
        self.speed = data.get("speed", 1)
        s = data.get("stats", {})
        self.stats = GameStats(
            playtime_seconds=s.get("playtime_seconds", 0.0),
            upgrades_bought=s.get("upgrades_bought", 0),
        )
        self.gold = data.get("gold", 0.0)
        self.depth = data.get("depth", 0.0)
        self.miners = data.get("miners", 3)
        self.dig_speed = data.get("dig_speed", 1.0)
        self.elevator_level = data.get("elevator_level", 1)
        self.smelter_level = data.get("smelter_level", 1)
        self.smelter_queue = data.get("smelter_queue", 0.0)
        self.auto_sell = data.get("auto_sell", False)
        self.ore_scanner = data.get("ore_scanner", False)
        self.upgrade_levels = dict(data.get("upgrade_levels", {}))
        self.ore_inventory = dict(data.get("ore_inventory", {}))

    # ── display ───────────────────────────────────────────────────────

    def status_lines(self) -> list[str]:
        return [
            self._tr("status_gold").format(self.gold),
            self._tr("status_depth").format(self.depth),
            self._tr("status_miners").format(self.miners),
        ]

    def render_grid(self) -> str:
        """Return a coloured vertical cross-section of the mine.

        Header line followed by VIEWPORT_ROWS of mine content, then a legend footer.
        Each content row shows: depth-label | shaft (9 chars) | rock (30 chars).
        """
        # Ore-symbol → rich colour mapping
        _ORE_COLORS: dict[str, str] = {
            "I": "white",
            "C": "yellow",
            "S": "cyan",
            "G": "bold yellow",
            "X": "magenta",
        }

        lines: list[str] = []

        # ── header ────────────────────────────────────────────────────
        header = self._tr("grid_header").format(self.depth, self.gold)
        lines.append(header)

        # Which viewport row contains the dig face
        dig_row = min(int(self.depth / METERS_PER_ROW), VIEWPORT_ROWS - 1)
        # Coarse time-phase for subtle animation
        phase = int(self._time * 0.2) % 8

        # Miner wiggles within the shaft columns
        miner_col = int(self._time * 2) % 9

        for row_idx in range(VIEWPORT_ROWS):
            depth_top = row_idx * METERS_PER_ROW
            depth_bottom = (row_idx + 1) * METERS_PER_ROW
            is_dug = depth_bottom <= self.depth
            is_dig_face = row_idx == dig_row

            # ── depth label (cols 0-4) ────────────────────────────────
            if row_idx % 2 == 0:
                label = f"[dim]{int(depth_top):>4}m[/]"
            else:
                label = "     "

            # ── left wall (col 5) ─────────────────────────────────────
            row_chars: list[str] = [label, "│"]

            # ── shaft (cols 6-14, 9 chars) ────────────────────────────
            for col in range(9):
                if is_dug:
                    if is_dig_face and col == miner_col:
                        row_chars.append("[bold yellow]m[/]")
                    else:
                        row_chars.append("[dim]░[/]")
                else:
                    row_chars.append("[dim]▓[/]")

            # ── right wall (col 15) ───────────────────────────────────
            row_chars.append("│")

            # ── rock face (cols 16-45, 30 chars) ──────────────────────
            for col in range(30):
                ore = self._ore_symbol(row_idx, col, phase)
                if ore is not None:
                    colour = _ORE_COLORS.get(ore)
                    if colour:
                        row_chars.append(f"[{colour}]{ore}[/]")
                    else:
                        row_chars.append(ore)
                else:
                    row_chars.append("[dim]▓[/]")

            lines.append("".join(row_chars))

        # ── footer legend ─────────────────────────────────────────────
        legend = self._tr("legend")
        lines.append(legend)

        return "\n".join(lines)

    # ── ore-vein placement ────────────────────────────────────────────

    def _ore_symbol(self, view_row: int, rock_col: int, phase: int) -> str | None:
        """Return an ore character for a rock cell, or None for barren rock."""
        depth_top = view_row * METERS_PER_ROW

        # Collect ore tiers present at this depth
        valid: list[dict[str, Any]] = [t for t in ORE_TIERS if depth_top < t["depth_max"]]
        if not valid:
            return None

        # Deterministic hash — stable between frames, shifts with phase
        h = _hash_seed(view_row, rock_col, phase) % 100

        # Higher density for shallower (more common) ores
        density = 4 if valid[0]["value"] <= 2 else 3

        if h < density:
            idx = (view_row * 3 + rock_col * 7 + phase) % len(valid)
            return valid[idx]["symbol"]
        return None
