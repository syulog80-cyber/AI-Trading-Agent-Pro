from ai.strategy_engine import StrategyEngine


def test_bullish_trend_selects_trend_following():
    result = StrategyEngine().analyze(
        structure={"direction": "Bullish", "structure_score": 85, "bos": False},
        trend={"direction": "Bullish", "bias": "BULLISH", "trend_score": 82},
        momentum={"bias": "BULLISH", "score": 78, "adx": 32, "rsi": 62, "volume_ratio": 1.2},
    )

    assert result["strategy"] == "Trend Following"
    assert result["direction"] == "BUY"
    assert result["confidence"] >= 70


def test_breakout_gets_selected_with_bos_and_volume():
    result = StrategyEngine().analyze(
        structure={"direction": "Bullish", "structure_score": 75, "bos": True},
        trend={"direction": "Neutral", "bias": "NEUTRAL", "trend_score": 55},
        momentum={"bias": "BULLISH", "score": 75, "adx": 28, "rsi": 64, "volume_ratio": 2.0},
    )

    assert result["strategy"] == "Breakout"
    assert result["direction"] == "BUY"


def test_conflicting_evidence_prefers_wait():
    result = StrategyEngine().analyze(
        structure={"direction": "Bullish", "structure_score": 70, "bos": False},
        trend={"direction": "Bullish", "bias": "BULLISH", "trend_score": 70},
        momentum={"bias": "BEARISH", "score": 30, "adx": 30, "rsi": 42, "volume_ratio": 1.0},
    )

    assert result["strategy"] == "Wait"
    assert result["direction"] == "HOLD"
