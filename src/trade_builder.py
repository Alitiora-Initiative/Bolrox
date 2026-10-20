"""Trade construction rules. Risk before reward."""
from typing import Dict, List, Optional

def build_trade(
    symbol: str,
    direction: str,
    entry: float,
    sl: float,
    tps: List[float],
    atr: float,
    equity: float = 10000.0,
    risk_pct: float = 0.5,
    pip_size: float = 0.0001,
    pip_value_per_lot: float = 10.0,
) -> Optional[Dict]:
    if direction.upper() == "LONG":
        if not (sl < entry < tps[0] < tps[1] < tps[2]):
            return None
        risk_distance = entry - sl
    else:
        if not (sl > entry > tps[0] > tps[1] > tps[2]):
            return None
        risk_distance = sl - entry

    if risk_distance <= 0:
        return None

    rr1 = abs(tps[0] - entry) / risk_distance
    if rr1 < 1.5:
        return None  # reject poor R:R

    # Position size
    risk_amount = equity * (risk_pct / 100.0)
    pips = risk_distance / pip_size
    lots = risk_amount / (pips * pip_value_per_lot) if pips > 0 else 0

    return {
        "symbol": symbol,
        "direction": direction.upper(),
        "entry": entry,
        "stop_loss": sl,
        "take_profits": tps,
        "rr": [round(rr1, 2), round(abs(tps[1]-entry)/risk_distance, 2), round(abs(tps[2]-entry)/risk_distance, 2)],
        "risk_pct": risk_pct,
        "suggested_lots": round(lots, 2),
        "invalidation": f"H1 close beyond SL or tier-one event before TP1",
    }
