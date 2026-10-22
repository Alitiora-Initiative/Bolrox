"""Optional RSS headlines from explicitly configured public feed URLs."""
import logging
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger("bolorox.fetch_news")


def get_headlines(limit: int = 10) -> Optional[List[Dict]]:
    """Read configured RSS/Atom feeds; return None when feeds are not configured."""
    if limit < 1:
        raise ValueError("limit must be at least 1")
    feeds = [url.strip() for url in os.getenv("BOLOROX_NEWS_FEEDS", "").split(",") if url.strip()]
    if not feeds:
        logger.info("News RSS feeds not configured")
        return None

    headlines = []
    successful_feeds = 0
    for url in feeds:
        try:
            response = requests.get(
                url, timeout=15,
                headers={"User-Agent": "BOLOROX/1.0", "Accept": "application/rss+xml, application/atom+xml, application/xml"},
            )
            response.raise_for_status()
            root = ET.fromstring(response.content)
            successful_feeds += 1
            for item in root.findall(".//item") + root.findall(".//{*}entry"):
                title = item.findtext("title") or item.findtext("{*}title")
                link = item.findtext("link") or item.findtext("{*}link")
                if not link:
                    link_node = item.find("{*}link")
                    if link_node is not None:
                        link = link_node.attrib.get("href")
                published = (
                    item.findtext("pubDate") or item.findtext("{*}published")
                    or item.findtext("{*}updated") or "time unavailable"
                )
                if title:
                    headlines.append({"title": title.strip(), "link": link, "published": published.strip(), "feed": url})
        except Exception as exc:
            logger.warning("RSS feed failed (%s): %s", urlparse(url).hostname or "configured feed", type(exc).__name__)
    if successful_feeds == 0:
        return None
    return headlines[:limit]
