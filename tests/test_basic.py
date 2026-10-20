"""Basic unit tests for core functions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from indicators import ema, atr, rsi
from structure import find_swings
from trade_builder import build_trade

def test_ema():
    s = pd.Series([1,2,3,4,5])
    e = ema(s, 3)
    assert len(e) == 5

def test_build_trade_valid():
    t = build_trade("EURUSD", "LONG", 1.1000, 1.0950, [1.1100, 1.1200, 1.1300])
    assert t is not None
    assert t["rr"][0] >= 1.5

def test_build_trade_bad_rr():
    t = build_trade("EURUSD", "LONG", 1.1000, 1.0990, [1.1010, 1.1020, 1.1030])
    assert t is None

if __name__ == "__main__":
    test_ema()
    test_build_trade_valid()
    test_build_trade_bad_rr()
    print("All basic tests passed.")
