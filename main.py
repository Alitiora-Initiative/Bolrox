"""BOLOROX command-line market analysis pipeline."""
import argparse
import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from src.cache import cache_stats
from src.charts import generate_chart_html
from src.fetch_calendar import get_upcoming_events
from src.fetch_cot import get_cot_net
from src.fetch_macro import get_macro_snapshot
from src.fetch_news import get_headlines
from src.fetch_prices import get_ohlc
from src.indicators import adx, atr, ema, rsi
from src.regime import classify_regime
from src.report import write_report
from src.trade_builder import build_trade


ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bolorox")


def load_config() -> dict:
    config_path = ROOT / "config.yaml"
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    if not isinstance(config, dict) or not isinstance(config.get("symbols"), dict):
        raise ValueError(f"Invalid configuration in {config_path}")
    return config


def _known_symbols(config: dict) -> set:
    return {str(symbol).upper() for group in config["symbols"].values() for symbol in (group or [])}


def _validate_symbol(symbol: str, config: dict) -> str:
    candidate = str(symbol).strip().upper()
    if candidate not in _known_symbols(config):
        choices = ", ".join(sorted(_known_symbols(config)))
        raise ValueError(f"Unknown symbol {candidate!r}. Configured symbols: {choices}")
    return candidate


def _closed_bars(frame: pd.DataFrame, hours: int, now: pd.Timestamp) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    timestamps = pd.DatetimeIndex(frame.index)
    if timestamps.tz is None:
        timestamps = timestamps.tz_localize("UTC")
    else:
        timestamps = timestamps.tz_convert("UTC")
    result = frame.copy()
    result.index = timestamps
    return result.loc[result.index + pd.Timedelta(hours=hours) <= now].copy()


def _bias(frame: pd.DataFrame, fast_period: int, slow_period: int) -> str:
    if frame is None or len(frame) < slow_period:
        return "UNKNOWN"
    fast = ema(frame["close"], fast_period).iloc[-1]
    slow = ema(frame["close"], slow_period).iloc[-1]
    price = frame["close"].iloc[-1]
    if pd.isna(fast) or pd.isna(slow):
        return "UNKNOWN"
    if price > fast > slow:
        return "BULLISH"
    if price < fast < slow:
        return "BEARISH"
    return "NEUTRAL"


def _build_candidate(symbol: str, hourly: pd.DataFrame, daily: pd.DataFrame,
                     risk_pct: float, rules: dict | None = None) -> tuple[list, dict]:
    """Build a transparent trend/pullback candidate; never assign a probability."""
    rules = rules or {}
    h1_fast, h1_slow = int(rules.get("h1_fast_ema", 50)), int(rules.get("h1_slow_ema", 200))
    d1_fast, d1_slow = int(rules.get("d1_fast_ema", 20)), int(rules.get("d1_slow_ema", 50))
    atr_period = int(rules.get("atr_period", 14))
    rsi_period = int(rules.get("rsi_period", 14))
    adx_period = int(rules.get("adx_period", 14))
    details = {"h1_bias": _bias(hourly, h1_fast, h1_slow), "d1_bias": _bias(daily, d1_fast, d1_slow)}
    if len(hourly) < h1_slow + 1 or len(daily) < d1_slow + 1:
        details["reason"] = "Not enough fully closed H1 and D1 candles for the configured indicators."
        return [], details

    working = hourly.copy()
    working["ema_fast"] = ema(working["close"], h1_fast)
    working["ema_slow"] = ema(working["close"], h1_slow)
    working["atr"] = atr(working, atr_period)
    working["rsi"] = rsi(working["close"], rsi_period)
    working["adx"] = adx(working, adx_period)
    last = working.iloc[-1]
    price, atr_value = float(last["close"]), float(last["atr"])
    rsi_value, adx_value = float(last["rsi"]), float(last["adx"])
    details.update({
        "h1_bias": _bias(working, h1_fast, h1_slow),
        "d1_bias": _bias(daily, d1_fast, d1_slow),
        "atr": atr_value,
        "rsi": rsi_value,
        "adx": adx_value,
        "regime": classify_regime(working),
    })
    if not all(math.isfinite(value) for value in (price, atr_value, rsi_value, adx_value)) or atr_value <= 0:
        details["reason"] = "Indicator data is incomplete or invalid."
        return [], details

    direction = None
    long_rsi = rules.get("rsi_long", [45, 68])
    short_rsi = rules.get("rsi_short", [32, 55])
    if (details["h1_bias"] == "BULLISH" and details["d1_bias"] == "BULLISH"
            and float(long_rsi[0]) <= rsi_value <= float(long_rsi[1])):
        direction = "LONG"
    elif (details["h1_bias"] == "BEARISH" and details["d1_bias"] == "BEARISH"
          and float(short_rsi[0]) <= rsi_value <= float(short_rsi[1])):
        direction = "SHORT"

    pullback_atr = float(rules.get("pullback_atr", 0.75))
    near_h1_mean = abs(price - float(last["ema_fast"])) <= pullback_atr * atr_value
    if direction is None or not near_h1_mean or adx_value < float(rules.get("min_adx", 20)):
        details["reason"] = "Trend alignment, pullback location, RSI, or ADX did not meet the setup rules."
        return [], details

    recent = working.tail(20)
    if direction == "LONG":
        stop = float(recent["low"].min() - float(rules.get("stop_buffer_atr", 0.2)) * atr_value)
        risk = price - stop
        targets = [price + float(multiple) * risk for multiple in rules.get("take_profit_r", [1.5, 2.5, 4.0])]
    else:
        stop = float(recent["high"].max() + float(rules.get("stop_buffer_atr", 0.2)) * atr_value)
        risk = stop - price
        targets = [price - float(multiple) * risk for multiple in rules.get("take_profit_r", [1.5, 2.5, 4.0])]
    if risk <= 0 or risk > float(rules.get("max_stop_atr", 2.5)) * atr_value:
        details["reason"] = "Recent swing structure puts the stop outside the 2.5 ATR setup limit."
        return [], details

    setup = build_trade(symbol, direction, price, stop, targets, atr=atr_value, risk_pct=risk_pct)
    if setup is None:
        details["reason"] = "Calculated levels failed the trade-level validation rules."
        return [], details
    setup.update({
        "status": "TECHNICAL_CANDIDATE",
        "as_of": hourly.index[-1].isoformat(),
        "rule": "H1 and D1 EMA trend alignment, H1 pullback within 0.75 ATR, ADX >= 20, directional RSI band",
        "probability": None,
    })
    details["reason"] = "A technical candidate passed the configured trend/pullback rules."
    return [setup], details


def _safe_call(label, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        logger.warning("%s unavailable: %s", label, exc)
        return None


def run_symbol(symbol: str, out_dir: Path, config: dict | None = None) -> dict:
    config = config or load_config()
    symbol = _validate_symbol(symbol, config)
    out_dir = Path(out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Running %s", symbol)

    now = pd.Timestamp.now(tz="UTC")
    raw_hourly = _safe_call("H1 prices", get_ohlc, symbol, interval="1h", period="60d")
    raw_daily = _safe_call("D1 prices", get_ohlc, symbol, interval="1d", period="2y")
    hourly = _closed_bars(raw_hourly, 1, now)
    daily = _closed_bars(raw_daily, 24, now)

    source = raw_hourly.attrs.get("source") if raw_hourly is not None else None
    latest_time = hourly.index[-1] if not hourly.empty else None
    age_hours = (now - latest_time).total_seconds() / 3600 if latest_time is not None else None
    max_age = float(config.get("freshness", {}).get("max_h1_age_hours", 6))
    stale = age_hours is None or age_hours > max_age
    data = {
        "source": source,
        "price": float(hourly["close"].iloc[-1]) if not hourly.empty else None,
        "last_candle": latest_time.isoformat() if latest_time is not None else None,
        "age_hours": round(age_hours, 2) if age_hours is not None else None,
        "stale": stale,
        "tradingview_interval": "60",
    }

    signals, details = [], {}
    if hourly.empty:
        details["reason"] = "No complete H1 OHLC candles were available from the configured price sources."
    elif daily.empty:
        details["reason"] = "No complete D1 OHLC candles were available from the configured price sources."
    elif stale:
        details["reason"] = f"The latest closed H1 candle is older than the {max_age:g}-hour freshness limit."
        rules = config.get("rules", {})
        details.update({
            "h1_bias": "UNKNOWN",
            "d1_bias": _bias(daily, int(rules.get("d1_fast_ema", 20)), int(rules.get("d1_slow_ema", 50))),
            "regime": "UNKNOWN",
        })
    else:
        risk_pct = float(config.get("risk", {}).get("default_pct", 0.5))
        signals, details = _build_candidate(symbol, hourly, daily, risk_pct, config.get("rules", {}))
    data.update(details)

    # External context is optional and never silently represented as "no risk".
    macro = _safe_call("macro snapshot", get_macro_snapshot) or {}
    events = _safe_call("calendar", get_upcoming_events)
    news = _safe_call("RSS headlines", get_headlines)
    cot_symbol = "EUR" if symbol.startswith("EUR") else "JPY" if symbol.endswith("JPY") or symbol == "USDJPY" else "GOLD" if symbol == "XAUUSD" else None
    cot = _safe_call("COT", get_cot_net, cot_symbol) if cot_symbol else None

    chart_levels = {}
    if signals:
        signal = signals[0]
        chart_levels = {
            "entry": signal["entry"], "stop_loss": signal["stop_loss"],
            "tp1": signal["take_profits"][0], "tp2": signal["take_profits"][1],
            "tp3": signal["take_profits"][2],
        }
    chart_path = generate_chart_html(
        symbol, data, chart_levels, out_dir / "chart.html",
        timezone=config.get("timezone", "Etc/UTC"),
    )
    data["chart"] = Path(chart_path).name
    report_path = write_report(
        {symbol: data}, signals, str(out_dir), events, macro, cot, news,
        timezone_name=config.get("timezone", "UTC"),
    )
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "market_data": data,
        "events": events,
        "headlines": news,
        "setups": signals,
    }
    with (out_dir / "signals.json").open("w", encoding="utf-8") as output_file:
        json.dump(output, output_file, indent=2, allow_nan=False, default=str)

    logger.info("Wrote %s, %s, and %s", report_path, out_dir / "signals.json", chart_path)
    print(f"{symbol}: {data.get('h1_bias', 'UNKNOWN')} H1 bias; {len(signals)} technical candidate(s)")
    print(f"Report: {report_path}")
    print(f"TradingView chart: {chart_path}")
    return output


def _output_dir(symbol: str) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return ROOT / "out" / f"{today}_{symbol}"


def _status(config: dict) -> None:
    stats = cache_stats()
    print("BOLOROX status")
    print(f"Configured default symbols: {', '.join(config['symbols'].get('default', []))}")
    print(f"Local price cache entries: {stats.get('entries', 'unknown')}")
    print(f"Cache location: {stats['path']}")
    print(f"Calendar feed configured: {'yes' if os.getenv('BOLOROX_CALENDAR_URL') else 'no'}")
    print(f"News feeds configured: {'yes' if os.getenv('BOLOROX_NEWS_FEEDS') else 'no'}")
    print("Commands: STATUS | RUN <symbol|ALL> | QUICK <symbol> | LEVELS <symbol> | NEWS")


def _print_levels(result: dict) -> None:
    print(json.dumps({"market_data": result["market_data"], "setups": result["setups"]}, indent=2, default=str))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="BOLOROX — reproducible forex market analysis")
    parser.add_argument("command", nargs="?", default="STATUS")
    parser.add_argument("symbol", nargs="?", default=None)
    args = parser.parse_args(argv)
    config = load_config()
    command = args.command.strip().upper()
    symbol_arg = args.symbol.strip().upper() if args.symbol else None
    if command == "RUN ALL" or (command == "RUN" and symbol_arg == "ALL"):
        symbols = config["symbols"].get("default", [])
        for symbol in symbols:
            run_symbol(symbol, _output_dir(symbol), config)
        return 0
    if command == "STATUS":
        _status(config)
        return 0
    if command in {"RUN", "QUICK", "LEVELS"}:
        if not symbol_arg:
            parser.error(f"{command} requires a symbol (or ALL for RUN)")
        symbol = _validate_symbol(symbol_arg, config)
        result = run_symbol(symbol, _output_dir(symbol), config)
        if command == "LEVELS":
            _print_levels(result)
        elif command == "QUICK":
            data = result["market_data"]
            print(f"{symbol}: price={data.get('price')} H1={data.get('h1_bias', 'UNKNOWN')} "
                  f"D1={data.get('d1_bias', 'UNKNOWN')} RSI={data.get('rsi', 'unknown')} "
                  f"setups={len(result['setups'])}; stale={data.get('stale')}")
        return 0
    if command == "NEWS":
        headlines = get_headlines()
        if headlines is None:
            print("News feeds are not configured. Set BOLOROX_NEWS_FEEDS to one or more public RSS/Atom URLs.")
            return 0
        for item in headlines:
            print(f"{item['published']} — {item['title']}\n{item.get('link') or ''}")
        if not headlines:
            print("No headlines were returned by the configured feeds.")
        return 0
    parser.error("Use STATUS | RUN <symbol|ALL> | QUICK <symbol> | LEVELS <symbol> | NEWS")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
