"""Analytics for completed paper trades.

This module only analyzes persisted paper-trade records; it never places orders.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List


class PaperAnalytics:
    def __init__(self, trades: Iterable[Dict[str, Any]]) -> None:
        self.trades: List[Dict[str, Any]] = [dict(t) for t in trades]

    @staticmethod
    def _stats(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        pnls = [float(t.get("pnl", 0.0)) for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        total = len(pnls)
        return {
            "trades": total,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": len(wins) / total * 100.0 if total else 0.0,
            "net_pnl": sum(pnls),
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": gross_profit / gross_loss if gross_loss else (float("inf") if gross_profit else 0.0),
            "average_win": gross_profit / len(wins) if wins else 0.0,
            "average_loss": gross_loss / len(losses) if losses else 0.0,
            "expectancy": sum(pnls) / total if total else 0.0,
        }

    def summary(self) -> Dict[str, Any]:
        return self._stats(self.trades)

    def by_field(self, field: str) -> Dict[str, Dict[str, Any]]:
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for trade in self.trades:
            value = str(trade.get(field, "UNKNOWN"))
            groups[value].append(trade)
        return {key: self._stats(items) for key, items in sorted(groups.items())}

    def by_strategy(self) -> Dict[str, Dict[str, Any]]:
        return self.by_field("strategy")

    def by_symbol(self) -> Dict[str, Dict[str, Any]]:
        return self.by_field("symbol")

    def by_grade(self) -> Dict[str, Dict[str, Any]]:
        return self.by_field("grade")

    def max_drawdown(self, starting_balance: float = 10_000.0) -> Dict[str, float]:
        if starting_balance <= 0:
            raise ValueError("starting_balance must be positive")
        equity = float(starting_balance)
        peak = equity
        max_dd = 0.0
        for trade in self.trades:
            equity += float(trade.get("pnl", 0.0))
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        return {
            "max_drawdown": max_dd,
            "max_drawdown_percent": max_dd / starting_balance * 100.0,
        }
