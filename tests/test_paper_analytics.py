from trading.paper_analytics import PaperAnalytics


def trades():
    return [
        {"symbol": "BNBUSDT", "strategy": "Breakout", "grade": "A+", "pnl": 40.0},
        {"symbol": "ETHUSDT", "strategy": "Trend Following", "grade": "A+", "pnl": -10.0},
        {"symbol": "BNBUSDT", "strategy": "Breakout", "grade": "A", "pnl": 20.0},
    ]


def test_summary_calculates_core_metrics():
    result = PaperAnalytics(trades()).summary()
    assert result["trades"] == 3
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["win_rate"] == 200 / 3
    assert result["net_pnl"] == 50.0
    assert result["profit_factor"] == 6.0


def test_grouping_by_strategy_and_symbol():
    analytics = PaperAnalytics(trades())
    assert analytics.by_strategy()["Breakout"]["trades"] == 2
    assert analytics.by_symbol()["BNBUSDT"]["net_pnl"] == 60.0


def test_grouping_by_grade():
    result = PaperAnalytics(trades()).by_grade()
    assert result["A+"]["trades"] == 2
    assert result["A"]["net_pnl"] == 20.0


def test_max_drawdown_is_reported():
    result = PaperAnalytics(trades()).max_drawdown(10000.0)
    assert result["max_drawdown"] == 10.0
    assert result["max_drawdown_percent"] == 0.1
