"""Economic calendar fetcher. Free sources only; degrades gracefully."""
import logging
from typing import List, Dict
from datetime import datetime, timezone, timedelta
import requests
import pandas as pd
from .cache import get_cached, set_cached

logger = logging.getLogger("bolorox.fetch_calendar")

def get_upcoming_events(hours_ahead: int = 72) -> List[Dict]:
    """
    Return list of events in next N hours.
    Uses a simple public endpoint if available; otherwise returns empty with warning.
    Cached 1 hour.
    """
    source = "calendar_free"
    key = "events"
    cached = get_cached(source, key, "72h", "next", max_age_hours=1.0)
    if cached is not None:
        try:
            # Stored as records
            return cached.to_dict(orient="records")
        except Exception:
            pass

    # Placeholder: many free calendars are rate-limited or require scraping.
    # Return structured empty list and log so the pipeline can continue.
    logger.warning("No free calendar endpoint configured; returning empty event list")
    events = []
    # Cache the empty result so we don't spam
    if events:
        df = pd.DataFrame(events)
        set_cached(source, key, "72h", "next", df)
    return events
