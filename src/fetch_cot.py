"""CFTC Legacy futures-and-options positioning from the public Socrata endpoint."""
import logging
from typing import Optional, Dict
import requests
import pandas as pd
try:
    from .cache import get_cached, set_cached
except ImportError:
    from cache import get_cached, set_cached

logger = logging.getLogger("bolorox.fetch_cot")

COT_URL = "https://publicreporting.cftc.gov/resource/jun7-fc8e.json"

# CFTC contract market codes for the corresponding listed futures markets.
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
    Fetch the latest net non-commercial position for a symbol.
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
        if not data or not isinstance(data, list):
            return None
        df = pd.DataFrame(data)
        latest_row = df.iloc[0]
        long_field, short_field = "noncomm_positions_long_all", "noncomm_positions_short_all"
        if long_field not in df.columns or short_field not in df.columns:
            logger.warning("COT response did not contain the expected Legacy net-position fields")
            return None
        long_positions = int(float(latest_row[long_field]))
        short_positions = int(float(latest_row[short_field]))
        latest = {
            "report_date": str(latest_row.get("report_date_as_yyyy_mm_dd", "")),
            "contract_market_code": code,
            "noncommercial_long": long_positions,
            "noncommercial_short": short_positions,
            "net_noncommercial": long_positions - short_positions,
            "open_interest": int(float(latest_row["open_interest_all"])) if latest_row.get("open_interest_all") else None,
            "source": "CFTC Legacy futures-and-options combined report",
        }
        cache_index = pd.to_datetime(latest["report_date"], utc=True)
        set_cached(source, symbol, "weekly", "latest", pd.DataFrame([latest], index=[cache_index]))
        logger.info(f"COT fetched for {symbol}")
        return latest
    except Exception as e:
        logger.warning(f"COT fetch failed for {symbol}: {e}")
        return None
