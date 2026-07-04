"""Space Colony — an idle game about building a self-sustaining colony.

🚀 Build modules, manage resources, grow your population, and survive
random space events.  Export surplus resources for credits and buy
upgrades to accelerate growth.
"""

from __future__ import annotations

import random
from typing import Any

from thatstui.core.game import Game, GameStats, Upgrade


# ── upgrade definitions ─────────────────────────────────────────────────

_UPGRADE_DEFS: dict[str, Upgrade] = {
    "solar_panel": Upgrade(
        id="solar_panel",
        name="Solar Panel",
        description="Build a solar panel (+1.0 energy/s)",
        cost=10,
    ),
    "greenhouse": Upgrade(
        id="greenhouse",
        name="Greenhouse",
        description="Build a greenhouse (+0.8 food/s, +0.5 oxygen/s)",
        cost=15,
    ),
    "water_purifier": Upgrade(
        id="water_purifier",
        name="Water Purifier",
        description="Build a water purifier (+0.8 water/s)",
        cost=12,
    ),
    "habitat": Upgrade(
        id="habitat",
        name="Habitat",
        description="Build a habitat (+4 pop cap)",
        cost=20,
    ),
    "shield": Upgrade(
        id="shield",
        name="Shield Generator",
        description="Build a shield generator (reduces event damage by 20%)",
        cost=30,
    ),
    "export_contract": Upgrade(
        id="export_contract",
        name="Export Contract",
        description="Double credits earned from surplus exports",
        cost=100,
        repeatable=False,
        max_level=1,
    ),
    "terraforming": Upgrade(
        id="terraforming",
        name="Terraforming",
        description="Passive +20% boost to all production",
        cost=200,
        repeatable=False,
        max_level=1,
    ),
}


# ── constants ──────────────────────────────────────────────────────────

PRODUCTION_RATES: dict[str, dict[str, float]] = {
    "solar_panel": {"energy": 1.0},
    "greenhouse": {"food": 0.8, "oxygen": 0.5},
    "water_purifier": {"water": 0.8},
}

CONSUMPTION_RATES: dict[str, float] = {
    "energy": 0.10,
    "food": 0.06,
    "water": 0.06,
    "oxygen": 0.04,
}

BASE_EXPORT_RATE = 0.12
POP_GROWTH_RATE = 0.02
POP_DECLINE_RATE = 0.005
BASE_POP_CAP = 5
POP_CAP_PER_HABITAT = 4
EVENT_INTERVAL_MIN = 60
EVENT_INTERVAL_MAX = 120

WIDTH = 44
HEIGHT = 16

# ── translations ────────────────────────────────────────────────────────

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Upgrade names
        "upg_solar_panel": "Solar Panel",
        "upg_greenhouse": "Greenhouse",
        "upg_water_purifier": "Water Purifier",
        "upg_habitat": "Habitat",
        "upg_shield": "Shield Generator",
        "upg_export_contract": "Export Contract",
        "upg_terraforming": "Terraforming",
        # Upgrade descriptions
        "desc_solar_panel": "Build a solar panel (+1.0 energy/s)",
        "desc_greenhouse": "Build a greenhouse (+0.8 food/s, +0.5 oxygen/s)",
        "desc_water_purifier": "Build a water purifier (+0.8 water/s)",
        "desc_habitat": "Build a habitat (+4 pop cap)",
        "desc_shield": "Build a shield generator (reduces event damage by 20%)",
        "desc_export_contract": "Double credits earned from surplus exports",
        "desc_terraforming": "Passive +20% boost to all production",
        # Status line labels
        "credits": "Credits",
        "pop": "Pop",
        "oxygen": "Oxygen",
        "water": "Water",
        "energy": "Energy",
        "food": "Food",
        # Grid header
        "grid_title": "Space Colony",
        "grid_pop": "Pop",
        # Event templates
        "event_meteor": "☄ Meteor strikes! Energy -{drain:.0f}",
        "event_solar_storm": "🌞 Solar storm! Energy -{drain:.0f}",
        "event_leak": "🔧 {resource} leak! {icon} -{drain:.0f}",
        # Resource names (for events)
        "oxygen_name": "Oxygen",
        "water_name": "Water",
        "food_name": "Food",
        # Keyword checks
        "keyword_leak": "leak",
        "keyword_meteor": "Meteor",
        "keyword_storm": "storm",
    },
    "uk": {
        "upg_solar_panel": "Сонячна панель",
        "upg_greenhouse": "Теплиця",
        "upg_water_purifier": "Очисник води",
        "upg_habitat": "Житло",
        "upg_shield": "Генератор щита",
        "upg_export_contract": "Експортний контракт",
        "upg_terraforming": "Тераформування",
        "desc_solar_panel": "Збудувати сонячну панель (+1.0 енергії/с)",
        "desc_greenhouse": "Збудувати теплицю (+0.8 їжі/с, +0.5 кисню/с)",
        "desc_water_purifier": "Збудувати очисник води (+0.8 води/с)",
        "desc_habitat": "Збудувати житло (+4 до ліміту населення)",
        "desc_shield": "Збудувати генератор щита (зменшує шкоду від подій на 20%)",
        "desc_export_contract": "Подвоїти кредити від надлишкового експорту",
        "desc_terraforming": "Пасивний +20% приріст до всього виробництва",
        "credits": "Кредити",
        "pop": "Населення",
        "oxygen": "Кисень",
        "water": "Вода",
        "energy": "Енергія",
        "food": "Їжа",
        "grid_title": "Космічна Колонія",
        "grid_pop": "Насел",
        "event_meteor": "☄ Метеорит! Енергія -{drain:.0f}",
        "event_solar_storm": "🌞 Сонячна буря! Енергія -{drain:.0f}",
        "event_leak": "🔧 Витік {resource}! {icon} -{drain:.0f}",
        "oxygen_name": "Кисень",
        "water_name": "Вода",
        "food_name": "Їжа",
        "keyword_leak": "витік",
        "keyword_meteor": "Метеорит",
        "keyword_storm": "буря",
    },
}


class SpaceColony(Game):
    """Space Colony idle game."""

    game_id = "space_colony"
    name = "Space Colony"
    emoji = "🚀"

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        # Initialise ALL fields before super().__init__ because from_dict
        # may need them to exist already.
        self.credits: float = 0.0
        self.oxygen: float = 0.0
        self.water: float = 0.0
        self.energy: float = 0.0
        self.food: float = 0.0
        self.population: int = 0
        self.solar_panels: int = 0
        self.greenhouses: int = 0
        self.water_purifiers: int = 0
        self.habitats: int = 0
        self.shields: int = 0
        self.upgrade_levels: dict[str, int] = {}
        self.export_rate: float = BASE_EXPORT_RATE
        self.terraforming_unlocked: bool = False
        self.event_log: list[str] = []
        self._event_timer: float = 0.0

        super().__init__(data)

        if data is None:
            # Fresh game initialisation
            self.credits = 0.0
            self.oxygen = 20.0
            self.water = 20.0
            self.energy = 20.0
            self.food = 20.0
            self.population = 3
            self.solar_panels = 1
            self.greenhouses = 1
            self.water_purifiers = 1
            self.habitats = 1
            self.shields = 1
            self.export_rate = BASE_EXPORT_RATE
            self.terraforming_unlocked = False
            self.event_log = []
            self._event_timer = random.uniform(
                EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX
            )

    # ── translation helper ───────────────────────────────────────────

    def _tr(self, key: str) -> str:
        """Look up a translated string by key based on ``self.lang``."""
        strings = _STRINGS.get(self.lang, _STRINGS["en"])
        return strings.get(key, _STRINGS["en"].get(key, key))

    # ── convenience properties ────────────────────────────────────────

    @property
    def pop_cap(self) -> int:
        return BASE_POP_CAP + self.habitats * POP_CAP_PER_HABITAT

    @property
    def production_bonus(self) -> float:
        return 1.2 if self.terraforming_unlocked else 1.0

    @property
    def shield_reduction(self) -> float:
        # Each shield reduces event impact by 20 %, capped at 80 %.
        return min(0.8, self.shields * 0.2)

    # ── tick ──────────────────────────────────────────────────────────

    def tick(self, dt: float) -> None:
        """Advance colony by *dt* seconds.

        Handles arbitrarily large *dt* by processing in 60-second chunks
        so that random events fire at appropriate intervals even during
        offline catch-up.  All resource deltas are linear in dt.
        """
        remaining = dt
        chunk = 60.0
        while remaining > 0:
            step = chunk if remaining > chunk else remaining
            self._tick_step(step)
            remaining -= step

    def _tick_step(self, dt: float) -> None:
        """Process one sub-tick (``dt <= 60``)."""
        bonus = self.production_bonus

        # ── production ──
        energy_prod = (
            self.solar_panels * PRODUCTION_RATES["solar_panel"]["energy"] * bonus
        )
        food_prod = (
            self.greenhouses * PRODUCTION_RATES["greenhouse"]["food"] * bonus
        )
        oxygen_prod = (
            self.greenhouses * PRODUCTION_RATES["greenhouse"]["oxygen"] * bonus
        )
        water_prod = (
            self.water_purifiers
            * PRODUCTION_RATES["water_purifier"]["water"]
            * bonus
        )

        # ── consumption ──
        energy_cons = CONSUMPTION_RATES["energy"] * self.population
        food_cons = CONSUMPTION_RATES["food"] * self.population
        water_cons = CONSUMPTION_RATES["water"] * self.population
        oxygen_cons = CONSUMPTION_RATES["oxygen"] * self.population

        # ── apply net deltas to stocks (linear in dt) ──
        self.energy += (energy_prod - energy_cons) * dt
        self.food += (food_prod - food_cons) * dt
        self.water += (water_prod - water_cons) * dt
        self.oxygen += (oxygen_prod - oxygen_cons) * dt

        # ── export surplus food / water / oxygen as credits ──
        surplus = (
            max(0.0, food_prod - food_cons)
            + max(0.0, water_prod - water_cons)
            + max(0.0, oxygen_prod - oxygen_cons)
        )
        self.credits += surplus * self.export_rate * dt

        # ── population dynamics ──
        if (
            self.energy > 0
            and self.food > 0
            and self.water > 0
            and self.oxygen > 0
        ):
            if self.population < self.pop_cap:
                growth = POP_GROWTH_RATE * self.population * dt
                n = int(growth)
                if random.random() < growth - n:
                    n += 1
                self.population = min(self.pop_cap, self.population + n)
        else:
            if self.population > 1:
                decline = POP_DECLINE_RATE * self.population * dt
                n = int(decline)
                if random.random() < decline - n:
                    n += 1
                self.population = max(1, self.population - n)

        # ── random events ──
        self._event_timer -= dt
        if self._event_timer <= 0:
            self._trigger_event()
            self._event_timer = random.uniform(
                EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX
            )

    # ── events ────────────────────────────────────────────────────────

    def _trigger_event(self) -> None:
        """Pick a random space event and apply its effects.

        All events are resource drains — they do **not** destroy modules,
        so the colony always remains self-sustaining.  Shields reduce the
        magnitude of each drain.
        """
        event_type = random.choice(["meteor", "solar_storm", "equipment_failure"])
        reduction = 1.0 - self.shield_reduction

        if event_type == "meteor":
            drain = 12.0 * reduction
            self.energy = max(-20.0, self.energy - drain)
            self.event_log.insert(
                0, self._tr("event_meteor").format(drain=drain)
            )

        elif event_type == "solar_storm":
            drain = 15.0 * reduction
            self.energy = max(-20.0, self.energy - drain)
            self.event_log.insert(
                0, self._tr("event_solar_storm").format(drain=drain)
            )

        elif event_type == "equipment_failure":
            resource = random.choice(["oxygen", "water", "food"])
            drain = 10.0 * reduction
            current = getattr(self, resource)
            setattr(self, resource, max(-20.0, current - drain))
            icons = {"oxygen": "O₂", "water": "💧", "food": "🍔"}
            self.event_log.insert(
                0,
                self._tr("event_leak").format(
                    resource=self._tr(resource + "_name"),
                    icon=icons[resource],
                    drain=drain,
                ),
            )

        self.event_log = self.event_log[:3]

    # ── upgrades ──────────────────────────────────────────────────────

    def upgrades(self) -> list[Upgrade]:
        """Return currently available upgrades with cost scaled by level."""
        result: list[Upgrade] = []
        for defn in _UPGRADE_DEFS.values():
            level = self.upgrade_levels.get(defn.id, 0)
            if defn.max_level > 0 and level >= defn.max_level:
                continue
            cost = defn.cost * (defn.cost_scale**level)
            result.append(
                Upgrade(
                    id=defn.id,
                    name=self._tr("upg_" + defn.id),
                    description=self._tr("desc_" + defn.id),
                    cost=cost,
                    cost_scale=defn.cost_scale,
                    repeatable=defn.repeatable,
                    max_level=defn.max_level,
                )
            )
        return result

    def buy_upgrade(self, upgrade_id: str) -> bool:
        """Attempt to purchase *upgrade_id*."""
        available = self.upgrades()
        target = next((u for u in available if u.id == upgrade_id), None)
        if target is None:
            return False
        if self.credits < target.cost:
            return False

        self.credits -= target.cost
        level = self.upgrade_levels.get(upgrade_id, 0) + 1
        self.upgrade_levels[upgrade_id] = level
        self.stats.upgrades_bought += 1

        # Apply effect
        if upgrade_id == "solar_panel":
            self.solar_panels += 1
        elif upgrade_id == "greenhouse":
            self.greenhouses += 1
        elif upgrade_id == "water_purifier":
            self.water_purifiers += 1
        elif upgrade_id == "habitat":
            self.habitats += 1
        elif upgrade_id == "shield":
            self.shields += 1
        elif upgrade_id == "export_contract":
            self.export_rate *= 2
        elif upgrade_id == "terraforming":
            self.terraforming_unlocked = True

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
            "credits": self.credits,
            "oxygen": self.oxygen,
            "water": self.water,
            "energy": self.energy,
            "food": self.food,
            "population": self.population,
            "solar_panels": self.solar_panels,
            "greenhouses": self.greenhouses,
            "water_purifiers": self.water_purifiers,
            "habitats": self.habitats,
            "shields": self.shields,
            "upgrade_levels": dict(self.upgrade_levels),
            "export_rate": self.export_rate,
            "terraforming_unlocked": self.terraforming_unlocked,
            "event_log": list(self.event_log),
            "_event_timer": self._event_timer,
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
        self.credits = data.get("credits", 0.0)
        self.oxygen = data.get("oxygen", 0.0)
        self.water = data.get("water", 0.0)
        self.energy = data.get("energy", 0.0)
        self.food = data.get("food", 0.0)
        self.population = data.get("population", 0)
        self.solar_panels = data.get("solar_panels", 0)
        self.greenhouses = data.get("greenhouses", 0)
        self.water_purifiers = data.get("water_purifiers", 0)
        self.habitats = data.get("habitats", 0)
        self.shields = data.get("shields", 0)
        self.upgrade_levels = dict(data.get("upgrade_levels", {}))
        self.export_rate = data.get("export_rate", BASE_EXPORT_RATE)
        self.terraforming_unlocked = data.get("terraforming_unlocked", False)
        self.event_log = list(data.get("event_log", []))
        self._event_timer = data.get(
            "_event_timer",
            random.uniform(EVENT_INTERVAL_MIN, EVENT_INTERVAL_MAX),
        )

    # ── display ───────────────────────────────────────────────────────

    def status_lines(self) -> list[str]:
        return [
            f"💰 {self._tr('credits')}: [green]{self.credits:.1f}[/]  "
            f"👨‍🚀 {self._tr('pop')}: [cyan]{self.population}/{self.pop_cap}[/]",
            f"[yellow]⚡ {self._tr('energy')}: {self.energy:.1f}[/]  "
            f"[green]🍔 {self._tr('food')}: {self.food:.1f}[/]  "
            f"[blue]💧 {self._tr('water')}: {self.water:.1f}[/]  "
            f"[cyan]O₂ {self._tr('oxygen')}: {self.oxygen:.1f}[/]",
        ]

    def render_grid(self) -> str:
        """Return an ASCII schematic of the colony (~44 × 16)."""
        content_width = WIDTH - 2  # space between ║ borders
        lines: list[str] = []

        # ── top border ──
        lines.append(f"╔{'═' * content_width}╗")

        # ── title ──
        title = (
            f"[bold]{self.emoji} {self._tr('grid_title')}[/]  |  "
            f"👨‍🚀 [cyan]{self._tr('grid_pop')} {self.population}[/]  |  "
            f"💳 [green]{self.credits:.1f}[/]"
        )
        lines.append(f"║ {title:<{content_width - 2}} ║")

        # ── modules row ──
        parts: list[str] = []
        if self.solar_panels:
            parts.append(f"[yellow]☀[/]{self.solar_panels}")
        if self.greenhouses:
            parts.append(f"[green]🌱[/]{self.greenhouses}")
        if self.water_purifiers:
            parts.append(f"[blue]💧[/]{self.water_purifiers}")
        if self.habitats:
            parts.append(f"[cyan]🏠[/]{self.habitats}")
        if self.shields:
            parts.append(f"[magenta]🛡[/]{self.shields}")
        modules_str = "  ".join(parts) if parts else "(no modules)"
        lines.append(f"║ {modules_str:^{content_width - 2}} ║")

        # ── separator ──
        lines.append(f"╠{'═' * content_width}╣")

        # ── resource bars (4 rows) ──
        bar_width = 14
        resource_colors = {
            "oxygen": "cyan",
            "water": "blue",
            "energy": "yellow",
            "food": "green",
        }
        resources = [
            ("O₂", self.oxygen, "oxygen"),
            ("💧", self.water, "water"),
            ("⚡", self.energy, "energy"),
            ("🍔", self.food, "food"),
        ]
        for icon, stock, res_name in resources:
            color = resource_colors[res_name]
            prod = self._production_rate(res_name)
            cons = self._consumption_rate(res_name)
            net = prod - cons
            rate_str = f"{net:+.2f}/s"
            max_stock = max(stock, 50.0)
            filled = max(0, min(bar_width, int((stock / max_stock) * bar_width)))
            fill_ratio = stock / max_stock if max_stock > 0 else 0
            bar_color = "red" if fill_ratio < 0.2 else color
            bar_fill = "█" * filled
            bar_empty = "░" * (bar_width - filled)
            bar = f"[{bar_color}]{bar_fill}{bar_empty}[/]"
            resource_line = f" {icon} {stock:5.1f} {bar} {rate_str}"
            lines.append(f"║{resource_line:<{content_width}}║")

        # ── separator ──
        lines.append(f"╠{'═' * content_width}╣")

        # ── stats line ──
        stats_line = (
            f"👨‍🚀 [cyan]{self.population}/{self.pop_cap}[/]  "
            f"💰 [green]{self.credits:.1f}[/]  "
            f"🛡 {self.shield_reduction * 100:.0f}%"
        )
        lines.append(f"║{stats_line:^{content_width}}║")

        # ── separator ──
        lines.append(f"╠{'═' * content_width}╣")

        # ── spacer ──
        lines.append(f"║{'':{content_width}}║")

        # ── event log (up to 3 lines) ──
        for i in range(3):
            if i < len(self.event_log):
                event = self.event_log[i]
                en_s = _STRINGS["en"]
                uk_s = _STRINGS["uk"]
                if en_s["keyword_leak"] in event or uk_s["keyword_leak"] in event:
                    event_colored = f"[yellow]{event}[/]"
                elif (
                    en_s["keyword_meteor"] in event
                    or en_s["keyword_storm"] in event
                    or uk_s["keyword_meteor"] in event
                    or uk_s["keyword_storm"] in event
                ):
                    event_colored = f"[red]{event}[/]"
                else:
                    event_colored = event
                lines.append(f"║ {event_colored:<{content_width - 1}}║")
            else:
                lines.append(f"║{'':{content_width}}║")

        # ── bottom border ──
        lines.append(f"╚{'═' * content_width}╝")

        return "\n".join(lines)

    # ── rate helpers ──────────────────────────────────────────────────

    def _production_rate(self, resource: str) -> float:
        """Total production per second for *resource*."""
        bonus = self.production_bonus
        if resource == "energy":
            return (
                self.solar_panels
                * PRODUCTION_RATES["solar_panel"]["energy"]
                * bonus
            )
        if resource == "food":
            return (
                self.greenhouses
                * PRODUCTION_RATES["greenhouse"]["food"]
                * bonus
            )
        if resource == "oxygen":
            return (
                self.greenhouses
                * PRODUCTION_RATES["greenhouse"]["oxygen"]
                * bonus
            )
        if resource == "water":
            return (
                self.water_purifiers
                * PRODUCTION_RATES["water_purifier"]["water"]
                * bonus
            )
        return 0.0

    def _consumption_rate(self, resource: str) -> float:
        return CONSUMPTION_RATES.get(resource, 0.0) * self.population
