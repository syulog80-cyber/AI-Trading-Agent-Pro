"""Run one paper-trading cycle while preserving the virtual account on disk."""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from trading.controller import TradingController
from trading.persistent_paper_runner import PersistentPaperTradingRunner

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Persistent one-cycle paper trading")
    parser.add_argument("symbols", nargs="*", default=DEFAULT_SYMBOLS)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--balance", type=float, default=10_000.0)
    parser.add_argument("--max-positions", type=int, default=3)
    parser.add_argument("--min-confidence", type=float, default=70.0)
    parser.add_argument("--portfolio", default="data/paper_portfolio.json")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    controller = TradingController()
    runner = PersistentPaperTradingRunner(
        controller, args.symbols, initial_balance=args.balance,
        max_positions=args.max_positions, min_confidence=args.min_confidence,
        portfolio_path=args.portfolio,
    )
    if args.reset:
        runner.reset()
        print("Paper portfolio reset to initial balance.")

    result = runner.step(timeframe=args.timeframe)
    perf = result["performance"]

    print("=" * 68)
    print("AI TRADING AGENT PRO — PERSISTENT PAPER TRADING")
    print("Public market data only — NO ORDER EXECUTION")
    print("=" * 68)
    print(f"Timeframe: {args.timeframe}")
    print(f"Symbols:   {', '.join(args.symbols)}")
    print(f"Portfolio: {args.portfolio}")
    print("\n--- OPPORTUNITIES ---")
    for item in result["opportunities"]:
        print(f"{item['symbol']}: {item['signal']} | confidence={item['confidence']:.1f} | "
              f"grade={item['grade']} | strategy={item['strategy']} | "
              f"opportunity={item['opportunity']:.1f}")
    if not result["opportunities"]:
        print("No scanner-eligible opportunities found.")

    print("\n--- OPENED ---")
    if result["opened"]:
        for p in result["opened"]:
            print(f"{p['symbol']}: {p['direction']} entry={p['entry_price']:.8f} "
                  f"stop={p['stop_loss']:.8f} target={p['take_profit']:.8f} "
                  f"quantity={p['position_size']:.8f}")
    else:
        print("No new virtual positions.")

    print("\n--- CLOSED ---")
    if result["closed"]:
        for t in result["closed"]:
            print(f"{t['symbol']}: {t['reason']} pnl={t['pnl']:.2f}")
    else:
        print("No positions closed.")

    print("\n--- PERSISTENT PAPER ACCOUNT ---")
    print(f"Balance:          ${perf.get('balance', 0):,.2f}")
    print(f"Position value:   ${perf.get('position_value', 0):,.2f}")
    print(f"Realized P&L:     ${perf.get('realized_pnl', 0):,.2f}")
    print(f"Unrealized P&L:   ${perf.get('unrealized_pnl', 0):,.2f}")
    print(f"Equity:           ${perf.get('equity', 0):,.2f}")
    print(f"Open positions:   {perf.get('open_positions', 0)}")
    print(f"Total trades:     {perf.get('total_trades', 0)}")
    print(f"Win rate:         {perf.get('win_rate', 0):.2f}%")
    print(f"Net P&L:          ${perf.get('net_pnl', 0):,.2f}")
    print(f"Profit factor:    {perf.get('profit_factor', 0):.2f}")
    print("\nPERSISTENT PAPER CYCLE COMPLETED")
    print("No real orders were submitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
