"""Integrated AI decision brain for AI Trading Agent Pro.

This orchestrator connects the tested analysis engines into one deterministic
pipeline. It is intentionally free of exchange/order execution logic.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from ai.confidence_engine import ConfidenceEngine
from ai.grade_engine import GradeEngine
from ai.market_structure import MarketStructure
from ai.momentum_engine import MomentumEngine
from ai.risk_engine import RiskEngine
from ai.strategy_engine import StrategyEngine
from ai.trend_engine import TrendEngine


class AIBrain:
    """Run the complete rule-based AI analysis pipeline."""

    def __init__(self) -> None:
        self.structure_engine = MarketStructure()
        self.trend_engine = TrendEngine()
        self.momentum_engine = MomentumEngine()
        self.strategy_engine = StrategyEngine()
        self.risk_engine = RiskEngine()
        self.confidence_engine = ConfidenceEngine()
        self.grade_engine = GradeEngine()

    def analyze(
        self,
        df: pd.DataFrame,
        account_balance: float = 10_000.0,
    ) -> Dict[str, Any]:
        """Analyze candles and return one scanner-compatible AI result."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")
        if df.empty:
            raise ValueError("Cannot analyze an empty dataframe")

        structure = self.structure_engine.analyze(df)
        trend = self.trend_engine.analyze(structure)
        momentum = self.momentum_engine.analyze(df)
        strategy = self.strategy_engine.analyze(structure, trend, momentum)

        entry_price = float(df.iloc[-1]["close"])
        risk = self.risk_engine.analyze(
            entry_price=entry_price,
            atr=float(df.iloc[-1]["ATR"]),
            direction=strategy["direction"],
            account_balance=account_balance,
        )

        confidence = self.confidence_engine.analyze(
            structure=structure,
            trend=trend,
            momentum=momentum,
            strategy=strategy,
            risk=risk,
        )
        grade = self.grade_engine.analyze(
            confidence=confidence,
            strategy=strategy,
            risk=risk,
        )

        # Final signal is deliberately gated by both confidence and grade.
        final_signal = strategy["direction"] if grade["tradable"] else "HOLD"

        market_condition = self._market_condition(
            adx=float(momentum["adx"]),
            atr_percent=float(momentum["atr_percent"]),
        )

        reasons = []
        reasons.extend(structure.get("reasons", [])[:2])
        reasons.extend(trend.get("reasons", [])[:2])
        reasons.extend(momentum.get("reasons", [])[:3])
        reasons.extend(strategy.get("reasons", [])[:3])
        reasons.extend(confidence.get("reasons", [])[-2:])
        reasons.extend(grade.get("reasons", [])[-2:])

        # Keep the public result compatible with the existing scanner while
        # exposing the complete component outputs for the new architecture.
        return {
            "signal": final_signal,
            "decision": final_signal,
            "score": grade["score"],
            "confidence": confidence["confidence"],
            "grade": grade["grade"],
            "strength": confidence["strength"],
            "trade_quality": self._trade_quality(grade["score"]),
            "trend": trend["trend"],
            "market_condition": market_condition,
            "risk": risk["risk_level"],
            "reward": "HIGH" if risk["risk_reward"] >= 2 else "MEDIUM" if risk["risk_reward"] >= 1.5 else "LOW",
            "recommended_position_size": risk["position_percent"] / 100.0,
            "position_size": risk["position_size"],
            "position_value": risk["position_value"],
            "entry_price": entry_price,
            "stop_loss": risk["stop_loss"],
            "take_profit": risk["take_profit"],
            "risk_reward": risk["risk_reward"],
            "atr": risk["atr"],
            "atr_percent": risk["atr_percent"],
            "strategy": strategy["strategy"],
            "reasons": reasons,
            "tradable": grade["tradable"],
            "hard_conflict": confidence.get("hard_conflict", False),
            "structure": structure,
            "trend_analysis": trend,
            "momentum": momentum,
            "strategy_analysis": strategy,
            "risk_analysis": risk,
            "confidence_analysis": confidence,
            "grade_analysis": grade,
        }

    @staticmethod
    def _market_condition(adx: float, atr_percent: float) -> str:
        if adx >= 40:
            return "Strong Trend"
        if adx >= 25:
            return "Trending"
        if atr_percent >= 4:
            return "Volatile"
        if atr_percent <= 1:
            return "Low Volatility"
        return "Sideways"

    @staticmethod
    def _trade_quality(score: float) -> str:
        if score >= 90:
            return "★★★★★"
        if score >= 80:
            return "★★★★☆"
        if score >= 70:
            return "★★★☆☆"
        if score >= 60:
            return "★★☆☆☆"
        return "★☆☆☆☆"
