"""Transparent confluence scoring for signed module strengths (-3 to +3)."""
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


def score_direction(modules: Dict[str, int], penalties: int = 0, direction: str = "LONG") -> int:
    """Score evidence aligned with LONG or SHORT on a 0-100 scale."""
    sign = {"LONG": 1, "SHORT": -1}.get(str(direction).upper())
    if sign is None:
        raise ValueError("direction must be LONG or SHORT")
    score = 0.0
    for block, weight in WEIGHTS.items():
        strength = max(-3.0, min(3.0, float(modules.get(block, 0))))
        aligned_strength = max(0.0, strength * sign)
        score += (aligned_strength / 3.0) * weight
    return int(max(0.0, min(100.0, score - max(0, int(penalties)))))


def grade_from_score(score: int, thresholds: dict) -> str:
    if score >= thresholds.get("a_grade", 75):
        return "A"
    if score >= thresholds.get("b_grade", 65):
        return "B"
    if score >= thresholds.get("watchlist", 55):
        return "WATCH"
    return "NO_TRADE"
