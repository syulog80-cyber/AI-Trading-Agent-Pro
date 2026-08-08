"""Integrated market scanner for AI Trading Agent Pro."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, Iterable, List

from trading.opportunity_engine import OpportunityEngine


class MarketScanner:
    """Scan symbols through the controller, MTF alignment and opportunity engine."""

    def __init__(self, controller, workers: int = 8) -> None:
        if workers < 1:
            raise ValueError("workers must be >= 1")
        self.controller = controller
        self.workers = workers
        self.opportunity = OpportunityEngine()

    def scan(
        self,
        symbols: Iterable[str],
        timeframe: str = "1h",
        workers: int | None = None,
        min_confidence: float = 70.0,
        allowed_grades: tuple[str, ...] = ("A+", "A", "B"),
    ) -> List[Dict[str, Any]]:
        """Return tradable opportunities sorted from strongest to weakest."""
        symbols = list(symbols)
        worker_count = workers or self.workers
        if worker_count < 1:
            raise ValueError("workers must be >= 1")

        def analyze(symbol: str) -> Dict[str, Any]:
            try:
                market = self.controller.analyze_market(symbol, timeframe=timeframe)
                prediction = market["prediction"]

                analyses = self.controller.multi_tf.analyze(symbol)
                alignment = self.controller.multi_tf.alignment(analyses)
                final_signal = self.controller.multi_tf.final_signal(analyses)

                opportunity = self.opportunity.evaluate(
                    prediction,
                    alignment_score=alignment["score"],
                )

                result = dict(prediction)
                result.update(
                    {
                        "symbol": symbol,
                        "signal": final_signal,
                        "single_timeframe_signal": prediction.get("signal", "HOLD"),
                        "alignment_buy": alignment["buy"],
                        "alignment_sell": alignment["sell"],
                        "alignment_hold": alignment["hold"],
                        "alignment_score": alignment["score"],
                        "opportunity": opportunity,
                        "scan_time": datetime.now(),
                    }
                )

                # Scanner eligibility is deliberately stricter than merely
                # having a BUY/SELL signal.
                result["scanner_eligible"] = (
                    final_signal in {"BUY", "SELL"}
                    and float(result.get("confidence", 0)) >= min_confidence
                    and result.get("grade", "D") in allowed_grades
                    and bool(result.get("tradable", False))
                )
                return result
            except Exception as exc:
                return {
                    "symbol": symbol,
                    "skipped": True,
                    "reason": str(exc),
                    "scan_time": datetime.now(),
                }

        results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(analyze, symbol) for symbol in symbols]
            for future in as_completed(futures):
                result = future.result()
                if not result.get("skipped", False):
                    results.append(result)

        results = [r for r in results if r.get("scanner_eligible", False)]
        results.sort(
            key=lambda r: (
                float(r.get("opportunity", 0)),
                float(r.get("confidence", 0)),
                float(r.get("score", 0)),
            ),
            reverse=True,
        )
        return results
