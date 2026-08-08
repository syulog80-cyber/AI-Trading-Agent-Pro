import pandas as pd

from trading.paper_runner import PaperTradingRunner


class FakeController:
    def __init__(self):
        self.price = 100.0
        self.scan_calls = 0
        self.plan_calls = 0

    def scan_market(self, symbols, timeframe="1h", min_confidence=70.0):
        self.scan_calls += 1
        return [
            {
                "symbol": "BTCUSDT",
                "signal": "BUY",
                "confidence": 90,
                "grade": "A+",
                "tradable": True,
                "scanner_eligible": True,
            }
        ]

    def get_trade_plan(self, symbol, timeframe="1h"):
        self.plan_calls += 1
        return {
            "tradable": True,
            "direction": "BUY",
            "entry_price": self.price,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "position_size": 10.0,
        }

    def load_market(self, symbol, timeframe="1m", limit=2):
        return pd.DataFrame({"close": [self.price - 1, self.price]})


def test_runner_opens_virtual_position():
    controller = FakeController()
    runner = PaperTradingRunner(controller, ["BTCUSDT"])

    result = runner.step()

    assert len(result["opened"]) == 1
    assert "BTCUSDT" in runner.session.paper_trader.positions
    assert result["performance"]["open_positions"] == 1


def test_runner_does_not_duplicate_open_position():
    controller = FakeController()
    runner = PaperTradingRunner(controller, ["BTCUSDT"])

    runner.step()
    result = runner.step()

    assert len(result["opened"]) == 0
    assert len(runner.session.paper_trader.positions) == 1


def test_runner_journals_closed_trade():
    controller = FakeController()
    runner = PaperTradingRunner(controller, ["BTCUSDT"])

    runner.step()
    controller.price = 110.0
    result = runner.step()

    assert len(result["closed"]) == 1
    assert result["closed"][0]["reason"] == "TAKE_PROFIT"
    assert result["performance"]["total_trades"] == 1
    assert result["performance"]["wins"] == 1


def test_runner_requires_symbols():
    controller = FakeController()

    try:
        PaperTradingRunner(controller, [])
        assert False, "Expected ValueError"
    except ValueError:
        pass
