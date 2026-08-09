"""Read-only live-market paper trading runner."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from trading.analytics import PaperTradingAnalytics
from trading.paper_session import PaperTradingSession
from trading.trade_journal import TradeJournal


class PaperTradingRunner:
    """Coordinate scanner, trade plans and virtual positions.

    This class never submits exchange orders. One ``step`` performs one scan
    cycle and updates existing virtual positions using current market prices
    and the latest 1-minute candle range for stop/target detection.
    """

    def __init__(
        self,
        controller,
        symbols: Iterable[str],
        initial_balance: float = 10_000.0,
        max_positions: int = 3,
        min_confidence: float = 70.0,
    ) -> None:
        self.controller = controller
        self.symbols = [str(s).upper() for s in symbols]
        if not self.symbols:
            raise ValueError("symbols must not be empty")
        self.session = PaperTradingSession(
            controller,
            initial_balance=initial_balance,
            max_positions=max_positions,
            min_confidence=min_confidence,
        )
        self.journal = TradeJournal()

    def step(self, timeframe: str = "1h") -> Dict[str, Any]:
        """Run one read-only scan/update cycle."""
        closed: List[Dict[str, Any]] = []
        current_prices: Dict[str, float] = {}
        exited_symbols = set()

        for symbol in list(self.session.paper_trader.positions):
            market = self._current_market(symbol)
            price = float(market["close"])
            current_prices[symbol] = price
            trade = self.session.paper_trader.update_range(
                symbol,
                low=float(market["low"]),
                high=float(market["high"]),
                close=price,
            )
            if trade is not None:
                self.journal.record(trade)
                closed.append(trade)
                exited_symbols.add(symbol)

        scan = self.controller.scan_market(
            self.symbols,
            timeframe=timeframe,
            min_confidence=self.session.min_confidence,
        )

        available = self.session.max_positions - len(self.session.paper_trader.positions)
        opened: List[Dict[str, Any]] = []
        for opportunity in scan:
            if len(opened) >= available:
                break

            symbol = str(opportunity.get("symbol", "")).upper()
            if not symbol or symbol in self.session.paper_trader.positions:
                continue
            if symbol in exited_symbols:
                continue
            if not opportunity.get("scanner_eligible", False):
                continue

            required_fields = ("entry_price", "stop_loss", "take_profit", "position_size")
            if all(opportunity.get(field) is not None for field in required_fields):
                plan = dict(opportunity)
                plan["direction"] = str(opportunity.get("signal", "HOLD")).upper()
            else:
                plan = self.controller.get_trade_plan(symbol, timeframe=timeframe)

            for key in ("signal", "confidence", "grade", "strategy", "opportunity", "timeframe"):
                if key in opportunity:
                    plan[key] = opportunity[key]
            plan.setdefault("timeframe", timeframe)

            try:
                position = self.session.paper_trader.open_position(plan, symbol)
                opened.append(position)
            except (KeyError, TypeError, ValueError):
                continue

        for symbol in self.session.paper_trader.positions:
            if symbol not in current_prices:
                current_prices[symbol] = self._current_price(symbol)

        return {
            "scan_count": len(scan),
            "opportunities": scan,
            "opened": opened,
            "closed": closed,
            "positions": list(self.session.paper_trader.positions.values()),
            "prices": current_prices,
            "performance": self.performance(current_prices),
        }

    def performance(self, prices: Dict[str, float] | None = None) -> Dict[str, Any]:
        """Return realized journal metrics, mark-to-market equity and breakdowns."""
        summary = self.journal.summary(self.session.paper_trader.initial_balance)
        mark = self.session.paper_trader.mark_to_market(prices or {})
        analytics = PaperTradingAnalytics(self.journal.trades).report()
        summary.update(mark)
        summary["analytics"] = analytics
        return summary

    def _current_market(self, symbol: str):
        market = self.controller.load_market(symbol, timeframe="1m", limit=2)
        required = {"high", "low", "close"}
        if not required.issubset(market.columns):
            raise ValueError("market data must contain high, low and close columns")
        return market.iloc[-1]

    def _current_price(self, symbol: str) -> float:
        return float(self._current_market(symbol)["close"])
