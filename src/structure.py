"""Market structure: swings, S/R zones, supply/demand."""
import pandas as pd
import numpy as np

def find_swings(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Fractal swing highs and lows. N bars each side."""
    highs = df["high"]
    lows = df["low"]
    swing_high = (highs == highs.rolling(2*n+1, center=True).max()) & (highs.shift(n) < highs) & (highs.shift(-n) < highs)
    swing_low = (lows == lows.rolling(2*n+1, center=True).min()) & (lows.shift(n) > lows) & (lows.shift(-n) > lows)
    result = pd.DataFrame(index=df.index)
    result["swing_high"] = swing_high
    result["swing_low"] = swing_low
    result["high_price"] = np.where(swing_high, highs, np.nan)
    result["low_price"] = np.where(swing_low, lows, np.nan)
    return result

def cluster_levels(prices: list, tolerance: float) -> list:
    """Simple clustering of swing prices within tolerance."""
    if not prices:
        return []
    prices = sorted(set(prices))
    clusters = []
    current = [prices[0]]
    for p in prices[1:]:
        if p - current[-1] <= tolerance:
            current.append(p)
        else:
            clusters.append(np.mean(current))
            current = [p]
    clusters.append(np.mean(current))
    return clusters
