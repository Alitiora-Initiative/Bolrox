"""Rule-based setup construction. This module never sends orders."""
import math
from typing import Dict, List, Optional


def build_trade(
    symbol: str,
    direction: str,
    entry: float,
    sl: float,
    tps: List[float],
    atr: Optional[float] = None,
    equity: Optional[float] = None,
    risk_pct: float = 0.5,
) -> Optional[Dict]:
    """Return a validated technical setup, or None when levels are inconsistent.

    No lot size is returned: the project has no broker contract or account-currency
    metadata, so a lot estimate would be misleading for many FX crosses and metals.
    """
    direction = str(direction).upper()
    if direction not in {"LONG", "SHORT"} or not isinstance(tps, (list, tuple)) or len(tps) != 3:
        return None
    try:
        entry, sl, risk_pct = float(entry), float(sl), float(risk_pct)
        tps = [float(value) for value in tps]
        equity = float(equity) if equity is not None else None
        atr = float(atr) if atr is not None else None
    except (TypeError, ValueError):
        return None
    values = [entry, sl, risk_pct, *tps] + ([equity] if equity is not None else [])
    if not all(math.isfinite(value) for value in values):
        return None
    if (entry <= 0 or sl <= 0 or any(target <= 0 for target in tps)
            or (equity is not None and equity <= 0) or not 0 < risk_pct <= 100):
        return None

    if direction == "LONG":
        valid = sl < entry < tps[0] < tps[1] < tps[2]
        risk_distance = entry - sl
    else:
        valid = sl > entry > tps[0] > tps[1] > tps[2]
        risk_distance = sl - entry
    if not valid or risk_distance <= 0:
        return None

    rewards = [abs(target - entry) / risk_distance for target in tps]
    if rewards[0] < 1.5:
        return None
    if atr is not None and (not math.isfinite(atr) or atr <= 0):
        return None

    setup = {
        "symbol": symbol,
        "direction": direction,
        "entry": entry,
        "stop_loss": sl,
        "take_profits": tps,
        "rr": [round(value, 2) for value in rewards],
        "risk_pct": float(risk_pct),
        "invalidation": "The setup is invalid if price closes beyond the stop-loss level.",
        "sizing_note": "Lot size not estimated; broker contract and account-currency data are required.",
    }
    if equity is not None:
        setup["risk_amount"] = round(float(equity) * float(risk_pct) / 100.0, 2)
    return setup
