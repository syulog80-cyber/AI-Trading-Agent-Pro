"""Risk management engine for AI Trading Agent Pro.

Calculates ATR-based stops, reward targets, risk/reward and risk-based
position sizing. This module does not place orders.
"""

from __future__ import annotations

from typing import Any, Dict


class RiskEngine:
    """Build a deterministic trade risk plan from price and ATR."""

    def __init__(
        self,
        risk_percent: float = 1.0,
        atr_stop_multiplier: float = 2.0,
        reward_r_multiple: float = 2.0,
        max_position_percent: float = 25.0,
    ) -> None:
        if not 0 < risk_percent <= 5:
            raise ValueError("risk_percent must be > 0 and <= 5")
        if atr_stop_multiplier <= 0:
            raise ValueError("atr_stop_multiplier must be positive")
        if reward_r_multiple <= 0:
            raise ValueError("reward_r_multiple must be positive")
        if not 0 < max_position_percent <= 100:
            raise ValueError("max_position_percent must be > 0 and <= 100")

        self.risk_percent = float(risk_percent)
        self.atr_stop_multiplier = float(atr_stop_multiplier)
        self.reward_r_multiple = float(reward_r_multiple)
        self.max_position_percent = float(max_position_percent)

    def analyze(
        self,
        entry_price: float,
        atr: float,
        direction: str,
        account_balance: float = 10_000.0,
    ) -> Dict[str, Any]:
        """Return stop, target, risk/reward and position sizing information."""
        entry_price = float(entry_price)
        atr = float(atr)
        account_balance = float(account_balance)
        direction = str(direction).upper()

        if entry_price <= 0:
            raise ValueError("entry_price must be positive")
        if atr <= 0:
            raise ValueError("atr must be positive")
        if account_balance <= 0:
            raise ValueError("account_balance must be positive")
        if direction not in {"BUY", "SELL", "HOLD"}:
            raise ValueError("direction must be BUY, SELL or HOLD")

        atr_percent = (atr / entry_price) * 100

        if direction == "HOLD":
            return {
                "tradable": False,
                "direction": "HOLD",
                "entry_price": entry_price,
                "stop_loss": None,
                "take_profit": None,
                "stop_distance": 0.0,
                "risk_reward": 0.0,
                "risk_amount": 0.0,
                "position_size": 0.0,
                "position_value": 0.0,
                "position_percent": 0.0,
                "atr": atr,
                "atr_percent": atr_percent,
                "risk_level": self._risk_level(atr_percent),
                "reason": "No position sizing for HOLD signal",
            }

        stop_distance = atr * self.atr_stop_multiplier
        reward_distance = stop_distance * self.reward_r_multiple

        if direction == "BUY":
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + reward_distance
        else:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - reward_distance

        # Prevent invalid negative target/stop prices in extreme inputs.
        stop_loss = max(0.0, stop_loss)
        take_profit = max(0.0, take_profit)

        risk_amount = account_balance * (self.risk_percent / 100.0)
        raw_position_size = risk_amount / stop_distance
        raw_position_value = raw_position_size * entry_price

        max_position_value = account_balance * (self.max_position_percent / 100.0)
        position_value = min(raw_position_value, max_position_value)
        position_size = position_value / entry_price
        position_percent = (position_value / account_balance) * 100

        actual_risk_amount = position_size * stop_distance
        risk_reward = reward_distance / stop_distance

        return {
            "tradable": True,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "stop_distance": stop_distance,
            "reward_distance": reward_distance,
            "risk_reward": risk_reward,
            "requested_risk_amount": risk_amount,
            "risk_amount": actual_risk_amount,
            "risk_percent": (actual_risk_amount / account_balance) * 100,
            "position_size": position_size,
            "position_value": position_value,
            "position_percent": position_percent,
            "atr": atr,
            "atr_percent": atr_percent,
            "risk_level": self._risk_level(atr_percent),
            "capped_by_max_position": raw_position_value > max_position_value,
        }

    @staticmethod
    def _risk_level(atr_percent: float) -> str:
        if atr_percent >= 5.0:
            return "VERY HIGH"
        if atr_percent >= 3.0:
            return "HIGH"
        if atr_percent >= 1.5:
            return "MODERATE"
        if atr_percent >= 0.5:
            return "LOW"
        return "VERY LOW"
