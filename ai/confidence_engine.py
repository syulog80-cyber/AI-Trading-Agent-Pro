"""Confidence scoring engine for AI Trading Agent Pro.

Combines independent AI evidence into a bounded confidence score. The
engine rewards agreement and explicitly penalizes directional conflicts.
"""

from __future__ import annotations

from typing import Any, Dict, List


class ConfidenceEngine:
    """Calculate confidence from structure, trend, momentum, strategy and risk."""

    def __init__(self, minimum_confidence: float = 40.0) -> None:
        if not 0 <= minimum_confidence <= 100:
            raise ValueError("minimum_confidence must be between 0 and 100")
        self.minimum_confidence = float(minimum_confidence)

    def analyze(
        self,
        structure: Dict[str, Any],
        trend: Dict[str, Any],
        momentum: Dict[str, Any],
        strategy: Dict[str, Any],
        risk: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return confidence, agreement and the evidence used."""
        for name, value in {
            "structure": structure,
            "trend": trend,
            "momentum": momentum,
            "strategy": strategy,
            "risk": risk,
        }.items():
            if not isinstance(value, dict):
                raise TypeError(f"{name} must be a dictionary")

        structure_score = self._score(structure, "structure_score", "score")
        trend_score = self._score(trend, "trend_score", "score")
        momentum_score = self._score(momentum, "score")
        strategy_score = self._score(strategy, "score")

        direction = str(strategy.get("direction", strategy.get("signal", "HOLD"))).upper()
        momentum_bias = str(momentum.get("bias", "NEUTRAL")).upper()
        trend_bias = str(trend.get("bias", trend.get("direction", "NEUTRAL"))).upper()
        structure_bias = str(structure.get("direction", structure.get("trend", "NEUTRAL"))).upper()

        base = (
            structure_score * 0.30
            + trend_score * 0.25
            + momentum_score * 0.20
            + strategy_score * 0.15
            + self._risk_quality(risk) * 0.10
        )

        penalties: List[str] = []
        conflict_penalty = 0.0

        bullish = {"BUY", "BULLISH", "BULL", "STRONG BULL"}
        bearish = {"SELL", "BEARISH", "BEAR", "STRONG BEAR"}

        if direction == "BUY":
            if momentum_bias in bearish:
                conflict_penalty += 20
                penalties.append("Bearish momentum conflicts with BUY")
            if trend_bias in bearish:
                conflict_penalty += 15
                penalties.append("Bearish trend conflicts with BUY")
            if structure_bias in bearish:
                conflict_penalty += 15
                penalties.append("Bearish structure conflicts with BUY")
        elif direction == "SELL":
            if momentum_bias in bullish:
                conflict_penalty += 20
                penalties.append("Bullish momentum conflicts with SELL")
            if trend_bias in bullish:
                conflict_penalty += 15
                penalties.append("Bullish trend conflicts with SELL")
            if structure_bias in bullish:
                conflict_penalty += 15
                penalties.append("Bullish structure conflicts with SELL")
        else:
            conflict_penalty += 5
            penalties.append("Strategy direction is HOLD")

        agreement = self._agreement(direction, structure_bias, trend_bias, momentum_bias)
        agreement_bonus = agreement * 5.0

        confidence = base + agreement_bonus - conflict_penalty
        confidence = max(0.0, min(100.0, confidence))
        confidence = round(confidence, 1)

        if confidence >= 90:
            grade = "A+"
        elif confidence >= 80:
            grade = "A"
        elif confidence >= 70:
            grade = "B"
        elif confidence >= 60:
            grade = "C"
        else:
            grade = "D"

        if confidence >= 90:
            strength = "VERY STRONG"
        elif confidence >= 80:
            strength = "STRONG"
        elif confidence >= 70:
            strength = "MODERATE"
        elif confidence >= 60:
            strength = "WEAK"
        else:
            strength = "VERY WEAK"

        hard_conflict = conflict_penalty >= 20
        tradable = (
            direction in {"BUY", "SELL"}
            and confidence >= self.minimum_confidence
            and bool(risk.get("tradable", False))
            and not hard_conflict
            and direction != "HOLD"
        )

        reasons = [
            f"Base evidence confidence: {base:.1f}",
            f"Directional agreement: {agreement}/3",
        ]
        if agreement_bonus:
            reasons.append(f"Agreement bonus: +{agreement_bonus:.1f}")
        if hard_conflict:
            reasons.append("Hard directional conflict blocks trade")
        reasons.extend(penalties)

        return {
            "confidence": confidence,
            "grade": grade,
            "strength": strength,
            "agreement": agreement,
            "agreement_bonus": agreement_bonus,
            "conflict_penalty": conflict_penalty,
            "hard_conflict": hard_conflict,
            "tradable": tradable,
            "direction": direction,
            "reasons": reasons,
        }

    @staticmethod
    def _score(data: Dict[str, Any], *keys: str) -> float:
        for key in keys:
            if key in data:
                try:
                    return max(0.0, min(100.0, float(data[key])))
                except (TypeError, ValueError):
                    pass
        return 50.0

    @staticmethod
    def _risk_quality(risk: Dict[str, Any]) -> float:
        if not risk.get("tradable", False):
            return 25.0
        rr = float(risk.get("risk_reward", 0.0))
        risk_level = str(risk.get("risk_level", "HIGH")).upper()
        score = min(100.0, rr * 30.0)
        if risk_level in {"VERY HIGH", "HIGH"}:
            score -= 20
        elif risk_level == "MODERATE":
            score -= 5
        return max(0.0, min(100.0, score))

    @staticmethod
    def _agreement(
        direction: str,
        structure_bias: str,
        trend_bias: str,
        momentum_bias: str,
    ) -> int:
        if direction == "BUY":
            return sum(
                bias in {"BULLISH", "BULL", "STRONG BULL"}
                for bias in (structure_bias, trend_bias, momentum_bias)
            )
        if direction == "SELL":
            return sum(
                bias in {"BEARISH", "BEAR", "STRONG BEAR"}
                for bias in (structure_bias, trend_bias, momentum_bias)
            )
        return 0
