"""Price data fetchers with SQLite caching and fallback chain. Never invent data."""
import logging
from typing import Optional
import pandas as pd
import yfinance as yf
import requests
import io

try:
    from .cache import get_cached, set_cached
except ImportError:  # Direct module imports are used by the repository scripts.
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

REQUIRED_COLUMNS = ["open", "high", "low", "close", "volume"]


def _clean_ohlc(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    if df is None or df.empty:
        return None
    cleaned = df.copy()
    cleaned.columns = [str(column).lower() for column in cleaned.columns]
    if isinstance(df.columns, pd.MultiIndex):
        cleaned.columns = [str(column).lower() for column in df.columns.get_level_values(0)]
    if not all(column in cleaned.columns for column in ("open", "high", "low", "close")):
        return None
    if "volume" not in cleaned.columns:
        cleaned["volume"] = 0
    cleaned = cleaned[REQUIRED_COLUMNS].apply(pd.to_numeric, errors="coerce")
    cleaned = cleaned.dropna(subset=["open", "high", "low", "close"])
    cleaned = cleaned[~cleaned.index.duplicated(keep="last")].sort_index()
    if cleaned.index.tz is None:
        cleaned.index = cleaned.index.tz_localize("UTC")
    else:
        cleaned.index = cleaned.index.tz_convert("UTC")
    valid = (cleaned[["open", "high", "low", "close"]] > 0).all(axis=1) & (
        cleaned["high"] >= cleaned[["open", "low", "close"]].max(axis=1)
    ) & (
        cleaned["low"] <= cleaned[["open", "high", "close"]].min(axis=1)
    )
    cleaned = cleaned.loc[valid]
    return cleaned if not cleaned.empty else None

def get_ohlc(sym: str, interval: str = "1h", period: str = "180d") -> Optional[pd.DataFrame]:
    """Fetch OHLCV with cache + fallback: Yahoo -> Stooq. Returns DataFrame or None."""
    max_age = FRESHNESS.get(interval, 1.0)

    if interval not in FRESHNESS:
        logger.warning("Unsupported interval %s; supported intervals are %s", interval, sorted(FRESHNESS))
        return None

    # Try cache first for each source.
    for name in ("yahoo", "stooq"):
        cached = get_cached(name, sym, interval, period, max_age_hours=max_age)
        if cached is not None and len(cached) > 50:
            cached = _clean_ohlc(cached)
            if cached is None:
                continue
            cached.attrs.update({"source": name, "fetched": "cache", "from_cache": True})
            logger.info(f"Using cached {name} for {sym} {interval}")
            return cached

    # Live fetch with fallback
    for name, fn in (("yahoo", _yahoo), ("stooq", _stooq)):
        try:
            df = fn(sym, interval, period)
            df = _clean_ohlc(df)
            if df is not None and len(df) > 50:
                df.attrs.update({
                    "source": name,
                    "fetched": pd.Timestamp.utcnow().isoformat(),
                    "from_cache": False,
                })
                set_cached(name, sym, interval, period, df)
                logger.info(f"{name} live fetch succeeded for {sym} {interval}")
                return df
        except Exception as e:
            logger.warning(f"{name} failed for {sym}: {e}")
        # Do not delay after the last source failed.

    logger.error(f"No price source available for {sym}")
    return None

def _yahoo(sym: str, interval: str, period: str) -> Optional[pd.DataFrame]:
    ticker = YF_TICKERS.get(sym, f"{sym}=X")
    df = yf.download(ticker, interval=interval, period=period, auto_adjust=False, progress=False)
    return _clean_ohlc(df)

def _stooq(sym: str, interval: str, period: str) -> Optional[pd.DataFrame]:
    i = {"1d": "d", "1h": "h"}.get(interval)
    if not i:
        return None
    url = f"https://stooq.com/q/d/l/?s={sym.lower()}&i={i}"
    r = requests.get(url, timeout=20, headers={"User-Agent": "BOLOROX/1.0"})
    if r.status_code != 200:
        return None
    df = pd.read_csv(io.StringIO(r.text), parse_dates=["Date"], index_col="Date")
    return _clean_ohlc(df)
