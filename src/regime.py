"""Regime detection skeleton."""
import pandas as pd

def classify_regime(df: pd.DataFrame, adx_threshold: float = 25.0) -> str:
    """Return TRENDING_UP, TRENDING_DOWN, RANGING, or VOLATILE."""
    if len(df) < 50:
        return "UNKNOWN"
    # Placeholder logic
    return "RANGING"
