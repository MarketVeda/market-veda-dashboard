# MarketVeda Dashboard
**`github.com/MarketVeda/market-veda-dashboard`**

Generate a complete HTML stock analysis dashboard for any NSE symbol by triggering one GitHub Actions workflow — from mobile, Claude, or any AI. No local machine. No Kite API key at generation time.

---

## How It Works

```
You (mobile / Claude / any AI)
        │
        │  trigger via GitHub Actions API or web UI
        ▼
GitHub Actions runs  build.py  SYMBOL
        │
        ├── fetch  data/live/latest.json          → live price OHLCV
        ├── fetch  data/daily/YYYY-MM-DD.json      → EOD + DMA + RS (10 days)
        ├── fetch  data/intraday/YYYY-MM-DD.json   → 15min candles
        ├── fetch  data/fno_oi/YYYY-MM-DD.json     → F&O Open Interest
        ├── fetch  data/delivery/YYYY-MM-DD.json   → NSE delivery %
        ├── fetch  data/financials/financials.json → 12yr P&L, ratios
        └── fetch  data/news/news.json             → announcements
                │
                ▼
        compute all indicators
        (RSI MACD ADX StochRSI CCI MAs Pivots CAGR Minervini PE-analysis)
                │
                ▼
        generate  out.html  (~160 KB, self-contained)
                │
                ▼
GitHub Artifact  →  download  →  open in browser / print PDF
```

Data comes from **`github.com/MarketVeda/nse-market-db`** — the automated pipeline that runs daily and hourly.

---

## Files

```
market-veda-dashboard/
├── build.py                           ← Single script. Does everything.
├── requirements.txt                   ← Only: requests
├── README.md                          ← This file
├── SKILL.md                           ← Instruction file for Claude / any AI
└── .github/
    └── workflows/
        └── dashboard.yml              ← GitHub Actions workflow (on-demand)
```

One script. No modules. No config files. No secrets needed.

---

## Step-by-Step Setup (do once)

### 1. Create the repository

Go to **github.com/new**
- Owner: `MarketVeda`
- Name: `market-veda-dashboard`
- Visibility: **Private**
- Click **Create repository**

### 2. Upload the files

Upload these files to the repo root (drag and drop in GitHub web UI):
```
build.py
requirements.txt
README.md
SKILL.md
.github/workflows/dashboard.yml
```

That's it. No secrets. No tokens. No configuration. The logo is already embedded inside `build.py`.

### 3. Enable Actions

Go to repo → **Actions** tab → click **"I understand my workflows, enable them"**

---

## How to Generate a Dashboard

### From GitHub Web UI (works on mobile too)

1. Open `github.com/MarketVeda/market-veda-dashboard`
2. Click **Actions**
3. Click **dashboard** (left sidebar)
4. Click **Run workflow** (top right)
5. Type the symbol: `RELIANCE` or `HDFCBANK` or `TITAN` or any NSE symbol
6. Click the green **Run workflow** button
7. Wait ~60 seconds
8. Click the completed run → scroll down → **Artifacts**
9. Download `MarketVeda-RELIANCE`
10. Unzip → open `out.html` in browser

### From Claude (via SKILL.md)

Claude reads `SKILL.md` and triggers the workflow via GitHub API. No PAT token needed for triggering from Claude — Claude uses its own GitHub tool.

### From curl (any script or AI)

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/MarketVeda/market-veda-dashboard/actions/workflows/dashboard.yml/dispatches \
  -d '{"ref":"main","inputs":{"symbol":"CGPOWER"}}'
```

---

## What the Dashboard Shows

### Row 1 — Overview · Price · Chart · Technicals
| Panel | Content |
|---|---|
| Overview | Company name, Market Cap, 52W H/L, Beta, P/E, Book Value, ROCE, ROE |
| Live Price | LTP, change %, OHLCV, Avg price, Upper/Lower circuit, Bid/Ask |
| Price Chart | Interactive Chart.js — 8 timeframes: 1D/1W/1M/3M/6M/1Y/2Y/5Y |
| Technical Summary | RSI, MACD, ADX, Stoch RSI, CCI, RS vs Nifty50/500, Minervini Stage |

### Row 2 — Moving Averages · Valuation · Volume · Risk
| Panel | Content |
|---|---|
| Moving Averages | SMA + EMA for 20/50/100/200 with signal. MA alignment badge. |
| Valuation | P/E, P/B, EV/EBITDA, PEG, ROE, ROCE grid |
| Volume | Today vs 20D avg, delivery %, Bid/Ask qty |
| Risk | 5 categories (Market/Sector/Company/Financial/Liquidity) + Overall |

### Row 3 — Financials · Triggers · S&R · Recommendation
| Panel | Content |
|---|---|
| Financial Summary | 5-year table: Revenue, Op Profit, OPM%, Net Profit, EPS, ROE |
| Key Triggers | Up to 6 positive ✅ and 4 negative ⚠️ from news + technicals |
| Support & Resistance | Classic pivot: S3 S2 S1 Pivot R1 R2 R3 |
| Recommendation | BUY/HOLD/SELL, 12M target, upside %, confidence bar, stop-loss, R:R |

### Row 4 — Results Tracker · Analyst Sentiment · Notes
| Panel | Content |
|---|---|
| Results Tracker | Last 8 quarters: Revenue, Net Profit, EPS, OPM%, BEAT label |
| Analyst Sentiment | Donut: BUY%/HOLD%/SELL% computed from news score + technicals |
| Notes | 5 auto-generated insight lines |

### Row 5 — Price Move · PE Analysis · Entry/Exit · OI
| Panel | Content |
|---|---|
| Price Move History | % return for 1D/2D/5D/7D/1W/1M/2M/6M + CAGR + 3M/6M/1Y targets |
| PE Valuation | Current vs 5Y mean, 10Y mean, sector PE, peer PE comparison |
| Entry / Exit | Entry zone, stop-loss, T1/T2/T3, R:R, ideal trigger condition |
| OI & Delivery | F&O OI 5-day trend + delivery % |

---

## Indicators Computed

All computed from raw OHLCV inside `build.py`. No external TA library.

| Indicator | Method |
|---|---|
| RSI (14) | Wilder smoothing |
| MACD (12,26,9) | EMA-based |
| ADX (14) | Wilder DMI |
| Stochastic RSI | RSI of RSI, then Stochastic |
| CCI (20) | Classic formula |
| SMA / EMA | 20, 50, 100, 200 periods |
| Pivot Points | Classic daily (S3–R3) |
| Minervini SEPA | 6 filters: price vs DMA50/150/200, DMA50>DMA200, 52W, RS |
| Price Returns | 1D, 2D, 5D, 7D, 1W, 1M, 2M, 6M |
| CAGR | Annualised from available EOD series |
| PE 5Y/10Y Mean | From financials.json ratios history |
| Sector PE | Built-in benchmark table (20 sectors) |

---

## Colour Palette (preserved exactly)

| Colour | Hex | Used for |
|---|---|---|
| Teal | `#00C896` | Primary accent, borders, bullish signals |
| Teal Dark | `#009B77` | Table headers, secondary accents |
| Teal Light | `#E6FAF5` | Row highlights, latest quarter |
| Red | `#F43F5E` | Bearish, negative, SELL |
| Amber | `#F59E0B` | Caution, HOLD, Stoch RSI warning |
| Body BG | `#0F0F0F` | Page background (near-black) |
| Card BG | `#FFFFFF` | Dashboard card background |

---

## Data Sources

| Data | nse-market-db file | Refreshed |
|---|---|---|
| Live price, OHLCV, Bid/Ask | `data/live/latest.json` | Hourly 9:15–15:30 IST |
| EOD close, DMAs, RS, 52W H/L | `data/daily/YYYY-MM-DD.json` | 4:00 PM IST daily |
| 15min candles (for 1D chart) | `data/intraday/YYYY-MM-DD.json` | 4:00 PM IST daily |
| F&O Open Interest | `data/fno_oi/YYYY-MM-DD.json` | 4:00 PM IST daily |
| Delivery % (NSE bhavcopy) | `data/delivery/YYYY-MM-DD.json` | 4:00 PM IST daily |
| 12yr fundamentals | `data/financials/financials.json` | 4:30 PM IST daily |
| Corporate announcements | `data/news/news.json` | Hourly |

---

## Relationship to nse-market-db

```
nse-market-db  (automated data pipeline)
      ↓  writes JSON to GitHub daily/hourly
market-veda-dashboard  (on-demand dashboard generator)
      ↓  reads JSON, computes, generates HTML
Your browser  (offline HTML file)
```

---

*MarketVeda · Knowledge Behind Every Trade · June 2026*
