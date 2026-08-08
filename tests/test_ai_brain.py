import pandas as pd

from ai.ai_brain import AIBrain


def make_df():
    return pd.DataFrame(
        {
            "high": [101, 103, 102, 105, 104, 108, 107, 110],
            "low": [99, 100, 100, 102, 102, 104, 104, 106],
            "close": [100, 102, 101, 104, 103, 107, 106, 109],
            "ATR": [2.0] * 8,
            "RSI": [62.0] * 8,
            "MACD": [2.0] * 8,
            "MACD_SIGNAL": [1.0] * 8,
            "ADX": [30.0] * 8,
            "volume": [1500.0] * 8,
            "VOL_SMA20": [1000.0] * 8,
        }
    )


def test_ai_brain_gates_final_signal(monkeypatch):
    brain = AIBrain()

    monkeypatch.setattr(
        brain.structure_engine,
        "analyze",
        lambda df: {"direction": "Bullish", "trend": "Bullish", "structure_score": 85, "reasons": []},
    )
    monkeypatch.setattr(
        brain.trend_engine,
        "analyze",
        lambda structure: {"trend": "Bullish", "bias": "BULLISH", "trend_score": 85, "reasons": []},
    )
    monkeypatch.setattr(
        brain.momentum_engine,
        "analyze",
        lambda df: {
            "bias": "BULLISH",
            "score": 85,
            "strength": "STRONG",
            "rsi": 62,
            "adx": 30,
            "atr": 2,
            "atr_percent": 2,
            "volume_ratio": 1.5,
            "reasons": [],
        },
    )
    monkeypatch.setattr(
        brain.strategy_engine,
        "analyze",
        lambda structure, trend, momentum: {
            "strategy": "Trend Following",
            "direction": "BUY",
            "score": 85,
            "confidence": 85,
            "reasons": [],
        },
    )
    monkeypatch.setattr(
        brain.risk_engine,
        "analyze",
        lambda entry_price, atr, direction, account_balance: {
            "tradable": True,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": 105,
            "take_profit": 117,
            "risk_reward": 2,
            "risk_level": "LOW",
            "position_size": 10,
            "position_value": 1090,
            "position_percent": 10.9,
            "atr": atr,
            "atr_percent": 2,
        },
    )
    monkeypatch.setattr(
        brain.confidence_engine,
        "analyze",
        lambda **kwargs: {
            "confidence": 88,
            "grade": "A",
            "strength": "STRONG",
            "agreement": 3,
            "agreement_bonus": 15,
            "conflict_penalty": 0,
            "tradable": True,
            "direction": "BUY",
            "hard_conflict": False,
            "reasons": [],
        },
    )
    monkeypatch.setattr(
        brain.grade_engine,
        "analyze",
        lambda **kwargs: {
            "grade": "A",
            "score": 88,
            "quality": "EXCELLENT",
            "tradable": True,
            "reasons": [],
        },
    )

    result = brain.analyze(make_df(), account_balance=10_000)

    assert result["signal"] == "BUY"
    assert result["decision"] == "BUY"
    assert result["tradable"] is True
    assert result["grade"] == "A"
    assert result["strategy"] == "Trend Following"


def test_ai_brain_returns_hold_when_grade_blocks_trade(monkeypatch):
    brain = AIBrain()

    monkeypatch.setattr(brain.structure_engine, "analyze", lambda df: {"direction": "Bullish", "trend": "Bullish", "structure_score": 80, "reasons": []})
    monkeypatch.setattr(brain.trend_engine, "analyze", lambda structure: {"trend": "Bullish", "bias": "BULLISH", "trend_score": 80, "reasons": []})
    monkeypatch.setattr(brain.momentum_engine, "analyze", lambda df: {"bias": "BEARISH", "score": 35, "rsi": 42, "adx": 30, "atr": 2, "atr_percent": 2, "volume_ratio": 1, "reasons": []})
    monkeypatch.setattr(brain.strategy_engine, "analyze", lambda structure, trend, momentum: {"strategy": "Wait", "direction": "HOLD", "score": 30, "confidence": 40, "reasons": []})
    monkeypatch.setattr(brain.risk_engine, "analyze", lambda entry_price, atr, direction, account_balance: {"tradable": False, "direction": "HOLD", "stop_loss": None, "take_profit": None, "risk_reward": 0, "risk_level": "HIGH", "position_size": 0, "position_value": 0, "position_percent": 0, "atr": atr, "atr_percent": 2})
    monkeypatch.setattr(brain.confidence_engine, "analyze", lambda **kwargs: {"confidence": 35, "grade": "D", "strength": "VERY WEAK", "agreement": 0, "agreement_bonus": 0, "conflict_penalty": 5, "tradable": False, "direction": "HOLD", "hard_conflict": False, "reasons": []})
    monkeypatch.setattr(brain.grade_engine, "analyze", lambda **kwargs: {"grade": "D", "score": 35, "quality": "POOR", "tradable": False, "reasons": []})

    result = brain.analyze(make_df())

    assert result["signal"] == "HOLD"
    assert result["decision"] == "HOLD"
    assert result["tradable"] is False
