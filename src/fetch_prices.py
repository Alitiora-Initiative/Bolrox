"""Price data fetchers with fallback chain. Never invent data."""
import time
import logging
from typing import Optional
import pandas as pd
import yfinance as yf
import requests
import io

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

def get_ohlc(sym: str, interval: str = "1h", period: str = "180d") -> Optional[pd.DataFrame]:
    """Fetch OHLCV with fallback: Yahoo -> Stooq. Returns DataFrame or None."""
    for name, fn in (("yahoo", _yahoo), ("stooq", _stooq)):
        try:
            df = fn(sym, interval, period)
            if df is not None and len(df) > 50:
                df.attrs.update({"source": name, "fetched": pd.Timestamp.utcnow().isoformat()})
                logger.info(f"{name} succeeded for {sym} {interval}")
                return df.dropna()
        except Exception as e:
            logger.warning(f"{name} failed for {sym}: {e}")
        time.sleep(1.0)
    logger.error(f"No price source available for {sym}")
    return None

def _yahoo(sym: str, interval: str, period: str) -> Optional[pd.DataFrame]:
    ticker = YF_TICKERS.get(sym, f"{sym}=X")
    df = yf.download(ticker, interval=interval, period=period, auto_adjust=False, progress=False)
    if df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)
    required = ["open", "high", "low", "close"]
    if not all(c in df.columns for c in required):
        return None
    if "volume" not in df.columns:
        df["volume"] = 0
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
    return df[["open", "high", "low", "close", "volume"]] if all(c in df.columns for c in ["open","high","low","close"]) else None
