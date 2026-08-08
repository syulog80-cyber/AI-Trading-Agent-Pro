"""Momentum analysis engine for AI Trading Agent Pro.

The engine combines RSI, MACD, ADX, volume and ATR into a normalized
momentum assessment. It does not make a trade decision by itself.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


class MomentumEngine:
    """Calculate momentum bias, strength and supporting evidence."""

    REQUIRED_COLUMNS = {
        "RSI",
        "MACD",
        "MACD_SIGNAL",
        "ADX",
        "volume",
        "VOL_SMA20",
        "ATR",
        "close",
    }

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return a normalized momentum analysis for the latest candle."""
        self._validate(df)

        last = df.iloc[-1]
        close = float(last["close"])
        rsi = float(last["RSI"])
        macd = float(last["MACD"])
        macd_signal = float(last["MACD_SIGNAL"])
        adx = float(last["ADX"])
        volume = float(last["volume"])
        vol_sma = float(last["VOL_SMA20"])
        atr = float(last["ATR"])

        volume_ratio = volume / vol_sma if vol_sma > 0 else 1.0
        atr_percent = (atr / close) * 100 if close > 0 else 0.0

        score = 50
        reasons: List[str] = []

        # RSI: reward directional momentum without treating overbought as
        # an automatic sell signal.
        if 55 <= rsi < 70:
            score += 15
            reasons.append("RSI supports bullish momentum")
        elif rsi >= 70:
            score += 5
            reasons.append("RSI is strongly bullish but overbought")
        elif 30 < rsi <= 45:
            score -= 15
            reasons.append("RSI supports bearish momentum")
        elif rsi <= 30:
            score -= 5
            reasons.append("RSI is strongly bearish but oversold")
        else:
            reasons.append("RSI is neutral")

        # MACD direction.
        if macd > macd_signal:
            score += 15
            reasons.append("MACD bullish")
            macd_bias = "BULLISH"
        elif macd < macd_signal:
            score -= 15
            reasons.append("MACD bearish")
            macd_bias = "BEARISH"
        else:
            macd_bias = "NEUTRAL"
            reasons.append("MACD neutral")

        # ADX measures trend strength, not direction.
        if adx >= 40:
            score += 10 if macd > macd_signal else -10 if macd < macd_signal else 0
            reasons.append("Very strong directional trend strength")
        elif adx >= 25:
            score += 5 if macd > macd_signal else -5 if macd < macd_signal else 0
            reasons.append("Moderate trend strength")
        else:
            reasons.append("Weak trend strength")

        # Volume confirmation.
        if volume_ratio >= 1.5:
            score += 10 if macd > macd_signal else -10 if macd < macd_signal else 0
            reasons.append("Strong volume confirmation")
        elif volume_ratio >= 1.1:
            score += 5 if macd > macd_signal else -5 if macd < macd_signal else 0
            reasons.append("Above-average volume")
        elif volume_ratio < 0.8:
            reasons.append("Low volume confirmation")
        else:
            reasons.append("Average volume")

        # Volatility is reported as context rather than being allowed to
        # overwhelm directional momentum.
        if atr_percent <= 0.5:
            volatility = "LOW"
            reasons.append("Low volatility")
        elif atr_percent >= 5:
            volatility = "HIGH"
            reasons.append("High volatility")
        else:
            volatility = "HEALTHY"
            reasons.append("Healthy volatility")

        score = max(0, min(100, int(round(score))))

        if score >= 70:
            bias = "BULLISH"
        elif score <= 30:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"

        distance = abs(score - 50)
        if distance >= 35:
            strength = "VERY STRONG"
        elif distance >= 25:
            strength = "STRONG"
        elif distance >= 15:
            strength = "MODERATE"
        else:
            strength = "WEAK"

        return {
            "bias": bias,
            "score": score,
            "strength": strength,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": macd_signal,
            "macd_bias": macd_bias,
            "adx": adx,
            "volume_ratio": volume_ratio,
            "atr": atr,
            "atr_percent": atr_percent,
            "volatility": volatility,
            "reasons": reasons,
        }

    @classmethod
    def _validate(cls, df: pd.DataFrame) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")
        if df.empty:
            raise ValueError("Cannot analyze an empty dataframe")

        missing = cls.REQUIRED_COLUMNS.difference(df.columns)
        if missing:
            raise ValueError(
                "Missing required momentum columns: "
                + ", ".join(sorted(missing))
            )

        numeric = df[list(cls.REQUIRED_COLUMNS)].apply(
            pd.to_numeric, errors="coerce"
        )
        if numeric.iloc[-1].isna().any():
            raise ValueError("Latest momentum inputs contain missing or non-numeric values")
