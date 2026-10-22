"""Basic volatility and trend-regime classification."""
import pandas as pd

try:  # Support both `python main.py` and direct imports used by scripts.
    from .indicators import adx, atr, ema
except ImportError:
    from indicators import adx, atr, ema


def classify_regime(df: pd.DataFrame, adx_threshold: float = 25.0) -> str:
    """Return TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE, or UNKNOWN."""
    if df is None or len(df) < 50:
        return "UNKNOWN"
    strength = adx(df).iloc[-1]
    volatility = atr(df).dropna()
    close = df["close"].dropna()
    if pd.isna(strength) or volatility.empty or close.empty or close.iloc[-1] <= 0:
        return "UNKNOWN"

    atr_ratio = volatility.iloc[-1] / close.iloc[-1]
    recent_baseline = volatility.tail(100).median()
    if pd.notna(recent_baseline) and recent_baseline > 0 and volatility.iloc[-1] > 2.0 * recent_baseline:
        return "VOLATILE"
    if strength < adx_threshold:
        return "RANGING"
    fast, slow = ema(close, 20).iloc[-1], ema(close, 50).iloc[-1]
    if pd.isna(fast) or pd.isna(slow) or atr_ratio <= 0:
        return "UNKNOWN"
    if fast > slow:
        return "TRENDING_UP"
    if fast < slow:
        return "TRENDING_DOWN"
    return "RANGING"
