"""Run one read-only paper-trading cycle against public market data."""

from __future__ import annotations

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from trading.controller import TradingController
from trading.paper_runner import PaperTradingRunner


DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]


def main() -> int:
    parser = argparse.ArgumentParser(description="One-cycle paper trading test")
    parser.add_argument("symbols", nargs="*", default=DEFAULT_SYMBOLS)
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--balance", type=float, default=10_000.0)
    parser.add_argument("--max-positions", type=int, default=3)
    parser.add_argument("--min-confidence", type=float, default=70.0)
    args = parser.parse_args()

    print("=" * 68)
    print("AI TRADING AGENT PRO — ONE-CYCLE PAPER TRADING")
    print("Public market data only — NO ORDER EXECUTION")
    print("=" * 68)
    print(f"Timeframe: {args.timeframe}")
    print(f"Symbols:   {', '.join(args.symbols)}")
    print(f"Balance:   ${args.balance:,.2f}")

    controller = TradingController()
    runner = PaperTradingRunner(
        controller,
        args.symbols,
        initial_balance=args.balance,
        max_positions=args.max_positions,
        min_confidence=args.min_confidence,
    )

    result = runner.step(timeframe=args.timeframe)

    print("\n--- OPPORTUNITIES ---")
    if not result["opportunities"]:
        print("No scanner-eligible opportunities found.")
    else:
        for item in result["opportunities"]:
            print(
                f"{item['symbol']}: {item['signal']} | "
                f"confidence={item['confidence']:.1f} | "
                f"grade={item['grade']} | "
                f"strategy={item['strategy']} | "
                f"opportunity={item['opportunity']:.1f}"
            )

    print("\n--- OPENED VIRTUAL POSITIONS ---")
    if not result["opened"]:
        print("No virtual positions opened.")
    else:
        for position in result["opened"]:
            print(
                f"{position['symbol']}: {position['direction']} | "
                f"entry={position['entry_price']:.8f} | "
                f"stop={position['stop_loss']:.8f} | "
                f"target={position['take_profit']:.8f} | "
                f"quantity={position['position_size']:.8f}"
            )

    performance = result["performance"]
    print("\n--- PAPER ACCOUNT ---")
    print(f"Balance:        ${performance.get('balance', args.balance):,.2f}")
    print(f"Open positions: {performance.get('open_positions', 0)}")
    print(f"Total trades:   {performance.get('total_trades', 0)}")
    print(f"Win rate:       {performance.get('win_rate', 0):.2f}%")
    print(f"Net P&L:        ${performance.get('net_pnl', 0):,.2f}")
    print(f"Profit factor:  {performance.get('profit_factor', 0):.2f}")

    print("\nPAPER TRADING CYCLE COMPLETED")
    print("No real orders were submitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
