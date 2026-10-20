"""Confluence scoring per Section 8 of the specification."""
from typing import Dict

WEIGHTS = {
    "htf_bias": 25,
    "location": 20,
    "momentum": 15,
    "intermarket_macro": 15,
    "event_session": 10,
    "positioning_sentiment": 5,
    "stat_edge": 10,
}

def score_direction(modules: Dict[str, int], penalties: int = 0) -> int:
    """
    modules: dict of block_name -> strength (0-3, signed for direction)
    Returns 0-100 score.
    """
    score = 0
    for block, weight in WEIGHTS.items():
        strength = modules.get(block, 0)
        # Map strength 0-3 to 0-weight
        score += max(0, min(weight, (strength / 3.0) * weight))
    score = max(0, min(100, score - penalties))
    return int(score)

def grade_from_score(score: int, thresholds: dict) -> str:
    if score >= thresholds.get("a_grade", 75):
        return "A"
    if score >= thresholds.get("b_grade", 65):
        return "B"
    if score >= thresholds.get("watchlist", 55):
        return "WATCH"
    return "NO_TRADE"
