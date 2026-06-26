#!/usr/bin/env python3
"""
build.py — MarketVeda Dashboard Orchestrator
Usage : python build.py SYMBOL
Output: SYMBOL_YYYY-MM-DD.html

Data source: nse-market-db — single daily JSON file per day
File path  : data/daily/YYYY-MM-DD.json
Schema     :
  d["symbols"][SYM] = {
      # Today's live scalars
      "open", "high", "low", "close", "volume", "prev_close", "change_pct",
      "dma_50", "dma_150", "dma_200", "rs_raw", "52w_high", "52w_low",
      "avg_vol_10", "avg_vol_20", "avg_vol_50", "atr_14", "minervini_pass",
      # Full history arrays (up to yesterday, 1200+ candles)
      "dates", "opens", "highs", "lows", "closes", "volumes", "candle_count"
  }
  d["nifty50_history"] = [{"d","o","h","l","c","v"}, ...]
  d["fetch_date"], d["fetch_time"], d["nifty50_close"]
"""

import sys, requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DB  = "https://raw.githubusercontent.com/MarketVeda/nse-market-db/main/"
IST = ZoneInfo("Asia/Kolkata")


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _get(path):
    for _ in range(3):
        try:
            r = requests.get(DB + path, timeout=30)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    return None


# ── Date helpers ──────────────────────────────────────────────────────────────

def trading_dates(n=10):
    """Return last n calendar dates (Mon-Fri) going back from today IST."""
    dates, d = [], datetime.now(IST).date()
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(str(d))
        d -= timedelta(days=1)
    return dates


# ── Main fetch ────────────────────────────────────────────────────────────────

def fetch(sym):
    sym = sym.upper()
    now = datetime.now(IST)

    # Try today first, then up to 5 previous trading days
    daily_raw = None
    fetch_date = None
    for dt in trading_dates(5):
        daily_raw = _get(f"data/daily/{dt}.json")
        if daily_raw and daily_raw.get("symbols", {}).get(sym):
            fetch_date = dt
            break

    if not daily_raw or not fetch_date:
        print(f"[MarketVeda] ERROR: No daily data found for {sym}", file=sys.stderr)
        # Return minimal empty structure
        return {
            "sym": sym, "live": {}, "eod": [], "candles": [],
            "oi": [], "deliv_pct": None, "deliv_date": None,
            "fin": {}, "news": {},
            "date_str": now.strftime("%d %b %Y"),
            "time_str": now.strftime("%H:%M"),
            "ts": now.strftime("%d %b %Y %H:%M IST"),
        }

    s = daily_raw["symbols"][sym]

    # ── Build EOD array from embedded history arrays ──────────────────────────
    # History arrays = all past candles (up to yesterday)
    # Today's live data = scalar fields open/high/low/close/volume
    dates   = s.get("dates",   [])
    opens   = s.get("opens",   [])
    highs   = s.get("highs",   [])
    lows    = s.get("lows",    [])
    closes  = s.get("closes",  [])
    volumes = s.get("volumes", [])

    # Build EOD list from history arrays
    # Pull pre-computed fields from scalar section for latest row
    avg20   = s.get("avg_vol_20", 0)
    dma50   = s.get("dma_50",  0)
    dma200  = s.get("dma_200", 0)
    rs_raw  = s.get("rs_raw",  1.0)
    h52     = s.get("52w_high", 0)
    l52     = s.get("52w_low",  0)

    eod = []
    for i, dt in enumerate(dates):
        eod.append({
            "date":   dt,
            "o":      opens[i]   if i < len(opens)   else 0,
            "h":      highs[i]   if i < len(highs)   else 0,
            "l":      lows[i]    if i < len(lows)     else 0,
            "c":      closes[i]  if i < len(closes)   else 0,
            "v":      volumes[i] if i < len(volumes)  else 0,
            "avg20":  avg20,
            "dma50":  dma50,
            "dma200": dma200,
            "rs":     rs_raw,
            "h52":    h52,
            "l52":    l52,
        })

    # Append today's live candle (scalar fields) if not already in history
    today_str = fetch_date
    if not eod or eod[-1]["date"] != today_str:
        eod.append({
            "date":   today_str,
            "o":      s.get("open",   0),
            "h":      s.get("high",   0),
            "l":      s.get("low",    0),
            "c":      s.get("close",  0),
            "v":      s.get("volume", 0),
            "avg20":  avg20,
            "dma50":  dma50,
            "dma200": dma200,
            "rs":     rs_raw,
            "h52":    h52,
            "l52":    l52,
        })

    # ── Live quote (from scalar fields) ──────────────────────────────────────
    live = {
        "ltp":        s.get("close",      0),
        "prev_close": s.get("prev_close", 0),
        "open":       s.get("open",       0),
        "high":       s.get("high",       0),
        "low":        s.get("low",        0),
        "volume":     s.get("volume",     0),
        "change_pct": s.get("change_pct", 0),
    }

    # ── Financials ────────────────────────────────────────────────────────────
    fin_raw = _get("data/financials/financials.json") or {}
    fin = (fin_raw.get("symbols") or {}).get(sym) or {}

    # ── News ──────────────────────────────────────────────────────────────────
    news_raw = _get("data/news/news.json") or {}
    news = (news_raw.get("symbols") or {}).get(sym) or {}

    # ── F&O OI ────────────────────────────────────────────────────────────────
    # Try to get OI from separate fno_oi file; graceful fallback
    oi = []
    for dt in trading_dates(7):
        fno = _get(f"data/fno_oi/{dt}.json") or {}
        row = (fno.get("symbols") or {}).get(sym)
        if row:
            oi.append({"date": dt, "oi": row.get("oi", 0), "ltp": row.get("last_price", 0)})

    # ── Delivery % ────────────────────────────────────────────────────────────
    deliv_pct = deliv_date = None
    for dt in trading_dates(5):
        d2 = _get(f"data/delivery/{dt}.json") or {}
        row = (d2.get("symbols") or {}).get(sym)
        if row:
            deliv_pct  = row.get("delivery_pct")
            deliv_date = dt
            break

    # ── Intraday candles ──────────────────────────────────────────────────────
    candles = []
    for dt in trading_dates(3):
        intra = _get(f"data/intraday/{dt}.json") or {}
        row = (intra.get("symbols") or {}).get(sym)
        if row:
            candles = row.get("15min") or []
            if candles:
                break

    return {
        "sym":        sym,
        "live":       live,
        "eod":        eod,
        "candles":    candles,
        "oi":         oi,
        "deliv_pct":  deliv_pct,
        "deliv_date": deliv_date,
        "fin":        fin,
        "news":       news,
        "date_str":   now.strftime("%d %b %Y"),
        "time_str":   now.strftime("%H:%M"),
        "ts":         now.strftime("%d %b %Y %H:%M IST"),
    }


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run(sym):
    sym = sym.strip().upper()
    print(f"[MarketVeda] ▶ {sym}", file=sys.stderr)

    data = fetch(sym)
    print(f"[MarketVeda] EOD rows: {len(data['eod'])} | "
          f"LTP: ₹{data['live'].get('ltp', 0):,.2f}", file=sys.stderr)

    from indicators import compute
    tech = compute(data)
    print(f"[MarketVeda] RSI: {tech['rsi']}  MACD: {tech['macd']}  "
          f"ADX: {tech['adx']}  Patterns: {len(tech['patterns'])}  "
          f"SR zones: {len(tech['sr'])}", file=sys.stderr)

    from scoring import get_sector, get_name
    fin    = data["fin"]
    sector = get_sector(sym, fin)
    name   = get_name(sym, fin)

    from financials import process
    fp = process(fin, sym, sector)
    print(f"[MarketVeda] Sector: {sector}  PE: {fp['pe'].get('cur_pe')}  "
          f"Value score: {fp['value'].get('score', 0)}", file=sys.stderr)

    from scoring import sentiment, recommend, triggers, risk
    sent  = sentiment(data["news"], tech)
    sc    = recommend(tech, fp, data["news"])
    pos, neg = triggers(data["news"], tech, fp)
    risk_r   = risk(tech, fp)
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
    sym  = sys.argv[1].strip().upper()
    html = run(sym)
    now  = datetime.now(IST)
    fname = f"{sym}_{now.strftime('%Y-%m-%d')}.html"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[MarketVeda] ✅ Saved → {fname}", file=sys.stderr)


if __name__ == "__main__":
    main()
