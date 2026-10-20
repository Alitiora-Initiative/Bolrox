# BOLOROX

**Autonomous Quantitative and Discretionary-Style Forex Analyst**

BOLOROX is a free, open-source pipeline that analyzes currency pairs and gold (XAUUSD), runs technical, intermarket, macro, positioning and sentiment analyses, and produces:

1. A ~1,000-word Markdown report  
2. Concrete trade signals with entry, SL, TP levels, probability, R:R, and invalidation — or a clear **no-trade** decision

It thinks like a **risk manager first** and a trader second.

> **Fork note:** This is a maintained fork of [Alitiora-Initiative/Bolrox](https://github.com/Alitiora-Initiative/Bolrox) with import fixes, CLI improvements, and a multipage marketing website under `website/`.

## Website

A modern dark multipage site lives in `website/`:

- Home · Features · How it Works · Docs  
- Responsive, gradient accents, mobile nav

To deploy to Vercel: set **Root Directory** to `website` and deploy the `main` branch (or connect this repo in the Vercel dashboard).

## Default Instrument Universe

- XAUUSD (gold)
- EURUSD
- USDJPY

Extended (on request): GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF, EURJPY, GBPJPY, EURGBP, XAGUSD, USOIL, DXY proxy.

## Non-Negotiable Rules

- Never fabricate data.
- Free only — no paid APIs required.
- Timestamp everything; flag stale data.
- Compute indicators in code.
- Risk before reward (min 1.5 R:R to TP1).
- No-trade is valid.
- Probabilities conservative (never >75% for a single trade).
- Not financial advice.

## Project Layout

```
Bolrox/
├── config.yaml
├── sources.yaml
├── main.py
├── requirements.txt
├── website/           # multipage static site
│   ├── index.html
│   ├── features.html
│   ├── how-it-works.html
│   ├── docs.html
│   ├── css/
│   └── js/
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
│   ├── charts.py
│   ├── report.py
│   └── cache.py
├── tests/
└── out/               # generated reports (gitignored)
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Optional: .env with FRED_API_KEY=your_free_key
python main.py STATUS
python main.py RUN EURUSD
python main.py RUN ALL
```

## Commands

| Command | Description |
|---------|-------------|
| `STATUS` | Config and readiness |
| `RUN <SYMBOL>` | Full pipeline for one symbol |
| `RUN ALL` | Default symbols |

## Fixes in this fork

- Relative imports for `src.cache` (was broken `from cache import`)
- Missing `pandas` import in calendar fetcher
- Argparse correctly handles `RUN ALL`
- Tests pass with correct `atr` argument and package path
- Multipage website + Vercel-ready `website/` folder

## Data Sources (all free)

Yahoo Finance (yfinance), Stooq CSV, CFTC COT public endpoint, optional FRED, public RSS placeholders.

## Disclaimer

Educational analysis software, not financial advice. Past performance is not indicative of future results. Use a demo account first. Markets involve risk of loss.

---

Built for disciplined, evidence-based analysis. Accuracy beats excitement. When in doubt, stay flat.
