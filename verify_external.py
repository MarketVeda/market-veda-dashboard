#!/usr/bin/env python3
"""
verify_external.py — MarketVeda external data verifier (STANDALONE / OPTIONAL)

Cross-checks the values MarketVeda derives from its own database
(github.com/MarketVeda/nse-market-db) against live external sources and reports
any differences.  External sources, when reachable and clearly authoritative,
take priority for live quote fields (price / OHLC / % change).

Usage
-----
    python verify_external.py SYMBOL [--json]

Design notes
------------
* This file is deliberately NOT imported by build.py's main path.  Run it on
  demand.  If you want build.py to overlay verified live values automatically,
  set the environment variable  MV_VERIFY_EXTERNAL=1  (build.py calls
  get_live_overlay() inside a try/except with a short timeout, so any failure
  silently falls back to the database values — it can never break the pipeline).
* Only the standard library + `requests` are used (no bs4/lxml), to match the
  project's minimal requirements.
* Sources may be blocked by your network policy or change their markup.  Every
  fetch is wrapped in try/except and returns None on failure; the verifier then
  simply reports "unavailable" for that source.

Sources
-------
* NSE quote API  — live price / OHLC / previous close / % change.
* screener.in    — current P/E, market cap, book value, ROE, 52w high/low.
"""

import sys
import re
import json

try:
    import requests
except Exception:                                       # pragma: no cover
    requests = None

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_HEADERS = {
    "User-Agent": _UA,
    "Accept": "text/html,application/json,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}
_TIMEOUT = 12


# ── helpers ───────────────────────────────────────────────────────────────────
def _num(x):
    """Parse a possibly-formatted number string ('1,234.5', '₹942', '12.3%')."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    m = re.search(r"-?\d[\d,]*\.?\d*", str(x).replace(",", ""))
    return float(m.group()) if m else None


# ── NSE live quote ────────────────────────────────────────────────────────────
def fetch_nse_quote(sym):
    """Live price / OHLC / prev-close / % change from NSE. None on any failure."""
    if requests is None:
        return None
    try:
        s = requests.Session()
        s.headers.update(_HEADERS)
        # priming request sets the cookies NSE requires for its API
        s.get("https://www.nseindia.com", timeout=_TIMEOUT)
        r = s.get(f"https://www.nseindia.com/api/quote-equity?symbol={sym.upper()}",
                  timeout=_TIMEOUT)
        if r.status_code != 200:
            return None
        j = r.json()
        pi = j.get("priceInfo", {}) or {}
        ihl = pi.get("intraDayHighLow", {}) or {}
        return {
            "ltp":        _num(pi.get("lastPrice")),
            "open":       _num(pi.get("open")),
            "high":       _num(ihl.get("max")),
            "low":        _num(ihl.get("min")),
            "prev_close": _num(pi.get("previousClose")),
            "pct_change": _num(pi.get("pChange")),
        }
    except Exception:
        return None


# ── screener.in fundamentals ──────────────────────────────────────────────────
def fetch_screener(sym):
    """Current fundamentals from screener.in's top-ratios block. None on failure."""
    if requests is None:
        return None
    try:
        r = requests.get(f"https://www.screener.in/company/{sym.upper()}/",
                         headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code != 200:
            # consolidated/standalone variants sometimes live at /consolidated/
            r = requests.get(f"https://www.screener.in/company/{sym.upper()}/consolidated/",
                             headers=_HEADERS, timeout=_TIMEOUT)
            if r.status_code != 200:
                return None
        html = r.text
        out = {}
        # Each ratio renders as: <li ...><span class="name">NAME</span> ...
        #   <span class="number">VALUE</span> ...</li>
        for li in re.findall(r"<li[^>]*>.*?</li>", html, re.S):
            nm = re.search(r'class="name">\s*(.*?)\s*<', li, re.S)
            val = re.search(r'class="(?:number|value)">\s*(.*?)\s*<', li, re.S)
            if not nm or not val:
                continue
            name = re.sub(r"\s+", " ", nm.group(1)).strip().lower()
            num = _num(val.group(1))
            if "stock p/e" in name or name == "p/e":
                out["pe"] = num
            elif "market cap" in name:
                out["market_cap"] = num
            elif "book value" in name:
                out["book_value"] = num
            elif name.startswith("roe"):
                out["roe"] = num
            elif "high / low" in name or "high/low" in name:
                nums = re.findall(r"-?\d[\d,]*\.?\d*", val.group(1).replace(",", ""))
                if len(nums) >= 2:
                    out["high_52w"], out["low_52w"] = float(nums[0]), float(nums[1])
        return out or None
    except Exception:
        return None


# ── our own database values (reuses the existing pipeline, read-only) ─────────
def fetch_ours(sym):
    try:
        from build import fetch
        from indicators import compute
        d = fetch(sym)
        t = compute(d)
        km = (d.get("fin", {}).get("key_metrics") or {})
        oh = t["ohlc"]
        return {
            "ltp": t["ltp"], "open": oh["o"], "high": oh["h"], "low": oh["l"],
            "prev_close": oh["pc"], "pct_change": t["chgp"],
            "pe": _num(km.get("Stock P/E") or km.get("P/E")),
            "book_value": _num(km.get("Book Value")),
            "roe": _num(km.get("ROE %") or km.get("ROE")),
            "market_cap": _num(km.get("Market Cap")),
        }
    except Exception as e:
        print(f"[verify] could not load our data: {e}", file=sys.stderr)
        return {}


# ── comparison ────────────────────────────────────────────────────────────────
def _cmp(label, ours, ext, tol_pct, unit=""):
    if ours is None or ext is None:
        return {"field": label, "ours": ours, "external": ext, "status": "n/a"}
    diff = abs(ours - ext)
    base = abs(ext) or 1
    ok = (diff / base * 100) <= tol_pct
    return {"field": label, "ours": ours, "external": ext,
            "diff_pct": round(diff / base * 100, 2),
            "status": "match" if ok else "MISMATCH", "unit": unit}


def verify(sym):
    ours = fetch_ours(sym)
    nse = fetch_nse_quote(sym)
    scr = fetch_screener(sym)

    rows = []
    if nse:
        rows += [
            _cmp("LTP", ours.get("ltp"), nse.get("ltp"), 0.5, "₹"),
            _cmp("Open", ours.get("open"), nse.get("open"), 0.5, "₹"),
            _cmp("High", ours.get("high"), nse.get("high"), 0.5, "₹"),
            _cmp("Low", ours.get("low"), nse.get("low"), 0.5, "₹"),
            _cmp("Prev Close", ours.get("prev_close"), nse.get("prev_close"), 0.5, "₹"),
            _cmp("% Change", ours.get("pct_change"), nse.get("pct_change"), 5.0, "%"),
        ]
    if scr:
        rows += [
            _cmp("P/E", ours.get("pe"), scr.get("pe"), 5.0, "x"),
            _cmp("Book Value", ours.get("book_value"), scr.get("book_value"), 5.0, "₹"),
            _cmp("ROE", ours.get("roe"), scr.get("roe"), 10.0, "%"),
            _cmp("Market Cap", ours.get("market_cap"), scr.get("market_cap"), 5.0, "Cr"),
        ]

    return {
        "symbol": sym.upper(),
        "sources": {"nse": nse is not None, "screener": scr is not None},
        "comparison": rows,
        # live fields where NSE (authoritative for quotes) disagrees with us
        "live_overlay": _live_overlay(ours, nse),
    }


def _live_overlay(ours, nse):
    """Return live quote fields from NSE that differ from ours (for optional use)."""
    if not nse:
        return {}
    overlay = {}
    for k in ("ltp", "open", "high", "low", "prev_close", "pct_change"):
        ov, ev = ours.get(k), nse.get(k)
        if ev is not None and (ov is None or abs(ov - ev) / (abs(ev) or 1) > 0.005):
            overlay[k] = ev
    return overlay


def get_live_overlay(sym):
    """Thin helper for an OPTIONAL build.py hook (guarded by MV_VERIFY_EXTERNAL)."""
    try:
        return _live_overlay(fetch_ours(sym), fetch_nse_quote(sym))
    except Exception:
        return {}


# ── CLI ───────────────────────────────────────────────────────────────────────
def _print_report(res):
    print(f"\nMarketVeda external verification — {res['symbol']}")
    print(f"  sources reachable: NSE={res['sources']['nse']}  "
          f"screener.in={res['sources']['screener']}")
    if not any(res["sources"].values()):
        print("  ⚠️  No external source reachable from this environment "
              "(network policy may block them). Run from an environment with "
              "access to nseindia.com / screener.in.")
        return
    print(f"  {'field':<12}{'ours':>14}{'external':>14}{'diff%':>9}   status")
    for r in res["comparison"]:
        if r["status"] == "n/a":
            continue
        u = r.get("unit", "")
        print(f"  {r['field']:<12}{str(r['ours'])+u:>14}{str(r['external'])+u:>14}"
              f"{r.get('diff_pct',''):>9}   {r['status']}")
    if res["live_overlay"]:
        print(f"  → live overlay (NSE authoritative): {res['live_overlay']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_external.py SYMBOL [--json]", file=sys.stderr)
        sys.exit(1)
    sym = sys.argv[1].strip().upper()
    res = verify(sym)
    if "--json" in sys.argv:
        print(json.dumps(res, indent=2))
    else:
        _print_report(res)


if __name__ == "__main__":
    main()
