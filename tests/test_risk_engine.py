import pytest

from ai.risk_engine import RiskEngine


def test_buy_risk_plan_uses_atr_stop_and_target():
    result = RiskEngine(
        risk_percent=1.0,
        atr_stop_multiplier=2.0,
        reward_r_multiple=2.0,
        max_position_percent=100.0,
    ).analyze(
        entry_price=100.0,
        atr=2.0,
        direction="BUY",
        account_balance=10_000.0,
    )

    assert result["tradable"] is True
    assert result["stop_loss"] == pytest.approx(96.0)
    assert result["take_profit"] == pytest.approx(108.0)
    assert result["risk_reward"] == pytest.approx(2.0)
    assert result["requested_risk_amount"] == pytest.approx(100.0)
    assert result["risk_amount"] == pytest.approx(100.0)
    assert result["position_size"] == pytest.approx(25.0)


def test_position_value_is_capped():
    result = RiskEngine(
        risk_percent=1.0,
        atr_stop_multiplier=2.0,
        reward_r_multiple=2.0,
        max_position_percent=25.0,
    ).analyze(
        entry_price=100.0,
        atr=0.5,
        direction="BUY",
        account_balance=10_000.0,
    )

    assert result["capped_by_max_position"] is True
    assert result["position_value"] == pytest.approx(2500.0)
    assert result["position_percent"] == pytest.approx(25.0)
    assert result["risk_amount"] <= result["requested_risk_amount"]


def test_sell_risk_plan_places_stop_above_entry():
    result = RiskEngine().analyze(
        entry_price=100.0,
        atr=2.0,
        direction="SELL",
        account_balance=10_000.0,
    )

    assert result["stop_loss"] > result["entry_price"]
    assert result["take_profit"] < result["entry_price"]


def test_hold_has_no_position():
    result = RiskEngine().analyze(
        entry_price=100.0,
        atr=2.0,
        direction="HOLD",
        account_balance=10_000.0,
    )

    assert result["tradable"] is False
    assert result["position_size"] == 0.0
    assert result["stop_loss"] is None


def test_invalid_risk_percent_is_rejected():
    with pytest.raises(ValueError, match="risk_percent"):
        RiskEngine(risk_percent=0)
