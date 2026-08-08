"""Persistent JSON-backed paper portfolio storage.

Paper-only: this module never connects to or submits orders to an exchange.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class PersistentPaperPortfolio:
    """Persist paper account state between runner invocations."""

    def __init__(self, path: str | Path = "data/paper_portfolio.json", initial_balance: float = 10_000.0) -> None:
        if initial_balance <= 0:
            raise ValueError("initial_balance must be positive")
        self.path = Path(path)
        self.initial_balance = float(initial_balance)
        self.state: Dict[str, Any] = self._load()

    def _default(self) -> Dict[str, Any]:
        return {
            "initial_balance": self.initial_balance,
            "balance": self.initial_balance,
            "positions": {},
            "trades": [],
            "created_at": None,
            "updated_at": None,
        }

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return self._default()
        with self.path.open("r", encoding="utf-8") as fh:
            state = json.load(fh)
        if not isinstance(state, dict):
            raise ValueError("portfolio file must contain a JSON object")
        return state

    def save(self) -> Dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(self.state, fh, indent=2, default=str)
        return self.state

    def reset(self) -> Dict[str, Any]:
        self.state = self._default()
        return self.save()

    def snapshot(self) -> Dict[str, Any]:
        return json.loads(json.dumps(self.state))
