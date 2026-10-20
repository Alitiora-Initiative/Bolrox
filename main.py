"""BOLOROX main entry point. Minimal end-to-end RUN support."""
import argparse
import logging
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

from src.fetch_prices import get_ohlc
from src.indicators import ema, atr, rsi
from src.fetch_macro import get_macro_snapshot
from src.fetch_calendar import get_upcoming_events
from src.fetch_cot import get_cot_net
from src.report import write_report
from src.trade_builder import build_trade

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bolorox")

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def run_symbol(symbol: str, out_dir: Path):
    """Minimal pipeline for one symbol: prices -> basic indicators -> signal or no-trade."""
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Running {symbol}")

    # Phase 1: prices
    df_h1 = get_ohlc(symbol, interval="1h", period="60d")
    df_d1 = get_ohlc(symbol, interval="1d", period="2y")
    if df_h1 is None or len(df_h1) < 100:
        logger.error(f"Insufficient price data for {symbol}")
        return

    # Basic indicators
    df_h1["ema50"] = ema(df_h1["close"], 50)
    df_h1["ema200"] = ema(df_h1["close"], 200)
    df_h1["atr"] = atr(df_h1, 14)
    df_h1["rsi"] = rsi(df_h1["close"], 14)

    last = df_h1.iloc[-1]
    price = float(last["close"])
    atr_val = float(last["atr"]) if not pd.isna(last["atr"]) else price * 0.001

    # Macro / COT / calendar (best-effort)
    macro = get_macro_snapshot()
    cot = get_cot_net("EUR" if "EUR" in symbol else "JPY" if "JPY" in symbol else "GOLD")
    events = get_upcoming_events()

    # Simple decision (placeholder logic for skeleton)
    bias = "NEUTRAL"
    if price > last["ema50"] and price > last["ema200"]:
        bias = "BULLISH"
    elif price < last["ema50"] and price < last["ema200"]:
        bias = "BEARISH"

    signals = []
    if bias != "NEUTRAL" and abs(price - last["ema50"]) < 1.5 * atr_val:
        direction = "LONG" if bias == "BULLISH" else "SHORT"
        entry = price
        if direction == "LONG":
            sl = entry - 1.5 * atr_val
            tps = [entry + 1.5 * 1.5 * atr_val, entry + 2.5 * 1.5 * atr_val, entry + 4 * 1.5 * atr_val]
        else:
            sl = entry + 1.5 * atr_val
            tps = [entry - 1.5 * 1.5 * atr_val, entry - 2.5 * 1.5 * atr_val, entry - 4 * 1.5 * atr_val]
        trade = build_trade(symbol, direction, entry, sl, tps, atr_val)
        if trade:
            trade["grade"] = "B"
            trade["prob_tp1"] = 0.55
            trade["confluence_score"] = 62
            trade["notes"] = "Minimal skeleton signal based on EMA alignment and proximity"
            signals.append(trade)

    # Report
    symbol_data = {symbol: {"bias": bias, "price": price, "atr": atr_val, "source": df_h1.attrs.get("source")}}
    write_report(symbol_data, signals, str(out_dir))

    # signals.json
    with open(out_dir / "signals.json", "w") as f:
        json.dump(signals, f, indent=2)

    logger.info(f"Wrote report and signals to {out_dir}")
    print(f"\n{symbol} complete. Bias: {bias}. Signals: {len(signals)}")
    print(f"Output: {out_dir}")

def main():
    parser = argparse.ArgumentParser(description="BOLOROX — autonomous forex analyst")
    parser.add_argument("command", nargs="?", default="STATUS")
    parser.add_argument("symbol", nargs="?", default=None)
    args = parser.parse_args()

    config = load_config()
    cmd = args.command.upper()

    if cmd == "STATUS":
        print("BOLOROX Status")
        print(f"Default symbols: {config['symbols']['default']}")
        print("Caching: enabled (data/cache.sqlite)")
        print("Ready for: python main.py RUN EURUSD")
    elif cmd == "RUN" and args.symbol:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out = Path("out") / f"{today}_{args.symbol.upper()}"
        run_symbol(args.symbol.upper(), out)
    elif cmd == "RUN ALL":
        for sym in config["symbols"]["default"]:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            out = Path("out") / f"{today}_{sym}"
            run_symbol(sym, out)
    else:
        print(f"Usage: python main.py STATUS | RUN EURUSD | RUN ALL")

if __name__ == "__main__":
    main()
