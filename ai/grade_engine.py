"""Trade quality grading engine for AI Trading Agent Pro."""

from __future__ import annotations

from typing import Any, Dict, List


class GradeEngine:
    """Convert confidence and risk evidence into a transparent trade grade."""

    def analyze(
        self,
        confidence: Dict[str, Any],
        strategy: Dict[str, Any],
        risk: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(confidence, dict):
            raise TypeError("confidence must be a dictionary")
        if not isinstance(strategy, dict):
            raise TypeError("strategy must be a dictionary")
        if not isinstance(risk, dict):
            raise TypeError("risk must be a dictionary")

        score = float(confidence.get("confidence", 0))
        direction = str(
            confidence.get("direction", strategy.get("direction", "HOLD"))
        ).upper()
        strategy_name = str(strategy.get("strategy", "Wait"))
        rr = float(risk.get("risk_reward", 0))
        tradable = bool(confidence.get("tradable", False)) and bool(
            risk.get("tradable", False)
        )
        hard_conflict = bool(confidence.get("hard_conflict", False))

        reasons: List[str] = []
        deductions = 0.0

        if rr < 1.0:
            deductions += 25
            reasons.append("Risk/reward is below 1:1")
        elif rr < 1.5:
            deductions += 10
            reasons.append("Risk/reward is below preferred 1.5:1")
        elif rr >= 2.0:
            reasons.append("Risk/reward is at least 2:1")

        if strategy_name == "Wait":
            deductions += 30
            reasons.append("Strategy is Wait")
        elif strategy_name in {"Trend Following", "Breakout", "Pullback Buy", "Momentum", "Short Trend"}:
            reasons.append(f"Defined strategy: {strategy_name}")
        elif strategy_name == "Mean Reversion":
            deductions += 5
            reasons.append("Mean reversion carries additional uncertainty")

        if hard_conflict:
            deductions += 50
            tradable = False
            reasons.append("Hard directional conflict detected")

        raw_score = max(0.0, min(100.0, score - deductions))

        if not tradable:
            raw_score = min(raw_score, 59.0)

        if raw_score >= 90:
            grade = "A+"
        elif raw_score >= 80:
            grade = "A"
        elif raw_score >= 70:
            grade = "B"
        elif raw_score >= 60:
            grade = "C"
        else:
            grade = "D"

        if grade in {"A+", "A"}:
            quality = "EXCELLENT"
        elif grade == "B":
            quality = "GOOD"
        elif grade == "C":
            quality = "FAIR"
        else:
            quality = "POOR"

        if not reasons:
            reasons.append("No additional grade adjustments")

        return {
            "grade": grade,
            "score": round(raw_score, 1),
            "quality": quality,
            "direction": direction,
            "strategy": strategy_name,
            "tradable": tradable and grade in {"A+", "A", "B"},
            "deductions": round(deductions, 1),
            "reasons": reasons,
        }
