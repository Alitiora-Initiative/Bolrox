"""Macro data fetchers (yields, real yields) with caching. Free sources only."""
import logging
from typing import Optional, Dict
import pandas as pd
import yfinance as yf
try:
    from .cache import get_cached, set_cached
except ImportError:
    from cache import get_cached, set_cached

logger = logging.getLogger("bolorox.fetch_macro")

# Yahoo tickers as free substitutes when FRED key is absent
YIELD_TICKERS = {
    "US10Y": "^TNX",      # 10-year yield index (quoted as 10x yield)
    "US13W": "^IRX",      # 13-week bill yield index, not a 2-year yield
    "US30Y": "^TYX",      # 30-year yield index (quoted as 10x yield)
    "VIX": "^VIX",
    "SPX": "^GSPC",
}

def get_yield(symbol: str = "US10Y", period: str = "1y") -> Optional[pd.Series]:
    """Fetch yield series. Uses Yahoo as free fallback. Cached 6 hours."""
    source = "yahoo_yield"
    cached = get_cached(source, symbol, "1d", period, max_age_hours=6.0)
    if cached is not None and not cached.empty:
        return cached["close"] if "close" in cached.columns else cached.iloc[:, 0]

    ticker = YIELD_TICKERS.get(symbol, symbol)
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        series = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
        if ticker in {"^TNX", "^IRX", "^TYX"}:
            series = series / 10.0
        series.name = symbol
        # Wrap for cache
        cache_df = pd.DataFrame({"close": series})
        set_cached(source, symbol, "1d", period, cache_df)
        logger.info(f"Fetched {symbol} yield via Yahoo")
        return series
    except Exception as e:
        logger.warning(f"Yield fetch failed for {symbol}: {e}")
        return None

def get_macro_snapshot() -> Dict[str, Dict]:
    """Latest Yahoo Finance macro proxies with their observation timestamp."""
    snap = {}
    for name in ("US10Y", "VIX", "SPX"):
        s = get_yield(name, "5d")
        if s is not None and len(s):
            snap[name] = {
                "value": float(s.iloc[-1]),
                "as_of": pd.Timestamp(s.index[-1]).isoformat(),
                "source": "Yahoo Finance",
            }
    return snap
