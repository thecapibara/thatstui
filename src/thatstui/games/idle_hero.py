"""Idle Hero — an auto-battling RPG idle game.

⚔️ Fight through dungeon floors, slay monsters, level up,
buy upgrades, and progress through an endless dungeon.
"""

from __future__ import annotations

import random
from typing import Any

from thatstui.core.game import Game, GameStats, Upgrade

# ── constants ──────────────────────────────────────────────────────────

CRIT_MULT = 1.0  # additional damage multiplier on crit (doubles damage)
COMPANION_DPS_BASE = 5.0  # base companion DPS when hired
POTION_HEAL_FRAC = 0.40  # fraction of max_hp restored per potion
AUTO_POTION_THRESHOLD = 0.30  # auto-use when hp below this fraction of max_hp
KILLS_PER_FLOOR = 8  # monsters to kill before descending a floor
SAFETY_MAX_EVENTS = 100000  # cap iterations inside a single tick

# ── upgrade definitions (base config) ──────────────────────────────────

_UPGRADE_DEFS: dict[str, Upgrade] = {
    "weapon": Upgrade(
        id="weapon",
        name="Weapon",
        description="+5 attack damage per level",
        cost=10,
    ),
    "armor": Upgrade(
        id="armor",
        name="Armor",
        description="+2 defense per level",
        cost=15,
    ),
    "attack_speed": Upgrade(
        id="attack_speed",
        name="Attack Speed",
        description="+0.15 attacks/sec per level",
        cost=20,
    ),
    "crit": Upgrade(
        id="crit",
        name="Critical Strike",
        description="+3% crit chance per level",
        cost=30,
    ),
    "auto_potion": Upgrade(
        id="auto_potion",
        name="Auto Potion",
        description="Auto-use potions when HP drops below 30%",
        cost=50,
        repeatable=False,
        max_level=1,
    ),
    "potion_stock": Upgrade(
        id="potion_stock",
        name="Potion Stock",
        description="Carry +1 additional potion per level",
        cost=40,
    ),
    "companion": Upgrade(
        id="companion",
        name="Companion",
        description="Hire a companion for bonus DPS",
        cost=75,
        repeatable=False,
        max_level=1,
    ),
    "companion_gear": Upgrade(
        id="companion_gear",
        name="Companion Gear",
        description="+100% companion DPS per level",
        cost=60,
    ),
}

GRID_WIDTH = 44
GRID_HEIGHT = 16

_MONSTER_TIERS: dict[int, str] = {
    1: "G",
    2: "S",
    3: "O",
    4: "T",
    5: "D",
    6: "W",
    7: "L",
    8: "B",
    9: "K",
    10: "E",
}


def _monster_emoji(_floor: int) -> str:
    """Return a monster glyph based on floor tier."""
    tier = (_floor - 1) // 3 + 1
    return _MONSTER_TIERS.get(tier, "X")


# ── translation strings ──────────────────────────────────────────────

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # ── upgrade names ──
        "upgrade_weapon_name": "Weapon",
        "upgrade_armor_name": "Armor",
        "upgrade_attack_speed_name": "Attack Speed",
        "upgrade_crit_name": "Critical Strike",
        "upgrade_auto_potion_name": "Auto Potion",
        "upgrade_potion_stock_name": "Potion Stock",
        "upgrade_companion_name": "Companion",
        "upgrade_companion_gear_name": "Companion Gear",
        # ── upgrade descriptions ──
        "upgrade_weapon_desc": "+5 attack damage per level",
        "upgrade_armor_desc": "+2 defense per level",
        "upgrade_attack_speed_desc": "+0.15 attacks/sec per level",
        "upgrade_crit_desc": "+3% crit chance per level",
        "upgrade_auto_potion_desc": "Auto-use potions when HP drops below 30%",
        "upgrade_potion_stock_desc": "Carry +1 additional potion per level",
        "upgrade_companion_desc": "Hire a companion for bonus DPS",
        "upgrade_companion_gear_desc": "+100% companion DPS per level",
        # ── status lines ──
        "hp_label": "HP",
        "floor_label": "Floor",
        "lv_label": "Lv",
        "gold_label": "Gold",
        "xp_label": "XP",
        # ── grid header ──
        "hero_title": "Hero",
        "floor_abbr": "F",
        "lv_abbr": "Lv",
        "xp_abbr": "XP",
        # ── combat log ──
        "begin_adventure": "Begin your adventure!",
        "level_up_msg": "Level up! Lv{level}",
        "potion_msg": "Potion +{heal:.0f}hp",
        "died_msg": "Died, respawn floor {floor}",
        "killed_msg": "Killed monster +{gold:.0f}g",
        "floor_msg": "Floor {floor}!",
        # ── combat header ──
        "combat_label": "Combat",
    },
    "uk": {
        # ── upgrade names ──
        "upgrade_weapon_name": "Зброя",
        "upgrade_armor_name": "Броня",
        "upgrade_attack_speed_name": "Швидкість атаки",
        "upgrade_crit_name": "Критичний удар",
        "upgrade_auto_potion_name": "Авто-зілля",
        "upgrade_potion_stock_name": "Запас зілля",
        "upgrade_companion_name": "Супутник",
        "upgrade_companion_gear_name": "Спорядження супутника",
        # ── upgrade descriptions ──
        "upgrade_weapon_desc": "+5 до атаки за рівень",
        "upgrade_armor_desc": "+2 до захисту за рівень",
        "upgrade_attack_speed_desc": "+0.15 атак/сек за рівень",
        "upgrade_crit_desc": "+3% шансу криту за рівень",
        "upgrade_auto_potion_desc": "Автоматичне зілля коли HP нижче 30%",
        "upgrade_potion_stock_desc": "+1 додаткове зілля за рівень",
        "upgrade_companion_desc": "Найняти супутника для додаткового DPS",
        "upgrade_companion_gear_desc": "+100% DPS супутника за рівень",
        # ── status lines ──
        "hp_label": "HP",
        "floor_label": "Поверх",
        "lv_label": "Рів",
        "gold_label": "Золото",
        "xp_label": "Досвід",
        # ── grid header ──
        "hero_title": "Герой",
        "floor_abbr": "Пов",
        "lv_abbr": "Рів",
        "xp_abbr": "Досв",
        # ── combat log ──
        "begin_adventure": "Почни свою пригоду!",
        "level_up_msg": "Новий рівень! Lv{level}",
        "potion_msg": "Зілля +{heal:.0f} HP",
        "died_msg": "Загибель, відродження на поверсі {floor}",
        "killed_msg": "Вбито монстра +{gold:.0f} зл",
        "floor_msg": "Поверх {floor}!",
        # ── combat header ──
        "combat_label": "Бій",
    },
}


# ── game class ─────────────────────────────────────────────────────────


class IdleHero(Game):
    """Idle Hero RPG — auto-battle through dungeon floors."""

    game_id = "idle_hero"
    name = "Idle Hero"
    emoji = "⚔️"

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        # init ALL fields BEFORE super().__init__(data) — from_dict
        # depends on them existing
        self.level: int = 1
        self.xp: float = 0.0
        self.max_hp: float = 100.0
        self.hp: float = 100.0
        self.attack: float = 10.0
        self.attack_speed: float = 1.0
        self.defense: float = 2.0
        self.crit_chance: float = 0.05
        self.floor: int = 1
        self.auto_potion: bool = False
        self.companion: bool = False
        self.potions: int = 0
        self.gold: float = 0.0

        # monster state
        self.m_hp: float = 0.0
        self.m_max_hp: float = 0.0
        self.m_attack: float = 0.0
        self.m_gold: float = 0.0
        self.m_xp: float = 0.0

        # tracking
        self.monsters_killed: int = 0
        self.kills_since_floor: int = 0
        self.upgrade_levels: dict[str, int] = {}
        self.log: list[str] = []

        super().__init__(data)

        if data is None:
            # fresh game
            self.gold = 5.0
            self._spawn_monster()
            self._add_log(self._tr("begin_adventure"))

    # ── helpers ────────────────────────────────────────────────────────

    def _tr(self, key: str) -> str:
        """Translate *key* according to ``self.lang`` (en/uk)."""
        return _STRINGS.get(self.lang, _STRINGS["en"]).get(key, key)

    def _add_log(self, msg: str) -> None:
        self.log.append(msg)
        if len(self.log) > 4:
            self.log.pop(0)

    def _xp_needed(self) -> float:
        return 50.0 * self.level

    def _potion_capacity(self) -> int:
        """How many potions the hero can carry."""
        return self.upgrade_levels.get("potion_stock", 0)

    def _spawn_monster(self) -> None:
        """Create a monster appropriate for the current floor."""
        self.m_max_hp = 20.0 + self.floor * 15.0
        self.m_attack = 3.0 + self.floor * 2.0
        self.m_gold = 2.0 + self.floor * 2.0
        self.m_xp = 5.0 + self.floor * 3.0
        self.m_hp = self.m_max_hp

    def _dps_hero(self) -> float:
        """Total hero DPS considering crit average and companion."""
        base = self.attack * self.attack_speed
        # average crit bonus
        dps = base * (1.0 + self.crit_chance * CRIT_MULT)
        if self.companion:
            cgl = self.upgrade_levels.get("companion_gear", 0)
            dps += COMPANION_DPS_BASE * (1.0 + cgl)
        return dps

    def _dps_monster(self) -> float:
        return max(0.0, self.m_attack - self.defense)

    def _level_up(self) -> None:
        self.level += 1
        self.max_hp += 20.0
        self.attack += 5.0
        self.hp = self.max_hp  # full heal on level up
        self.potions = self._potion_capacity()
        self._add_log(self._tr("level_up_msg").format(level=self.level))

    def _use_potion(self) -> None:
        if self.potions <= 0:
            return
        heal = self.max_hp * POTION_HEAL_FRAC
        self.hp = min(self.max_hp, self.hp + heal)
        self.potions -= 1
        self._add_log(self._tr("potion_msg").format(heal=heal))

    def _die(self) -> None:
        old_floor = self.floor
        self.floor = max(1, self.floor // 2)
        self.gold *= 0.9
        self.hp = self.max_hp
        self.potions = self._potion_capacity()
        self._spawn_monster()
        self._add_log(self._tr("died_msg").format(floor=self.floor))

    # ── tick ──────────────────────────────────────────────────────────

    def tick(self, dt: float) -> None:
        """Advance game by *dt* seconds of game-time.

        Uses event-based simulation so large dt values (up to 3600s for
        offline catch-up) are handled correctly — multiple monster kills,
        level-ups, floor descents, and deaths are processed in order.
        """
        if dt <= 0 or self.hp <= 0:
            return

        remaining = dt
        safety = SAFETY_MAX_EVENTS

        while remaining > 1e-9 and safety > 0:
            safety -= 1

            hero_dps = self._dps_hero()
            monster_dps = self._dps_monster()

            if hero_dps <= 0 and monster_dps <= 0:
                break

            # time until next meaningful event
            ttk = self.m_hp / hero_dps if hero_dps > 0 else float("inf")
            ttd = self.hp / monster_dps if monster_dps > 0 else float("inf")
            t_event = min(ttk, ttd, remaining)

            if t_event <= 0:
                break

            # apply damage
            self.m_hp -= hero_dps * t_event
            self.hp -= monster_dps * t_event
            remaining -= t_event

            # auto-potion check (only if hero is still alive)
            if (
                self.auto_potion
                and self.hp > 0
                and self.hp < AUTO_POTION_THRESHOLD * self.max_hp
                and self.potions > 0
            ):
                self._use_potion()

            # hero death
            if self.hp <= 0:
                self._die()
                # stop processing time after death; the respawn resets the
                # fight for the new floor
                break

            # monster death
            if self.m_hp <= 0:
                self._on_monster_killed()

    def _on_monster_killed(self) -> None:
        """Handle monster death rewards and progression."""
        self.gold += self.m_gold
        self.xp += self.m_xp
        self.monsters_killed += 1
        self.kills_since_floor += 1
        self._add_log(self._tr("killed_msg").format(gold=self.m_gold))

        # level-up check (may level multiple times with large xp rewards)
        while self.xp >= self._xp_needed():
            self.xp -= self._xp_needed()
            self._level_up()

        # floor descent
        if self.kills_since_floor >= KILLS_PER_FLOOR:
            self.floor += 1
            self.kills_since_floor = 0
            self._add_log(self._tr("floor_msg").format(floor=self.floor))

        # spawn next monster
        self._spawn_monster()

    # ── upgrades ──────────────────────────────────────────────────────

    def upgrades(self) -> list[Upgrade]:
        """Return available upgrades with cost scaled by current level."""
        result: list[Upgrade] = []
        for defn in _UPGRADE_DEFS.values():
            level = self.upgrade_levels.get(defn.id, 0)
            if defn.max_level > 0 and level >= defn.max_level:
                continue  # maxed out
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
        if self.gold < upgrade.cost:
            return False

        self.gold -= upgrade.cost
        level = self.upgrade_levels.get(upgrade_id, 0) + 1
        self.upgrade_levels[upgrade_id] = level
        self.stats.upgrades_bought += 1

        # apply effects
        if upgrade_id == "weapon":
            self.attack = 10.0 + level * 5.0
        elif upgrade_id == "armor":
            self.defense = 2.0 + level * 2.0
        elif upgrade_id == "attack_speed":
            self.attack_speed = 1.0 + level * 0.15
        elif upgrade_id == "crit":
            self.crit_chance = min(0.05 + level * 0.03, 0.8)
        elif upgrade_id == "auto_potion":
            self.auto_potion = True
        elif upgrade_id == "potion_stock":
            self.potions = level  # refill on purchase
        elif upgrade_id == "companion":
            self.companion = True
        elif upgrade_id == "companion_gear":
            pass  # effect computed via _dps_hero()

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
            "level": self.level,
            "xp": self.xp,
            "max_hp": self.max_hp,
            "hp": self.hp,
            "attack": self.attack,
            "attack_speed": self.attack_speed,
            "defense": self.defense,
            "crit_chance": self.crit_chance,
            "floor": self.floor,
            "auto_potion": self.auto_potion,
            "companion": self.companion,
            "potions": self.potions,
            "gold": self.gold,
            "m_hp": self.m_hp,
            "m_max_hp": self.m_max_hp,
            "m_attack": self.m_attack,
            "m_gold": self.m_gold,
            "m_xp": self.m_xp,
            "monsters_killed": self.monsters_killed,
            "kills_since_floor": self.kills_since_floor,
            "upgrade_levels": dict(self.upgrade_levels),
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
        self.level = data["level"]
        self.xp = data["xp"]
        self.max_hp = data["max_hp"]
        self.hp = data["hp"]
        self.attack = data["attack"]
        self.attack_speed = data["attack_speed"]
        self.defense = data["defense"]
        self.crit_chance = data["crit_chance"]
        self.floor = data["floor"]
        self.auto_potion = data["auto_potion"]
        self.companion = data["companion"]
        self.potions = data["potions"]
        self.gold = data["gold"]
        self.m_hp = data["m_hp"]
        self.m_max_hp = data["m_max_hp"]
        self.m_attack = data["m_attack"]
        self.m_gold = data["m_gold"]
        self.m_xp = data["m_xp"]
        self.monsters_killed = data["monsters_killed"]
        self.kills_since_floor = data["kills_since_floor"]
        self.upgrade_levels = dict(data.get("upgrade_levels", {}))
        self.log = []  # transient — not persisted

    # ── display helpers ───────────────────────────────────────────────

    def status_lines(self) -> list[str]:
        h_frac = self.hp / self.max_hp if self.max_hp > 0 else 0
        hc = "green" if h_frac >= 0.5 else ("yellow" if h_frac >= 0.25 else "red")
        return [
            f"❤️ {self._tr('hp_label')}: [{hc}]{self.hp:.0f}/{self.max_hp:.0f}[/]",
            f"⚔️ {self._tr('floor_label')} [red]{self.floor}[/]  {self._tr('lv_label')}[cyan]{self.level}[/]",
            f"💰 {self._tr('gold_label')}: [yellow]{self.gold:.1f}[/]",
            f"👾 {self._tr('xp_label')}: {self.xp:.0f}/{self._xp_needed():.0f}",
        ]

    @staticmethod
    def _hp_bar(current: float, maximum: float, length: int = 8) -> str:
        """Return HP bar fill string (e.g. ``████░░``, no brackets)."""
        if maximum <= 0:
            return "░" * length
        fraction = max(0.0, min(1.0, current / maximum))
        filled = int(fraction * length)
        empty = length - filled
        return "█" * filled + "░" * empty

    def render_grid(self) -> str:
        """Render the dungeon arena as a ~44x16 multi-line string."""
        W = GRID_WIDTH
        lines: list[str] = []

        def pad(s: str) -> str:
            return s.ljust(W)

        # ── top border ──
        lines.append("╔" + "═" * (W - 2) + "╗")

        # ── coloured header line 1: title + floor/level ──
        hdr1 = (
            f"⚔️[bold]{self._tr('hero_title')}[/] {self._tr('floor_abbr')}[red]{self.floor}[/] {self._tr('lv_abbr')}[cyan]{self.level}[/]"
        )
        lines.append("║" + hdr1.center(W - 2) + "║")

        # ── coloured header line 2: gold + xp ──
        hdr2 = (
            f"💰[yellow]{self.gold:.1f}[/]  "
            f"{self._tr('xp_abbr')} {self.xp:.0f}/{self._xp_needed():.0f}"
        )
        lines.append("║" + hdr2.center(W - 2) + "║")

        # ── blank separator ──
        lines.append("║" + " " * (W - 2) + "║")

        # ── arena — hero left, monster right ──
        hero_glyph = "[cyan]🧙[/]"
        mon_glyph = "[red]👾[/]"
        arena_line = f"     {hero_glyph}               {mon_glyph}"
        lines.append("║" + arena_line.ljust(W - 2) + "║")

        # ── HP bars side by side ──
        h_frac = self.hp / self.max_hp if self.max_hp > 0 else 0
        if h_frac >= 0.5:
            hc = "green"
        elif h_frac >= 0.25:
            hc = "yellow"
        else:
            hc = "red"

        hero_bar = self._hp_bar(self.hp, self.max_hp, 4)
        mon_bar = self._hp_bar(self.m_hp, self.m_max_hp, 4)
        hp_bar_line = (
            f" H[{hc}]{hero_bar}[/]{self.hp:.0f}/{self.max_hp:.0f}"
            f" M[red]{mon_bar}[/]{self.m_hp:.0f}/{self.m_max_hp:.0f}"
        )
        lines.append("║" + hp_bar_line.ljust(W - 2) + "║")

        # ── blank separator ──
        lines.append("║" + " " * (W - 2) + "║")

        # ── combat log header ──
        if self.companion:
            cgl = self.upgrade_levels.get("companion_gear", 0)
            comp_part = f"  🐾{COMPANION_DPS_BASE * (1.0 + cgl):.1f}dps"
        else:
            comp_part = ""
        log_header = (
            f"  ── {self._tr('combat_label')} ({self._dps_hero():.1f} dps"
            f" vs {self._dps_monster():.1f} dps)"
            f"{comp_part} ──"
        )
        lines.append("║" + log_header.ljust(W - 2) + "║")

        # ── log entries (up to 4) ──
        for entry in self.log[-4:]:
            if "Died" in entry or "Загибель" in entry:
                coloured = f"[bold red]{entry}[/]"
            elif "Level up" in entry or "Новий рівень" in entry:
                coloured = f"[bold cyan]{entry}[/]"
            elif "Killed" in entry or "Вбито" in entry:
                coloured = f"[green]{entry}[/]"
            elif "Potion" in entry or "Зілля" in entry:
                coloured = f"[green]{entry}[/]"
            elif "Floor" in entry or "Поверх" in entry:
                coloured = f"[cyan]{entry}[/]"
            else:
                coloured = entry
            entry_str = f"  > {coloured}"
            lines.append("║" + entry_str.ljust(W - 2) + "║")

        # ── fill remaining rows ──
        while len(lines) < GRID_HEIGHT - 1:
            lines.append("║" + " " * (W - 2) + "║")

        # ── bottom border ──
        lines.append("╚" + "═" * (W - 2) + "╝")

        return "\n".join(lines)
