"""Forest — an ecosystem idle game.

🌲 Grow a forest, introduce wildlife, and watch the ecosystem balance itself.
Trees grow and spread, herbivores graze, and carnivores hunt.
"""

from __future__ import annotations

import math
import random
from typing import Any

from thatstui.core.game import Game, GameStats, Upgrade


# ── constants ────────────────────────────────────────────────────────────

WIDTH = 40
HEIGHT = 14
MAX_TREES = 80
MAX_HERBIVORES = 40
MAX_CARNIVORES = 20

# Tree stage thresholds (seconds of simulated age)
AGE_SEEDLING_MAX = 15.0  # . -> t
AGE_SAPLING_MAX = 60.0  # t -> T
AGE_TREE_MAX = 300.0  # T -> ♣
AGE_OLD_MAX = 600.0  # ♣ dies

# Seed spread
SEED_INTERVAL = 20.0  # seconds between spread events
BASE_SEED_PROB = 0.30  # per mature tree per interval

# Animal movement chunk size (avoids hyper-movement on large dt)
MOVE_CHUNK = 10.0  # seconds per movement step

# Ecology chunk size — processes tree lifecycles in smaller steps so that
# trees can reproduce before dying of old age during large-dt ticks.
ECOLOGY_CHUNK = 60.0

# Animal speeds (cells / second)
HERBIVORE_SPEED = 0.8
CARNIVORE_SPEED = 1.2

# Energy
HERBIVORE_ENERGY_DECAY = 0.04  # per second
CARNIVORE_ENERGY_DECAY = 0.03
HERBIVORE_EAT_ENERGY = 4.0  # energy gained per tree eaten
CARNIVORE_EAT_ENERGY = 10.0  # energy gained per herbivore eaten
HERBIVORE_REPRODUCE_THRESHOLD = 8.0
CARNIVORE_REPRODUCE_THRESHOLD = 12.0
HERBIVORE_REPRODUCE_COST = 4.0
CARNIVORE_REPRODUCE_COST = 6.0
HERBIVORE_START_ENERGY = 6.0
CARNIVORE_START_ENERGY = 10.0
HERBIVORE_REPRO_RATE = 0.008  # Poisson rate per second
CARNIVORE_REPRO_RATE = 0.005
HERBIVORE_EAT_RADIUS = 1.0
CARNIVORE_EAT_RADIUS = 1.2
HERBIVORE_SEEK_RADIUS = 8.0
CARNIVORE_SEEK_RADIUS = 10.0

# Biomass generated per second per tree stage (0–3)
BIOMASS_RATES = (0.04, 0.10, 0.22, 0.35)

# Biomass yielded on death per tree stage
DEATH_BIOMASS = (0.0, 0.5, 2.0, 5.0)

# Tree display characters by stage
TREE_CHARS = (".", "t", "T", "♣")


# ── helpers ──────────────────────────────────────────────────────────────

def tree_stage(age: float) -> int:
    """0=seedling, 1=sapling, 2=tree, 3=old."""
    if age < AGE_SEEDLING_MAX:
        return 0
    if age < AGE_SAPLING_MAX:
        return 1
    if age < AGE_TREE_MAX:
        return 2
    return 3


def tree_sym(age: float) -> str:
    """Single character representing a tree of the given age."""
    return TREE_CHARS[tree_stage(age)]


# ── upgrade definitions (base config) ───────────────────────────────────

_UPGRADE_DEFS: dict[str, Upgrade] = {
    "plant_trees": Upgrade(
        id="plant_trees",
        name="Plant Trees",
        description="Instantly adds trees and boosts seed spread rate",
        cost=8.0,
        cost_scale=1.15,
    ),
    "introduce_herbivores": Upgrade(
        id="introduce_herbivores",
        name="Introduce Herbivores",
        description="Add herbivores to the ecosystem",
        cost=25.0,
        cost_scale=1.15,
    ),
    "introduce_carnivores": Upgrade(
        id="introduce_carnivores",
        name="Introduce Carnivores",
        description="Add carnivores to balance the ecosystem",
        cost=100.0,
        cost_scale=1.15,
    ),
    "fertilize": Upgrade(
        id="fertilize",
        name="Fertilize Soil",
        description="Increase soil fertility for faster growth and seed spread",
        cost=15.0,
        cost_scale=1.15,
    ),
    "rain_ritual": Upgrade(
        id="rain_ritual",
        name="Rain Ritual",
        description="Boost overall growth rate with periodic rain",
        cost=30.0,
        cost_scale=1.15,
    ),
    "biodiversity": Upgrade(
        id="biodiversity",
        name="Biodiversity",
        description="Old trees yield double biomass when they die",
        cost=80.0,
        repeatable=False,
        max_level=1,
    ),
}


# ── translations ─────────────────────────────────────────────────────────

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Upgrade names
        "upgrade_plant_trees_name": "Plant Trees",
        "upgrade_plant_trees_desc": "Instantly adds trees and boosts seed spread rate",
        "upgrade_introduce_herbivores_name": "Introduce Herbivores",
        "upgrade_introduce_herbivores_desc": "Add herbivores to the ecosystem",
        "upgrade_introduce_carnivores_name": "Introduce Carnivores",
        "upgrade_introduce_carnivores_desc": "Add carnivores to balance the ecosystem",
        "upgrade_fertilize_name": "Fertilize Soil",
        "upgrade_fertilize_desc": "Increase soil fertility for faster growth and seed spread",
        "upgrade_rain_ritual_name": "Rain Ritual",
        "upgrade_rain_ritual_desc": "Boost overall growth rate with periodic rain",
        "upgrade_biodiversity_name": "Biodiversity",
        "upgrade_biodiversity_desc": "Old trees yield double biomass when they die",
        # Status labels
        "status_biomass": "Biomass",
        "status_trees": "Trees",
        "status_herbivores": "Herbivores",
        "status_carnivores": "Carnivores",
        "status_fertility": "Fertility",
        # Grid header
        "grid_header_forest": "Forest",
        # Grid legend
        "legend_sapling": "sapling",
        "legend_tree": "tree",
        "legend_old": "old",
        "legend_herbivore": "herbivore",
        "legend_carnivore": "carnivore",
    },
    "uk": {
        "upgrade_plant_trees_name": "Посадити дерева",
        "upgrade_plant_trees_desc": "Миттєво додає дерева і пришвидшує поширення насіння",
        "upgrade_introduce_herbivores_name": "Заселити травоїдних",
        "upgrade_introduce_herbivores_desc": "Додає травоїдних в екосистему",
        "upgrade_introduce_carnivores_name": "Заселити хижаків",
        "upgrade_introduce_carnivores_desc": "Додає хижаків для балансу екосистеми",
        "upgrade_fertilize_name": "Удобрити ґрунт",
        "upgrade_fertilize_desc": "Підвищує родючість для швидшого росту та поширення насіння",
        "upgrade_rain_ritual_name": "Ритуал дощу",
        "upgrade_rain_ritual_desc": "Пришвидшує загальний ріст завдяки періодичним дощам",
        "upgrade_biodiversity_name": "Біорізноманіття",
        "upgrade_biodiversity_desc": "Старі дерева дають вдвічі більше біомаси",
        # Status labels
        "status_biomass": "Біомаса",
        "status_trees": "Дерева",
        "status_herbivores": "Травоїдні",
        "status_carnivores": "Хижаки",
        "status_fertility": "Родючість",
        # Grid header
        "grid_header_forest": "Ліс",
        # Grid legend
        "legend_sapling": "паросток",
        "legend_tree": "дерево",
        "legend_old": "старе",
        "legend_herbivore": "травоїдне",
        "legend_carnivore": "хижак",
    },
}


# ── game class ───────────────────────────────────────────────────────────

class Forest(Game):
    """Forest ecosystem idle game."""

    game_id = "forest"
    name = "Forest"
    emoji = "🌲"

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        # All fields MUST be set before super().__init__ because from_dict
        # is called from there when *data* is provided.
        self.trees: list[list[float]] = []  # each: [x, y, age]
        self.herbivores: list[list[float]] = []  # each: [x, y, energy]
        self.carnivores: list[list[float]] = []  # each: [x, y, energy]
        self.upgrade_levels: dict[str, int] = {}
        self.biomass: float = 0.0
        self.fertility: float = 1.0
        self.growth_mult: float = 1.0
        self.seed_boost: int = 0  # extra seed attempts per mature tree per interval
        self.biodiversity_unlocked: bool = False
        self.carnivores_unlocked: bool = False
        self.seed_timer: float = 0.0

        super().__init__(data)

        if data is None:
            # ── fresh game initialisation ──
            self.biomass = 1.0
            for _ in range(8):
                self._add_random_tree()

    # ── i18n helper ──────────────────────────────────────────────────────

    def _tr(self, key: str) -> str:
        """Look up a translated string by key, falling back to English."""
        lang_map = _STRINGS.get(self.lang, _STRINGS["en"])
        return lang_map.get(key, _STRINGS["en"].get(key, key))

    # ── spawn helpers ───────────────────────────────────────────────────

    def _add_random_tree(self) -> None:
        """Place one tree at a random unoccupied cell."""
        if len(self.trees) >= MAX_TREES:
            return
        occupied = {(int(t[0]), int(t[1])) for t in self.trees}
        for _ in range(200):
            x = random.randint(0, WIDTH - 1)
            y = random.randint(0, HEIGHT - 1)
            if (x, y) not in occupied:
                age = random.uniform(0.0, 30.0)
                self.trees.append([float(x), float(y), age])
                return
        # Fallback: force into first empty cell
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if (x, y) not in occupied:
                    self.trees.append([float(x), float(y), random.uniform(0.0, 5.0)])
                    return

    def _add_random_herbivore(self) -> None:
        if len(self.herbivores) >= MAX_HERBIVORES:
            return
        x = random.uniform(1.0, float(WIDTH - 2))
        y = random.uniform(1.0, float(HEIGHT - 2))
        energy = HERBIVORE_START_ENERGY + random.uniform(-2.0, 2.0)
        self.herbivores.append([x, y, max(1.0, energy)])

    def _add_random_carnivore(self) -> None:
        if len(self.carnivores) >= MAX_CARNIVORES:
            return
        x = random.uniform(1.0, float(WIDTH - 2))
        y = random.uniform(1.0, float(HEIGHT - 2))
        energy = CARNIVORE_START_ENERGY + random.uniform(-3.0, 3.0)
        self.carnivores.append([x, y, max(1.0, energy)])

    def _find_empty_adjacent(
        self, x: int, y: int
    ) -> tuple[int | None, int | None]:
        """Return a random empty cell adjacent to (x,y), or (None, None)."""
        dirs = [
            (dx, dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if dx != 0 or dy != 0
        ]
        random.shuffle(dirs)
        occupied = {(int(t[0]), int(t[1])) for t in self.trees}
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and (nx, ny) not in occupied:
                return nx, ny
        return None, None

    # ── tick sub-methods ────────────────────────────────────────────────

    def _die_old_trees(self) -> None:
        """Remove trees past AGE_OLD_MAX and add death biomass."""
        surviving: list[list[float]] = []
        for t in self.trees:
            if t[2] >= AGE_OLD_MAX:
                stage = tree_stage(t[2])
                yield_bio = DEATH_BIOMASS[stage]
                if self.biodiversity_unlocked:
                    yield_bio *= 2.0
                self.biomass += yield_bio
            else:
                surviving.append(t)
        self.trees = surviving

    def _collect_biomass(self, dt: float) -> None:
        """Add biomass from living tree growth."""
        for t in self.trees:
            stage = tree_stage(t[2])
            self.biomass += BIOMASS_RATES[stage] * dt * self.growth_mult

    def _spread_seeds(self) -> None:
        """One seed-spread event.

        Each mature tree may spawn a seedling in a random adjacent empty
        cell.
        """
        if len(self.trees) >= MAX_TREES:
            return
        mature = [t for t in self.trees if tree_stage(t[2]) >= 2]
        random.shuffle(mature)

        attempts = 1 + self.seed_boost
        prob = BASE_SEED_PROB * self.fertility
        for tree in mature:
            if len(self.trees) >= MAX_TREES:
                return
            for _ in range(attempts):
                if random.random() < prob:
                    adj_x, adj_y = self._find_empty_adjacent(
                        int(tree[0]), int(tree[1])
                    )
                    if adj_x is not None and adj_y is not None:
                        self.trees.append(
                            [float(adj_x), float(adj_y), random.uniform(0.0, 2.0)]
                        )
                        break  # at most one seedling per tree per event

    # ── animal movement ─────────────────────────────────────────────────

    def _move_herbivores(self, dt: float) -> None:
        """Move herbivores toward trees; eat if close enough."""
        eaten: set[int] = set()

        for h in self.herbivores:
            # Nearest tree not already marked eaten
            best_idx = -1
            best_dist = HERBIVORE_SEEK_RADIUS
            for i, t in enumerate(self.trees):
                if i in eaten:
                    continue
                d = math.hypot(t[0] - h[0], t[1] - h[1])
                if d < best_dist:
                    best_dist = d
                    best_idx = i

            if best_idx >= 0:
                t = self.trees[best_idx]
                dx = t[0] - h[0]
                dy = t[1] - h[1]
                d = math.hypot(dx, dy)

                if d <= HERBIVORE_EAT_RADIUS:
                    # Eat this tree
                    stage = tree_stage(t[2])
                    h[2] += HERBIVORE_EAT_ENERGY
                    self.biomass += DEATH_BIOMASS[stage] * 0.3
                    eaten.add(best_idx)
                else:
                    move = min(HERBIVORE_SPEED * dt, d)
                    if d > 0.001:
                        h[0] += (dx / d) * move
                        h[1] += (dy / d) * move
            else:
                # No tree in range — random wander
                move = HERBIVORE_SPEED * dt
                h[0] += random.uniform(-move, move)
                h[1] += random.uniform(-move, move)

            # Clamp to grid bounds
            h[0] = max(0.0, min(float(WIDTH - 1), h[0]))
            h[1] = max(0.0, min(float(HEIGHT - 1), h[1]))

        # Remove eaten trees
        if eaten:
            self.trees = [t for i, t in enumerate(self.trees) if i not in eaten]

    def _move_carnivores(self, dt: float) -> None:
        """Move carnivores toward herbivores; eat if close enough."""
        eaten: set[int] = set()

        for c in self.carnivores:
            best_idx = -1
            best_dist = CARNIVORE_SEEK_RADIUS
            for hi, h in enumerate(self.herbivores):
                if hi in eaten:
                    continue
                d = math.hypot(h[0] - c[0], h[1] - c[1])
                if d < best_dist:
                    best_dist = d
                    best_idx = hi

            if best_idx >= 0:
                h = self.herbivores[best_idx]
                dx = h[0] - c[0]
                dy = h[1] - c[1]
                d = math.hypot(dx, dy)

                if d <= CARNIVORE_EAT_RADIUS:
                    c[2] += CARNIVORE_EAT_ENERGY
                    eaten.add(best_idx)
                else:
                    move = min(CARNIVORE_SPEED * dt, d)
                    if d > 0.001:
                        c[0] += (dx / d) * move
                        c[1] += (dy / d) * move
            else:
                move = CARNIVORE_SPEED * dt
                c[0] += random.uniform(-move, move)
                c[1] += random.uniform(-move, move)

            c[0] = max(0.0, min(float(WIDTH - 1), c[0]))
            c[1] = max(0.0, min(float(HEIGHT - 1), c[1]))

        if eaten:
            self.herbivores = [
                h for i, h in enumerate(self.herbivores) if i not in eaten
            ]

    # ── animal population dynamics ──────────────────────────────────────

    def _animal_energy_decay(self, dt: float) -> None:
        """Subtract passive energy consumption over *dt*."""
        for h in self.herbivores:
            h[2] -= HERBIVORE_ENERGY_DECAY * dt
        for c in self.carnivores:
            c[2] -= CARNIVORE_ENERGY_DECAY * dt

    def _animal_reproduction(self, dt: float) -> None:
        """Animals reproduce via a Poisson process over *dt*."""
        # ── herbivores ──
        new_h: list[list[float]] = []
        for h in self.herbivores:
            if h[2] < HERBIVORE_REPRODUCE_THRESHOLD:
                continue
            can_repro = len(self.herbivores) + len(new_h) < MAX_HERBIVORES
            if not can_repro:
                break
            expected = HERBIVORE_REPRO_RATE * dt
            count = int(expected) + (1 if random.random() < expected - int(expected) else 0)
            for _ in range(count):
                if len(self.herbivores) + len(new_h) >= MAX_HERBIVORES:
                    break
                h[2] -= HERBIVORE_REPRODUCE_COST
                nx = max(0.0, min(float(WIDTH - 1), h[0] + random.uniform(-1.5, 1.5)))
                ny = max(0.0, min(float(HEIGHT - 1), h[1] + random.uniform(-1.5, 1.5)))
                new_h.append([nx, ny, HERBIVORE_START_ENERGY])
        self.herbivores.extend(new_h)

        # ── carnivores ──
        if not self.carnivores:
            return
        new_c: list[list[float]] = []
        for c in self.carnivores:
            if c[2] < CARNIVORE_REPRODUCE_THRESHOLD:
                continue
            can_repro = len(self.carnivores) + len(new_c) < MAX_CARNIVORES
            if not can_repro:
                break
            expected = CARNIVORE_REPRO_RATE * dt
            count = int(expected) + (1 if random.random() < expected - int(expected) else 0)
            for _ in range(count):
                if len(self.carnivores) + len(new_c) >= MAX_CARNIVORES:
                    break
                c[2] -= CARNIVORE_REPRODUCE_COST
                nx = max(0.0, min(float(WIDTH - 1), c[0] + random.uniform(-1.5, 1.5)))
                ny = max(0.0, min(float(HEIGHT - 1), c[1] + random.uniform(-1.5, 1.5)))
                new_c.append([nx, ny, CARNIVORE_START_ENERGY])
        self.carnivores.extend(new_c)

    def _animal_starvation(self) -> None:
        """Remove animals whose energy has dropped to zero or below."""
        self.herbivores = [h for h in self.herbivores if h[2] > 0]
        self.carnivores = [c for c in self.carnivores if c[2] > 0]

    # ── tick ────────────────────────────────────────────────────────────

    def _tick_chunk(self, chunk: float) -> None:
        """Process one time-chunk: ecology, animal movement, and population.

        Everything is kept temporally consistent within the chunk so that
        the ecosystem behaves realistically even for large *dt* values.
        """
        # ── Ecology (trees) ───────────────────────────────────────────
        for t in self.trees:
            t[2] += chunk
        self._collect_biomass(chunk)

        self.seed_timer += chunk
        while self.seed_timer >= SEED_INTERVAL and len(self.trees) < MAX_TREES:
            self.seed_timer -= SEED_INTERVAL
            self._spread_seeds()

        # Old trees die after spreading seeds one last time
        self._die_old_trees()

        # ── Animal movement (sub-chunked) ─────────────────────────────
        move_remaining = chunk
        while move_remaining > 0.0:
            step = MOVE_CHUNK if move_remaining > MOVE_CHUNK else move_remaining
            self._move_herbivores(step)
            self._move_carnivores(step)
            move_remaining -= step

        # ── Population dynamics (linear over this chunk) ──────────────
        self._animal_energy_decay(chunk)
        self._animal_reproduction(chunk)
        self._animal_starvation()

    def tick(self, dt: float) -> None:
        """Advance the forest ecosystem by *dt* seconds of game time.

        Large *dt* values (up to 3600 during offline catch-up) are handled
        by processing in small chunks so the ecosystem remains alive and
        self-sustaining throughout.
        """
        remaining = dt
        while remaining > 0.0:
            chunk = ECOLOGY_CHUNK if remaining > ECOLOGY_CHUNK else remaining
            self._tick_chunk(chunk)
            remaining -= chunk

    # ── upgrades ────────────────────────────────────────────────────────

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
                    name=self._tr(f"upgrade_{defn.id}_name"),
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
        if self.biomass < upgrade.cost:
            return False

        self.biomass -= upgrade.cost
        level = self.upgrade_levels.get(upgrade_id, 0) + 1
        self.upgrade_levels[upgrade_id] = level
        self.stats.upgrades_bought += 1

        # ── Apply effects ──
        if upgrade_id == "plant_trees":
            self.seed_boost += 1
            for _ in range(3):
                self._add_random_tree()
        elif upgrade_id == "introduce_herbivores":
            for _ in range(2):
                self._add_random_herbivore()
        elif upgrade_id == "introduce_carnivores":
            self.carnivores_unlocked = True
            count = 2 if level == 1 else 1
            for _ in range(count):
                self._add_random_carnivore()
        elif upgrade_id == "fertilize":
            self.fertility = 1.0 + level * 0.2
        elif upgrade_id == "rain_ritual":
            self.growth_mult = 1.0 + level * 0.2
        elif upgrade_id == "biodiversity":
            self.biodiversity_unlocked = True

        return True

    # ── serialisation ───────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_saved": self.last_saved,
            "paused": self.paused,
            "speed": self.speed,
            "stats": {
                "playtime_seconds": self.stats.playtime_seconds,
                "upgrades_bought": self.stats.upgrades_bought,
            },
            "biomass": self.biomass,
            "trees": [list(t) for t in self.trees],
            "herbivores": [list(h) for h in self.herbivores],
            "carnivores": [list(c) for c in self.carnivores],
            "upgrade_levels": dict(self.upgrade_levels),
            "fertility": self.fertility,
            "growth_mult": self.growth_mult,
            "seed_boost": self.seed_boost,
            "biodiversity_unlocked": self.biodiversity_unlocked,
            "carnivores_unlocked": self.carnivores_unlocked,
            "seed_timer": self.seed_timer,
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
        self.biomass = data["biomass"]
        self.trees = [list(t) for t in data["trees"]]
        self.herbivores = [list(h) for h in data["herbivores"]]
        self.carnivores = [list(c) for c in data["carnivores"]]
        self.upgrade_levels = dict(data.get("upgrade_levels", {}))
        self.fertility = data["fertility"]
        self.growth_mult = data["growth_mult"]
        self.seed_boost = data["seed_boost"]
        self.biodiversity_unlocked = data["biodiversity_unlocked"]
        self.carnivores_unlocked = data["carnivores_unlocked"]
        self.seed_timer = data["seed_timer"]

    # ── display ─────────────────────────────────────────────────────────

    def status_lines(self) -> list[str]:
        """Short status lines shown in the hub menu."""
        lines = [
            f"[green]v[/] [green]{self._tr('status_biomass')}: {self.biomass:.1f}[/]",
            f"[green]▲[/] [green]{self._tr('status_trees')}: {len(self.trees)}/{MAX_TREES}[/]",
            f"[cyan]r[/] [cyan]{self._tr('status_herbivores')}: {len(self.herbivores)}/{MAX_HERBIVORES}[/]",
        ]
        if self.carnivores or self.carnivores_unlocked:
            lines.append(
                f"[red]w[/] [red]{self._tr('status_carnivores')}: {len(self.carnivores)}/{MAX_CARNIVORES}[/]"
            )
        lines.append(f"[green]~[/] {self._tr('status_fertility')}: {self.fertility:.1f}")
        return lines

    def render_grid(self) -> str:
        """Multi-line ASCII grid (~40×14) of the forest."""
        grid: list[list[str]] = [["[dim] [/]"] * WIDTH for _ in range(HEIGHT)]

        # Trees
        for t in self.trees:
            x, y = int(t[0]), int(t[1])
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                sym = tree_sym(t[2])
                stage = tree_stage(t[2])
                if stage == 0:
                    grid[y][x] = f"[dim green]{sym}[/]"
                elif stage == 1:
                    grid[y][x] = f"[green]{sym}[/]"
                elif stage == 2:
                    grid[y][x] = f"[bold green]{sym}[/]"
                else:
                    grid[y][x] = f"[yellow]{sym}[/]"

        # Herbivores (overwrites trees)
        for h in self.herbivores:
            x, y = int(round(h[0])), int(round(h[1]))
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                grid[y][x] = "[cyan]h[/]"

        # Carnivores (overwrites both)
        for c in self.carnivores:
            x, y = int(round(c[0])), int(round(c[1]))
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                grid[y][x] = "[red]c[/]"

        header = (
            f"[bold]🌲 {self._tr('grid_header_forest')}[/]  |  "
            f"🌱 {self._tr('status_biomass')}: [green]{self.biomass:.1f}[/]  |  "
            f"{self._tr('status_trees')} {len(self.trees)}  |  "
            f"🦌 {len(self.herbivores)}  |  "
            f"🐺 {len(self.carnivores)}"
        )
        legend = (
            f"[green]t[/] {self._tr('legend_sapling')}  "
            f"[bold green]T[/] {self._tr('legend_tree')}  "
            f"[yellow]♣[/] {self._tr('legend_old')}  "
            f"[cyan]h[/] {self._tr('legend_herbivore')}  "
            f"[red]c[/] {self._tr('legend_carnivore')}"
        )
        return "\n".join([header] + ["".join(row) for row in grid] + [legend])
