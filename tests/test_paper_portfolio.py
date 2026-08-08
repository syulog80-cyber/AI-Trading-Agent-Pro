import pytest

from trading.paper_trader import PaperTrader


def buy_plan():
    return {
        "tradable": True,
        "direction": "BUY",
        "entry_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "position_size": 10.0,
    }


def test_mark_to_market_calculates_unrealized_pnl_and_equity():
    trader = PaperTrader(10_000)
    trader.open_position(buy_plan(), "BTCUSDT")

    mark = trader.mark_to_market({"BTCUSDT": 105.0})

    assert mark["balance"] == pytest.approx(10_000.0)
    assert mark["realized_pnl"] == pytest.approx(0.0)
    assert mark["unrealized_pnl"] == pytest.approx(50.0)
    assert mark["equity"] == pytest.approx(10_050.0)
    assert mark["position_value"] == pytest.approx(1050.0)


def test_mark_to_market_supports_short_positions():
    trader = PaperTrader(10_000)
    plan = buy_plan()
    plan.update({
        "direction": "SELL",
        "entry_price": 100.0,
        "stop_loss": 105.0,
        "take_profit": 90.0,
    })
    trader.open_position(plan, "BTCUSDT")

    mark = trader.mark_to_market({"BTCUSDT": 95.0})

    assert mark["unrealized_pnl"] == pytest.approx(50.0)
    assert mark["equity"] == pytest.approx(10_050.0)


def test_missing_price_does_not_invent_unrealized_pnl():
    trader = PaperTrader(10_000)
    trader.open_position(buy_plan(), "BTCUSDT")

    mark = trader.mark_to_market({})

    assert mark["unrealized_pnl"] == pytest.approx(0.0)
    assert mark["equity"] == pytest.approx(10_000.0)
    assert mark["positions"] == []
