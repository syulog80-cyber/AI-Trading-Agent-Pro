import pandas as pd

from ai.market_structure import MarketStructure


def make_candles(closes):
    return pd.DataFrame(
        {
            "open": closes,
            "high": [x + 1 for x in closes],
            "low": [x - 1 for x in closes],
            "close": closes,
            "volume": [100.0] * len(closes),
        }
    )


def test_market_structure_returns_expected_keys():
    closes = [10, 12, 15, 12, 11, 14, 18, 15, 14, 17, 21, 18, 17, 20, 24]
    result = MarketStructure().analyze(make_candles(closes))

    assert "trend" in result
    assert "structure_score" in result
    assert "swing_highs" in result
    assert "swing_lows" in result
    assert "events" in result


def test_empty_dataframe_is_rejected():
    df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

    try:
        MarketStructure().analyze(df)
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_market_structure_handles_datetime_index():
    closes = [10, 12, 15, 12, 11, 14, 18, 15, 14, 17, 21, 18, 17, 20, 24]
    df = make_candles(closes)
    df.index = pd.date_range("2026-01-01", periods=len(df), freq="h")

    result = MarketStructure().analyze(df)

    assert isinstance(result["events"], list)
    assert all(isinstance(event["position"], int) for event in result["events"])
