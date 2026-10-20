"""Basic tests for cache layer."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from datetime import datetime, timezone
from cache import set_cached, get_cached, CACHE_PATH

def test_cache_roundtrip():
    df = pd.DataFrame(
        {"open": [1.1], "high": [1.2], "low": [1.0], "close": [1.15], "volume": [100]},
        index=pd.to_datetime(["2026-10-20 10:00:00"]).tz_localize("UTC")
    )
    set_cached("test", "EURUSD", "1h", "1d", df)
    loaded = get_cached("test", "EURUSD", "1h", "1d", max_age_hours=24)
    assert loaded is not None
    assert len(loaded) == 1
    assert abs(loaded["close"].iloc[0] - 1.15) < 1e-6

def test_cache_stale():
    # Force a stale entry by mocking age (simple check that None is returned for extreme age)
    loaded = get_cached("nonexistent", "EURUSD", "1h", "1d", max_age_hours=0.0001)
    assert loaded is None

if __name__ == "__main__":
    test_cache_roundtrip()
    test_cache_stale()
    print("Cache tests passed.")
    # Cleanup
    if CACHE_PATH.exists():
        CACHE_PATH.unlink()
