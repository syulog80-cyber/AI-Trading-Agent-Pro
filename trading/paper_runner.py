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
        """Run one read-only scan/update cycle.

        A scanner result is authoritative when it already contains the full
        trade-plan fields. Lightweight scanner implementations may return only
        eligibility metadata; for those, the controller's trade-plan method is
        used as a compatibility fallback.
        """
        closed: List[Dict[str, Any]] = []
        for symbol in list(self.session.paper_trader.positions):
            price = self._current_price(symbol)
            trade = self.session.paper_trader.update_price(symbol, price)
            if trade is not None:
                self.journal.record(trade)
                closed.append(trade)

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
            if not opportunity.get("scanner_eligible", False):
                continue

            # Prefer the exact scanner snapshot so live MTF state is not
            # unnecessarily recalculated. Fall back for minimal/mock scanner
            # results that do not carry risk fields.
            required_fields = ("entry_price", "stop_loss", "take_profit", "position_size")
            if all(opportunity.get(field) is not None for field in required_fields):
                plan = dict(opportunity)
                plan["direction"] = str(opportunity.get("signal", "HOLD")).upper()
            else:
                plan = self.controller.get_trade_plan(symbol, timeframe=timeframe)

            try:
                position = self.session.paper_trader.open_position(plan, symbol)
                opened.append(position)
            except (KeyError, TypeError, ValueError):
                continue

        return {
            "scan_count": len(scan),
            "opportunities": scan,
            "opened": opened,
            "closed": closed,
            "positions": list(self.session.paper_trader.positions.values()),
            "performance": self.performance(),
        }

    def performance(self) -> Dict[str, Any]:
        """Return journal and current virtual-account metrics."""
        summary = self.journal.summary(self.session.paper_trader.initial_balance)
        summary["balance"] = self.session.paper_trader.balance
        summary["open_positions"] = len(self.session.paper_trader.positions)
        return summary

    def _current_price(self, symbol: str) -> float:
        market = self.controller.load_market(symbol, timeframe="1m", limit=2)
        return float(market["close"].iloc[-1])
