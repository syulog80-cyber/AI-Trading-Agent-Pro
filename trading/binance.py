"""Public Binance market-data connector.

This module intentionally uses public market-data endpoints only. Order
execution and API-key management are kept outside this connector for now.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List

import pandas as pd


class BinanceConnector:
    """Small dependency-light connector for Binance Spot public endpoints."""

    BASE_URL = "https://api.binance.com"

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = int(timeout)

    def _get(self, path: str, params: Dict[str, Any] | None = None) -> Any:
        query = urllib.parse.urlencode(params or {})
        url = f"{self.BASE_URL}{path}"
        if query:
            url = f"{url}?{query}"

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "AI-Trading-Agent-Pro/1.0"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Binance HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Unable to reach Binance: {exc.reason}") from exc

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        symbol = str(symbol).strip().upper().replace("/", "")
        if not symbol:
            raise ValueError("symbol cannot be empty")
        return symbol

    def get_price(self, symbol: str) -> float:
        data = self._get("/api/v3/ticker/price", {"symbol": self._normalize_symbol(symbol)})
        return float(data["price"])

    def get_candles(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 500,
    ) -> pd.DataFrame:
        if not 1 <= int(limit) <= 1000:
            raise ValueError("limit must be between 1 and 1000")

        data = self._get(
            "/api/v3/klines",
            {
                "symbol": self._normalize_symbol(symbol),
                "interval": timeframe,
                "limit": int(limit),
            },
        )

        columns = [
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore",
        ]
        df = pd.DataFrame(data, columns=columns)

        numeric_columns = [
            "open", "high", "low", "close", "volume", "quote_volume",
            "taker_buy_base", "taker_buy_quote",
        ]
        for column in numeric_columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        df = df.set_index("timestamp")
        df.index.name = "timestamp"

        return df[numeric_columns + ["trades", "open_time", "close_time"]]

    def get_symbols(self) -> List[str]:
        data = self._get("/api/v3/exchangeInfo")
        return [
            item["symbol"]
            for item in data.get("symbols", [])
            if item.get("status") == "TRADING"
            and item.get("quoteAsset") in {"USDT", "USDC"}
        ]
