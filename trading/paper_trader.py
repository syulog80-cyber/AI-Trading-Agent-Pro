"""Safe paper-trading simulator for AI Trading Agent Pro.

No exchange orders are submitted. The simulator opens, manages and closes
virtual positions using the trade plan produced by the AI system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class PaperTrader:
    """Maintain virtual positions and account equity without real orders."""

    def __init__(self, initial_balance: float = 10_000.0) -> None:
        if initial_balance <= 0:
            raise ValueError("initial_balance must be positive")
        self.initial_balance = float(initial_balance)
        self.balance = float(initial_balance)
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.closed_trades: List[Dict[str, Any]] = []

    def open_position(self, plan: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Open a virtual position only when the AI trade plan is tradable."""
        symbol = str(symbol).upper()
        if symbol in self.positions:
            raise ValueError(f"Position already open for {symbol}")
        if not plan.get("tradable", False):
            raise ValueError("Trade plan is not tradable")

        direction = str(plan.get("direction", "HOLD")).upper()
        if direction not in {"BUY", "SELL"}:
            raise ValueError("Paper position requires BUY or SELL")

        entry = float(plan["entry_price"])
        stop = float(plan["stop_loss"])
        target = float(plan["take_profit"])
        size = float(plan["position_size"])

        if entry <= 0 or size <= 0:
            raise ValueError("entry_price and position_size must be positive")
        if direction == "BUY" and not (stop < entry < target):
            raise ValueError("Invalid BUY stop/target")
        if direction == "SELL" and not (target < entry < stop):
            raise ValueError("Invalid SELL stop/target")

        position = {
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry,
            "stop_loss": stop,
            "take_profit": target,
            "position_size": size,
            "position_value": entry * size,
            "opened_at": datetime.now(timezone.utc),
        }
        self.positions[symbol] = position
        return dict(position)

    def update_price(self, symbol: str, price: float) -> Optional[Dict[str, Any]]:
        """Evaluate a virtual position against its stop and target."""
        symbol = str(symbol).upper()
        price = float(price)
        if price <= 0:
            raise ValueError("price must be positive")

        position = self.positions.get(symbol)
        if position is None:
            return None

        direction = position["direction"]
        stop_hit = price <= position["stop_loss"] if direction == "BUY" else price >= position["stop_loss"]
        target_hit = price >= position["take_profit"] if direction == "BUY" else price <= position["take_profit"]

        if stop_hit:
            return self.close_position(symbol, price, "STOP_LOSS")
        if target_hit:
            return self.close_position(symbol, price, "TAKE_PROFIT")
        return None

    def close_position(self, symbol: str, exit_price: float, reason: str = "MANUAL") -> Dict[str, Any]:
        """Close a virtual position and update simulated balance."""
        symbol = str(symbol).upper()
        if symbol not in self.positions:
            raise ValueError(f"No open position for {symbol}")

        exit_price = float(exit_price)
        if exit_price <= 0:
            raise ValueError("exit_price must be positive")

        position = self.positions.pop(symbol)
        if position["direction"] == "BUY":
            pnl = (exit_price - position["entry_price"]) * position["position_size"]
        else:
            pnl = (position["entry_price"] - exit_price) * position["position_size"]

        self.balance += pnl
        trade = {
            **position,
            "exit_price": exit_price,
            "pnl": pnl,
            "reason": reason,
            "closed_at": datetime.now(timezone.utc),
            "balance_after": self.balance,
        }
        self.closed_trades.append(trade)
        return trade

    def mark_to_market(self, prices: Dict[str, float]) -> Dict[str, Any]:
        """Value open virtual positions using supplied current prices."""
        unrealized = 0.0
        position_value = 0.0
        details: List[Dict[str, Any]] = []

        for symbol, position in self.positions.items():
            if symbol not in prices:
                continue
            price = float(prices[symbol])
            if price <= 0:
                raise ValueError("current prices must be positive")

            if position["direction"] == "BUY":
                pnl = (price - position["entry_price"]) * position["position_size"]
            else:
                pnl = (position["entry_price"] - price) * position["position_size"]

            value = price * position["position_size"]
            unrealized += pnl
            position_value += value
            details.append({
                "symbol": symbol,
                "direction": position["direction"],
                "entry_price": position["entry_price"],
                "current_price": price,
                "position_value": value,
                "unrealized_pnl": pnl,
            })

        realized_pnl = self.balance - self.initial_balance
        equity = self.balance + unrealized
        return {
            "balance": self.balance,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized,
            "equity": equity,
            "position_value": position_value,
            "open_positions": len(self.positions),
            "positions": details,
        }

    def summary(self) -> Dict[str, Any]:
        """Return basic paper-trading performance statistics."""
        wins = sum(1 for trade in self.closed_trades if trade["pnl"] > 0)
        losses = sum(1 for trade in self.closed_trades if trade["pnl"] < 0)
        total = len(self.closed_trades)
        pnl = self.balance - self.initial_balance
        win_rate = (wins / total * 100.0) if total else 0.0

        return {
            "initial_balance": self.initial_balance,
            "balance": self.balance,
            "pnl": pnl,
            "return_percent": pnl / self.initial_balance * 100.0,
            "open_positions": len(self.positions),
            "closed_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
        }
