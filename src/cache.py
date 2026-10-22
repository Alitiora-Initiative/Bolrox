"""SQLite cache for price and macro data. Idempotent within freshness windows."""
import sqlite3
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger("bolorox.cache")

CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "cache.sqlite"

def _get_conn() -> sqlite3.Connection:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CACHE_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            source TEXT,
            symbol TEXT,
            interval TEXT,
            fetched_utc TEXT,
            last_candle_utc TEXT,
            data_json TEXT
        )
    """)
    conn.commit()
    return conn

def cache_key(source: str, symbol: str, interval: str, period: str) -> str:
    return f"{source}|{symbol}|{interval}|{period}"

def get_cached(source: str, symbol: str, interval: str, period: str, max_age_hours: float = 1.0) -> Optional[pd.DataFrame]:
    """Return cached DataFrame if fresh enough, else None."""
    key = cache_key(source, symbol, interval, period)
    try:
        with _get_conn() as conn:
            row = conn.execute("SELECT fetched_utc, data_json FROM cache WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        fetched = datetime.fromisoformat(row[0])
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - fetched
        if age > timedelta(hours=max_age_hours):
            logger.info(f"Cache stale for {key} (age {age})")
            return None
        df = pd.read_json(row[1], orient="split")
        df.index = pd.to_datetime(df.index)
        logger.info(f"Cache hit for {key}")
        return df
    except Exception as e:
        logger.warning(f"Cache read failed: {e}")
        return None

def set_cached(source: str, symbol: str, interval: str, period: str, df: pd.DataFrame) -> None:
    """Store DataFrame in cache."""
    if df is None or df.empty:
        return
    key = cache_key(source, symbol, interval, period)
    try:
        last_candle = df.index.max().isoformat() if len(df) else None
        data_json = df.to_json(orient="split", date_format="iso")
        with _get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO cache
                   (key, source, symbol, interval, fetched_utc, last_candle_utc, data_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (key, source, symbol, interval, datetime.now(timezone.utc).isoformat(), last_candle, data_json)
            )
        logger.info(f"Cached {key} ({len(df)} rows)")
    except Exception as e:
        logger.warning(f"Cache write failed: {e}")


def cache_stats() -> dict:
    """Return local cache metadata without opening or displaying cached values."""
    if not CACHE_PATH.exists():
        return {"entries": 0, "path": str(CACHE_PATH)}
    try:
        with _get_conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
        return {"entries": int(count), "path": str(CACHE_PATH)}
    except Exception as e:
        logger.warning(f"Cache status failed: {e}")
        return {"entries": None, "path": str(CACHE_PATH), "error": str(e)}
