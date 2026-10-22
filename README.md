# BOLOROX

BOLOROX is a command-line forex and metals market-analysis tool. It fetches OHLC data, computes indicators locally, writes a source-labelled report, and exports an interactive TradingView chart. It does not connect to a broker, place orders, or connect a crypto wallet.

## What it produces

- A Markdown report with the latest fully closed candle, feed, data age, technical state, and any optional macro, calendar, news, or CFTC context that was actually available.
- A JSON snapshot for each run.
- A responsive `chart.html` using TradingView's official Advanced Real-Time Chart widget. The chart and the Bolorox analysis can use different market providers, so their displayed quotes can differ. Bolorox levels are listed beside the chart; they are not drawn as TradingView lines.
- Rule-based technical candidates when H1 and D1 trend, pullback, RSI, ADX, freshness, and level validation rules all pass. Candidates do not include a win probability.

The tool does not calculate broker lot sizes or cash risk because account equity, contract specifications, and account currency are not configured. It reports the configured risk percentage only. Treat every candidate as educational analysis, verify it with your broker, and account for spreads, slippage, and event risk yourself.

## Default instruments

- `XAUUSD`
- `EURUSD`
- `USDJPY`

The extended list is in `config.yaml`. TradingView widget symbols are explicitly mapped in `src/charts.py`; unsupported instruments fail clearly instead of silently showing the wrong market.

## Install

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Commands

```powershell
python main.py STATUS
python main.py RUN EURUSD
python main.py RUN ALL
python main.py QUICK XAUUSD
python main.py LEVELS USDJPY
python main.py NEWS
```

Reports and charts are written under `out/YYYY-MM-DD_SYMBOL/`. Run commands from any working directory; paths are anchored to the repository.

## Data sources and limits

- Historical analysis candles and macro series: Yahoo Finance via `yfinance`, with Stooq as a daily-data fallback. Free feeds can be delayed, rate-limited, incomplete, or revised; they are not broker execution quotes.
- Interactive chart and visible calendar: TradingView's official embedded widget. It uses TradingView's own market feed and requires an internet connection when the generated HTML is opened.
- Weekly positioning: the public CFTC Socrata feed where a contract mapping exists.
- Programmatic economic calendar: optional public JSON endpoint configured with `BOLOROX_CALENDAR_URL`. The endpoint must return an array of events with ISO `datetime` or `date` and `title` or `event` fields. Without it, reports say event risk is unknown.
- RSS/Atom headlines: optional comma-separated public feed URLs in `BOLOROX_NEWS_FEEDS`. Headlines are displayed as received and are not sentiment-scored.

For example, configure optional feeds in PowerShell for the current session:

```powershell
$env:BOLOROX_CALENDAR_URL = "https://example.org/events.json"
$env:BOLOROX_NEWS_FEEDS = "https://example.org/markets.rss,https://example.net/forex.xml"
```

No feed URL is configured by default. Do not enter wallet keys or broker credentials; this repository has no wallet or order-execution feature.

## Safety and interpretation

- Indicators are computed from downloaded OHLC candles; the newest incomplete candle is excluded.
- Reports flag stale hourly data and do not produce a candidate from stale or insufficient data.
- The technical rules are not a backtest and do not support a win-rate claim. The report deliberately does not invent probabilities.
- No event feed means event risk is unknown, not that the calendar is clear.
- Not financial advice. Markets involve risk of loss.

## GitHub Actions

The weekday workflow runs the configured analysis and stores reports and charts as artifacts. It does not email reports or require mail secrets. A workflow-dispatch run can select one configured symbol, run all defaults, or show status.
