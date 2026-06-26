# MarketVeda Dashboard
**`github.com/MarketVeda/market-veda-dashboard`**

> Complete stock intelligence dashboard for any NSE symbol.  
> Triggered on demand — from mobile, Claude, or GitHub web UI.  
> No local machine needed. Opens directly in browser. No zip file.

---

## What This Generates

A self-contained HTML dashboard (~180 KB) with dark neon design:

| Row | Panels |
|---|---|
| **Row 1** | Overview · Live Price + OHLCV · **Candlestick Chart with S&R Zones** · Technical Summary |
| **Row 2** | Moving Averages (9/20/50/100/200) · Valuation Metrics · Volume Analysis · Risk Analysis |
| **Row 3** | 5-Year Financials · Key Triggers · Support & Resistance Pivots · Recommendation |
| **Row 4** | 8-Quarter Results Tracker · Analyst Sentiment (donut) · Notes & Insights |
| **Row 5** | Price Move History + CAGR Targets · PE Analysis · Entry/Exit Strategy + **Chart Patterns** · **Institutional Value Analysis** |

---

## 4-Module Architecture

```
build.py          ← Entry point. Fetches data, calls all 4 modules.
indicators.py     ← RSI MACD ADX StochRSI CCI MAs Pivots S&R Patterns CAGR Entry/Exit Minervini
financials.py     ← PE analysis PEG ROE FCF Value score Institutional research
scoring.py        ← News sentiment Recommendation Risk Triggers
design.py         ← Complete HTML dashboard (dark neon + candlestick + S&R overlay)
```

---

## How to Trigger a Dashboard

### From GitHub Web UI (works on mobile too)
1. Go to `github.com/MarketVeda/market-veda-dashboard`
2. Click **Actions** → **dashboard** → **Run workflow**
3. Type any NSE symbol: `CGPOWER` / `RELIANCE` / `HDFCBANK` / `TITAN` etc.
4. Click **Run workflow**
5. Wait ~45 seconds
6. Click the completed run → copy the URL from the **Summary** section
7. Open URL directly in browser — no download, no zip

### From Claude
Say: *"give me CGPOWER dashboard"* → Claude reads `SKILL.md` and triggers automatically.

### From curl / any script
```bash
curl -X POST \
  -H "Authorization: token YOUR_PAT_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/MarketVeda/market-veda-dashboard/actions/workflows/dashboard.yml/dispatches \
  -d '{"ref":"main","inputs":{"symbol":"CGPOWER"}}'
```

### Direct Dashboard URL (after workflow runs)
```
https://marketveda.github.io/market-veda-dashboard/SYMBOL_YYYY-MM-DD.html
```
Example:
```
https://marketveda.github.io/market-veda-dashboard/CGPOWER_2026-06-26.html
```

All dashboards index:
```
https://marketveda.github.io/market-veda-dashboard/
```

---

## One-Time Setup

### Step 1 — Enable GitHub Pages
1. Go to repo → **Settings** → **Pages**
2. Source → **Deploy from a branch**
3. Branch → **gh-pages** → **/ (root)**
4. Click **Save**

### Step 2 — Enable Actions
Go to **Actions** tab → click **"enable workflows"** if prompted.

That's it. No secrets needed. Logo is embedded inside `design.py`.

---

## What the Dashboard Shows

### Colour Palette (preserved exactly)
| Colour | Hex | Used for |
|---|---|---|
| Neon Green | `#00E87A` | Primary accent, bullish signals, borders |
| Dark Red | `#FF3B6B` | Bearish, negative, SELL |
| Amber | `#F59E0B` | Caution, HOLD, neutral |
| Page BG | `#070B14` | Dark near-black background |
| Card BG | `#0D1117` | Dashboard card (GitHub dark) |
| Text | `#C9D1D9` | Body text |

### Candlestick Chart — 3 Modes
- **🕯 Candle** — OHLC candlesticks with S&R zone overlays
- **📈 Line** — Clean price line
- **📊 S&R** — Highlighted support and resistance zones

Timeframes: 1D · 1W · 1M · 3M · 6M · 1Y · 5Y

### Chart Patterns Detected (automatically)
| Pattern | Direction | Signal |
|---|---|---|
| VCP (Volatility Contraction) | Bullish | Pre-breakout setup — key Minervini signal |
| Double Bottom | Bullish | Reversal at support |
| Head & Shoulders | Bearish | Reversal at resistance |
| Cup & Handle | Bullish | Continuation breakout |
| Bullish Flag | Bullish | Pullback in uptrend |
| Bearish Flag | Bearish | Bounce in downtrend |
| Doji | Neutral | Indecision — watch next candle |
| Hammer | Bullish | Reversal candle after downtrend |
| Shooting Star | Bearish | Reversal candle after uptrend |

### Support & Resistance Zones
Detected algorithmically from swing highs and lows:
- Minimum 2 touches to qualify as a zone
- Zones within 1% of each other are merged
- 4 resistance zones above + 4 support zones below current price
- Displayed as coloured lines on the candlestick chart

---

## Indicators Computed

All computed from raw OHLCV. No external TA library.

| Indicator | Method | Period |
|---|---|---|
| RSI | Wilder smoothing | 14 |
| MACD | EMA-based | 12, 26, 9 |
| ADX | Wilder DMI | 14 |
| Stochastic RSI | RSI of RSI | 14, 14, K=3, D=3 |
| CCI | Classic formula | 20 |
| VWAP | Price × Volume weighted | Intraday |
| SMA / EMA | Rolling / Exponential | 9, 20, 50, 100, 200 |
| Pivot Points | Classic daily | S3 S2 S1 Pivot R1 R2 R3 |
| Minervini SEPA | 6 filters | Price vs DMA + RS + 52W |
| Price Returns | % change | 1D 2D 5D 7D 1W 1M 2M 6M |
| CAGR | Annualised from series | From available EOD |
| S&R Zones | Swing high/low detection | Window=3, Min touches=2 |
| Chart Patterns | Rule-based detection | 9 pattern types |

---

## PE & Valuation Analysis

### PE vs History
```
Current PE        → from financials.json
5Y Mean PE        → average of last 5 annual PE values
10Y Mean PE       → average of last 10 annual PE values
Sector PE         → built-in sector benchmark table
Peer PE           → peer list per sector (queried symbol excluded)

Verdict:
  Current < 85% of 5Y mean  → CHEAP ✅
  Current 85–110% of 5Y mean → FAIR VALUE
  Current 110–130% of 5Y mean → SLIGHTLY EXPENSIVE
  Current > 130% of 5Y mean  → EXPENSIVE ⚠️
```

### PEG Ratio
```
PEG = Current PE / EPS CAGR (5Y)

PEG < 1.0  → Growth available at a discount — very attractive
PEG 1–1.5  → Fair growth-adjusted valuation
PEG 1.5–2.5 → Paying premium for growth
PEG > 2.5  → Very expensive for the growth rate
```

---

## Institutional Value Analysis (New)

Scores the stock 0–100 based on:

| Factor | Max Points |
|---|---|
| Revenue CAGR 5Y (≥20% = excellent) | +15 |
| PAT CAGR 5Y (≥25% = excellent) | +15 |
| Average ROE (≥20% = high quality) | +10 |
| PE vs 5Y mean (cheap = bonus) | +15 |
| PEG ratio (< 1 = large bonus) | +15 |
| FCF consistency | +8 |

**Verdict:**
- 80–100 → **STRONG BUY 💚 (Institutional Grade)**
- 65–79 → **BUY 🟢 (Attractive Valuation)**
- 50–64 → **HOLD 🟡 (Fair Value)**
- 35–49 → **REDUCE 🟠 (Expensive)**
- 0–34 → **AVOID 🔴 (Overvalued / Deteriorating)**

---

## Data Sources

All data from `github.com/MarketVeda/nse-market-db`:

| Data | File | Refreshed |
|---|---|---|
| Live price, OHLCV, Bid/Ask | `data/live/latest.json` | Hourly 9:15–15:30 IST |
| EOD close, DMAs, RS, 52W | `data/daily/YYYY-MM-DD.json` | 4:00 PM IST |
| 15-min intraday candles | `data/intraday/YYYY-MM-DD.json` | 4:00 PM IST |
| F&O Open Interest | `data/fno_oi/YYYY-MM-DD.json` | 4:00 PM IST |
| Delivery % | `data/delivery/YYYY-MM-DD.json` | 4:00 PM IST |
| Fundamentals (12yr P&L) | `data/financials/financials.json` | 4:30 PM IST |
| News & Announcements | `data/news/news.json` | Hourly |

---

## Relationship to nse-market-db

```
nse-market-db  (automated data pipeline — runs daily + hourly)
      ↓  pushes JSON files to GitHub
market-veda-dashboard  (on-demand dashboard — runs when you trigger it)
      ↓  reads JSON → computes → generates HTML → publishes to GitHub Pages
Browser  (open URL directly — no download needed)
```

---

## Notes

1. **RSI/MACD/ADX accuracy** improves as nse-market-db accumulates more days of EOD data. With 2 days it shows N/A; with 15+ trading days all indicators work correctly.

2. **Candlestick chart** shows true OHLC candles for 1Y timeframe using EOD data. Other timeframes use line charts.

3. **S&R zones** are detected from swing highs and lows in available EOD data. More data = more accurate zones.

4. **PEG ratio** is computed from EPS CAGR in `financials.json`. If screener.in data is incomplete, it shows N/A.

5. **Artifact expiry**: The GitHub Actions artifact (zip backup) expires in 1 day, but the GitHub Pages URL is permanent.

---

## Connect Claude as a Skill

See `SKILL.md` for full instructions. In short:

1. Share your GitHub PAT token with Claude (scope: `repo` + `workflow`)
2. Say: *"give me RELIANCE dashboard"*
3. Claude triggers the workflow via API and gives you the direct URL

---

*MarketVeda · Knowledge Behind Every Trade · June 2026*

---

## Connecting AI Assistants

See **SKILL.md** for complete instructions. Quick summary:

| AI Platform | How to Connect |
|---|---|
| Claude Mobile App | Share PAT token → say "give me CGPOWER dashboard" → Claude triggers and sends you the URL |
| Claude Web | Same as mobile — works identically |
| ChatGPT | Configure as a ChatGPT Action using the GitHub API endpoint in SKILL.md |
| Gemini | Use Gemini Extensions or function calling with the API from SKILL.md |
| Any chatbot | POST to GitHub API from your backend — PAT stored server-side |
| iOS/Android shortcut | Create an HTTP Request shortcut — no AI needed |

### Fastest way from your mobile
1. Open Claude mobile app
2. Type: *"give me TITAN dashboard"*
3. Claude triggers GitHub Actions automatically
4. Claude sends you the direct link
5. Tap the link — dashboard opens in your phone browser instantly

