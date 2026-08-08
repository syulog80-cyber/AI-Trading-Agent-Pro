import json
from pathlib import Path

from trading.persistent_paper_runner import PersistentPaperTradingRunner


class FakeController:
    def __init__(self):
        self.price = 100.0

    def scan_market(self, symbols, timeframe="1h", min_confidence=70.0):
        return [{"symbol": "BTCUSDT", "signal": "BUY", "confidence": 90,
                 "grade": "A+", "tradable": True, "scanner_eligible": True}]

    def get_trade_plan(self, symbol, timeframe="1h"):
        return {"tradable": True, "direction": "BUY", "entry_price": self.price,
                "stop_loss": 95.0, "take_profit": 110.0, "position_size": 10.0}

    def load_market(self, symbol, timeframe="1m", limit=2):
        import pandas as pd
        return pd.DataFrame({"close": [self.price - 1, self.price]})


def test_persistent_runner_saves_and_restores(tmp_path: Path):
    path = tmp_path / "portfolio.json"
    controller = FakeController()
    first = PersistentPaperTradingRunner(controller, ["BTCUSDT"], portfolio_path=path)
    result = first.step()

    assert len(result["opened"]) == 1
    assert path.exists()

    second = PersistentPaperTradingRunner(controller, ["BTCUSDT"], portfolio_path=path)
    assert "BTCUSDT" in second.session.paper_trader.positions
    assert second.session.paper_trader.balance == 10_000.0


def test_persistent_runner_reset(tmp_path: Path):
    path = tmp_path / "portfolio.json"
    controller = FakeController()
    runner = PersistentPaperTradingRunner(controller, ["BTCUSDT"], portfolio_path=path)
    runner.step()
    state = runner.reset()

    assert state["balance"] == 10_000.0
    assert state["positions"] == {}
    assert state["trades"] == []

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["balance"] == 10_000.0
