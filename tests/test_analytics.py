from trading.analytics import PaperTradingAnalytics


def trades():
    return [
        {"symbol": "BNBUSDT", "strategy": "Breakout", "grade": "A+", "signal": "BUY", "pnl": 40.0},
        {"symbol": "BNBUSDT", "strategy": "Breakout", "grade": "A+", "signal": "BUY", "pnl": -30.0},
        {"symbol": "ETHUSDT", "strategy": "Trend Following", "grade": "A+", "signal": "BUY", "pnl": 20.0},
    ]


def test_overall_metrics():
    result = PaperTradingAnalytics(trades()).overall()
    assert result["trades"] == 3
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["win_rate"] == 2 / 3 * 100
    assert result["net_pnl"] == 30.0
    assert result["profit_factor"] == 2.0


def test_grouped_strategy_metrics():
    result = PaperTradingAnalytics(trades()).by("strategy")
    assert result["BREAKOUT"]["trades"] == 2
    assert result["BREAKOUT"]["net_pnl"] == 10.0
    assert result["TREND FOLLOWING"]["wins"] == 1


def test_report_contains_required_breakdowns():
    report = PaperTradingAnalytics(trades()).report()
    assert set(report) == {"overall", "by_symbol", "by_strategy", "by_grade", "by_signal"}
