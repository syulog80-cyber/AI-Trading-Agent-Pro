"""Continuous read-only persistent paper-trading runner.

Public market data only. This script never submits exchange orders.
Press Ctrl+C to stop safely; the persistent portfolio is saved after each cycle.
"""
from __future__ import annotations

import argparse
import time
from typing import Any

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from trading.controller import TradingController
from trading.persistent_paper_runner import PersistentPaperTradingRunner

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]


def print_cycle(result: dict[str, Any], cycle: int) -> None:
    performance = result["performance"]
    print("\n" + "=" * 68)
    print(f"PAPER CYCLE #{cycle}")
    print("=" * 68)
    print(f"Opportunities: {result['scan_count']}")

    for item in result["opportunities"]:
        print(
            f"  {item.get('symbol')}: {item.get('signal')} | "
            f"confidence={float(item.get('confidence', 0)):.1f} | "
            f"grade={item.get('grade')} | strategy={item.get('strategy')} | "
            f"opportunity={float(item.get('opportunity', 0)):.1f}"
        )

    print(f"Opened: {len(result['opened'])} | Closed: {len(result['closed'])}")
    print(f"Open positions: {performance.get('open_positions', 0)}")
    print(f"Balance: ${performance.get('balance', 0):,.2f}")
    print(f"Unrealized P&L: ${performance.get('unrealized_pnl', 0):,.2f}")
    print(f"Equity: ${performance.get('equity', 0):,.2f}")
    print(f"Closed trades: {performance.get('closed_trades', 0)}")
    print(f"Win rate: {performance.get('win_rate', 0):.2f}%")


def main() -> int:
    parser = argparse.ArgumentParser(description="Continuous persistent paper trading")
    parser.add_argument("symbols", nargs="*", default=DEFAULT_SYMBOLS)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--interval", type=int, default=300, help="Seconds between cycles")
    parser.add_argument("--balance", type=float, default=10_000.0)
    parser.add_argument("--max-positions", type=int, default=3)
    parser.add_argument("--min-confidence", type=float, default=70.0)
    parser.add_argument("--portfolio", default="data/paper_portfolio.json")
    parser.add_argument("--cycles", type=int, default=0, help="0 means run until Ctrl+C")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.interval < 1:
        parser.error("--interval must be at least 1 second")
    if args.cycles < 0:
        parser.error("--cycles must be zero or positive")

    controller = TradingController()
    runner = PersistentPaperTradingRunner(
        controller,
        args.symbols,
        initial_balance=args.balance,
        max_positions=args.max_positions,
        min_confidence=args.min_confidence,
        portfolio_path=args.portfolio,
    )

    if args.reset:
        runner.reset()
        print("Paper portfolio reset to initial balance.")

    print("=" * 68)
    print("AI TRADING AGENT PRO — CONTINUOUS PAPER TRADING")
    print("Public market data only — NO ORDER EXECUTION")
    print("Press Ctrl+C to stop safely.")
    print("=" * 68)
    print(f"Timeframe: {args.timeframe}")
    print(f"Symbols:   {', '.join(args.symbols)}")
    print(f"Interval:  {args.interval}s")
    print(f"Portfolio: {args.portfolio}")

    cycle = 0
    try:
        while args.cycles == 0 or cycle < args.cycles:
            cycle += 1
            try:
                result = runner.step(timeframe=args.timeframe)
                print_cycle(result, cycle)
            except Exception as exc:
                print(f"\nCycle #{cycle} failed: {type(exc).__name__}: {exc}")
                print("Existing persistent state was not intentionally reset.")

            if args.cycles != 0 and cycle >= args.cycles:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped by user. Persistent portfolio remains saved.")

    print("\nCONTINUOUS PAPER TRADING STOPPED")
    print("No real orders were submitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
