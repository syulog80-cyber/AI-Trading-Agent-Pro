"""
Market Structure Engine
=======================

Price-action structure analysis for AI Trading Agent Pro.

The engine detects:
    - Swing highs / lows
    - Higher Highs (HH)
    - Higher Lows (HL)
    - Lower Highs (LH)
    - Lower Lows (LL)
    - Break of Structure (BOS)
    - Change of Character (CHoCH)
    - Structure direction and score

This module deliberately does not depend on EMA, RSI, MACD, or other
indicators. It provides structural information that higher-level AI
components can combine with indicators later.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass(frozen=True)
class SwingPoint:
    """A confirmed local swing point."""

    index: Any
    position: int
    price: float
    kind: str  # "HIGH" or "LOW"


@dataclass(frozen=True)
class StructureEvent:
    """A structural event such as BOS or CHoCH."""

    event: str
    direction: str
    position: int
    price: float
    reference_price: float


class MarketStructure:
    """Analyze market structure using confirmed price swings."""

    def __init__(self, swing_left: int = 2, swing_right: int = 2) -> None:
        if swing_left < 1 or swing_right < 1:
            raise ValueError("swing_left and swing_right must be >= 1")

        self.swing_left = swing_left
        self.swing_right = swing_right

    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return a complete market-structure analysis."""
        self._validate_dataframe(df)

        swings = self.detect_swings(df)
        highs = [s for s in swings if s.kind == "HIGH"]
        lows = [s for s in swings if s.kind == "LOW"]

        classifications = self.classify_structure(highs, lows)
        events = self.detect_structure_events(df, highs, lows)

        score = self._structure_score(classifications, events)
        direction = self._direction(score, classifications)
        strength = self._strength(score, classifications)

        reasons = self._build_reasons(
            direction=direction,
            strength=strength,
            classifications=classifications,
            events=events,
        )

        return {
            "trend": direction,
            "direction": direction,
            "strength": strength,
            "structure_score": score,
            "swing_highs": len(highs),
            "swing_lows": len(lows),
            "higher_highs": len(classifications["higher_highs"]),
            "higher_lows": len(classifications["higher_lows"]),
            "lower_highs": len(classifications["lower_highs"]),
            "lower_lows": len(classifications["lower_lows"]),
            "bos": any(e.event == "BOS" for e in events),
            "choch": any(e.event == "CHoCH" for e in events),
            "last_bos": self._last_event(events, "BOS"),
            "last_choch": self._last_event(events, "CHoCH"),
            "swings": [asdict(s) for s in swings],
            "events": [asdict(e) for e in events],
            "reasons": reasons,
        }

    def detect_swings(self, df: pd.DataFrame) -> List[SwingPoint]:
        """Detect confirmed swing highs and lows."""
        self._validate_dataframe(df)

        highs = df["high"].astype(float).reset_index(drop=False)
        lows = df["low"].astype(float).reset_index(drop=False)

        swings: List[SwingPoint] = []
        left = self.swing_left
        right = self.swing_right

        for i in range(left, len(df) - right):
            high = float(highs.iloc[i]["high"])
            low = float(lows.iloc[i]["low"])

            left_highs = highs.iloc[i - left:i]["high"]
            right_highs = highs.iloc[i + 1:i + right + 1]["high"]
            left_lows = lows.iloc[i - left:i]["low"]
            right_lows = lows.iloc[i + 1:i + right + 1]["low"]

            if high > float(left_highs.max()) and high > float(right_highs.max()):
                swings.append(
                    SwingPoint(
                        index=highs.iloc[i]["timestamp"] if "timestamp" in highs else df.index[i],
                        position=i,
                        price=high,
                        kind="HIGH",
                    )
                )

            if low < float(left_lows.min()) and low < float(right_lows.min()):
                swings.append(
                    SwingPoint(
                        index=lows.iloc[i]["timestamp"] if "timestamp" in lows else df.index[i],
                        position=i,
                        price=low,
                        kind="LOW",
                    )
                )

        swings.sort(key=lambda x: x.position)
        return swings

    def classify_structure(
        self,
        highs: List[SwingPoint],
        lows: List[SwingPoint],
    ) -> Dict[str, List[SwingPoint]]:
        """Classify consecutive swing points by price progression."""
        result: Dict[str, List[SwingPoint]] = {
            "higher_highs": [],
            "higher_lows": [],
            "lower_highs": [],
            "lower_lows": [],
        }

        for previous, current in zip(highs, highs[1:]):
            if current.price > previous.price:
                result["higher_highs"].append(current)
            elif current.price < previous.price:
                result["lower_highs"].append(current)

        for previous, current in zip(lows, lows[1:]):
            if current.price > previous.price:
                result["higher_lows"].append(current)
            elif current.price < previous.price:
                result["lower_lows"].append(current)

        return result

    def detect_structure_events(
        self,
        df: pd.DataFrame,
        highs: List[SwingPoint],
        lows: List[SwingPoint],
    ) -> List[StructureEvent]:
        """Detect structural breaks using closes beyond prior swings."""
        if not highs and not lows:
            return []

        events: List[StructureEvent] = []
        structure_direction = self._initial_direction(highs, lows)
        candidates = sorted(highs + lows, key=lambda s: s.position)

        last_high: Optional[SwingPoint] = None
        last_low: Optional[SwingPoint] = None

        for swing in candidates:
            if swing.kind == "HIGH":
                last_high = swing
            else:
                last_low = swing

            start = swing.position + 1
            end = min(len(df), start + self.swing_right + 1)
            if start >= end:
                continue

            closes = df["close"].iloc[start:end].astype(float)

            if last_high is not None and not closes.empty:
                crossed_high = closes[closes > last_high.price]
                if not crossed_high.empty:
                    # ``crossed_high.index[0]`` may be a Timestamp when live
                    # OHLCV data uses a DatetimeIndex.  Convert the matching
                    # index label to a positional offset instead of subtracting
                    # labels (which produces a Timedelta).
                    crossed_index = crossed_high.index[0]
                    offset = closes.index.get_loc(crossed_index)
                    pos = start + int(offset)
                    event_type = "BOS" if structure_direction == "BULLISH" else "CHoCH"
                    events.append(
                        StructureEvent(
                            event=event_type,
                            direction="BULLISH",
                            position=pos,
                            price=float(df["close"].iloc[pos]),
                            reference_price=last_high.price,
                        )
                    )
                    structure_direction = "BULLISH"
                    last_high = None

            if last_low is not None and not closes.empty:
                crossed_low = closes[closes < last_low.price]
                if not crossed_low.empty:
                    crossed_index = crossed_low.index[0]
                    offset = closes.index.get_loc(crossed_index)
                    pos = start + int(offset)
                    event_type = "BOS" if structure_direction == "BEARISH" else "CHoCH"
                    events.append(
                        StructureEvent(
                            event=event_type,
                            direction="BEARISH",
                            position=pos,
                            price=float(df["close"].iloc[pos]),
                            reference_price=last_low.price,
                        )
                    )
                    structure_direction = "BEARISH"
                    last_low = None

        unique: List[StructureEvent] = []
        seen = set()
        for event in sorted(events, key=lambda e: e.position):
            key = (event.event, event.direction, event.position)
            if key not in seen:
                seen.add(key)
                unique.append(event)

        return unique

    def _structure_score(
        self,
        classifications: Dict[str, List[SwingPoint]],
        events: List[StructureEvent],
    ) -> int:
        score = 50
        score += 8 * len(classifications["higher_highs"])
        score += 8 * len(classifications["higher_lows"])
        score -= 8 * len(classifications["lower_highs"])
        score -= 8 * len(classifications["lower_lows"])

        for event in events[-4:]:
            if event.event == "BOS":
                score += 12 if event.direction == "BULLISH" else -12
            elif event.event == "CHoCH":
                score += 8 if event.direction == "BULLISH" else -8

        return max(0, min(100, int(score)))

    def _direction(
        self,
        score: int,
        classifications: Dict[str, List[SwingPoint]],
    ) -> str:
        bullish = len(classifications["higher_highs"]) + len(classifications["higher_lows"])
        bearish = len(classifications["lower_highs"]) + len(classifications["lower_lows"])

        if score >= 75 and bullish >= bearish:
            return "Strong Bull" if score >= 88 else "Bullish"
        if score <= 25 and bearish >= bullish:
            return "Strong Bear" if score <= 12 else "Bearish"
        return "Sideways"

    def _strength(
        self,
        score: int,
        classifications: Dict[str, List[SwingPoint]],
    ) -> str:
        distance = abs(score - 50)
        structure_count = sum(len(v) for v in classifications.values())

        if distance >= 35 and structure_count >= 4:
            return "VERY STRONG"
        if distance >= 25:
            return "STRONG"
        if distance >= 15:
            return "MODERATE"
        return "WEAK"

    def _initial_direction(
        self,
        highs: List[SwingPoint],
        lows: List[SwingPoint],
    ) -> str:
        if len(highs) >= 2 and len(lows) >= 2:
            high_up = highs[-1].price > highs[-2].price
            low_up = lows[-1].price > lows[-2].price
            high_down = highs[-1].price < highs[-2].price
            low_down = lows[-1].price < lows[-2].price

            if high_up and low_up:
                return "BULLISH"
            if high_down and low_down:
                return "BEARISH"

        return "NEUTRAL"

    @staticmethod
    def _last_event(events: List[StructureEvent], event_type: str) -> Optional[Dict[str, Any]]:
        for event in reversed(events):
            if event.event == event_type:
                return asdict(event)
        return None

    @staticmethod
    def _build_reasons(
        direction: str,
        strength: str,
        classifications: Dict[str, List[SwingPoint]],
        events: List[StructureEvent],
    ) -> List[str]:
        reasons: List[str] = []

        if direction == "Strong Bull":
            reasons.append("Strong bullish market structure")
        elif direction == "Bullish":
            reasons.append("Bullish market structure")
        elif direction == "Strong Bear":
            reasons.append("Strong bearish market structure")
        elif direction == "Bearish":
            reasons.append("Bearish market structure")
        else:
            reasons.append("No dominant market structure")

        if classifications["higher_highs"]:
            reasons.append("Higher highs detected")
        if classifications["higher_lows"]:
            reasons.append("Higher lows detected")
        if classifications["lower_highs"]:
            reasons.append("Lower highs detected")
        if classifications["lower_lows"]:
            reasons.append("Lower lows detected")

        if events:
            last = events[-1]
            reasons.append(f"Latest {last.event}: {last.direction}")

        reasons.append(f"Structure strength: {strength}")
        return reasons

    @staticmethod
    def _validate_dataframe(df: pd.DataFrame) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")

        required = {"high", "low", "close"}
        missing = required.difference(df.columns)
        if missing:
            raise ValueError(
                f"Missing required OHLC columns: {', '.join(sorted(missing))}"
            )

        if df.empty:
            raise ValueError("Cannot analyze an empty dataframe")

        if len(df) < 2:
            raise ValueError("At least 2 candles are required")

        numeric = df[["high", "low", "close"]].apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any():
            raise ValueError("OHLC data contains non-numeric or missing values")
