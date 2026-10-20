"""CFTC Commitments of Traders fetcher (public Socrata endpoint)."""
import logging
from typing import Optional, Dict
import requests
import pandas as pd
from cache import get_cached, set_cached

logger = logging.getLogger("bolorox.fetch_cot")

COT_URL = "https://publicreporting.cftc.gov/resource/jun7-fc8e.json"

# Common contract codes (approximate; verify against latest feed)
CONTRACTS = {
    "EUR": "099741",
    "JPY": "097741",
    "GBP": "096742",
    "AUD": "232741",
    "CAD": "090741",
    "CHF": "092741",
    "GOLD": "088691",
}

def get_cot_net(symbol: str = "EUR") -> Optional[Dict]:
    """
    Fetch latest net non-commercial position for a symbol.
    Cached 24 hours (COT is weekly).
    """
    source = "cftc"
    cached = get_cached(source, symbol, "weekly", "latest", max_age_hours=24.0)
    if cached is not None and not cached.empty:
        row = cached.iloc[-1].to_dict()
        return row

    code = CONTRACTS.get(symbol.upper())
    if not code:
        logger.warning(f"No COT code for {symbol}")
        return None

    try:
        params = {
            "$where": f"cftc_contract_market_code='{code}'",
            "$order": "report_date_as_yyyy_mm_dd DESC",
            "$limit": 5,
        }
        r = requests.get(COT_URL, params=params, timeout=30, headers={"User-Agent": "BOLOROX/1.0"})
        if r.status_code != 200:
            logger.warning(f"COT HTTP {r.status_code}")
            return None
        data = r.json()
        if not data:
            return None
        df = pd.DataFrame(data)
        # Keep useful columns
        keep = [c for c in df.columns if any(x in c.lower() for x in ("report_date", "noncomm", "net", "long", "short"))]
        if keep:
            df = df[keep]
        set_cached(source, symbol, "weekly", "latest", df)
        latest = df.iloc[0].to_dict()
        logger.info(f"COT fetched for {symbol}")
        return latest
    except Exception as e:
        logger.warning(f"COT fetch failed for {symbol}: {e}")
        return None
