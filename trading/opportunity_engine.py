class OpportunityEngine:
    """
    Professional Opportunity Ranking Engine
    """

    def __init__(self):

        self.grade_bonus = {

            "A+": 15,
            "A": 10,
            "B": 5,
            "C": 2,
            "D": 0

        }

        self.strategy_bonus = {

            "Trend Following": 15,

            "Breakout": 12,

            "Pullback Buy": 10,

            "Momentum": 8,

            "Mean Reversion": 5,

            "Short Trend": 8,

            "Wait": 0

        }

        self.market_bonus = {

            "Strong Trend": 10,

            "Trending": 7,

            "Volatile": 4,

            "Low Volatility": 2,

            "Sideways": 0

        }

    # =====================================

    def evaluate(self, prediction, alignment_score=0):

        score = prediction.get("score", 0)

        confidence = prediction.get("confidence", 0)

        grade = prediction.get("grade", "D")

        strategy = prediction.get("strategy", "Wait")

        market = prediction.get(

            "market_condition",

            "Sideways"

        )

        opportunity = (

            score * 0.40 +

            confidence * 0.35 +

            self.grade_bonus.get(grade, 0) +

            self.strategy_bonus.get(strategy, 0) +

            self.market_bonus.get(market, 0) +

            alignment_score

        )

        return round(opportunity, 2)