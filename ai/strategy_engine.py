"""Strategy selection engine for AI Trading Agent Pro.

This module converts independently measured market structure, trend and
momentum evidence into a strategy classification. It does not execute trades
and does not calculate position size.
"""

from __future__ import annotations

from typing import Any, Dict, List


class StrategyEngine:
    """Select the best-supported trading strategy from AI evidence."""

    STRATEGIES = (
        "Trend Following",
        "Breakout",
        "Pullback Buy",
        "Momentum",
        "Mean Reversion",
        "Short Trend",
        "Wait",
    )

    def analyze(
        self,
        structure: Dict[str, Any],
        trend: Dict[str, Any],
        momentum: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return strategy, score, direction and supporting reasons."""
        if not isinstance(structure, dict):
            raise TypeError("structure must be a dictionary")
        if not isinstance(trend, dict):
            raise TypeError("trend must be a dictionary")
        if not isinstance(momentum, dict):
            raise TypeError("momentum must be a dictionary")

        structure_direction = str(
            structure.get("direction", structure.get("trend", "Sideways"))
        ).upper()
        trend_direction = str(
            trend.get("direction", trend.get("trend", "NEUTRAL"))
        ).upper()
        trend_bias = str(trend.get("bias", "NEUTRAL")).upper()
        momentum_bias = str(momentum.get("bias", "NEUTRAL")).upper()

        structure_score = float(structure.get("structure_score", 50))
        trend_score = float(trend.get("trend_score", trend.get("score", 50)))
        momentum_score = float(momentum.get("score", 50))

        adx = float(momentum.get("adx", 0))
        rsi = float(momentum.get("rsi", 50))
        volume_ratio = float(momentum.get("volume_ratio", 1.0))
        has_bos = bool(structure.get("bos", False))

        candidates: Dict[str, float] = {name: 0.0 for name in self.STRATEGIES}
        reasons: Dict[str, List[str]] = {name: [] for name in self.STRATEGIES}

        bullish_structure = structure_direction in {"BULLISH", "STRONG BULL", "BULL"}
        bearish_structure = structure_direction in {"BEARISH", "STRONG BEAR", "BEAR"}
        bullish_trend = trend_direction in {"BULLISH", "STRONG BULL", "BULL"} or trend_bias == "BULLISH"
        bearish_trend = trend_direction in {"BEARISH", "STRONG BEAR", "BEAR"} or trend_bias == "BEARISH"

        # Trend Following: requires agreement between structure and trend.
        if bullish_structure and bullish_trend:
            candidates["Trend Following"] += 35
            reasons["Trend Following"].append("Bullish structure and trend agree")
        if bearish_structure and bearish_trend:
            candidates["Short Trend"] += 35
            reasons["Short Trend"].append("Bearish structure and trend agree")
        if adx >= 25:
            candidates["Trend Following"] += 15
            candidates["Short Trend"] += 15
            reasons["Trend Following"].append("ADX confirms trend strength")
            reasons["Short Trend"].append("ADX confirms trend strength")

        # Breakout: structure break plus momentum/volume confirmation.
        if has_bos:
            candidates["Breakout"] += 30
            reasons["Breakout"].append("Break of Structure detected")
        if volume_ratio >= 1.5:
            candidates["Breakout"] += 20
            reasons["Breakout"].append("Strong volume confirms expansion")
        if momentum_bias in {"BULLISH", "BEARISH"}:
            candidates["Breakout"] += 10
            reasons["Breakout"].append("Directional momentum confirms breakout")

        # Pullback Buy: bullish trend/structure with temporarily softer RSI.
        if bullish_structure and bullish_trend and 30 < rsi <= 50:
            candidates["Pullback Buy"] += 55
            reasons["Pullback Buy"].append("Bullish trend with controlled RSI weakness")
        if bullish_structure and momentum_bias == "BULLISH":
            candidates["Pullback Buy"] += 10

        # Momentum: strong directional momentum without enough structure
        # confirmation for a higher-conviction trend strategy.
        if momentum_score >= 70:
            candidates["Momentum"] += 30
            reasons["Momentum"].append("Strong momentum score")
        if adx >= 25:
            candidates["Momentum"] += 15
            reasons["Momentum"].append("ADX supports directional momentum")
        if volume_ratio >= 1.5:
            candidates["Momentum"] += 10
            reasons["Momentum"].append("Volume confirms momentum")

        # Mean reversion: only attractive in non-trending conditions.
        sideways = (
            structure_direction in {"SIDEWAYS", "NEUTRAL"}
            and trend_bias in {"SIDEWAYS", "NEUTRAL"}
        )
        if sideways:
            candidates["Mean Reversion"] += 30
            reasons["Mean Reversion"].append("Market structure is sideways")
        if rsi <= 30 or rsi >= 70:
            candidates["Mean Reversion"] += 25
            reasons["Mean Reversion"].append("RSI is at an extreme")
        if adx < 25:
            candidates["Mean Reversion"] += 15
            reasons["Mean Reversion"].append("ADX indicates limited trend strength")

        # Wait is deliberately competitive when evidence conflicts.
        directional_votes = sum(
            [bullish_structure, bullish_trend, momentum_bias == "BULLISH"]
        ) + sum(
            [bearish_structure, bearish_trend, momentum_bias == "BEARISH"]
        )
        if directional_votes <= 1:
            candidates["Wait"] += 30
            reasons["Wait"].append("Insufficient directional evidence")

        bullish_evidence = bullish_structure and bullish_trend and momentum_bias == "BEARISH"
        bearish_evidence = bearish_structure and bearish_trend and momentum_bias == "BULLISH"
        if bullish_evidence or bearish_evidence:
            candidates["Wait"] += 25
            reasons["Wait"].append("Trend and momentum conflict")

        # Prevent weak strategies from winning simply because they received
        # one generic bonus.
        if max(candidates.values()) < 40:
            selected = "Wait"
        else:
            selected = max(candidates, key=candidates.get)

        score = int(round(candidates[selected]))
        score = max(0, min(100, score))

        if selected in {"Trend Following", "Breakout", "Pullback Buy", "Momentum"}:
            direction = "BUY"
        elif selected == "Short Trend":
            direction = "SELL"
        elif selected == "Mean Reversion":
            direction = "BUY" if rsi <= 30 else "SELL" if rsi >= 70 else "HOLD"
        else:
            direction = "HOLD"

        confidence = int(round(
            structure_score * 0.35
            + trend_score * 0.30
            + momentum_score * 0.35
        ))
        confidence = max(0, min(100, confidence))

        return {
            "strategy": selected,
            "direction": direction,
            "score": score,
            "confidence": confidence,
            "candidates": {k: round(v, 1) for k, v in candidates.items()},
            "reasons": reasons[selected] or ["No strategy has sufficient evidence"],
        }
