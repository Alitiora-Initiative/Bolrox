"""Technical indicators computed from the supplied OHLC series."""
import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    if period < 1:
        raise ValueError("period must be at least 1")
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def _true_range(df: pd.DataFrame) -> pd.Series:
    required = {"high", "low", "close"}
    if not required.issubset(df.columns):
        raise ValueError(f"OHLC data must include {sorted(required)}")
    previous_close = df["close"].shift(1)
    return pd.concat([
        df["high"] - df["low"],
        (df["high"] - previous_close).abs(),
        (df["low"] - previous_close).abs(),
    ], axis=1).max(axis=1)


def _wilder(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    if period < 1:
        raise ValueError("period must be at least 1")
    return _wilder(_true_range(df), period)


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    if period < 1:
        raise ValueError("period must be at least 1")
    delta = series.diff()
    avg_gain = _wilder(delta.clip(lower=0), period)
    avg_loss = _wilder(-delta.clip(upper=0), period)
    relative_strength = avg_gain / avg_loss.replace(0, np.nan)
    result = 100 - (100 / (1 + relative_strength))
    result = result.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    result = result.mask((avg_loss == 0) & (avg_gain == 0), 50.0)
    return result


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    if min(fast, slow, signal) < 1 or fast >= slow:
        raise ValueError("MACD periods must be positive and fast must be less than slow")
    line = ema(series, fast) - ema(series, slow)
    signal_line = line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return line, signal_line, line - signal_line


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder's Average Directional Index (ADX)."""
    if period < 1:
        raise ValueError("period must be at least 1")
    high, low = df["high"], df["low"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    smoothed_tr = _wilder(_true_range(df), period)
    plus_di = 100 * _wilder(plus_dm, period) / smoothed_tr.replace(0, np.nan)
    minus_di = 100 * _wilder(minus_dm, period) / smoothed_tr.replace(0, np.nan)
    denominator = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / denominator
    return _wilder(dx, period)


def bollinger(series: pd.Series, period: int = 20, std: float = 2.0):
    if period < 1 or std <= 0:
        raise ValueError("period and standard deviation must be positive")
    mid = series.rolling(period, min_periods=period).mean()
    sd = series.rolling(period, min_periods=period).std()
    upper, lower = mid + std * sd, mid - std * sd
    bandwidth = (upper - lower) / mid.replace(0, np.nan)
    return upper, mid, lower, bandwidth
