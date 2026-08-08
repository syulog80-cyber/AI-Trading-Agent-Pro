from pathlib import Path


def test_continuous_paper_script_exists():
    path = Path("scripts/persistent_paper_trade.py")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "NO ORDER EXECUTION" in text
    assert "--interval" in text
    assert "--cycles" in text
    assert "--reset" in text
