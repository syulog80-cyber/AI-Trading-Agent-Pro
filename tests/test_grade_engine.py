import pytest

from ai.grade_engine import GradeEngine


def test_high_quality_trade_gets_a_grade():
    result = GradeEngine().analyze(
        confidence={"confidence": 92, "direction": "BUY", "tradable": True},
        strategy={"strategy": "Trend Following", "direction": "BUY"},
        risk={"tradable": True, "risk_reward": 2.0},
    )

    assert result["grade"] == "A+"
    assert result["quality"] == "EXCELLENT"
    assert result["tradable"] is True


def test_moderate_trade_gets_b_grade():
    result = GradeEngine().analyze(
        confidence={"confidence": 76, "direction": "BUY", "tradable": True},
        strategy={"strategy": "Momentum", "direction": "BUY"},
        risk={"tradable": True, "risk_reward": 1.8},
    )

    assert result["grade"] == "B"
    assert result["tradable"] is True


def test_wait_cannot_be_tradable():
    result = GradeEngine().analyze(
        confidence={"confidence": 80, "direction": "HOLD", "tradable": False},
        strategy={"strategy": "Wait", "direction": "HOLD"},
        risk={"tradable": False, "risk_reward": 0},
    )

    assert result["grade"] == "D"
    assert result["tradable"] is False


def test_hard_conflict_blocks_trade():
    result = GradeEngine().analyze(
        confidence={
            "confidence": 88,
            "direction": "BUY",
            "tradable": False,
            "hard_conflict": True,
        },
        strategy={"strategy": "Trend Following", "direction": "BUY"},
        risk={"tradable": True, "risk_reward": 2.0},
    )

    assert result["tradable"] is False
    assert result["score"] < 60
    assert "Hard directional conflict detected" in result["reasons"]


def test_invalid_inputs_are_rejected():
    with pytest.raises(TypeError):
        GradeEngine().analyze([], {}, {})
