# MarketVeda build.py VERSION=FUNDAMENTALS_V3
#!/usr/bin/env python3
"""
build.py — MarketVeda Dashboard Orchestrator
Usage : python build.py SYMBOL
Output: SYMBOL_YYYY-MM-DD.html

Data source: nse-market-db — single daily JSON per day
Schema per symbol:
  Scalars: open high low close volume prev_close change_pct
           dma_50 dma_150 dma_200 rs_raw 52w_high 52w_low
           atr_14 atr_21 atr_pct avg_vol_10/20/50 minervini_pass
  Arrays:  dates opens highs lows closes volumes (full history)
  Top-level: nifty50_history fetch_date nifty50_close
"""

import sys, requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DB  = "https://raw.githubusercontent.com/MarketVeda/nse-market-db/main/"
IST = ZoneInfo("Asia/Kolkata")

# ── Fallback fundamentals (used when financials.json unavailable) ─────────────
# Key metrics: pe, roe, bv (book value per share), pb (price/book)
# Source: screener.in — update quarterly
FUNDAMENTALS = {
    "TRENT":       {"pe":99,  "roe":29, "bv":131,  "mktcap":171533},
    "RELIANCE":    {"pe":24,  "roe":9,  "bv":1089, "mktcap":1680000},
    "HDFCBANK":    {"pe":19,  "roe":16, "bv":580,  "mktcap":1260000},
    "ICICIBANK":   {"pe":17,  "roe":17, "bv":358,  "mktcap":960000},
    "TCS":         {"pe":29,  "roe":51, "bv":198,  "mktcap":1430000},
    "INFY":        {"pe":24,  "roe":32, "bv":210,  "mktcap":610000},
    "SBIN":        {"pe":11,  "roe":18, "bv":462,  "mktcap":750000},
    "BAJFINANCE":  {"pe":30,  "roe":22, "bv":580,  "mktcap":520000},
    "KOTAKBANK":   {"pe":20,  "roe":15, "bv":430,  "mktcap":395000},
    "HINDUNILVR":  {"pe":55,  "roe":22, "bv":45,   "mktcap":590000},
    "CGPOWER":     {"pe":95,  "roe":38, "bv":38,   "mktcap":109000},
    "ADANIPORTS":  {"pe":22,  "roe":18, "bv":288,  "mktcap":295000},
    "WIPRO":       {"pe":22,  "roe":15, "bv":155,  "mktcap":255000},
    "TITAN":       {"pe":88,  "roe":32, "bv":156,  "mktcap":320000},
    "SUNPHARMA":   {"pe":38,  "roe":18, "bv":295,  "mktcap":390000},
    "MARUTI":      {"pe":28,  "roe":19, "bv":2580, "mktcap":410000},
    "AXISBANK":    {"pe":13,  "roe":18, "bv":445,  "mktcap":370000},
    "LT":          {"pe":35,  "roe":16, "bv":550,  "mktcap":490000},
    "NTPC":        {"pe":15,  "roe":12, "bv":185,  "mktcap":360000},
    "ONGC":        {"pe":8,   "roe":13, "bv":220,  "mktcap":340000},
    "M&M":         {"pe":32,  "roe":22, "bv":280,  "mktcap":290000},
    "BHARTIARTL":  {"pe":55,  "roe":12, "bv":125,  "mktcap":945000},
    "NESTLEIND":   {"pe":75,  "roe":95, "bv":65,   "mktcap":225000},
    "DRREDDY":     {"pe":25,  "roe":20, "bv":580,  "mktcap":200000},
    "DIVISLAB":    {"pe":40,  "roe":22, "bv":390,  "mktcap":195000},
    "CIPLA":       {"pe":32,  "roe":16, "bv":265,  "mktcap":160000},
    "ULTRACEMCO":  {"pe":35,  "roe":14, "bv":1380, "mktcap":370000},
    "HCLTECH":     {"pe":26,  "roe":25, "bv":220,  "mktcap":430000},
    "TECHM":       {"pe":20,  "roe":14, "bv":320,  "mktcap":145000},
    "PERSISTENT":  {"pe":55,  "roe":28, "bv":460,  "mktcap":85000},
    "KAYNES":      {"pe":90,  "roe":18, "bv":220,  "mktcap":22000},
    "DIXON":       {"pe":85,  "roe":22, "bv":380,  "mktcap":52000},
    "CDSL":        {"pe":55,  "roe":38, "bv":120,  "mktcap":30000},
    "BSE":         {"pe":60,  "roe":22, "bv":280,  "mktcap":38000},
    "ANGELONE":    {"pe":18,  "roe":32, "bv":295,  "mktcap":18000},
    "HAL":         {"pe":45,  "roe":28, "bv":450,  "mktcap":290000},
    "BEL":         {"pe":50,  "roe":22, "bv":25,   "mktcap":195000},
    "MAZDOCK":     {"pe":38,  "roe":35, "bv":98,   "mktcap":73000},
    "GRSE":        {"pe":42,  "roe":18, "bv":145,  "mktcap":18000},
    "RVNL":        {"pe":25,  "roe":18, "bv":65,   "mktcap":57000},
    "TATASTEEL":   {"pe":10,  "roe":8,  "bv":165,  "mktcap":185000},
    "JSWSTEEL":    {"pe":15,  "roe":12, "bv":310,  "mktcap":225000},
    "HINDALCO":    {"pe":12,  "roe":10, "bv":390,  "mktcap":145000},
    "TATAPOWER":   {"pe":30,  "roe":10, "bv":95,   "mktcap":98000},
    "DLF":         {"pe":45,  "roe":8,  "bv":215,  "mktcap":195000},
    "GODREJPROP":  {"pe":60,  "roe":10, "bv":280,  "mktcap":82000},
    "BAJAJ-AUTO":  {"pe":30,  "roe":28, "bv":1250, "mktcap":255000},
    "TVSMOTOR":    {"pe":38,  "roe":32, "bv":155,  "mktcap":118000},
    "EICHERMOT":   {"pe":35,  "roe":30, "bv":580,  "mktcap":130000},
    "PIDILITIND":  {"pe":75,  "roe":28, "bv":95,   "mktcap":145000},
    "DABUR":       {"pe":52,  "roe":20, "bv":55,   "mktcap":90000},
    "MARICO":      {"pe":50,  "roe":35, "bv":28,   "mktcap":75000},
    "BRITANNIA":   {"pe":55,  "roe":55, "bv":82,   "mktcap":120000},
    "ITC":         {"pe":28,  "roe":28, "bv":48,   "mktcap":485000},
    "POWERGRID":   {"pe":14,  "roe":18, "bv":155,  "mktcap":295000},
    "RECLTD":      {"pe":8,   "roe":18, "bv":265,  "mktcap":115000},
    "PFC":         {"pe":7,   "roe":20, "bv":175,  "mktcap":145000},
    "IRFC":        {"pe":16,  "roe":14, "bv":42,   "mktcap":195000},
    "IRCTC":       {"pe":58,  "roe":38, "bv":45,   "mktcap":82000},
    "CHOLAFIN":    {"pe":25,  "roe":18, "bv":210,  "mktcap":95000},
    "MANAPPURAM":  {"pe":7,   "roe":22, "bv":105,  "mktcap":22000},
    "MUTHOOTFIN":  {"pe":15,  "roe":22, "bv":580,  "mktcap":95000},
    "SHRIRAMFIN":  {"pe":15,  "roe":16, "bv":560,  "mktcap":110000},
    "HDFCLIFE":    {"pe":80,  "roe":12, "bv":55,   "mktcap":155000},
    "SBILIFE":     {"pe":70,  "roe":14, "bv":82,   "mktcap":175000},
    "ICICIPRULI":  {"pe":55,  "roe":15, "bv":45,   "mktcap":95000},
    "LICI":        {"pe":15,  "roe":55, "bv":28,   "mktcap":1050000},
    "BAJAJFINSV":  {"pe":14,  "roe":15, "bv":620,  "mktcap":255000},
    "HDFCAMC":     {"pe":42,  "roe":30, "bv":145,  "mktcap":95000},
    "NAUKRI":      {"pe":55,  "roe":18, "bv":420,  "mktcap":98000},
    "ETERNAL":     {"pe":250, "roe":5,  "bv":28,   "mktcap":280000},
    "SWIGGY":      {"pe":None,"roe":-5, "bv":42,   "mktcap":95000},
    "PAYTM":       {"pe":None,"roe":-8, "bv":88,   "mktcap":55000},
    "POLICYBZR":   {"pe":None,"roe":2,  "bv":62,   "mktcap":45000},
    "ZOMATO":      {"pe":250, "roe":4,  "bv":25,   "mktcap":280000},
    "WAAREEENER":  {"pe":45,  "roe":28, "bv":195,  "mktcap":52000},
    "SUZLON":      {"pe":38,  "roe":22, "bv":8,    "mktcap":58000},
    "INOXWIND":    {"pe":28,  "roe":18, "bv":55,   "mktcap":8500},
    "JSWENERGY":   {"pe":25,  "roe":12, "bv":115,  "mktcap":58000},
    "ADANIGREEN":  {"pe":95,  "roe":8,  "bv":55,   "mktcap":180000},
    "CAMS":        {"pe":45,  "roe":38, "bv":220,  "mktcap":22000},
    "KFINTECH":    {"pe":38,  "roe":28, "bv":145,  "mktcap":15000},
    "MCX":         {"pe":55,  "roe":22, "bv":280,  "mktcap":18000},
    "MOTILALOFS":  {"pe":22,  "roe":22, "bv":480,  "mktcap":45000},
    "NUVAMA":      {"pe":18,  "roe":18, "bv":620,  "mktcap":18000},
}


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

    daily_raw = None
    fetch_date = None
    for dt in trading_dates(5):
        daily_raw = _get(f"data/daily/{dt}.json")
        if daily_raw and daily_raw.get("symbols", {}).get(sym):
            fetch_date = dt
            break

    if not daily_raw or not fetch_date:
        print(f"[MarketVeda] ERROR: No daily data found for {sym}", file=sys.stderr)
        return {
            "sym": sym, "live": {}, "eod": [], "candles": [],
            "oi": [], "deliv_pct": None, "deliv_date": None,
            "fin": {}, "news": {},
            "date_str": now.strftime("%d %b %Y"),
            "time_str": now.strftime("%H:%M"),
            "ts": now.strftime("%d %b %Y %H:%M IST"),
        }

    s = daily_raw["symbols"][sym]

    # ── Build EOD from embedded arrays ───────────────────────────────────────
    dates   = s.get("dates",   [])
    opens   = s.get("opens",   [])
    highs   = s.get("highs",   [])
    lows    = s.get("lows",    [])
    closes  = s.get("closes",  [])
    volumes = s.get("volumes", [])

    avg20  = s.get("avg_vol_20", 0)
    dma50  = s.get("dma_50",  0)
    dma200 = s.get("dma_200", 0)
    rs_raw = s.get("rs_raw",  1.0)
    h52    = s.get("52w_high", 0)
    l52    = s.get("52w_low",  0)
    atr14  = s.get("atr_14",  0)

    eod = []
    for i, dt in enumerate(dates):
        eod.append({
            "date":   dt,
            "o":      opens[i]   if i < len(opens)   else 0,
            "h":      highs[i]   if i < len(highs)   else 0,
            "l":      lows[i]    if i < len(lows)     else 0,
            "c":      closes[i]  if i < len(closes)   else 0,
            "v":      volumes[i] if i < len(volumes)  else 0,
            "avg20":  avg20, "dma50": dma50, "dma200": dma200,
            "rs":     rs_raw, "h52": h52, "l52": l52, "atr_14": atr14,
        })

    if not eod or eod[-1]["date"] != fetch_date:
        eod.append({
            "date":   fetch_date,
            "o":      s.get("open",   0),
            "h":      s.get("high",   0),
            "l":      s.get("low",    0),
            "c":      s.get("close",  0),
            "v":      s.get("volume", 0),
            "avg20":  avg20, "dma50": dma50, "dma200": dma200,
            "rs":     rs_raw, "h52": h52, "l52": l52, "atr_14": atr14,
        })

    # ── Live quote ────────────────────────────────────────────────────────────
    live = {
        "ltp":        s.get("close",      0),
        "prev_close": s.get("prev_close", 0),
        "open":       s.get("open",       0),
        "high":       s.get("high",       0),
        "low":        s.get("low",        0),
        "volume":     s.get("volume",     0),
        "change_pct": s.get("change_pct", 0),
        "atr_14":     atr14,   # ← now passed through live dict
    }

    # ── Financials — try DB first, fall back to FUNDAMENTALS table ───────────
    fin_raw = _get("data/financials/financials.json") or {}
    fin = (fin_raw.get("symbols") or {}).get(sym) or {}

    # Overlay key_metrics from FUNDAMENTALS table when:
    # (a) fin is empty, OR (b) fin exists but lacks PE/ROE/BV (common with screener data)
    if sym in FUNDAMENTALS:
        fb  = FUNDAMENTALS[sym]
        ltp = s.get("close", 0)
        bv  = fb.get("bv", 0)
        pe  = fb.get("pe")
        roe = fb.get("roe")
        pb  = round(ltp / bv, 1) if bv else None
        km  = fin.get("key_metrics") or {}
        # Only inject fields that are missing
        if not km.get("P/E") and not km.get("Price to Earning"):
            km["P/E"] = pe
        if not km.get("ROE %") and not km.get("ROE"):
            km["ROE %"] = roe
        if not km.get("Book Value"):
            km["Book Value"] = bv
        if not km.get("Price to Book") and not km.get("P/B"):
            km["Price to Book"] = pb
        if not km.get("Market Cap"):
            km["Market Cap"] = fb.get("mktcap")
        if not fin:
            fin = {}
        fin["key_metrics"] = km
        print(f"[MarketVeda] Fundamentals: PE={pe} ROE={roe} BV={bv} P/B={pb}", file=sys.stderr)

    # ── News, OI, Delivery, Intraday ─────────────────────────────────────────
    news_raw = _get("data/news/news.json") or {}
    news = (news_raw.get("symbols") or {}).get(sym) or {}

    oi = []
    for dt in trading_dates(7):
        fno = _get(f"data/fno_oi/{dt}.json") or {}
        row = (fno.get("symbols") or {}).get(sym)
        if row:
            oi.append({"date": dt, "oi": row.get("oi", 0), "ltp": row.get("last_price", 0)})

    deliv_pct = deliv_date = None
    for dt in trading_dates(5):
        d2 = _get(f"data/delivery/{dt}.json") or {}
        row = (d2.get("symbols") or {}).get(sym)
        if row:
            deliv_pct  = row.get("delivery_pct")
            deliv_date = dt
            break

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
    print(f"[MarketVeda] RSI:{tech['rsi']}  MACD:{tech['macd']}  "
          f"ADX:{tech['adx']}  ATR:{data['live'].get('atr_14')}  "
          f"Patterns:{len(tech['patterns'])}  SR:{len(tech['sr'])}", file=sys.stderr)

    from scoring import get_sector, get_name
    fin    = data["fin"]
    sector = get_sector(sym, fin)
    name   = get_name(sym, fin)

    from financials import process
    fp = process(fin, sym, sector)
    print(f"[MarketVeda] Sector:{sector}  PE:{fp['pe'].get('cur_pe')}  "
          f"ROE:{fp.get('km',{}).get('ROE %')}  "
          f"Value score:{fp['value'].get('score', 0)}", file=sys.stderr)

    from scoring import sentiment, recommend, triggers, risk
    sent     = sentiment(data["news"], tech)
    sc       = recommend(tech, fp, data["news"])
    pos, neg = triggers(data["news"], tech, fp)
    risk_r   = risk(tech, fp)
    print(f"[MarketVeda] Action:{sc['action']}  Conf:{sc['conf']}%  "
          f"Sentiment:{sent['cons']}", file=sys.stderr)

    from design import generate
    html = generate(sym, data, tech, fp, sc, sent, pos, neg, risk_r)
    print(f"[MarketVeda] HTML:{len(html):,} bytes", file=sys.stderr)
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
