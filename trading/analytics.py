"""Analytics for completed paper trades."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable


class PaperTradingAnalytics:
    """Calculate portfolio and grouped performance from completed trades."""

    def __init__(self, trades: Iterable[Dict[str, Any]] = ()) -> None:
        self.trades = [dict(t) for t in trades]

    def _stats(self, trades: list[Dict[str, Any]]) -> Dict[str, Any]:
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
            "win_rate": len(wins) * 100.0 / total if total else 0.0,
            "net_pnl": sum(pnls),
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": gross_profit / gross_loss if gross_loss else (float("inf") if gross_profit else 0.0),
            "average_win": gross_profit / len(wins) if wins else 0.0,
            "average_loss": gross_loss / len(losses) if losses else 0.0,
            "expectancy": sum(pnls) / total if total else 0.0,
        }

    def overall(self) -> Dict[str, Any]:
        return self._stats(self.trades)

    def by(self, field: str) -> Dict[str, Dict[str, Any]]:
        groups: dict[str, list[Dict[str, Any]]] = defaultdict(list)
        for trade in self.trades:
            value = trade.get(field, "UNKNOWN")
            groups[str(value).upper()].append(trade)
        return {key: self._stats(items) for key, items in sorted(groups.items())}

    def report(self) -> Dict[str, Any]:
        return {
            "overall": self.overall(),
            "by_symbol": self.by("symbol"),
            "by_strategy": self.by("strategy"),
            "by_grade": self.by("grade"),
            "by_signal": self.by("signal"),
        }
