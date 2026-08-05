
class MultiTimeframeAnalyzer:
    """AI Trading Agent Pro v2 - Multi Timeframe Analysis"""

    WEIGHTS = {
        "15m": 1,
        "1h": 2,
        "4h": 3,
        "1d": 4,
    }

    def __init__(self, controller):
        self.controller = controller

    def analyze(self, symbol, timeframes=("15m", "1h", "4h", "1d")):
        analyses = {}

        for tf in timeframes:
            try:
                market = self.controller.analyze_market(
                    symbol=symbol,
                    timeframe=tf
                )
                analyses[tf] = market["prediction"]
            except Exception:
                analyses[tf] = None

        return analyses

    def alignment(self, analyses):
        buy = sell = hold = score = 0

        for tf, prediction in analyses.items():

            if prediction is None:
                continue

            weight = self.WEIGHTS.get(tf, 1)
            signal = prediction.get("signal", "HOLD")

            if signal == "BUY":
                buy += 1
                score += weight

            elif signal == "SELL":
                sell += 1
                score -= weight

            else:
                hold += 1

        return {
            "buy": buy,
            "sell": sell,
            "hold": hold,
            "score": score
        }

    def final_signal(self, analyses):
        alignment = self.alignment(analyses)
        score = alignment["score"]

        daily = analyses.get("1d")

        if daily:
            trend = daily.get("trend", "Sideways")
        else:
            trend = "Sideways"

        if score >= 6 and trend in ("Bullish", "Strong Bull"):
            return "BUY"

        if score <= -6 and trend in ("Bearish", "Strong Bear"):
            return "SELL"

        return "HOLD"

    def summary(self, analyses):
        align = self.alignment(analyses)

        return {
            "final_signal": self.final_signal(analyses),
            "alignment": align,
            "timeframes": analyses
        }
