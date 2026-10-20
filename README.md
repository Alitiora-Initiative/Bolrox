# BOLOROX

**Autonomous Quantitative and Discretionary-Style Forex Analyst**

BOLOROX is a free, open-source pipeline that analyzes currency pairs and gold (XAUUSD), runs a wide battery of technical, intermarket, macro, positioning and sentiment analyses, and produces:

1. A ~1,000-word Markdown report
2. Concrete trade signals with entry, stop loss (SL), take profit (TP) levels, stated probability, risk-to-reward, and invalidation conditions

It thinks like a **risk manager first** and a trader second. The edge is discipline: only recommend a trade when independent evidence lines up. No-trade is a valid and often correct output.

## Default Instrument Universe

- XAUUSD (gold)
- EURUSD
- USDJPY

Extended universe (on request): GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF, EURJPY, GBPJPY, EURGBP, XAGUSD, USOIL, DXY proxy.

## Non-Negotiable Rules

- Never fabricate data. Every price, indicator, calendar event, COT figure must come from a tool call in the current run.
- Free only. No paid APIs or credit cards required.
- Timestamp everything. Flag stale data.
- Compute indicators in code, never guess.
- Risk before reward. Minimum 1.5 R:R to TP1. Positive expectancy under stated probabilities.
- No-trade is valid when confluence is low, events are imminent, or data quality is poor.
- Probabilities are calibrated and conservative (never >75% for a single trade).
- Not financial advice.

## Project Layout

```
bolorox/
├── config.yaml          # symbols, timeframes, risk %, thresholds, timezone
├── sources.yaml         # source registry and health
├── .env                 # optional FRED_API_KEY only
├── data/
│   ├── cache.sqlite
│   └── journal.sqlite
├── src/
│   ├── fetch_prices.py
│   ├── fetch_macro.py
│   ├── fetch_calendar.py
│   ├── fetch_cot.py
│   ├── fetch_news.py
│   ├── indicators.py
│   ├── structure.py
│   ├── regime.py
│   ├── intermarket.py
│   ├── confluence.py
│   ├── trade_builder.py
│   ├── backtest.py
│   ├── charts.py
│   └── report.py
├── out/YYYY-MM-DD_SYMBOL/
│   ├── report.md
│   ├── signals.json
│   ├── chart.html
│   ├── chart.png
│   ├── pine.txt
│   └── run.log
├── tests/
└── main.py
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
# Optional: create .env with FRED_API_KEY=your_free_key
python main.py RUN ALL
```

## Commands

- `RUN ALL` — full pipeline for default symbols
- `RUN <SYMBOL>` — analyze one symbol
- `QUICK <SYMBOL>` — short summary
- `LEVELS <SYMBOL>` — key levels only
- `NEWS` — next 72h events
- `STATUS` — source health and journal stats

## Data Sources (all free)

- Yahoo Finance (yfinance)
- Stooq CSV
- Dukascopy (optional)
- FRED (optional free key)
- CFTC COT public endpoint
- Free economic calendar feeds
- Public RSS for news/headlines

## Disclaimer

This is educational analysis software, not financial advice. Past performance is not indicative of future results. Always use a demo account first. Markets involve risk of loss.

---

Built for disciplined, evidence-based analysis. Accuracy beats excitement. When in doubt, stay flat.
