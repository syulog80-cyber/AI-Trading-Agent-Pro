"""
Trend Engine
============

Converts market-structure output into a normalized trend assessment.

The engine intentionally consumes the MarketStructure result instead of
recalculating swings. This keeps price-structure detection and trend
interpretation as separate responsibilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping


class TrendEngine:
    """Interpret market structure and produce a normalized trend signal."""

    VALID_TRENDS = {
        "Strong Bull",
        "Bullish",
        "Sideways",
        "Bearish",
        "Strong Bear",
    }

    def analyze(self, structure: Mapping[str, Any]) -> Dict[str, Any]:
        """Return trend direction, strength, score and supporting reasons.

        Parameters
        ----------
        structure:
            Result returned by :class:`ai.market_structure.MarketStructure`.

        Returns
        -------
        dict
            A normalized trend analysis suitable for the AI brain and
            opportunity/scanner layers.
        """
        if not isinstance(structure, Mapping):
            raise TypeError("structure must be a mapping")

        trend = str(structure.get("trend", "Sideways"))
        score = self._normalize_score(structure.get("structure_score", 50))

        if trend not in self.VALID_TRENDS:
            trend = self._trend_from_score(score)

        strength = self._strength_from_score(score, trend)
        bias = self._bias(trend)
        reasons = self._reasons(structure, trend, strength)

        return {
            "trend": trend,
            "bias": bias,
            "strength": strength,
            "trend_score": score,
            "structure_score": score,
            "higher_highs": int(structure.get("higher_highs", 0) or 0),
            "higher_lows": int(structure.get("higher_lows", 0) or 0),
            "lower_highs": int(structure.get("lower_highs", 0) or 0),
            "lower_lows": int(structure.get("lower_lows", 0) or 0),
            "bos": bool(structure.get("bos", False)),
            "choch": bool(structure.get("choch", False)),
            "reasons": reasons,
        }

    @staticmethod
    def _normalize_score(value: Any) -> int:
        try:
            score = float(value)
        except (TypeError, ValueError):
            score = 50.0

        return max(0, min(100, int(round(score))))

    @staticmethod
    def _trend_from_score(score: int) -> str:
        if score >= 88:
            return "Strong Bull"
        if score >= 65:
            return "Bullish"
        if score <= 12:
            return "Strong Bear"
        if score <= 35:
            return "Bearish"
        return "Sideways"

    @staticmethod
    def _strength_from_score(score: int, trend: str) -> str:
        if trend == "Sideways":
            return "WEAK"

        distance = abs(score - 50)

        if distance >= 35:
            return "VERY STRONG"
        if distance >= 25:
            return "STRONG"
        if distance >= 15:
            return "MODERATE"
        return "WEAK"

    @staticmethod
    def _bias(trend: str) -> str:
        if trend in ("Strong Bull", "Bullish"):
            return "LONG"
        if trend in ("Strong Bear", "Bearish"):
            return "SHORT"
        return "NEUTRAL"

    @staticmethod
    def _reasons(
        structure: Mapping[str, Any],
        trend: str,
        strength: str,
    ) -> List[str]:
        reasons: List[str] = []

        reasons.append(f"Trend: {trend}")
        reasons.append(f"Trend strength: {strength}")

        if structure.get("higher_highs", 0):
            reasons.append("Higher highs support bullish structure")
        if structure.get("higher_lows", 0):
            reasons.append("Higher lows support bullish structure")
        if structure.get("lower_highs", 0):
            reasons.append("Lower highs support bearish structure")
        if structure.get("lower_lows", 0):
            reasons.append("Lower lows support bearish structure")
        if structure.get("bos"):
            reasons.append("Break of Structure detected")
        if structure.get("choch"):
            reasons.append("Change of Character detected")

        return reasons
