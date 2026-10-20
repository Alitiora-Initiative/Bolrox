"""Chart generation skeleton (lightweight-charts HTML + PNG)."""
def generate_chart_html(symbol: str, data, levels: dict, out_path: str):
    """Write a minimal chart.html. Full Lightweight Charts integration to be completed."""
    html = f"""<!DOCTYPE html>
<html>
<head><title>BOLOROX {symbol}</title></head>
<body>
<h1>{symbol} — BOLOROX Levels</h1>
<p>Interactive chart generation pending full implementation.</p>
<p>Entry: {levels.get('entry')}</p>
<p>SL: {levels.get('sl')}</p>
</body>
</html>"""
    with open(out_path, "w") as f:
        f.write(html)
