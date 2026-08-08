"""Compatibility adapter between the trading layer and the new AI brain."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from ai.ai_brain import AIBrain


class AIPredictor:
    """Expose the new AIBrain through the existing predictor interface."""

    def __init__(self, brain: Optional[AIBrain] = None) -> None:
        self.brain = brain or AIBrain()

    def predict(
        self,
        candles: pd.DataFrame,
        account_balance: float = 10_000.0,
    ) -> Dict[str, Any]:
        """Analyze an indicator-enriched candle dataframe.

        The controller can continue calling ``predict(candles)`` while the
        actual decision logic lives in ``ai.AIBrain``.
        """
        return self.brain.analyze(
            candles,
            account_balance=account_balance,
        )
