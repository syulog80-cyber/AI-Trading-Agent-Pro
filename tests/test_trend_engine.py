from ai.trend_engine import TrendEngine


def test_trend_engine_uses_market_structure():
    engine = TrendEngine()

    result = engine.analyze(
        {
            "trend": "Strong Bull",
            "structure_score": 92,
            "higher_highs": 4,
            "higher_lows": 3,
            "lower_highs": 0,
            "lower_lows": 0,
            "bos": True,
            "choch": False,
        }
    )

    assert result["trend"] == "Strong Bull"
    assert result["bias"] == "LONG"
    assert result["trend_score"] == 92
    assert result["strength"] == "VERY STRONG"
    assert result["bos"] is True


def test_trend_engine_falls_back_to_score():
    engine = TrendEngine()

    result = engine.analyze({"trend": "Unknown", "structure_score": 20})

    assert result["trend"] == "Bearish"
    assert result["bias"] == "SHORT"


def test_sideways_is_neutral():
    engine = TrendEngine()

    result = engine.analyze(
        {
            "trend": "Sideways",
            "structure_score": 50,
        }
    )

    assert result["trend"] == "Sideways"
    assert result["bias"] == "NEUTRAL"
    assert result["strength"] == "WEAK"
