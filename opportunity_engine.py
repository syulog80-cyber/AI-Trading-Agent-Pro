
class OpportunityEngine:
    """
    AI Trading Agent Pro v2

    Calculates a normalized opportunity score used by the market scanner
    to rank trading candidates.
    """

    GRADE_BONUS = {
        "A+": 15,
        "A": 10,
        "B": 5,
        "C": 2,
        "D": 0
    }

    STRATEGY_BONUS = {
        "Trend Following": 15,
        "Breakout": 12,
        "Pullback Buy": 10,
        "Momentum": 8,
        "Mean Reversion": 5,
        "Short Trend": 8,
        "Wait": 0
    }

    MARKET_BONUS = {
        "Strong Trend": 10,
        "Trending": 7,
        "Volatile": 4,
        "Low Volatility": 2,
        "Sideways": 0
    }

    RISK_PENALTY = {
        "LOW": 0,
        "MEDIUM": -3,
        "HIGH": -8
    }

    def evaluate(self, prediction, alignment_score=0):
        score = float(prediction.get("score", 0))
        confidence = float(prediction.get("confidence", 0))
        grade = prediction.get("grade", "D")
        strategy = prediction.get("strategy", "Wait")
        market = prediction.get("market_condition", "Sideways")
        risk = prediction.get("risk", "MEDIUM")

        opportunity = (
            score * 0.40
            + confidence * 0.35
            + self.GRADE_BONUS.get(grade, 0)
            + self.STRATEGY_BONUS.get(strategy, 0)
            + self.MARKET_BONUS.get(market, 0)
            + alignment_score
            + self.RISK_PENALTY.get(risk, -3)
        )

        return round(opportunity, 2)

    def rank(self, predictions):
        return sorted(
            predictions,
            key=lambda x: x.get("opportunity", 0),
            reverse=True
        )

    def is_tradeable(self, prediction):
        return (
            prediction.get("signal") != "HOLD"
            and prediction.get("confidence", 0) >= 70
            and prediction.get("grade", "D") in ("A+", "A", "B")
        )
