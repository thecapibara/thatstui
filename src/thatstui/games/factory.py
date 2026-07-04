"""Factory — a Factorio-lite production chain idle game.

🏭 Mine ore, smelt ingots, craft parts, assemble devices, sell for profit.
"""

from __future__ import annotations

from typing import Any

from thatstui.core.game import Game, GameStats, Upgrade


# ── constants ──────────────────────────────────────────────────────────

MINE_BASE_RATE = 1.0          # ore/sec at mine level 1
MINE_RATE_PER_LEVEL = 0.5     # extra ore/sec per mine level beyond 1
SMELTER_RATE = 0.4            # ingots/sec per smelter machine
CRAFT_RATE = 0.25             # parts/sec per crafter
ASSEMBLY_RATE = 0.15          # devices/sec per assembler
BASE_SELL_PRICE = 8.0         # base money per device
SELL_PRICE_PER_LEVEL = 2.0    # extra money per device per sell price upgrade

BASE_STOCK_CAP = 100.0        # base stockpile capacity per stage
STORAGE_MULTIPLIER = 2.0      # stock cap multiplier for storage upgrade
AUTOMATION_MULTIPLIER = 2.0   # production rate multiplier for automation

UPGRADE_COST_SCALE = 1.15

BAR_WIDTH = 8


# ── upgrade definitions ───────────────────────────────────────────────

_UPGRADE_DEFS: dict[str, Upgrade] = {
    "mine_output": Upgrade(
        id="mine_output",
        name="Mine Output",
        description="Increase ore mining rate by +0.5/s",
        cost=10,
        cost_scale=UPGRADE_COST_SCALE,
        repeatable=True,
    ),
    "smelter_machines": Upgrade(
        id="smelter_machines",
        name="Smelter Machines",
        description="Add one smelter machine (+0.4 ingots/s)",
        cost=15,
        cost_scale=UPGRADE_COST_SCALE,
        repeatable=True,
    ),
    "sell_price": Upgrade(
        id="sell_price",
        name="Sell Price",
        description="Raise device sell price by $2.00",
        cost=20,
        cost_scale=UPGRADE_COST_SCALE,
        repeatable=True,
    ),
    "craft_machines": Upgrade(
        id="craft_machines",
        name="Craft Machines",
        description="Add one crafter (+0.25 parts/s)",
        cost=25,
        cost_scale=UPGRADE_COST_SCALE,
        repeatable=True,
    ),
    "assembly_machines": Upgrade(
        id="assembly_machines",
        name="Assembly Machines",
        description="Add one assembler (+0.15 devices/s)",
        cost=40,
        cost_scale=UPGRADE_COST_SCALE,
        repeatable=True,
    ),
    "storage": Upgrade(
        id="storage",
        name="Storage Expansion",
        description="Double all stockpile caps",
        cost=100,
        repeatable=False,
        max_level=1,
    ),
    "automation": Upgrade(
        id="automation",
        name="Automation",
        description="2x production rate for all machines",
        cost=200,
        repeatable=False,
        max_level=1,
    ),
}


# ── game class ─────────────────────────────────────────────────────────

class Factory(Game):
    """Factory idle game — build a production chain from ore to profit."""

    game_id = "factory"
    name = "Factory"
    emoji = "🏭"

    _STRINGS: dict[str, dict[str, str]] = {
        "en": {
            "upg_mine_output_name": "Mine Output",
            "upg_mine_output_desc": "Increase ore mining rate by +0.5/s",
            "upg_smelter_machines_name": "Smelter Machines",
            "upg_smelter_machines_desc": "Add one smelter machine (+0.4 ingots/s)",
            "upg_sell_price_name": "Sell Price",
            "upg_sell_price_desc": "Raise device sell price by $2.00",
            "upg_craft_machines_name": "Craft Machines",
            "upg_craft_machines_desc": "Add one crafter (+0.25 parts/s)",
            "upg_assembly_machines_name": "Assembly Machines",
            "upg_assembly_machines_desc": "Add one assembler (+0.15 devices/s)",
            "upg_storage_name": "Storage Expansion",
            "upg_storage_desc": "Double all stockpile caps",
            "upg_automation_name": "Automation",
            "upg_automation_desc": "2x production rate for all machines",
            "stat_money": "💰 Money: ${:.2f}",
            "stat_ore": "⛏️ Ore: {:.1f}/{:.0f}  ↑{:.1f}/s",
            "stat_ingots": "🏗️ Ingots: {:.1f}/{:.0f}  ↑{:.2f}/s",
            "stat_parts": "⚙️ Parts: {:.1f}/{:.0f}  ↑{:.2f}/s",
            "stat_devices": "📱 Devices sold: ↑{:.2f}/s  @ ${:.2f}",
            "grid_header": "🏭 Factory",
            "stage_ORE": "ORE",
            "stage_INGOT": "INGOT",
            "stage_PART": "PART",
            "stage_DEVICE": "DEVICE",
            "legend_ore": "Ore",
            "legend_ingot": "Ingot",
            "legend_part": "Part",
            "legend_device": "Device",
        },
        "uk": {
            "upg_mine_output_name": "Видобуток руди",
            "upg_mine_output_desc": "Збільшити швидкість видобутку руди на +0.5/с",
            "upg_smelter_machines_name": "Плавильні машини",
            "upg_smelter_machines_desc": "Додати плавильну машину (+0.4 зливків/с)",
            "upg_sell_price_name": "Ціна продажу",
            "upg_sell_price_desc": "Підняти ціну продажу приладів на $2.00",
            "upg_craft_machines_name": "Виробничі машини",
            "upg_craft_machines_desc": "Додати верстат (+0.25 деталей/с)",
            "upg_assembly_machines_name": "Складальні машини",
            "upg_assembly_machines_desc": "Додати складальник (+0.15 приладів/с)",
            "upg_storage_name": "Розширення сховища",
            "upg_storage_desc": "Подвоїти всі ліміти запасів",
            "upg_automation_name": "Автоматизація",
            "upg_automation_desc": "2x швидкість виробництва для всіх машин",
            "stat_money": "💰 Гроші: ${:.2f}",
            "stat_ore": "⛏️ Руда: {:.1f}/{:.0f}  ↑{:.1f}/с",
            "stat_ingots": "🏗️ Зливки: {:.1f}/{:.0f}  ↑{:.2f}/с",
            "stat_parts": "⚙️ Деталі: {:.1f}/{:.0f}  ↑{:.2f}/с",
            "stat_devices": "📱 Прилади продано: ↑{:.2f}/с  @ ${:.2f}",
            "grid_header": "🏭 Фабрика",
            "stage_ORE": "РУДА",
            "stage_INGOT": "ЗЛИВОК",
            "stage_PART": "ДЕТАЛЬ",
            "stage_DEVICE": "ПРИЛАД",
            "legend_ore": "Руда",
            "legend_ingot": "Зливок",
            "legend_part": "Деталь",
            "legend_device": "Прилад",
        },
    }

    def _tr(self, key: str) -> str:
        return self._STRINGS.get(self.lang, self._STRINGS["en"]).get(key, key)

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        # All fields must be set BEFORE super().__init__(data)
        self.money: float = 0.0
        self.ore_stock: float = 0.0
        self.ingot_stock: float = 0.0
        self.part_stock: float = 0.0
        self.device_stock: float = 0.0

        self.mine_level: int = 1
        self.smelter_machines: int = 1
        self.craft_machines: int = 1
        self.assembly_machines: int = 1
        self.sell_price_level: int = 0

        self.storage_expanded: bool = False
        self.automation_unlocked: bool = False

        self.stock_cap: float = BASE_STOCK_CAP

        self.upgrade_levels: dict[str, int] = {}

        super().__init__(data)

        # Fresh game init — defaults above are sufficient

    # ── computed properties ──────────────────────────────────────────────

    @property
    def _auto_mult(self) -> float:
        return AUTOMATION_MULTIPLIER if self.automation_unlocked else 1.0

    @property
    def _sell_price(self) -> float:
        return BASE_SELL_PRICE + self.sell_price_level * SELL_PRICE_PER_LEVEL

    @property
    def _mine_rate(self) -> float:
        return MINE_BASE_RATE + (self.mine_level - 1) * MINE_RATE_PER_LEVEL

    @property
    def _smelter_throughput(self) -> float:
        return self.smelter_machines * SMELTER_RATE * self._auto_mult

    @property
    def _craft_throughput(self) -> float:
        return self.craft_machines * CRAFT_RATE * self._auto_mult

    @property
    def _assembly_throughput(self) -> float:
        return self.assembly_machines * ASSEMBLY_RATE * self._auto_mult

    # ── tick ─────────────────────────────────────────────────────────────

    def tick(self, dt: float) -> None:
        """Advance the factory by *dt* seconds.

        Handles large *dt* (up to 3600) via linear throughput accumulation —
        no capping or no-oping on large dt.
        """
        # Stage 1: Mine — produce ore
        ore_produced = self._mine_rate * dt
        self.ore_stock = min(self.ore_stock + ore_produced, self.stock_cap)

        # Stage 2: Smelter — ore → ingot
        smelter_capacity = self._smelter_throughput * dt
        ingots_made = min(smelter_capacity, self.ore_stock)
        self.ore_stock -= ingots_made
        self.ingot_stock = min(self.ingot_stock + ingots_made, self.stock_cap)

        # Stage 3: Crafter — ingot → part
        craft_capacity = self._craft_throughput * dt
        parts_made = min(craft_capacity, self.ingot_stock)
        self.ingot_stock -= parts_made
        self.part_stock = min(self.part_stock + parts_made, self.stock_cap)

        # Stage 4: Assembler — part → device
        assembly_capacity = self._assembly_throughput * dt
        devices_made = min(assembly_capacity, self.part_stock)
        self.part_stock -= devices_made
        self.device_stock = min(self.device_stock + devices_made, self.stock_cap)

        # Stage 5: Sell — devices → money
        self.money += self.device_stock * self._sell_price
        self.device_stock = 0.0

    # ── upgrades ─────────────────────────────────────────────────────────

    def upgrades(self) -> list[Upgrade]:
        """Return currently available upgrades with cost scaled by level."""
        result: list[Upgrade] = []
        for defn in _UPGRADE_DEFS.values():
            level = self.upgrade_levels.get(defn.id, 0)
            if defn.max_level > 0 and level >= defn.max_level:
                continue
            cost = defn.cost * (defn.cost_scale ** level)
            result.append(
                Upgrade(
                    id=defn.id,
                    name=self._tr(f"upg_{defn.id}_name"),
                    description=self._tr(f"upg_{defn.id}_desc"),
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
        if self.money < upgrade.cost:
            return False

        self.money -= upgrade.cost
        level = self.upgrade_levels.get(upgrade_id, 0) + 1
        self.upgrade_levels[upgrade_id] = level
        self.stats.upgrades_bought += 1

        # Apply effects
        if upgrade_id == "mine_output":
            self.mine_level += 1
        elif upgrade_id == "smelter_machines":
            self.smelter_machines += 1
        elif upgrade_id == "craft_machines":
            self.craft_machines += 1
        elif upgrade_id == "assembly_machines":
            self.assembly_machines += 1
        elif upgrade_id == "sell_price":
            self.sell_price_level += 1
        elif upgrade_id == "storage" and not self.storage_expanded:
            self.storage_expanded = True
            self.stock_cap = BASE_STOCK_CAP * STORAGE_MULTIPLIER
        elif upgrade_id == "automation" and not self.automation_unlocked:
            self.automation_unlocked = True

        return True

    # ── serialisation ─────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict representing the full state."""
        return {
            "last_saved": self.last_saved,
            "paused": self.paused,
            "speed": self.speed,
            "stats": {
                "playtime_seconds": self.stats.playtime_seconds,
                "upgrades_bought": self.stats.upgrades_bought,
            },
            "money": self.money,
            "ore_stock": self.ore_stock,
            "ingot_stock": self.ingot_stock,
            "part_stock": self.part_stock,
            "device_stock": self.device_stock,
            "mine_level": self.mine_level,
            "smelter_machines": self.smelter_machines,
            "craft_machines": self.craft_machines,
            "assembly_machines": self.assembly_machines,
            "sell_price_level": self.sell_price_level,
            "storage_expanded": self.storage_expanded,
            "automation_unlocked": self.automation_unlocked,
            "upgrade_levels": dict(self.upgrade_levels),
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore full state from *data* (output of ``to_dict``)."""
        self.last_saved = data.get("last_saved", 0.0)
        self.paused = data.get("paused", False)
        self.speed = data.get("speed", 1)
        s = data.get("stats", {})
        self.stats = GameStats(
            playtime_seconds=s.get("playtime_seconds", 0.0),
            upgrades_bought=s.get("upgrades_bought", 0),
        )
        self.money = data.get("money", 0.0)
        self.ore_stock = data.get("ore_stock", 0.0)
        self.ingot_stock = data.get("ingot_stock", 0.0)
        self.part_stock = data.get("part_stock", 0.0)
        self.device_stock = data.get("device_stock", 0.0)
        self.mine_level = data.get("mine_level", 1)
        self.smelter_machines = data.get("smelter_machines", 1)
        self.craft_machines = data.get("craft_machines", 1)
        self.assembly_machines = data.get("assembly_machines", 1)
        self.sell_price_level = data.get("sell_price_level", 0)
        self.storage_expanded = data.get("storage_expanded", False)
        self.automation_unlocked = data.get("automation_unlocked", False)
        self.upgrade_levels = dict(data.get("upgrade_levels", {}))

        # Derive computed fields
        self.stock_cap = BASE_STOCK_CAP
        if self.storage_expanded:
            self.stock_cap *= STORAGE_MULTIPLIER

    # ── display helpers ───────────────────────────────────────────────

    def status_lines(self) -> list[str]:
        """Short status lines shown in the hub menu."""
        return [
            f"[bold green]{self._tr('stat_money').format(self.money)}[/]",
            f"[blue]{self._tr('stat_ore').format(self.ore_stock, self.stock_cap, self._mine_rate)}[/]",
            f"[cyan]{self._tr('stat_ingots').format(self.ingot_stock, self.stock_cap, self._smelter_throughput)}[/]",
            f"[yellow]{self._tr('stat_parts').format(self.part_stock, self.stock_cap, self._craft_throughput)}[/]",
            f"[magenta]{self._tr('stat_devices').format(self._assembly_throughput, self._sell_price)}[/]",
        ]

    @staticmethod
    def _render_bar(value: float, cap: float, width: int = BAR_WIDTH) -> str:
        """Return a progress bar string like '████░░░░'."""
        if cap <= 0:
            return "░" * width
        filled = int((value / cap) * width)
        filled = max(0, min(filled, width))
        return "█" * filled + "░" * (width - filled)

    def render_grid(self) -> str:
        """Return a colored production-chain overview using rich markup."""
        lines: list[str] = []

        # ── header ──────────────────────────────────────────────────────
        lines.append(f"[bold]{self._tr('grid_header')}[/]                    [bold green]💰 ${self.money:.1f}[/]")
        lines.append("─" * 44)

        # ── production stages ──────────────────────────────────────────
        stage_info = [
            ("ORE", self.ore_stock, f"{self._mine_rate:.1f}/s"),
            ("INGOT", self.ingot_stock, f"{self._smelter_throughput:.2f}/s"),
            ("PART", self.part_stock, f"{self._craft_throughput:.2f}/s"),
            ("DEVICE", self.device_stock, f"{self._assembly_throughput:.2f}/s"),
        ]
        colors = {"ORE": "blue", "INGOT": "cyan", "PART": "yellow", "DEVICE": "magenta"}

        for i, (sid, stock, rate_str) in enumerate(stage_info):
            c = colors[sid]
            sname = self._tr(f"stage_{sid}")
            bar = self._render_bar(stock, self.stock_cap)
            stock_str = f"{stock:.0f}/{self.stock_cap:.0f}"
            lines.append(f"  [{c}]{sname:<6} {bar}  {stock_str:>7}  ↑{rate_str}[/]")
            if i < len(stage_info) - 1:
                lines.append("    [dim]↓[/]")

        # ── footer ──────────────────────────────────────────────────────
        rates = (
            f"{self._mine_rate:.1f} → {self._smelter_throughput:.2f} → "
            f"{self._craft_throughput:.2f} → {self._assembly_throughput:.2f}"
        )
        lines.append("")
        lines.append(
            f"  [dim]Throughput: {rates}  |  Sell:[/dim]"
            f" [bold green]${self._sell_price:.2f}[/][dim]/ea[/]"
        )
        lines.append(
            "  [dim]  [blue]■[/blue] {}  [cyan]■[/cyan] {}"
            "  [yellow]■[/yellow] {}  [magenta]■[/magenta] {}[/dim]".format(
                self._tr("legend_ore"),
                self._tr("legend_ingot"),
                self._tr("legend_part"),
                self._tr("legend_device"),
            )
        )

        return "\n".join(lines)
