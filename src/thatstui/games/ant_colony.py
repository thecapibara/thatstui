"""Ant Colony — the reference idle game.

🐜 Build and manage an ant colony.  Ants forage for food, the queen
lays eggs, and the player buys upgrades to accelerate growth.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from thatstui.core.game import Game, GameStats, Upgrade


# ── internal data structures ──────────────────────────────────────────

@dataclass
class Ant:
    x: float = 0.0
    y: float = 0.0
    carrying_food: float = 0.0
    returning: bool = False
    explore: bool = False  # scout ant — wanders farther


@dataclass
class FoodSource:
    x: float = 0.0
    y: float = 0.0
    amount: float = 10.0


# ── upgrade definitions (base config) ─────────────────────────────────

_UPGRADE_DEFS: dict[str, Upgrade] = {
    "forage_radius": Upgrade(
        id="forage_radius",
        name="Forage Radius",
        description="Ants search farther for food",
        cost=10,
        max_level=20,
    ),
    "ant_speed": Upgrade(
        id="ant_speed",
        name="Ant Speed",
        description="Ants move faster",
        cost=15,
    ),
    "queen_fertility": Upgrade(
        id="queen_fertility",
        name="Queen Fertility",
        description="Queen lays eggs faster",
        cost=20,
    ),
    "max_population": Upgrade(
        id="max_population",
        name="Max Population",
        description="Raise the colony's population cap",
        cost=25,
    ),
    "scout_ants": Upgrade(
        id="scout_ants",
        name="Scout Ants",
        description="Unlock scout ants — 10% explore farther",
        cost=100,
        repeatable=False,
        max_level=1,
    ),
}

# ── localisation strings ────────────────────────────────────────────

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Upgrade names
        "upgrade_forage_radius": "Forage Radius",
        "upgrade_forage_radius_desc": "Ants search farther for food",
        "upgrade_ant_speed": "Ant Speed",
        "upgrade_ant_speed_desc": "Ants move faster",
        "upgrade_queen_fertility": "Queen Fertility",
        "upgrade_queen_fertility_desc": "Queen lays eggs faster",
        "upgrade_max_population": "Max Population",
        "upgrade_max_population_desc": "Raise the colony's population cap",
        "upgrade_scout_ants": "Scout Ants",
        "upgrade_scout_ants_desc": "Unlock scout ants — 10% explore farther",
        # Status lines
        "food_label": "🍗 Food: [green]{:.1f}[/]",
        "pop_label": "🐜 Pop: [cyan]{}[/]/[cyan]{}[/]",
        "eggs_label": "🥚 Eggs: [yellow]{:.2f}[/]",
        # Grid header
        "grid_title": "🐜 Ant Colony",
        "grid_pop": "Pop",
        # Grid footer legend
        "legend_ant": "ant",
        "legend_carrying": "carrying",
        "legend_scout": "scout",
        "legend_food": "food",
        "legend_nest": "nest",
    },
    "uk": {
        "upgrade_forage_radius": "Радіус збору",
        "upgrade_forage_radius_desc": "Мурашки шукають їжу далі",
        "upgrade_ant_speed": "Швидкість мурах",
        "upgrade_ant_speed_desc": "Мурахи рухаються швидше",
        "upgrade_queen_fertility": "Плідність королеви",
        "upgrade_queen_fertility_desc": "Королева відкладає яйця швидше",
        "upgrade_max_population": "Макс. населення",
        "upgrade_max_population_desc": "Збільшити ліміт населення колонії",
        "upgrade_scout_ants": "Мурахи-розвідники",
        "upgrade_scout_ants_desc": "Відкриває мурах-розвідників — 10% шукають далі",
        "food_label": "🍗 Їжа: [green]{:.1f}[/]",
        "pop_label": "🐜 Насел: [cyan]{}[/]/[cyan]{}[/]",
        "eggs_label": "🥚 Яйця: [yellow]{:.2f}[/]",
        "grid_title": "🐜 Мурашник",
        "grid_pop": "Насел",
        "legend_ant": "мураха",
        "legend_carrying": "несе",
        "legend_scout": "розвідник",
        "legend_food": "їжа",
        "legend_nest": "гніздо",
    },
}

# ── game constants ────────────────────────────────────────────────────

WIDTH = 40
HEIGHT = 12
NEST_X = WIDTH // 2
NEST_Y = HEIGHT // 2
MAX_ANTS = 200


# ── game class ─────────────────────────────────────────────────────────

class AntColony(Game):
    """Ant Colony idle game."""

    game_id = "ant_colony"
    name = "Ant Colony"
    emoji = "🐜"

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        # Set these before super().__init__ because from_dict depends on them
        self.ants: list[Ant] = []
        self.food_sources: list[FoodSource] = []
        self.upgrade_levels: dict[str, int] = {}
        self.food: float = 0.0
        self.population: int = 0
        self.eggs: float = 0.0
        self.forage_radius: int = 5
        self.ant_speed: float = 1.0
        self.queen_fertility: float = 0.5
        self.max_population: int = 50
        self.scout_unlocked: bool = False

        super().__init__(data)

        if data is None:
            # Fresh game initialisation
            self.food = 20.0
            self.population = 3
            # Spawn initial ants
            for _ in range(3):
                self._spawn_ant()
            # Scatter initial food sources
            for _ in range(6):
                self._add_food_source()

    # ── tick ──────────────────────────────────────────────────────────

    def tick(self, dt: float) -> None:
        """Advance the colony by *dt* seconds."""
        # Cap to avoid huge jumps
        dt = min(dt, 10.0)

        self._queen_phase(dt)
        self._hatch_eggs()
        self._move_ants(dt)
        self._cleanup()
        self._regrow_food(dt)

    def _queen_phase(self, dt: float) -> None:
        """Queen consumes food and produces eggs."""
        if self.food <= 0:
            return
        consumption = self.queen_fertility * dt * 0.5
        consumed = min(self.food, max(0.1, consumption))
        self.food -= consumed
        # Convert consumed food into eggs (0.2 eggs per unit food)
        self.eggs += consumed * self.queen_fertility * 0.2

    def _hatch_eggs(self) -> None:
        """Hatch accumulated eggs into ants."""
        while self.eggs >= 1.0 and len(self.ants) < min(self.max_population, MAX_ANTS):
            self.eggs -= 1.0
            self.population += 1
            self._spawn_ant()

    def _spawn_ant(self) -> None:
        """Place a new ant near the nest."""
        x = NEST_X + random.uniform(-1.5, 1.5)
        y = NEST_Y + random.uniform(-1.5, 1.5)
        x = max(0.0, min(float(WIDTH - 1), x))
        y = max(0.0, min(float(HEIGHT - 1), y))
        ant = Ant(x=x, y=y)
        if self.scout_unlocked and random.random() < 0.10:
            ant.explore = True
        self.ants.append(ant)

    def _move_ants(self, dt: float) -> None:
        """Move each ant toward food / nest."""
        for ant in self.ants:
            self._move_ant(ant, dt)

    def _move_ant(self, ant: Ant, dt: float) -> None:
        speed = self.ant_speed * (1.5 if ant.explore else 1.0)
        dist = speed * dt

        if ant.returning:
            self._move_toward(ant, float(NEST_X), float(NEST_Y), dist)
            # Check if nest reached
            if math.hypot(ant.x - NEST_X, ant.y - NEST_Y) < 0.8:
                self.food += ant.carrying_food
                ant.carrying_food = 0.0
                ant.returning = False
        else:
            target = self._find_closest_food(ant.x, ant.y)
            if target is not None:
                self._move_toward(ant, target.x, target.y, dist)
                if math.hypot(ant.x - target.x, ant.y - target.y) < 0.8:
                    take = min(1.0, target.amount)
                    ant.carrying_food = take
                    target.amount -= take
                    ant.returning = True
            else:
                # No food nearby — wander
                wander = dist * (3.0 if ant.explore else 1.0)
                ant.x += random.uniform(-wander, wander)
                ant.y += random.uniform(-wander, wander)

        # Clamp to bounds
        ant.x = max(0.0, min(float(WIDTH - 1), ant.x))
        ant.y = max(0.0, min(float(HEIGHT - 1), ant.y))

    @staticmethod
    def _move_toward(ant: Ant, tx: float, ty: float, dist: float) -> None:
        dx = tx - ant.x
        dy = ty - ant.y
        d = math.hypot(dx, dy)
        if d > 0.01:
            step = min(dist, d)
            ant.x += (dx / d) * step
            ant.y += (dy / d) * step

    def _find_closest_food(self, x: float, y: float) -> FoodSource | None:
        radius = self.forage_radius
        candidates = [
            fs
            for fs in self.food_sources
            if abs(fs.x - x) <= radius and abs(fs.y - y) <= radius
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda fs: (fs.x - x) ** 2 + (fs.y - y) ** 2)

    def _cleanup(self) -> None:
        """Remove depleted food sources."""
        self.food_sources = [fs for fs in self.food_sources if fs.amount > 0.0]

    def _regrow_food(self, dt: float) -> None:
        """Periodically spawn new food sources when few remain."""
        if len(self.food_sources) < 4 and random.random() < dt * 0.03:
            self._add_food_source()

    def _add_food_source(self) -> None:
        """Place a new food source away from the nest."""
        for _ in range(50):
            x = random.uniform(1.0, float(WIDTH - 2))
            y = random.uniform(1.0, float(HEIGHT - 2))
            if abs(x - NEST_X) >= 3 or abs(y - NEST_Y) >= 3:
                self.food_sources.append(
                    FoodSource(x=x, y=y, amount=random.uniform(8.0, 18.0))
                )
                return

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
                    name=self._tr(f"upgrade_{defn.id}"),
                    description=self._tr(f"upgrade_{defn.id}_desc"),
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
        if self.food < upgrade.cost:
            return False

        self.food -= upgrade.cost
        level = self.upgrade_levels.get(upgrade_id, 0) + 1
        self.upgrade_levels[upgrade_id] = level
        self.stats.upgrades_bought += 1

        # Apply effect
        if upgrade_id == "forage_radius":
            self.forage_radius = 5 + level
        elif upgrade_id == "ant_speed":
            self.ant_speed = 1.0 + level * 0.2
        elif upgrade_id == "queen_fertility":
            self.queen_fertility = 0.5 + level * 0.1
        elif upgrade_id == "max_population":
            self.max_population = 50 + level * 10
        elif upgrade_id == "scout_ants":
            self.scout_unlocked = True

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
            "food": self.food,
            "population": self.population,
            "eggs": self.eggs,
            "ants": [
                {
                    "x": a.x,
                    "y": a.y,
                    "carrying_food": a.carrying_food,
                    "returning": a.returning,
                    "explore": a.explore,
                }
                for a in self.ants
            ],
            "food_sources": [
                {"x": fs.x, "y": fs.y, "amount": fs.amount}
                for fs in self.food_sources
            ],
            "upgrade_levels": dict(self.upgrade_levels),
            "forage_radius": self.forage_radius,
            "ant_speed": self.ant_speed,
            "queen_fertility": self.queen_fertility,
            "max_population": self.max_population,
            "scout_unlocked": self.scout_unlocked,
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
        self.food = data["food"]
        self.population = data["population"]
        self.eggs = data["eggs"]
        self.ants = [Ant(**a) for a in data["ants"]]
        self.food_sources = [FoodSource(**fs) for fs in data["food_sources"]]
        self.upgrade_levels = dict(data.get("upgrade_levels", {}))
        self.forage_radius = data["forage_radius"]
        self.ant_speed = data["ant_speed"]
        self.queen_fertility = data["queen_fertility"]
        self.max_population = data["max_population"]
        self.scout_unlocked = data["scout_unlocked"]

    # ── localisation helper ───────────────────────────────────────────

    def _tr(self, key: str) -> str:
        """Look up a UI string for the current language."""
        return _STRINGS.get(self.lang, _STRINGS["en"]).get(key, key)

    # ── display helpers ───────────────────────────────────────────────

    def status_lines(self) -> list[str]:
        return [
            self._tr("food_label").format(self.food),
            self._tr("pop_label").format(len(self.ants), self.max_population),
            self._tr("eggs_label").format(self.eggs),
        ]

    def render_grid(self) -> str:
        """Return the coloured map of the colony as a multi-line string."""
        # Initialise grid with dim ground
        grid: list[list[str]] = [["[dim]·[/]"] * WIDTH for _ in range(HEIGHT)]

        # Food sources — green bold
        for fs in self.food_sources:
            x, y = int(round(fs.x)), int(round(fs.y))
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                grid[y][x] = "[bold green]*[/]"

        # Nest — yellow bold (overwrites food so the nest is always visible)
        grid[NEST_Y][NEST_X] = "[bold yellow]◉[/]"

        # Ants (do not overwrite nest)
        for ant in self.ants:
            x, y = int(round(ant.x)), int(round(ant.y))
            if 0 <= x < WIDTH and 0 <= y < HEIGHT and (x != NEST_X or y != NEST_Y):
                if ant.carrying_food > 0:
                    grid[y][x] = "[bold green]A[/]"
                elif ant.explore:
                    grid[y][x] = "[magenta]a[/]"
                else:
                    grid[y][x] = "[red]a[/]"

        # Coloured header
        header = (
            f"[bold]{self._tr('grid_title')}[/]  |  🍗 [green]{self.food:.1f}[/]  "
            f"|  {self._tr('grid_pop')} [cyan]{len(self.ants)}[/]/[cyan]{self.max_population}[/]  "
            f"|  🥚 [yellow]{self.eggs:.1f}[/]"
        )

        # Coloured footer: thin rule + legend
        footer = (
            f"[dim]{'─' * WIDTH}[/]\n"
            f"[red]a[/] {self._tr('legend_ant')}  [bold green]A[/] {self._tr('legend_carrying')}  "
            f"[magenta]a[/] {self._tr('legend_scout')}  [bold green]*[/] {self._tr('legend_food')}  "
            f"[bold yellow]◉[/] {self._tr('legend_nest')}"
        )

        return header + "\n" + "\n".join("".join(row) for row in grid) + "\n" + footer
