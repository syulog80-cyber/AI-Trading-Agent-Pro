import pandas as pd
import pytest

from ai.momentum_engine import MomentumEngine


def make_frame(**latest):
    base = {
        "RSI": 62.0,
        "MACD": 2.0,
        "MACD_SIGNAL": 1.0,
        "ADX": 30.0,
        "volume": 1500.0,
        "VOL_SMA20": 1000.0,
        "ATR": 200.0,
        "close": 10000.0,
    }
    base.update(latest)
    return pd.DataFrame([base])


def test_bullish_momentum():
    result = MomentumEngine().analyze(make_frame())

    assert result["bias"] == "BULLISH"
    assert result["score"] > 50
    assert result["macd_bias"] == "BULLISH"
    assert result["volume_ratio"] == pytest.approx(1.5)


def test_bearish_momentum():
    result = MomentumEngine().analyze(
        make_frame(
            RSI=38.0,
            MACD=-2.0,
            MACD_SIGNAL=-1.0,
            ADX=30.0,
            volume=1500.0,
        )
    )

    assert result["bias"] == "BEARISH"
    assert result["score"] < 50
    assert result["macd_bias"] == "BEARISH"


def test_missing_column_is_rejected():
    df = make_frame().drop(columns=["RSI"])

    with pytest.raises(ValueError, match="Missing required momentum columns"):
        MomentumEngine().analyze(df)
