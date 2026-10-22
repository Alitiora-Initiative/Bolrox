"""Factual Markdown report assembly."""
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


DISCLAIMER = (
    "Educational market analysis only; not financial advice or a recommendation to trade. "
    "A technical setup is not a calibrated probability or a guarantee of results. "
    "Markets involve risk of loss. Verify quotes, spread, contract size, and event risk with your broker."
)


def _fmt(value, digits=5):
    if value is None:
        return "unavailable"
    try:
        return f"{float(value):,.{digits}f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def write_report(symbol_data: dict, signals: list, out_dir: str,
                 events=None, macro=None, cot=None, news=None,
                 timezone_name: str = "UTC") -> str:
    now = datetime.now(timezone.utc)
    try:
        local = now.astimezone(ZoneInfo(timezone_name))
    except Exception:
        local = now
        timezone_name = "UTC"
    lines = [
        f"# BOLOROX Market Report — {local.strftime('%Y-%m-%d %H:%M %Z')} ({timezone_name})",
        f"Generated at {now.strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
        "This report records data and rule-based technical setups available during this run. "
        "It does not estimate a win probability or place trades.",
        "",
    ]

    if macro:
        lines.extend([
            "## Macro snapshot", "",
            "Yahoo Finance proxies; treasury yield indices are scaled to percentage points.",
            "",
        ])
        for name, value in macro.items():
            if isinstance(value, dict):
                observation = f" (as of {value.get('as_of', 'time unavailable')}; {value.get('source', 'source unavailable')})"
                lines.append(f"- **{name}:** {_fmt(value.get('value'), 3)}{observation}")
            else:
                lines.append(f"- **{name}:** {_fmt(value, 3)}")
        lines.append("")
    else:
        lines.extend(["## Macro snapshot", "", "Macro series were unavailable for this run.", ""])

    lines.extend(["## Instrument snapshots", ""])
    for symbol, data in symbol_data.items():
        lines.append(f"### {symbol}")
        lines.append(f"- Latest closed H1 price: **{_fmt(data.get('price'))}**")
        lines.append(f"- H1 data source: **{data.get('source') or 'unavailable'}**")
        lines.append(f"- Last candle: **{data.get('last_candle') or 'unavailable'}**")
        lines.append(f"- Data age: **{_fmt(data.get('age_hours'), 2)} hours**; stale: **{data.get('stale', 'unknown')}**")
        lines.append(f"- H1 / D1 bias: **{data.get('h1_bias', 'unknown')} / {data.get('d1_bias', 'unknown')}**")
        lines.append(f"- Regime: **{data.get('regime', 'unknown')}**; ADX: **{_fmt(data.get('adx'), 2)}**")
        lines.append(f"- ATR(14): **{_fmt(data.get('atr'))}**; RSI(14): **{_fmt(data.get('rsi'), 2)}**")
        if data.get("reason"):
            lines.append(f"- Data note: {data['reason']}")
        if data.get("chart"):
            lines.append(f"- Interactive TradingView chart: [open chart]({data['chart']})")
        lines.append("")

    lines.extend(["## Technical setups", ""])
    if not signals:
        lines.append("No setup passed the configured technical rules with the available data.")
    else:
        lines.extend([
            "These are rule-based technical candidates. They are not calibrated probabilities, "
            "and event risk and broker execution conditions must be checked separately.",
            "",
            "| Symbol | Direction | Entry | Stop | TP1 | TP2 | TP3 | R:R | Risk % |",
            "|---|---|---:|---:|---:|---:|---:|---|---:|",
        ])
        for setup in signals:
            targets = setup["take_profits"]
            rr = "/".join(str(value) for value in setup["rr"])
            lines.append(
                f"| {setup['symbol']} | {setup['direction']} | {_fmt(setup['entry'])} | "
                f"{_fmt(setup['stop_loss'])} | {_fmt(targets[0])} | {_fmt(targets[1])} | "
                f"{_fmt(targets[2])} | {rr} | {_fmt(setup['risk_pct'], 2)}% |"
            )
        lines.append("")

    lines.extend(["## Events and headlines", ""])
    if events is None:
        lines.append("Economic calendar data is not configured or was unavailable. No event-risk clearance is implied.")
    elif not events:
        lines.append("The configured calendar returned no events in the requested window.")
    else:
        for event in events:
            when = event.get("datetime") or event.get("date") or "time unavailable"
            title = event.get("title") or event.get("event") or "event name unavailable"
            currency = event.get("currency") or event.get("country") or ""
            impact = event.get("impact") or ""
            lines.append(f"- {when} — {currency} {title} ({impact})".strip())
    if news is None:
        lines.append("\nNews RSS feeds are not configured or were unavailable.")
    elif not news:
        lines.append("\nNo headlines were returned by the configured feeds.")
    else:
        for item in news:
            title = item.get("title", "Headline")
            link = item.get("link")
            published = item.get("published", "time unavailable")
            lines.append(f"\n- [{title}]({link}) — {published}" if link else f"\n- {title} — {published}")
    if cot is None:
        lines.append("\nCOT positioning was unavailable or does not apply to the selected instrument.")
    else:
        lines.append(f"\nCFTC positioning snapshot: `{cot}`")

    lines.extend(["", "## Data and risk notes", ""])
    lines.append("The analysis feed and TradingView chart can use different providers, timestamps, and market venues. Compare quotes before acting.")
    lines.append("Cash risk and position size are not estimated because account equity, broker contract specifications, and account currency are not configured.")
    lines.extend(["", "## Disclaimer", "", DISCLAIMER, ""])

    path = Path(out_dir) / "report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
