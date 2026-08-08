"""Persistent adapter for the existing read-only paper trading runner."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable

from trading.paper_runner import PaperTradingRunner
from trading.persistent_portfolio import PersistentPaperPortfolio
from trading.trade_journal import TradeJournal


class PersistentPaperTradingRunner(PaperTradingRunner):
    """Keep the paper account across separate Python process runs."""

    def __init__(self, controller, symbols: Iterable[str], initial_balance: float = 10_000.0,
                 max_positions: int = 3, min_confidence: float = 70.0,
                 portfolio_path: str | Path = "data/paper_portfolio.json") -> None:
        super().__init__(controller, symbols, initial_balance, max_positions, min_confidence)
        self.portfolio = PersistentPaperPortfolio(portfolio_path, initial_balance=initial_balance)
        self._restore_persistent_state()

    @staticmethod
    def _parse_datetime(value: Any) -> Any:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return value
        return value

    def _restore_persistent_state(self) -> None:
        state = self.portfolio.state
        trader = self.session.paper_trader
        trader.initial_balance = float(state.get("initial_balance", trader.initial_balance))
        trader.balance = float(state.get("balance", trader.balance))
        trader.positions = {
            symbol: {**position, "opened_at": self._parse_datetime(position.get("opened_at"))}
            for symbol, position in state.get("positions", {}).items()
        }
        trader.closed_trades = [
            {**trade,
             "opened_at": self._parse_datetime(trade.get("opened_at")),
             "closed_at": self._parse_datetime(trade.get("closed_at"))}
            for trade in state.get("trades", [])
        ]
        self.journal = TradeJournal()
        self.journal.extend(trader.closed_trades)

    def _save_persistent_state(self) -> None:
        trader = self.session.paper_trader
        self.portfolio.state.update({
            "initial_balance": trader.initial_balance,
            "balance": trader.balance,
            "positions": trader.positions,
            "trades": trader.closed_trades,
            "updated_at": datetime.now().isoformat(),
        })
        if self.portfolio.state.get("created_at") is None:
            self.portfolio.state["created_at"] = self.portfolio.state["updated_at"]
        self.portfolio.save()

    def step(self, timeframe: str = "1h") -> Dict[str, Any]:
        result = super().step(timeframe=timeframe)
        self._save_persistent_state()
        return result

    def reset(self) -> Dict[str, Any]:
        state = self.portfolio.reset()
        trader = self.session.paper_trader
        trader.initial_balance = self.portfolio.initial_balance
        trader.balance = self.portfolio.initial_balance
        trader.positions.clear()
        trader.closed_trades.clear()
        self.journal = TradeJournal()
        return state
