import pytest

from trading.paper_trader import PaperTrader


def buy_plan():
    return {
        "tradable": True,
        "direction": "BUY",
        "entry_price": 100.0,
        "stop_loss": 96.0,
        "take_profit": 108.0,
        "position_size": 25.0,
    }


def test_paper_buy_reaches_target():
    trader = PaperTrader(10_000)
    position = trader.open_position(buy_plan(), "BTCUSDT")

    assert position["position_value"] == pytest.approx(2500.0)
    trade = trader.update_price("BTCUSDT", 108.0)

    assert trade["reason"] == "TAKE_PROFIT"
    assert trade["pnl"] == pytest.approx(200.0)
    assert trader.balance == pytest.approx(10_200.0)


def test_paper_buy_hits_stop():
    trader = PaperTrader(10_000)
    trader.open_position(buy_plan(), "BTCUSDT")
    trade = trader.update_price("BTCUSDT", 96.0)

    assert trade["reason"] == "STOP_LOSS"
    assert trade["pnl"] == pytest.approx(-100.0)
    assert trader.balance == pytest.approx(9_900.0)


def test_untradable_plan_is_rejected():
    trader = PaperTrader()
    plan = buy_plan()
    plan["tradable"] = False

    with pytest.raises(ValueError, match="not tradable"):
        trader.open_position(plan, "BTCUSDT")


def test_summary_reports_win_rate():
    trader = PaperTrader(10_000)
    trader.open_position(buy_plan(), "BTCUSDT")
    trader.update_price("BTCUSDT", 108.0)

    summary = trader.summary()

    assert summary["closed_trades"] == 1
    assert summary["wins"] == 1
    assert summary["win_rate"] == pytest.approx(100.0)
