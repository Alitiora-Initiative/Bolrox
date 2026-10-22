"""TradingView Advanced Chart widget export."""
import html
import json
from pathlib import Path


TRADINGVIEW_SYMBOLS = {
    "XAUUSD": "OANDA:XAUUSD",
    "EURUSD": "FX:EURUSD",
    "USDJPY": "FX:USDJPY",
    "GBPUSD": "FX:GBPUSD",
    "AUDUSD": "FX:AUDUSD",
    "NZDUSD": "FX:NZDUSD",
    "USDCAD": "FX:USDCAD",
    "USDCHF": "FX:USDCHF",
    "EURJPY": "FX:EURJPY",
    "GBPJPY": "FX:GBPJPY",
    "EURGBP": "FX:EURGBP",
    "XAGUSD": "OANDA:XAGUSD",
    "USOIL": "TVC:USOIL",
    "DXY": "TVC:DXY",
}


def _price(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):,.5f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return "—"


def generate_chart_html(symbol: str, data, levels: dict, out_path: str,
                        timezone: str = "Etc/UTC") -> str:
    """Write a responsive official TradingView widget plus the analysis snapshot.

    TradingView supplies the embedded chart's market data. The separately labelled
    values below come from Bolorox's configured OHLC source and may differ.
    """
    symbol = symbol.upper()
    tv_symbol = TRADINGVIEW_SYMBOLS.get(symbol)
    if not tv_symbol:
        raise ValueError(f"No TradingView widget symbol is configured for {symbol}")

    source = (data or {}).get("source") or "unavailable"
    last_candle = (data or {}).get("last_candle") or "unavailable"
    price = _price((data or {}).get("price"))
    interval = str((data or {}).get("tradingview_interval") or "60")
    config = {
        "autosize": True,
        "symbol": tv_symbol,
        "interval": interval,
        "timezone": timezone if timezone in {"Etc/UTC", "exchange", "Africa/Nairobi", "America/New_York", "Europe/London"} else "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "allow_symbol_change": True,
        "calendar": True,
        "details": True,
        "hide_side_toolbar": False,
        "hide_top_toolbar": False,
        "hide_legend": False,
        "hide_volume": False,
        "save_image": False,
        "withdateranges": True,
        "support_host": "https://www.tradingview.com",
    }
    widget_json = json.dumps(config, ensure_ascii=True, separators=(",", ":"))
    safe_symbol = html.escape(symbol)
    link_symbol = html.escape(tv_symbol.replace(":", "-"), quote=True)

    rows = []
    labels = (("Analysis price", "price"), ("Entry", "entry"),
              ("Stop loss", "stop_loss"), ("Take profit 1", "tp1"),
              ("Take profit 2", "tp2"), ("Take profit 3", "tp3"))
    for label, key in labels:
        value = price if key == "price" else _price((levels or {}).get(key))
        if value != "—":
            rows.append(f"<tr><th scope=\"row\">{label}</th><td>{html.escape(value)}</td></tr>")
    table = "\n".join(rows) or '<tr><td colspan="2">No analysis levels were produced.</td></tr>'

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>BOLOROX · {safe_symbol} chart</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background:#080b12; color:#e8edf6; }}
    * {{ box-sizing: border-box; }} body {{ margin:0; padding:24px; }}
    main {{ max-width:1440px; margin:0 auto; }}
    header {{ display:flex; justify-content:space-between; align-items:flex-end; gap:16px; margin-bottom:18px; }}
    h1 {{ margin:0; font-size:clamp(1.5rem, 3vw, 2.25rem); }}
    p {{ color:#9ba8bc; line-height:1.55; }}
    a {{ color:#76d6c4; }}
    .widget {{ height:min(72vh, 760px); min-height:420px; width:100%; border:1px solid #263042; border-radius:14px; overflow:hidden; }}
    .tradingview-widget-container, .tradingview-widget-container__widget {{ height:100%; width:100%; }}
    .tradingview-widget-copyright {{ padding:6px 10px; font-size:12px; }}
    .snapshot {{ margin-top:20px; padding:18px; border:1px solid #263042; border-radius:14px; background:#101521; }}
    .snapshot h2 {{ margin:0 0 6px; font-size:1.1rem; }}
    .snapshot table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
    th,td {{ padding:9px 4px; border-bottom:1px solid #263042; text-align:left; }} th {{ color:#9ba8bc; font-weight:500; }}
    td {{ text-align:right; font-variant-numeric:tabular-nums; }}
    small {{ color:#8491a7; }}
    @media (max-width:650px) {{ body {{ padding:14px; }} header {{ display:block; }} .widget {{ min-height:390px; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <div><p>BOLOROX MARKET VIEW</p><h1>{safe_symbol} · TradingView chart</h1></div>
      <a href="https://www.tradingview.com/symbols/{link_symbol}/" target="_blank" rel="noopener noreferrer">Open {safe_symbol} on TradingView ↗</a>
    </header>
    <section class="widget" aria-label="TradingView interactive chart">
      <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" target="_blank" rel="noopener nofollow">Charts by TradingView</a></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
          {widget_json}
        </script>
      </div>
    </section>
    <section class="snapshot">
      <h2>Bolorox analysis snapshot</h2>
      <p>These levels use Bolorox's source data (<strong>{html.escape(str(source))}</strong>), last candle <strong>{html.escape(str(last_candle))}</strong>. TradingView's chart uses its own selected market feed; quote differences are possible. Levels are listed here and are not drawn on the TradingView chart.</p>
      <table><tbody>{table}</tbody></table>
      <p><small>TradingView widget data availability and delays depend on the selected exchange or market. This page is informational and does not place orders.</small></p>
    </section>
  </main>
</body>
</html>
"""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")
    return str(path)
