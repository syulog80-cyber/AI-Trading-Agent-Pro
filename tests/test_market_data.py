import pandas as pd

from trading.binance import BinanceConnector
from trading.indicators import IndicatorEngine


def make_ohlcv(rows=80):
    index = pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC")
    close = pd.Series([100 + i * 0.2 for i in range(rows)], index=index)
    return pd.DataFrame(
        {
            "open": close - 0.1,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1000.0,
        },
        index=index,
    )


def test_indicator_engine_produces_ai_required_columns():
    result = IndicatorEngine().calculate(make_ohlcv())

    required = {
        "RSI",
        "MACD",
        "MACD_SIGNAL",
        "ADX",
        "ATR",
        "VOL_SMA20",
    }
    assert required.issubset(result.columns)
    assert result[list(required)].iloc[-1].notna().all()


def test_binance_symbol_normalization():
    assert BinanceConnector._normalize_symbol("btc/usdt") == "BTCUSDT"
    assert BinanceConnector._normalize_symbol(" ethusdt ") == "ETHUSDT"


def test_binance_rejects_invalid_limit():
    connector = BinanceConnector()
    try:
        connector.get_candles("BTCUSDT", limit=0)
    except ValueError as exc:
        assert "between 1 and 1000" in str(exc)
    else:
        raise AssertionError("Expected invalid limit to be rejected before network access")
