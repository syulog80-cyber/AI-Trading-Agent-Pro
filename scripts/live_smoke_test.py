"""Manual live smoke test for the public Binance analysis pipeline.

This script reads public market data only. It does not place orders.
Run from the repository root with:
    python scripts/live_smoke_test.py BTCUSDT
"""

from __future__ import annotations

import argparse
import json
import sys

from trading.controller import TradingController


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Trading Agent live smoke test")
    parser.add_argument("symbol", nargs="?", default="BTCUSDT")
    parser.add_argument("--timeframe", default="1h")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    controller = TradingController()

    print("=" * 60)
    print("AI TRADING AGENT PRO — LIVE MARKET SMOKE TEST")
    print("Public market data only — NO ORDER EXECUTION")
    print("=" * 60)
    print(f"Symbol:    {symbol}")
    print(f"Timeframe: {args.timeframe}")

    try:
        market = controller.analyze_market(symbol, timeframe=args.timeframe)
        prediction = market["prediction"]

        print("\n--- SINGLE TIMEFRAME ---")
        print(f"Signal:      {prediction.get('signal', 'HOLD')}")
        print(f"Confidence:  {prediction.get('confidence', 0)}")
        print(f"Grade:       {prediction.get('grade', 'D')}")
        print(f"Strategy:    {prediction.get('strategy', 'Wait')}")
        print(f"Trend:       {prediction.get('trend', 'Unknown')}")
        print(f"Tradable:    {prediction.get('tradable', False)}")
        print(f"Entry:       {prediction.get('entry_price')}")
        print(f"Stop Loss:   {prediction.get('stop_loss')}")
        print(f"Take Profit: {prediction.get('take_profit')}")
        print(f"Risk/Reward: {prediction.get('risk_reward')}")
        print(f"Candle time: {market.get('candle_time')}")

        mtf = controller.analyze_multi_timeframe(symbol)
        print("\n--- MULTI-TIMEFRAME ---")
        print(f"Final Signal: {mtf['signal']}")
        print(f"Alignment:    {json.dumps(mtf['alignment'], default=str)}")

        for timeframe, analysis in mtf["analyses"].items():
            if analysis is None:
                print(f"{timeframe:>4}: unavailable")
            else:
                print(
                    f"{timeframe:>4}: "
                    f"{analysis.get('signal', 'HOLD')} | "
                    f"confidence={analysis.get('confidence', 0)} | "
                    f"grade={analysis.get('grade', 'D')}"
                )

        print("\nLIVE SMOKE TEST COMPLETED")
        print("No orders were submitted.")
        return 0

    except Exception as exc:
        print("\nLIVE SMOKE TEST FAILED")
        print(f"{type(exc).__name__}: {exc}")
        print("No orders were submitted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
