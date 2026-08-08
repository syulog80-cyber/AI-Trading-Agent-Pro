"""Read-only market-data paper trading session orchestration."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from trading.paper_trader import PaperTrader


class PaperTradingSession:
    """Connect the live scanner to PaperTrader without sending orders."""

    def __init__(
        self,
        controller,
        initial_balance: float = 10_000.0,
        max_positions: int = 3,
        min_confidence: float = 70.0,
    ) -> None:
        if max_positions < 1:
            raise ValueError("max_positions must be >= 1")
        if not 0 <= min_confidence <= 100:
            raise ValueError("min_confidence must be between 0 and 100")
        self.controller = controller
        self.paper_trader = PaperTrader(initial_balance=initial_balance)
        self.max_positions = max_positions
        self.min_confidence = float(min_confidence)

    def scan_and_open(
        self,
        symbols: Iterable[str],
        timeframe: str = "1h",
    ) -> List[Dict[str, Any]]:
        """Scan live data and open eligible virtual positions up to the cap."""
        available = self.max_positions - len(self.paper_trader.positions)
        if available <= 0:
            return []

        opportunities = self.controller.scan_market(
            list(symbols),
            timeframe=timeframe,
            min_confidence=self.min_confidence,
        )

        opened: List[Dict[str, Any]] = []
        for opportunity in opportunities:
            if len(opened) >= available:
                break
            symbol = str(opportunity.get("symbol", "")).upper()
            if not symbol or symbol in self.paper_trader.positions:
                continue
            if not opportunity.get("scanner_eligible", False):
                continue

            plan = self.controller.get_trade_plan(symbol, timeframe=timeframe)
            if not plan.get("tradable", False):
                continue

            opened.append(self.paper_trader.open_position(plan, symbol))

        return opened

    def update_prices(self, prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Update virtual positions and close any that hit stop or target."""
        closed: List[Dict[str, Any]] = []
        for symbol, price in prices.items():
            trade = self.paper_trader.update_price(symbol, price)
            if trade is not None:
                closed.append(trade)
        return closed

    def summary(self) -> Dict[str, Any]:
        """Return current virtual account statistics."""
        return self.paper_trader.summary()
