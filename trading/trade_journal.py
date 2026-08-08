"""Persistent-in-memory trade journal and performance metrics."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


class TradeJournal:
    """Record completed paper trades and calculate trading statistics."""

    def __init__(self) -> None:
        self.trades: List[Dict[str, Any]] = []

    def record(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        required = ("symbol", "direction", "entry_price", "exit_price", "pnl")
        missing = [key for key in required if key not in trade]
        if missing:
            raise ValueError(f"Missing trade fields: {', '.join(missing)}")

        item = dict(trade)
        item["symbol"] = str(item["symbol"]).upper()
        item["direction"] = str(item["direction"]).upper()
        item["pnl"] = float(item["pnl"])
        self.trades.append(item)
        return item

    def extend(self, trades: Iterable[Dict[str, Any]]) -> None:
        for trade in trades:
            self.record(trade)

    def summary(self, starting_balance: float = 10_000.0) -> Dict[str, Any]:
        if starting_balance <= 0:
            raise ValueError("starting_balance must be positive")

        total = len(self.trades)
        wins = [t["pnl"] for t in self.trades if t["pnl"] > 0]
        losses = [t["pnl"] for t in self.trades if t["pnl"] < 0]
        net_pnl = sum(float(t["pnl"]) for t in self.trades)
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))

        equity = float(starting_balance)
        peak = equity
        max_drawdown = 0.0
        for trade in self.trades:
            equity += float(trade["pnl"])
            peak = max(peak, equity)
            drawdown = peak - equity
            max_drawdown = max(max_drawdown, drawdown)

        return {
            "total_trades": total,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": (len(wins) / total * 100.0) if total else 0.0,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "net_pnl": net_pnl,
            "return_percent": net_pnl / starting_balance * 100.0,
            "profit_factor": (gross_profit / gross_loss) if gross_loss else (float("inf") if gross_profit else 0.0),
            "average_win": gross_profit / len(wins) if wins else 0.0,
            "average_loss": gross_loss / len(losses) if losses else 0.0,
            "expectancy": net_pnl / total if total else 0.0,
            "max_drawdown": max_drawdown,
            "max_drawdown_percent": max_drawdown / starting_balance * 100.0,
        }
