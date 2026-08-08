class MultiTimeframeAnalyzer:
    """
    Professional Multi-Timeframe Analysis Engine
    """

    def __init__(self, controller):

        self.controller = controller

    # =====================================
    # Analyze Multiple Timeframes
    # =====================================

    def analyze(

        self,

        symbol,

        timeframes=("15m", "1h", "4h", "1d")

    ):

        analyses = {}

        for tf in timeframes:

            try:

                market = self.controller.analyze_market(

                    symbol,

                    timeframe=tf

                )

                analyses[tf] = market["prediction"]

            except Exception:

                analyses[tf] = None

        return analyses

        # =====================================
    # Alignment
    # =====================================

    def alignment(self, analyses):

        buy = 0
        sell = 0
        hold = 0

        score = 0

        weights = {

                "15m":1,

                "1h":2,

                "4h":3,

                "1d":4

              }

        for tf, prediction in analyses.items():

            if prediction is None:

                continue

            signal = prediction.get("signal", "HOLD")

            if signal == "BUY":

                buy += 1
                score += weights.get(tf, 1)

            elif signal == "SELL":

                sell += 1
                score -= weights.get(tf, 1)

            else:

                hold += 1

        return {

            "buy": buy,

            "sell": sell,

            "hold": hold,

            "score": score

        }

    # =====================================
    # Final Decision
    # =====================================

        # =====================================
    # Final Decision
    # =====================================

    def final_signal(self, analyses):

        alignment = self.alignment(analyses)

        score = alignment["score"]

        daily = analyses.get("1d")

    # -----------------------------
    # Daily Trend Filter
    # -----------------------------

        if daily:

          daily_trend = daily.get(
            "trend",
            "Sideways"
        )

        else:

          daily_trend = "Sideways"

    # -----------------------------
    # BUY
    # -----------------------------

        if (

          score >= 6

          and daily_trend in (

            "Bullish",

            "Strong Bull"

         )

        ):

         return "BUY"

    # -----------------------------
    # SELL
    # -----------------------------

        if (

          score <= -6

          and daily_trend in (

            "Bearish",

            "Strong Bear"

         )

        ):

         return "SELL"

        return "HOLD"