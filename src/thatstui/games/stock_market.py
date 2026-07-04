"""Stock Market — an auto-trading idle game.

📈 Buy and sell stocks with an automated trader.  Prices wiggle,
net worth trends upward, and upgrades make everything faster.
"""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from thatstui.core.game import Game, GameStats, Upgrade


# ── constants ────────────────────────────────────────────────────

_CHART_BLOCKS = "▁▂▃▄▅▆▇█"
_MAX_HISTORY = 40
_GRID_WIDTH = 50
_GRID_HEIGHT = 18

# ── upgrade definitions ──────────────────────────────────────────

_UPGRADE_DEFS: dict[str, Upgrade] = {
    "capital": Upgrade(
        id="capital",
        name="Capital Injection",
        description="Inject more cash into your account",
        cost=50,
        max_level=20,
    ),
    "aggressive": Upgrade(
        id="aggressive",
        name="Aggressive Trading",
        description="Autotrader trades larger fractions of cash/shares",
        cost=100,
    ),
    "unlock_stock": Upgrade(
        id="unlock_stock",
        name="Unlock Market",
        description="Unlock an additional stock market",
        cost=200,
        cost_scale=1.5,
        max_level=3,
    ),
    "insider": Upgrade(
        id="insider",
        name="Insider Info",
        description="Autotrader gets a small edge on buy/sell prices",
        cost=500,
        repeatable=False,
        max_level=1,
    ),
    "low_fees": Upgrade(
        id="low_fees",
        name="Low Fees",
        description="Reduce transaction costs",
        cost=300,
        repeatable=False,
        max_level=1,
    ),
    "diversify": Upgrade(
        id="diversify",
        name="Diversify",
        description="Autotrader spreads trades across all unlocked stocks",
        cost=400,
        repeatable=False,
        max_level=1,
    ),
}

# ── stock definitions ────────────────────────────────────────────

_STOCK_DEFS: list[dict[str, Any]] = [
    {
        "ticker": "TEK",
        "name": "Tech Corp",
        "price": 50.0,
        "drift": 0.045,
        "volatility": 0.25,
        "mean_rev_target": 50.0,
        "mean_rev_strength": 0.10,
    },
    {
        "ticker": "BLU",
        "name": "Blue Chip Inc",
        "price": 100.0,
        "drift": 0.030,
        "volatility": 0.18,
        "mean_rev_target": 100.0,
        "mean_rev_strength": 0.08,
    },
    {
        "ticker": "NRG",
        "name": "Energy Corp",
        "price": 25.0,
        "drift": 0.040,
        "volatility": 0.30,
        "mean_rev_target": 25.0,
        "mean_rev_strength": 0.12,
    },
    {
        "ticker": "BIO",
        "name": "BioHealth Ltd",
        "price": 60.0,
        "drift": 0.050,
        "volatility": 0.28,
        "mean_rev_target": 60.0,
        "mean_rev_strength": 0.10,
    },
    {
        "ticker": "FIN",
        "name": "Financial Trust",
        "price": 45.0,
        "drift": 0.035,
        "volatility": 0.20,
        "mean_rev_target": 45.0,
        "mean_rev_strength": 0.09,
    },
    {
        "ticker": "AER",
        "name": "AeroSpace Co",
        "price": 150.0,
        "drift": 0.040,
        "volatility": 0.22,
        "mean_rev_target": 150.0,
        "mean_rev_strength": 0.08,
    },
]


# ── internal data structures ─────────────────────────────────────

@dataclass
class _Stock:
    """A single stock with its price dynamics and history."""

    ticker: str
    name: str
    price: float
    drift: float
    volatility: float
    mean_rev_target: float
    mean_rev_strength: float
    history: deque[float] = field(
        default_factory=lambda: deque(maxlen=_MAX_HISTORY)
    )


# ── i18n strings ─────────────────────────────────────────────────

_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "cash": "Cash",
        "net": "Net",
        "stocks": "Stocks",
        "aggro": "Aggro Lv{}",
        "stock_market_title": "Stock Market",
        "net_worth": "Net Worth",
        "ticker": "Ticker",
        "shrs": "Shrs",
        "price": "Price",
        "value": "Value",
        "cash_row": "Cash",
        "net_w": "Net W",
        "name_capital": "Capital Injection",
        "name_aggressive": "Aggressive Trading",
        "name_unlock_stock": "Unlock Market",
        "name_insider": "Insider Info",
        "name_low_fees": "Low Fees",
        "name_diversify": "Diversify",
        "desc_capital": "Inject more cash into your account",
        "desc_aggressive": "Autotrader trades larger fractions of cash/shares",
        "desc_unlock_stock": "Unlock an additional stock market",
        "desc_insider": "Autotrader gets a small edge on buy/sell prices",
        "desc_low_fees": "Reduce transaction costs",
        "desc_diversify": "Autotrader spreads trades across all unlocked stocks",
    },
    "uk": {
        "cash": "Готівка",
        "net": "Активи",
        "stocks": "Акції",
        "aggro": "Агр. рів.{}",
        "stock_market_title": "Біржа",
        "net_worth": "Чисті активи",
        "ticker": "Тікер",
        "shrs": "Акц.",
        "price": "Ціна",
        "value": "Вартість",
        "cash_row": "Готівка",
        "net_w": "Активи",
        "name_capital": "Ін'єкція капіталу",
        "name_aggressive": "Агресивна торгівля",
        "name_unlock_stock": "Відкрити ринок",
        "name_insider": "Інсайдерська інформація",
        "name_low_fees": "Низькі комісії",
        "name_diversify": "Диверсифікація",
        "desc_capital": "Внести більше готівки на рахунок",
        "desc_aggressive": "Автотрейдер торгує більшими частками готівки/акцій",
        "desc_unlock_stock": "Відкрити додатковий ринок акцій",
        "desc_insider": "Автотрейдер отримує невелику перевагу",
        "desc_low_fees": "Зменшити витрати на транзакції",
        "desc_diversify": "Автотрейдер розподіляє торгівлю між усіма ринками",
    },
}

# ── game class ───────────────────────────────────────────────────

class StockMarket(Game):
    """Stock Market idle game — auto-trading with upgrades."""

    game_id = "stock_market"
    name = "Stock Market"
    emoji = "📈"

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        # Init ALL fields before super().__init__ (from_dict depends on them)
        self.cash: float = 0.0
        self.stocks: list[_Stock] = []
        self.shares: dict[str, int] = {}
        self.net_worth_history: deque[float] = deque(maxlen=_MAX_HISTORY)
        self.upgrade_levels: dict[str, int] = {}
        self.focused_index: int = 0

        # Cached upgrade effects (set before super().__init__ so from_dict
        # can overwrite them)
        self._aggressiveness: float = 1.0
        self._insider_unlocked: bool = False
        self._low_fees_unlocked: bool = False
        self._diversify_unlocked: bool = False
        self._unlocked_stocks: int = 3

        super().__init__(data)

        if data is None:
            # ── fresh game initialisation ──────────────────────────
            self.cash = 1000.0
            for sd in _STOCK_DEFS[:3]:
                s = _Stock(**sd)
                # Pre-fill history so moving averages work immediately
                for _ in range(10):
                    s.history.append(s.price)
                self.stocks.append(s)
            self.shares = {"TEK": 5, "BLU": 3, "NRG": 4}
            self.net_worth_history.append(self._net_worth())

    # ── internal helpers ──────────────────────────────────────────

    def _net_worth(self) -> float:
        """Total cash + market value of all holdings."""
        holdings_value = sum(
            self.shares.get(s.ticker, 0) * s.price for s in self.stocks
        )
        return self.cash + holdings_value

    def _moving_average(self, stock: _Stock, period: int = 10) -> float:
        """Simple moving average over the last *period* prices."""
        hist = list(stock.history)
        if len(hist) < 2:
            return stock.price
        period = min(period, len(hist))
        return sum(hist[-period:]) / period

    def _tr(self, key: str) -> str:
        """Translate *key* using :attr:`lang` (falls back to English)."""
        lang_strings = _STRINGS.get(self.lang, _STRINGS["en"])
        return lang_strings.get(key, _STRINGS["en"].get(key, key))

    # ── tick ──────────────────────────────────────────────────────

    def tick(self, dt: float) -> None:
        """Advance the market by *dt* seconds.

        Prices are evolved with sub-stepping for large *dt* (up to 600
        steps max) to keep the random walk numerically stable.  The
        autotrader runs once after all price updates.
        """
        self._step_prices(dt)
        self._step_autotrader()
        self.net_worth_history.append(self._net_worth())

    def _step_prices(self, dt: float) -> None:
        """Evolve all stock prices, sub-stepping for large *dt*."""
        if dt <= 1.0:
            self._step_prices_raw(dt)
        else:
            max_steps = 600
            step_dt = max(1.0, dt / max_steps)
            steps = int(dt / step_dt)
            remainder = dt - steps * step_dt
            for _ in range(steps):
                self._step_prices_raw(step_dt)
            if remainder > 0:
                self._step_prices_raw(remainder)

        # Record final price for charting / MA
        for s in self.stocks:
            s.history.append(s.price)

    def _step_prices_raw(self, dt: float) -> None:
        """Single price-update step (GBM + mean reversion)."""
        sqrt_dt = math.sqrt(dt)
        for s in self.stocks:
            r = random.gauss(0, 1)
            drift_term = s.drift * dt
            mr_term = (
                s.mean_rev_strength
                * (s.mean_rev_target - s.price)
                / max(s.price, 0.01)
                * dt
            )
            vol_term = s.volatility * sqrt_dt * r
            total = drift_term + mr_term + vol_term
            # Clamp to avoid extreme single-step moves
            total = max(-0.5, min(0.5, total))
            s.price *= math.exp(total)
            s.price = max(0.01, s.price)

    def _step_autotrader(self) -> None:
        """Run the automated trading rules once.

        Buys when price dips below 0.95×MA (or tighter with insider
        info), sells when price rises above 1.05×MA.
        """
        fee = 0.0003 if self._low_fees_unlocked else 0.001
        edge = 0.02 if self._insider_unlocked else 0.0
        fraction = 0.1 * self._aggressiveness

        # Which stocks to trade
        if self._diversify_unlocked:
            trade_stocks = self.stocks
        else:
            trade_stocks = self.stocks[:1]  # focused stock only

        for s in trade_stocks:
            if len(s.history) < 5:
                continue
            ma = self._moving_average(s, 10)
            buy_threshold = ma * (0.95 - edge)
            sell_threshold = ma * (1.05 + edge)

            cash_portion = self.cash * fraction
            shares_held = self.shares.get(s.ticker, 0)

            # ── buy signal ────────────────────────────────────────
            if s.price < buy_threshold and cash_portion > s.price:
                budget = min(cash_portion, self.cash * 0.5)
                can_buy = int(budget / s.price)
                if can_buy > 0:
                    cost = can_buy * s.price * (1 + fee)
                    if cost <= self.cash:
                        self.cash -= cost
                        self.shares[s.ticker] = shares_held + can_buy

            # ── sell signal ───────────────────────────────────────
            elif s.price > sell_threshold and shares_held > 0:
                to_sell = max(1, int(shares_held * fraction))
                to_sell = min(to_sell, shares_held)
                proceeds = to_sell * s.price * (1 - fee)
                self.cash += proceeds
                self.shares[s.ticker] = shares_held - to_sell

    # ── upgrades ──────────────────────────────────────────────────

    def upgrades(self) -> list[Upgrade]:
        """Return currently available upgrades with cost scaled by level."""
        result: list[Upgrade] = []
        for defn in _UPGRADE_DEFS.values():
            level = self.upgrade_levels.get(defn.id, 0)

            # Skip maxed-out upgrades
            if defn.max_level > 0 and level >= defn.max_level:
                continue

            # Stock unlock: limit to stocks that actually exist
            if defn.id == "unlock_stock":
                max_unlock = len(_STOCK_DEFS) - 3
                if level >= max_unlock:
                    continue

            cost = defn.cost * (defn.cost_scale**level)
            result.append(
                Upgrade(
                    id=defn.id,
                    name=self._tr(f"name_{defn.id}"),
                    description=self._tr(f"desc_{defn.id}"),
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
        if self.cash < upgrade.cost:
            return False

        self.cash -= upgrade.cost
        level = self.upgrade_levels.get(upgrade_id, 0) + 1
        self.upgrade_levels[upgrade_id] = level
        self.stats.upgrades_bought += 1

        # ── apply upgrade effects ────────────────────────────────
        if upgrade_id == "capital":
            grant = 200.0 * level
            self.cash += grant
        elif upgrade_id == "aggressive":
            self._aggressiveness = 1.0 + level * 0.5
        elif upgrade_id == "unlock_stock":
            self._unlocked_stocks = 3 + level
            idx = 3 + level - 1
            if idx < len(_STOCK_DEFS):
                sd = _STOCK_DEFS[idx]
                if not any(s.ticker == sd["ticker"] for s in self.stocks):
                    s = _Stock(**sd)
                    for _ in range(10):
                        s.history.append(s.price)
                    self.stocks.append(s)
                    self.shares.setdefault(sd["ticker"], 0)
        elif upgrade_id == "insider":
            self._insider_unlocked = True
        elif upgrade_id == "low_fees":
            self._low_fees_unlocked = True
        elif upgrade_id == "diversify":
            self._diversify_unlocked = True

        return True

    # ── serialisation ─────────────────────────────────────────────

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
            "cash": self.cash,
            "stocks": [
                {
                    "ticker": s.ticker,
                    "name": s.name,
                    "price": s.price,
                    "drift": s.drift,
                    "volatility": s.volatility,
                    "mean_rev_target": s.mean_rev_target,
                    "mean_rev_strength": s.mean_rev_strength,
                    "history": list(s.history),
                }
                for s in self.stocks
            ],
            "shares": dict(self.shares),
            "net_worth_history": list(self.net_worth_history),
            "upgrade_levels": dict(self.upgrade_levels),
            "focused_index": self.focused_index,
            "_aggressiveness": self._aggressiveness,
            "_insider_unlocked": self._insider_unlocked,
            "_low_fees_unlocked": self._low_fees_unlocked,
            "_diversify_unlocked": self._diversify_unlocked,
            "_unlocked_stocks": self._unlocked_stocks,
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
        self.cash = data.get("cash", 0.0)

        self.stocks = []
        for sd in data.get("stocks", []):
            hist = deque(sd.get("history", []), maxlen=_MAX_HISTORY)
            self.stocks.append(
                _Stock(
                    ticker=sd["ticker"],
                    name=sd.get("name", sd["ticker"]),
                    price=sd["price"],
                    drift=sd.get("drift", 0.03),
                    volatility=sd.get("volatility", 0.2),
                    mean_rev_target=sd.get("mean_rev_target", sd["price"]),
                    mean_rev_strength=sd.get("mean_rev_strength", 0.1),
                    history=hist,
                )
            )
        self.shares = dict(data.get("shares", {}))
        self.net_worth_history = deque(
            data.get("net_worth_history", []), maxlen=_MAX_HISTORY
        )
        self.upgrade_levels = dict(data.get("upgrade_levels", {}))
        self.focused_index = data.get("focused_index", 0)
        self._aggressiveness = data.get("_aggressiveness", 1.0)
        self._insider_unlocked = data.get("_insider_unlocked", False)
        self._low_fees_unlocked = data.get("_low_fees_unlocked", False)
        self._diversify_unlocked = data.get("_diversify_unlocked", False)
        self._unlocked_stocks = data.get("_unlocked_stocks", 3)

    # ── display helpers ───────────────────────────────────────────

    def status_lines(self) -> list[str]:
        """Short text lines shown in the hub menu."""
        nw = self._net_worth()
        return [
            f"[green]$[/] {self._tr('cash')}: [green]${self.cash:,.2f}[/]",
            f"[cyan]■[/] {self._tr('net')}: [cyan]${nw:,.2f}[/]",
            f"[yellow]▲[/] {self._tr('stocks')}: {len(self.stocks)}",
            f"[blue]●[/] {self._tr('aggro').format(self.upgrade_levels.get('aggressive', 0))}",
        ]

    def _sparkline(self, values: list[float], width: int = 40) -> str:
        """Render a single-line sparkline from *values* using block chars."""
        if not values:
            return " " * width
        if len(values) == 1:
            mid = len(_CHART_BLOCKS) // 2
            return _CHART_BLOCKS[mid] * width

        lo = min(values)
        hi = max(values)
        span = hi - lo
        if span < 0.001:
            mid = len(_CHART_BLOCKS) // 2
            return _CHART_BLOCKS[mid] * width

        result: list[str] = []
        n = len(values)
        if n <= width:
            # Fewer points than width — pad last value
            for v in values:
                norm = (v - lo) / span
                idx = min(7, int(norm * 7.99))
                result.append(_CHART_BLOCKS[idx])
            while len(result) < width:
                result.append(result[-1] if result else _CHART_BLOCKS[0])
        else:
            # More points than width — sample evenly
            step = (n - 1) / max(width - 1, 1)
            for i in range(width):
                idx = min(int(i * step), n - 1)
                v = values[idx]
                norm = (v - lo) / span
                block_idx = min(7, int(norm * 7.99))
                result.append(_CHART_BLOCKS[block_idx])
        return "".join(result)

    def render_grid(self) -> str:
        """Return a multi-line ASCII grid (~50×18)."""
        nw = self._net_worth()
        lines: list[str] = []

        # Net-worth trend arrow
        nw_list = list(self.net_worth_history)
        nw_trend = ""
        if len(nw_list) >= 2:
            nw_trend = (
                "[green]▲[/]" if nw_list[-1] >= nw_list[0] else "[red]▼[/]"
            )

        # ═══════════════════════════════════════════════════════════
        # line 1 — colored header with trend arrow
        # ═══════════════════════════════════════════════════════════
        header = (
            f"[bold]{self.emoji} {self._tr('stock_market_title')}[/]  |  "
            f"💵 {self._tr('cash')} [green]${self.cash:>8,.0f}[/]  |  "
            f"📊 {self._tr('net_worth')} [cyan]${nw:>10,.0f}[/] {nw_trend}"
        )
        lines.append(header)

        # ═══════════════════════════════════════════════════════════
        # line 2 — separator
        # ═══════════════════════════════════════════════════════════
        lines.append("─" * _GRID_WIDTH)

        # ═══════════════════════════════════════════════════════════
        # line 3–4 — focused stock price + colored sparkline
        # ═══════════════════════════════════════════════════════════
        if self.stocks:
            focused = self.stocks[self.focused_index % len(self.stocks)]
            hist = list(focused.history)
            spark = self._sparkline(hist, width=_GRID_WIDTH - 16)
            if len(hist) >= 2:
                clr = "green" if hist[-1] >= hist[0] else "red"
                spark = f"[{clr}]{spark}[/]"
            price_str = f"[yellow]${focused.price:>8,.2f}[/]"
            lines.append(f"[bold]{focused.ticker}[/] {price_str}  {spark}")
        else:
            lines.append("No stocks available".ljust(_GRID_WIDTH))

        # ═══════════════════════════════════════════════════════════
        # line 5 — separator
        # ═══════════════════════════════════════════════════════════
        lines.append("─" * _GRID_WIDTH)

        # ═══════════════════════════════════════════════════════════
        # line 6–10 — colored portfolio table with day-change arrow
        # ═══════════════════════════════════════════════════════════
        lines.append(
            f"[bold]{self._tr('ticker'):<6}[/] [cyan]{self._tr('shrs'):<5}[/] "
            f"[yellow]{self._tr('price'):>10}[/] [green]{self._tr('value'):>10}[/]"
        )
        holdings_value = 0.0
        for s in self.stocks:
            sh = self.shares.get(s.ticker, 0)
            val = sh * s.price
            holdings_value += val
            hist_list = list(s.history)
            if len(hist_list) >= 2:
                change = s.price - hist_list[-2]
            else:
                change = 0.0
            chg_str = f"[green]▲[/]" if change >= 0 else f"[red]▼[/]"
            lines.append(
                f"[bold]{s.ticker:<6}[/] [cyan]{sh:<5}[/] "
                f"[yellow]${s.price:>8,.2f}[/] "
                f"[green]${val:>9,.2f}[/]  {chg_str}"
            )
        lines.append(
            f"{self._tr('cash_row'):<6} {'':<5} {'':>10} [green]${self.cash:>9,.2f}[/]"
        )

        # ═══════════════════════════════════════════════════════════
        # line 11 — separator
        # ═══════════════════════════════════════════════════════════
        lines.append("─" * _GRID_WIDTH)

        # ═══════════════════════════════════════════════════════════
        # line 12–13 — colored net worth sparkline + value
        # ═══════════════════════════════════════════════════════════
        nw_spark = self._sparkline(nw_list, width=_GRID_WIDTH - 8)
        if len(nw_list) >= 2:
            clr = "green" if nw_list[-1] >= nw_list[0] else "red"
            nw_spark = f"[{clr}]{nw_spark}[/]"
        lines.append(f"{self._tr('net_w')}: {nw_spark}")
        lines.append(f"       [cyan]${nw:>10,.2f}[/]")

        # ═══════════════════════════════════════════════════════════
        # line 14 — separator
        # ═══════════════════════════════════════════════════════════
        lines.append("─" * _GRID_WIDTH)

        # ═══════════════════════════════════════════════════════════
        # line 15 — upgrade / status summary
        # ═══════════════════════════════════════════════════════════
        caps = self.upgrade_levels.get("capital", 0)
        agg = self.upgrade_levels.get("aggressive", 0)
        ins = "✓" if self._insider_unlocked else "✗"
        fees = "✓" if self._low_fees_unlocked else "✗"
        n_stocks = len(self.stocks)
        status_line = (
            f"Cap Lv{caps}  Agg Lv{agg}  "
            f"In{ins}  Fee{fees}  {n_stocks}/6"
        )
        lines.append(status_line[:_GRID_WIDTH])

        # ── pad / trim to exactly GRID_HEIGHT lines ───────────────
        while len(lines) < _GRID_HEIGHT:
            lines.append("")
        return "\n".join(lines[:_GRID_HEIGHT])
