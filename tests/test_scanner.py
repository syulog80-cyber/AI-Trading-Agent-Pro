from trading.scanner import MarketScanner


class FakeMTF:
    def analyze(self, symbol):
        return {
            "15m": {"signal": "BUY"},
            "1h": {"signal": "BUY"},
            "4h": {"signal": "BUY"},
            "1d": {"signal": "BUY"},
        }

    def alignment(self, analyses):
        return {"buy": 4, "sell": 0, "hold": 0, "score": 10}

    def final_signal(self, analyses):
        return "BUY"


class FakeController:
    multi_tf = FakeMTF()

    def analyze_market(self, symbol, timeframe="1h"):
        return {
            "prediction": {
                "signal": "BUY",
                "score": 85,
                "confidence": 88,
                "grade": "A",
                "tradable": True,
                "strategy": "Trend Following",
                "market_condition": "Trending",
            }
        }


def test_scanner_returns_mtf_aligned_opportunity():
    result = MarketScanner(FakeController(), workers=1).scan(["BTCUSDT"])

    assert len(result) == 1
    item = result[0]
    assert item["symbol"] == "BTCUSDT"
    assert item["signal"] == "BUY"
    assert item["alignment_buy"] == 4
    assert item["alignment_sell"] == 0
    assert item["alignment_hold"] == 0
    assert item["scanner_eligible"] is True
    assert item["opportunity"] > 0


def test_scanner_rejects_low_confidence():
    controller = FakeController()
    controller.analyze_market = lambda symbol, timeframe="1h": {
        "prediction": {
            "signal": "BUY",
            "score": 85,
            "confidence": 60,
            "grade": "B",
            "tradable": True,
        }
    }

    result = MarketScanner(controller, workers=1).scan(["BTCUSDT"])

    assert result == []
