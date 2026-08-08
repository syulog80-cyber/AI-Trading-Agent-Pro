"""Technical indicator calculations used by the AI analysis pipeline."""

from __future__ import annotations

import pandas as pd


class IndicatorEngine:
    """Calculate the normalized indicator columns required by the AI engines."""

    def calculate(self, candles: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(candles, pd.DataFrame):
            raise TypeError("candles must be a pandas DataFrame")
        if candles.empty:
            raise ValueError("Cannot calculate indicators on an empty dataframe")

        required = {"open", "high", "low", "close", "volume"}
        missing = required.difference(candles.columns)
        if missing:
            raise ValueError(
                "Missing required OHLCV columns: " + ", ".join(sorted(missing))
            )

        df = candles.copy()
        for column in ["open", "high", "low", "close", "volume"]:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        close = df["close"]
        high = df["high"]
        low = df["low"]

        # RSI(14), Wilder-style smoothing via exponential moving average.
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
        avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
        rs = avg_gain / avg_loss.replace(0, pd.NA)
        df["RSI"] = 100 - (100 / (1 + rs))
        df["RSI"] = pd.to_numeric(df["RSI"], errors="coerce").fillna(50.0)

        # MACD(12, 26, 9).
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]

        # True range and ATR(14).
        previous_close = close.shift(1)
        true_range = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        df["TR"] = true_range
        df["ATR"] = true_range.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
        df["ATR"] = df["ATR"].fillna(true_range.expanding(min_periods=1).mean())

        # ADX(14).
        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

        atr = df["ATR"].replace(0, pd.NA)
        plus_di = 100 * plus_dm.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean() / atr
        minus_di = 100 * minus_dm.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean() / atr
        denominator = (plus_di + minus_di).replace(0, pd.NA)
        dx = 100 * (plus_di - minus_di).abs() / denominator
        df["PLUS_DI"] = plus_di.fillna(0.0)
        df["MINUS_DI"] = minus_di.fillna(0.0)
        df["ADX"] = dx.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean().fillna(0.0)

        # Volume confirmation.
        df["VOL_SMA20"] = df["volume"].rolling(20, min_periods=1).mean()
        df["VOLUME_RATIO"] = df["volume"] / df["VOL_SMA20"].replace(0, pd.NA)
        df["VOLUME_RATIO"] = pd.to_numeric(df["VOLUME_RATIO"], errors="coerce").fillna(1.0)

        # Useful trend context for downstream consumers.
        df["EMA20"] = close.ewm(span=20, adjust=False).mean()
        df["EMA50"] = close.ewm(span=50, adjust=False).mean()
        df["EMA200"] = close.ewm(span=200, adjust=False).mean()

        # Ensure the latest row has valid values for every AI-required field.
        required_ai = ["RSI", "MACD", "MACD_SIGNAL", "ADX", "ATR", "VOL_SMA20"]
        df[required_ai] = df[required_ai].ffill().bfill()

        if df[required_ai].isna().any().any():
            raise ValueError("Unable to produce valid indicator values")

        return df
