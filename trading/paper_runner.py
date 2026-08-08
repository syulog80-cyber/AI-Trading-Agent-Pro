"""Read-only live-market paper trading runner."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from trading.paper_session import PaperTradingSession
from trading.trade_journal import TradeJournal


class PaperTradingRunner:
    """Coordinate scanner, trade plans and virtual positions.

    This class never submits exchange orders. One ``step`` performs one scan
    cycle and updates existing virtual positions using current market prices.
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
        scan = self.controller.scan_market(
            self.symbols,
            timeframe=timeframe,
            min_confidence=self.session.min_confidence,
        )

        closed: List[Dict[str, Any]] = []
        for symbol in list(self.session.trader.positions):
            price = self._current_price(symbol)
            trade = self.session.update_price(symbol, price)
            if trade is not None:
                self.journal.record(trade)
                closed.append(trade)

        opened: List[Dict[str, Any]] = []
        for opportunity in scan:
            symbol = opportunity["symbol"]
            if symbol in self.session.trader.positions:
                continue
            if len(self.session.trader.positions) >= self.session.max_positions:
                break
            plan = self.controller.get_trade_plan(symbol, timeframe=timeframe)
            try:
                position = self.session.open_trade(symbol, plan)
                opened.append(position)
            except ValueError:
                continue

        return {
            "scan_count": len(scan),
            "opportunities": scan,
            "opened": opened,
            "closed": closed,
            "positions": list(self.session.trader.positions.values()),
            "performance": self.performance(),
        }

    def performance(self) -> Dict[str, Any]:
        """Return journal and current virtual-account metrics."""
        summary = self.journal.summary(self.session.trader.initial_balance)
        summary["balance"] = self.session.trader.balance
        summary["open_positions"] = len(self.session.trader.positions)
        return summary

    def _current_price(self, symbol: str) -> float:
        market = self.controller.load_market(symbol, timeframe="1m", limit=2)
        return float(market["close"].iloc[-1])
