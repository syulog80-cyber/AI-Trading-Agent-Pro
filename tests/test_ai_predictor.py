import pandas as pd

from trading.ai_predictor import AIPredictor


def make_candles(rows=40):
    values = []
    price = 100.0
    for i in range(rows):
        close = price + (1.0 if i % 2 == 0 else -0.2)
        values.append(
            {
                "open": price,
                "high": max(price, close) + 1.0,
                "low": min(price, close) - 1.0,
                "close": close,
                "RSI": 60.0,
                "MACD": 1.0,
                "MACD_SIGNAL": 0.5,
                "ADX": 30.0,
                "volume": 1500.0,
                "VOL_SMA20": 1000.0,
                "ATR": 2.0,
            }
        )
        price = close
    return pd.DataFrame(values)


def test_predictor_exposes_brain_result():
    result = AIPredictor().predict(make_candles())

    assert "signal" in result
    assert "confidence" in result
    assert "grade" in result
    assert "strategy" in result
    assert "risk_analysis" in result
    assert "structure" in result
