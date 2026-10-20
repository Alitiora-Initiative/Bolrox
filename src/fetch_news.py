"""News headline fetcher (RSS only, no full article text)."""
import logging
from typing import List, Dict
from cache import get_cached, set_cached

logger = logging.getLogger("bolorox.fetch_news")

def get_headlines(symbol: str = "EURUSD", limit: int = 10) -> List[Dict]:
    """Return recent headlines. Placeholder until free RSS feeds are wired."""
    logger.info(f"News fetch for {symbol} (placeholder)")
    return []
