from pathlib import Path


def test_paper_trade_once_script_exists():
    path = Path("scripts/paper_trade_once.py")
    assert path.exists()
    assert "NO ORDER EXECUTION" in path.read_text(encoding="utf-8")
