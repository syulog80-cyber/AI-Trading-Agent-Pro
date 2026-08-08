import pandas as pd

from trading.controller import TradingController


class FakeExchange:
    def __init__(self, candles):
        self.candles = candles

    def get_candles(self, symbol, timeframe="1h", limit=500):
        return self.candles.copy()

    def get_price(self, symbol):
        return float(self.candles.iloc[-1]["close"])

    def get_symbols(self):
        return ["BTCUSDT"]


def make_candles(rows=120):
    index = pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC")
    close = pd.Series([100 + i * 0.15 for i in range(rows)], index=index)
    return pd.DataFrame(
        {
            "open": close - 0.1,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": 1000.0,
        },
        index=index,
    )


def test_controller_analyze_market_uses_ai_pipeline():
    controller = TradingController()
    controller.exchange = FakeExchange(make_candles())

    result = controller.analyze_market("BTCUSDT", timeframe="1h", limit=120)

    assert "candles" in result
    assert "prediction" in result
    assert "signal" in result["prediction"]
    assert "confidence" in result["prediction"]
    assert "grade" in result["prediction"]
    assert "stop_loss" in result["prediction"]
    assert "take_profit" in result["prediction"]


def test_controller_get_trade_plan_exposes_mtf_fields(monkeypatch):
    controller = TradingController()
    controller.exchange = FakeExchange(make_candles())

    def fake_mtf(symbol, timeframes=("15m", "1h", "4h", "1d")):
        prediction = controller.predictor.predict(controller.load_market(symbol))
        return {tf: prediction for tf in timeframes}

    monkeypatch.setattr(controller.multi_tf, "analyze", fake_mtf)

    result = controller.get_trade_plan("BTCUSDT")

    assert result["symbol"] == "BTCUSDT"
    assert "analyses" in result
    assert "alignment" in result
    assert "signal" in result
    assert "entry_price" in result
    assert "risk_reward" in result
