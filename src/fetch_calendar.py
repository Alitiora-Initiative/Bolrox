"""Optional calendar adapter for user-configured public JSON feeds."""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("bolorox.fetch_calendar")


def get_upcoming_events(hours_ahead: int = 72) -> Optional[List[Dict]]:
    """Fetch events from BOLOROX_CALENDAR_URL; return None if no feed is configured.

    A feed must return a JSON array of events containing an ISO `datetime` (or
    `date`) and a `title` (or `event`). Unknown feed formats fail closed.
    """
    if hours_ahead < 1:
        raise ValueError("hours_ahead must be at least 1")
    url = os.getenv("BOLOROX_CALENDAR_URL", "").strip()
    if not url:
        logger.info("Calendar feed not configured")
        return None
    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "BOLOROX/1.0"})
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            payload = payload.get("events") or payload.get("results")
        if not isinstance(payload, list):
            raise ValueError("calendar feed must be a JSON array or contain an events array")

        now = datetime.now(timezone.utc)
        end = now + timedelta(hours=hours_ahead)
        events = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            raw_time = item.get("datetime") or item.get("date")
            title = item.get("title") or item.get("event")
            if not raw_time or not title:
                continue
            event_time = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
            if event_time.tzinfo is None:
                logger.warning("Ignoring calendar event with timezone-naive timestamp: %s", title)
                continue
            event_time = event_time.astimezone(timezone.utc)
            if now <= event_time <= end:
                events.append({
                    "datetime": event_time.isoformat(),
                    "title": str(title),
                    "currency": item.get("currency") or item.get("country"),
                    "impact": item.get("impact"),
                })
        return sorted(events, key=lambda event: event["datetime"])
    except Exception as exc:
        logger.warning("Calendar fetch failed: %s", type(exc).__name__)
        return None
