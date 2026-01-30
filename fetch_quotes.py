import json
import time
from datetime import datetime, timezone, timedelta
import requests
from pathlib import Path

TZ_TW = timezone(timedelta(hours=8))

SYMBOLS = [
    {"symbol": "2330.TW", "name": "台積電 2330"},
    {"symbol": "0050.TW", "name": "0050 元大台灣50"},
]

def fetch_yahoo_quotes(symbols):
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    params = {"symbols": ",".join([s["symbol"] for s in symbols])}
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    results = data.get("quoteResponse", {}).get("result", [])
    by_symbol = {q.get("symbol"): q for q in results}
    return by_symbol

def main():
    Path("data").mkdir(exist_ok=True)

    by_symbol = fetch_yahoo_quotes(SYMBOLS)

    now_tw = datetime.now(TZ_TW).strftime("%Y年%m月%d日 %H:%M")
    out = {
        "fetched_at": now_tw,
        "items": {}
    }

    for s in SYMBOLS:
        sym = s["symbol"]
        q = by_symbol.get(sym, {}) or {}

        latest = q.get("regularMarketPrice")
        prev_close = q.get("regularMarketPreviousClose")

        out["items"][sym] = {
            "name": s["name"],
            "latest": latest,
            "prev_close": prev_close,
        }

    with open("data/quotes.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
