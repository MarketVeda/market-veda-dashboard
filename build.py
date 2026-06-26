#!/usr/bin/env python3
"""
build.py — MarketVeda Dashboard Orchestrator
Usage : python build.py SYMBOL
Output: SYMBOL_YYYY-MM-DD.html

4-module architecture:
  indicators.py — RSI MACD ADX StochRSI CCI MAs Pivots S&R Patterns CAGR Entry/Exit Minervini
  financials.py — PE analysis Value investing PEG ROE CAGR Institutional research
  scoring.py    — News Sentiment Recommendation Risk Triggers
  design.py     — HTML Dashboard (dark neon, candlestick chart, S&R zones)
"""

import sys, requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DB = "https://raw.githubusercontent.com/MarketVeda/nse-market-db/main/"
IST = ZoneInfo("Asia/Kolkata")


# ── Data Fetcher ──────────────────────────────────────────────────────────────

def _get(path):
    for _ in range(3):
        try:
            r = requests.get(DB + path, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    return None

def trading_dates(n=12):
    dates, d = [], datetime.now(IST).date()
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(str(d))
        d -= timedelta(days=1)
    return dates

def fetch(sym):
    sym = sym.upper()
    dates = trading_dates(12)

    live_raw = _get("data/live/latest.json") or {}
    live = (live_raw.get("quotes") or {}).get(sym) or {}

    eod = []
    for dt in reversed(dates):
        daily = _get(f"data/daily/{dt}.json") or {}
        s = (daily.get("symbols") or {}).get(sym)
        if s:
            eod.append({
                "date": dt,
                "o": s.get("open", 0), "h": s.get("high", 0),
                "l": s.get("low", 0),
                "c": s.get("close") or s.get("last_price", 0),
                "v": s.get("volume", 0),
                "avg20": s.get("avg_vol_20", 0),
                "dma50": s.get("dma_50", 0),
                "dma200": s.get("dma_200", 0),
                "rs": s.get("rs_raw", 1.0),
                "h52": s.get("52w_high", 0),
                "l52": s.get("52w_low", 0),
            })

    candles = []
    for dt in dates[:3]:
        intra = _get(f"data/intraday/{dt}.json") or {}
        s = (intra.get("symbols") or {}).get(sym)
        if s:
            candles = s.get("15min") or []
            if candles: break

    oi = []
    for dt in reversed(dates[:7]):
        fno = _get(f"data/fno_oi/{dt}.json") or {}
        s = (fno.get("symbols") or {}).get(sym)
        if s:
            oi.append({"date": dt, "oi": s.get("oi", 0), "ltp": s.get("last_price", 0)})

    deliv_pct = deliv_date = None
    for dt in dates[:5]:
        d2 = _get(f"data/delivery/{dt}.json") or {}
        s = (d2.get("symbols") or {}).get(sym)
        if s:
            deliv_pct = s.get("delivery_pct")
            deliv_date = dt
            break

    fin_raw = _get("data/financials/financials.json") or {}
    fin = (fin_raw.get("symbols") or {}).get(sym) or {}

    news_raw = _get("data/news/news.json") or {}
    news = (news_raw.get("symbols") or {}).get(sym) or {}

    now = datetime.now(IST)
    return {
        "sym": sym, "live": live, "eod": eod, "candles": candles,
        "oi": oi, "deliv_pct": deliv_pct, "deliv_date": deliv_date,
        "fin": fin, "news": news,
        "date_str": now.strftime("%d %b %Y"),
        "time_str": now.strftime("%H:%M"),
        "ts": now.strftime("%d %b %Y %H:%M IST"),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def run(sym):
    sym = sym.strip().upper()
    print(f"[MarketVeda] ▶ {sym}", file=sys.stderr)

    data = fetch(sym)
    print(f"[MarketVeda] EOD rows: {len(data['eod'])}", file=sys.stderr)

    from indicators import compute
    tech = compute(data)
    print(f"[MarketVeda] LTP: ₹{tech['ltp']:,.2f}  RSI: {tech['rsi']}  "
          f"Patterns: {len(tech['patterns'])}  SR zones: {len(tech['sr'])}", file=sys.stderr)

    from scoring import get_sector, get_name
    fin = data["fin"]
    sector = get_sector(sym, fin)
    name = get_name(sym, fin)

    from financials import process
    fp = process(fin, sym, sector)
    print(f"[MarketVeda] Sector: {sector}  PE: {fp['pe'].get('cur_pe')}  "
          f"Value score: {fp['value'].get('score',0)}", file=sys.stderr)

    from scoring import sentiment, recommend, triggers, risk
    sent = sentiment(data["news"], tech)
    sc = recommend(tech, fp, data["news"])
    pos, neg = triggers(data["news"], tech, fp)
    risk_r = risk(tech, fp)
    print(f"[MarketVeda] Action: {sc['action']}  Conf: {sc['conf']}%  "
          f"Sentiment: {sent['cons']}", file=sys.stderr)

    from design import generate
    html = generate(sym, data, tech, fp, sc, sent, pos, neg, risk_r)
    print(f"[MarketVeda] HTML: {len(html):,} bytes", file=sys.stderr)
    return html


def main():
    if len(sys.argv) < 2:
        print("Usage: python build.py SYMBOL", file=sys.stderr)
        sys.exit(1)
    sym = sys.argv[1].strip().upper()
    html = run(sym)
    now = datetime.now(IST)
    fname = f"{sym}_{now.strftime('%Y-%m-%d')}.html"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[MarketVeda] ✅ Saved → {fname}", file=sys.stderr)


if __name__ == "__main__":
    main()
