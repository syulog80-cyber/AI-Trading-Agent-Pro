import pytest

from ai.confidence_engine import ConfidenceEngine


def base_inputs():
    return {
        "structure": {"direction": "Bullish", "structure_score": 90},
        "trend": {"bias": "BULLISH", "trend_score": 88},
        "momentum": {"bias": "BULLISH", "score": 85},
        "strategy": {"direction": "BUY", "score": 90},
        "risk": {
            "tradable": True,
            "risk_reward": 2.0,
            "risk_level": "LOW",
        },
    }


def test_high_agreement_produces_strong_confidence():
    result = ConfidenceEngine().analyze(**base_inputs())

    assert result["confidence"] >= 80
    assert result["grade"] in {"A", "A+"}
    assert result["agreement"] == 3
    assert result["conflict_penalty"] == 0
    assert result["tradable"] is True


def test_conflicting_momentum_reduces_buy_confidence():
    inputs = base_inputs()
    inputs["momentum"] = {"bias": "BEARISH", "score": 35}

    result = ConfidenceEngine().analyze(**inputs)

    assert result["conflict_penalty"] >= 20
    assert result["confidence"] < 80
    assert result["tradable"] is False


def test_sell_agreement_is_supported():
    inputs = base_inputs()
    inputs["structure"] = {"direction": "Bearish", "structure_score": 85}
    inputs["trend"] = {"bias": "BEARISH", "trend_score": 82}
    inputs["momentum"] = {"bias": "BEARISH", "score": 80}
    inputs["strategy"] = {"direction": "SELL", "score": 85}

    result = ConfidenceEngine().analyze(**inputs)

    assert result["direction"] == "SELL"
    assert result["agreement"] == 3
    assert result["conflict_penalty"] == 0


def test_hold_is_not_tradable():
    inputs = base_inputs()
    inputs["strategy"] = {"direction": "HOLD", "score": 40}
    inputs["risk"] = {"tradable": False, "risk_reward": 0, "risk_level": "HIGH"}

    result = ConfidenceEngine().analyze(**inputs)

    assert result["direction"] == "HOLD"
    assert result["tradable"] is False


def test_invalid_minimum_confidence_is_rejected():
    with pytest.raises(ValueError, match="minimum_confidence"):
        ConfidenceEngine(minimum_confidence=101)
