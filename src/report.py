"""Report assembly. Target ~1000 words."""
from datetime import datetime, timezone
import json

DISCLAIMER = (
    "Educational analysis only. Not financial advice. "
    "No guarantee of results. Markets involve risk of loss. "
    "Use a demo account first. Past performance is not indicative of future results."
)

def write_report(symbol_data: dict, signals: list, out_dir: str) -> str:
    now = datetime.now(timezone.utc)
    local = now  # TODO: convert to Africa/Nairobi
    lines = [
        f"# BOLOROX Report — {now.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Executive Summary",
        "Market regime assessment and best opportunity (or no-trade) based on current data.",
        "",
        "## Macro and Event Backdrop",
        "Dollar, yields, risk tone, and upcoming high-impact events.",
        "",
    ]
    for sym, data in symbol_data.items():
        lines.append(f"## {sym} Technical Analysis")
        lines.append(f"Bias, regime, key levels, and volatility notes for {sym}.")
        lines.append("")

    lines.append("## Signals")
    if not signals:
        lines.append("NO TRADE — confluence below threshold or data quality insufficient.")
    else:
        lines.append("| Symbol | Dir | Grade | Entry | SL | TP1 | TP2 | TP3 | R:R | P(TP1) |")
        lines.append("|--------|-----|-------|-------|----|-----|-----|-----|-----|--------|")
        for s in signals:
            lines.append(
                f"| {s['symbol']} | {s['direction']} | {s.get('grade','')} | "
                f"{s['entry']} | {s['stop_loss']} | {s['take_profits'][0]} | "
                f"{s['take_profits'][1]} | {s['take_profits'][2]} | "
                f"{s['rr'][0]}/{s['rr'][1]}/{s['rr'][2]} | {s.get('prob_tp1',0.55)} |"
            )

    lines.append("")
    lines.append("## Disclaimer")
    lines.append(DISCLAIMER)
    report = "\n".join(lines)
    path = f"{out_dir}/report.md"
    with open(path, "w") as f:
        f.write(report)
    return path
