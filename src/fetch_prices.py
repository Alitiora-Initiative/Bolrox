"""Price data fetchers with SQLite caching and fallback chain. Never invent data."""
import time
import logging
from typing import Optional
import pandas as pd
import yfinance as yf
import requests
import io

from cache import get_cached, set_cached

logger = logging.getLogger("bolorox.fetch_prices")

YF_TICKERS = {
    "EURUSD": "EURUSD=X",
    "USDJPY": "USDJPY=X",
    "XAUUSD": "XAUUSD=X",
    "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "USDCHF": "USDCHF=X",
    "XAGUSD": "XAGUSD=X",
    "DXY": "DX-Y.NYB",
    "USOIL": "CL=F",
    "SPX": "^GSPC",
    "VIX": "^VIX",
    "TNX": "^TNX",
}

# Freshness windows (hours) by interval
FRESHNESS = {
    "1m": 0.25,
    "5m": 0.5,
    "15m": 1.0,
    "1h": 2.0,
    "1d": 12.0,
}

def get_ohlc(sym: str, interval: str = "1h", period: str = "180d") -> Optional[pd.DataFrame]:
    """Fetch OHLCV with cache + fallback: Yahoo -> Stooq. Returns DataFrame or None."""
    max_age = FRESHNESS.get(interval, 1.0)

    # Try cache first for each source
    for name in ("yahoo", "stooq"):
        cached = get_cached(name, sym, interval, period, max_age_hours=max_age)
        if cached is not None and len(cached) > 50:
            cached.attrs.update({"source": name, "fetched": "cache", "from_cache": True})
            logger.info(f"Using cached {name} for {sym} {interval}")
            return cached.dropna()

    # Live fetch with fallback
    for name, fn in (("yahoo", _yahoo), ("stooq", _stooq)):
        try:
            df = fn(sym, interval, period)
            if df is not None and len(df) > 50:
                df.attrs.update({
                    "source": name,
                    "fetched": pd.Timestamp.utcnow().isoformat(),
                    "from_cache": False,
                })
                set_cached(name, sym, interval, period, df)
                logger.info(f"{name} live fetch succeeded for {sym} {interval}")
                return df.dropna()
        except Exception as e:
            logger.warning(f"{name} failed for {sym}: {e}")
        time.sleep(1.0)

    logger.error(f"No price source available for {sym}")
    return None

def _yahoo(sym: str, interval: str, period: str) -> Optional[pd.DataFrame]:
    ticker = YF_TICKERS.get(sym, f"{sym}=X")
    df = yf.download(ticker, interval=interval, period=period, auto_adjust=False, progress=False)
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)
    required = ["open", "high", "low", "close"]
    if not all(c in df.columns for c in required):
        return None
    if "volume" not in df.columns:
        df["volume"] = 0
    # Ensure timezone-aware index if possible
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df[["open", "high", "low", "close", "volume"]]

def _stooq(sym: str, interval: str, period: str) -> Optional[pd.DataFrame]:
    i = {"1d": "d", "1h": "h"}.get(interval)
    if not i:
        return None
    url = f"https://stooq.com/q/d/l/?s={sym.lower()}&i={i}"
    r = requests.get(url, timeout=20, headers={"User-Agent": "BOLOROX/1.0"})
    if r.status_code != 200:
        return None
    df = pd.read_csv(io.StringIO(r.text), parse_dates=["Date"], index_col="Date")
    df = df.rename(columns=str.lower)
    if "volume" not in df.columns:
        df["volume"] = 0
    if not all(c in df.columns for c in ["open", "high", "low", "close"]):
        return None
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df[["open", "high", "low", "close", "volume"]]
