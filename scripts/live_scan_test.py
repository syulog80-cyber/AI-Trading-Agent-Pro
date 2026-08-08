"""Read-only live scanner smoke test.

Usage:
    python scripts/live_scan_test.py BTCUSDT ETHUSDT BNBUSDT SOLUSDT

No orders are submitted.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from trading.controller import TradingController


DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]


def main() -> int:
    symbols = [s.upper() for s in sys.argv[1:]] or DEFAULT_SYMBOLS
    timeframe = os.getenv("AI_SCAN_TIMEFRAME", "1h")

    print("=" * 68)
    print("AI TRADING AGENT PRO — LIVE MULTI-SYMBOL SCAN")
    print("Public market data only — NO ORDER EXECUTION")
    print("=" * 68)
    print(f"Timeframe: {timeframe}")
    print(f"Symbols:   {', '.join(symbols)}")
    print()

    controller = TradingController()
    results = controller.scan_market(symbols, timeframe=timeframe)

    if not results:
        print("No scanner-eligible opportunities found.")
        print("This is normal when the multi-timeframe/risk gates reject all symbols.")
        print("\nLIVE MULTI-SYMBOL SCAN COMPLETED")
        print("No orders were submitted.")
        return 0

    print(f"Eligible opportunities: {len(results)}")
    print()
    print("SYMBOL       SIGNAL  CONF   GRADE  STRATEGY             OPP     MTF")
    print("-" * 68)

    for result in results:
        symbol = str(result.get("symbol", "?"))[:10]
        signal = str(result.get("signal", "HOLD"))[:6]
        confidence = float(result.get("confidence", 0))
        grade = str(result.get("grade", "D"))[:4]
        strategy = str(result.get("strategy", "Wait"))[:20]
        opportunity = float(result.get("opportunity", 0))
        mtf = (
            f"B{result.get('alignment_buy', 0)} "
            f"S{result.get('alignment_sell', 0)} "
            f"H{result.get('alignment_hold', 0)}"
        )
        print(
            f"{symbol:<10} {signal:<7} {confidence:>5.1f} "
            f"{grade:<6} {strategy:<20} {opportunity:>6.1f} {mtf}"
        )

    print()
    print("LIVE MULTI-SYMBOL SCAN COMPLETED")
    print("No orders were submitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
