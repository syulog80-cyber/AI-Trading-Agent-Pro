import pytest

from trading.paper_session import PaperTradingSession


class FakeController:
    def __init__(self):
        self.opened = []

    def scan_market(self, symbols, timeframe="1h", min_confidence=70.0):
        return [
            {
                "symbol": "BNBUSDT",
                "scanner_eligible": True,
                "confidence": 93.0,
                "grade": "A+",
            }
        ]

    def get_trade_plan(self, symbol, timeframe="1h"):
        return {
            "symbol": symbol,
            "direction": "BUY",
            "tradable": True,
            "entry_price": 100.0,
            "stop_loss": 96.0,
            "take_profit": 108.0,
            "position_size": 10.0,
        }


def test_session_opens_eligible_virtual_position():
    session = PaperTradingSession(FakeController(), initial_balance=10_000)

    opened = session.scan_and_open(["BNBUSDT"])

    assert len(opened) == 1
    assert opened[0]["symbol"] == "BNBUSDT"
    assert session.summary()["open_positions"] == 1


def test_session_does_not_open_duplicate_position():
    session = PaperTradingSession(FakeController(), initial_balance=10_000)

    session.scan_and_open(["BNBUSDT"])
    opened_again = session.scan_and_open(["BNBUSDT"])

    assert opened_again == []
    assert session.summary()["open_positions"] == 1


def test_session_updates_and_closes_virtual_position():
    session = PaperTradingSession(FakeController(), initial_balance=10_000)
    session.scan_and_open(["BNBUSDT"])

    closed = session.update_prices({"BNBUSDT": 108.0})

    assert len(closed) == 1
    assert closed[0]["reason"] == "TAKE_PROFIT"
    assert closed[0]["pnl"] == pytest.approx(80.0)
    assert session.summary()["open_positions"] == 0


def test_position_cap_is_enforced():
    session = PaperTradingSession(FakeController(), max_positions=1)
    session.paper_trader.open_position(
        {
            "direction": "BUY",
            "tradable": True,
            "entry_price": 100,
            "stop_loss": 96,
            "take_profit": 108,
            "position_size": 1,
        },
        "ETHUSDT",
    )

    assert session.scan_and_open(["BNBUSDT"]) == []


def test_invalid_session_configuration_is_rejected():
    with pytest.raises(ValueError):
        PaperTradingSession(FakeController(), max_positions=0)
