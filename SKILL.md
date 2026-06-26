# SKILL: MarketVeda Dashboard Generator

**Repository:** `github.com/MarketVeda/market-veda-dashboard`  
**Works with:** Claude (mobile app, web, API) · ChatGPT · Gemini · Any AI with API access  
**Purpose:** Generate a complete NSE stock intelligence dashboard for any symbol on demand

---

## TRIGGER PHRASES

When the user says any of these → run the workflow:

```
"give me [SYMBOL] dashboard"
"generate dashboard for [SYMBOL]"
"[SYMBOL] dashboard"
"dashboard [SYMBOL]"
"analyse [SYMBOL]"
"[SYMBOL] report"
"show me [SYMBOL]"
"stock analysis for [SYMBOL]"
```

If no symbol is specified → ask: **"Which NSE symbol? (e.g. CGPOWER, RELIANCE, HDFCBANK)"**

---

## STEP 1 — TRIGGER THE GITHUB ACTIONS WORKFLOW

### API Call (for Claude/ChatGPT/Gemini with tool/API access)

```
METHOD: POST
URL: https://api.github.com/repos/MarketVeda/market-veda-dashboard/actions/workflows/dashboard.yml/dispatches
HEADERS:
  Authorization: token GITHUB_PAT_TOKEN
  Accept: application/vnd.github.v3+json
  Content-Type: application/json
BODY:
  {
    "ref": "main",
    "inputs": {
      "symbol": "SYMBOL_HERE"
    }
  }
```

A successful trigger returns **HTTP 204** (No Content) — this is correct, not an error.

### For Claude Mobile App (no API tool access)
If Claude cannot make direct API calls, give the user this exact URL to open in their browser:

```
https://github.com/MarketVeda/market-veda-dashboard/actions/workflows/dashboard.yml
```

Then say:
> "Tap **Run workflow** → type **SYMBOL** → tap **Run workflow** (green button). Takes ~45 seconds. The dashboard URL will appear in the Summary."

---

## STEP 2 — WAIT FOR COMPLETION (~30–45 seconds)

Check workflow status:

```
METHOD: GET
URL: https://api.github.com/repos/MarketVeda/market-veda-dashboard/actions/runs?per_page=1
HEADERS:
  Authorization: token GITHUB_PAT_TOKEN
```

Poll every 10 seconds until:
```json
{
  "status": "completed",
  "conclusion": "success"
}
```

---

## STEP 3 — GIVE THE USER THE DIRECT URL

Construct the dashboard URL:

```
https://marketveda.github.io/market-veda-dashboard/SYMBOL_YYYY-MM-DD.html
```

Get today's date in IST (UTC+5:30) → format as YYYY-MM-DD.

**Example:**
```
https://marketveda.github.io/market-veda-dashboard/CGPOWER_2026-06-26.html
```

**All dashboards index:**
```
https://marketveda.github.io/market-veda-dashboard/
```

---

## WHAT TO SAY TO THE USER

### After triggering:
> "Generating your **CGPOWER** dashboard now — takes about 45 seconds..."

### After success:
> ✅ **CGPOWER Dashboard Ready**
>
> 🔗 Open directly in your browser (no download needed):
> `https://marketveda.github.io/market-veda-dashboard/CGPOWER_2026-06-26.html`
>
> 📋 All your past dashboards: `https://marketveda.github.io/market-veda-dashboard/`

### If workflow fails:
> "The dashboard generation encountered an error. Please try running it again from GitHub Actions, or let me know and I'll help debug."

---

## GITHUB PAT TOKEN

The user needs a GitHub Personal Access Token with these scopes:
- `repo` (full repository access)
- `workflow` (trigger GitHub Actions)

**How to create one:**
1. Go to `github.com/settings/tokens`
2. Click **Generate new token (classic)**
3. Name: `MarketVeda Dashboard`
4. Check: `repo` and `workflow`
5. Click **Generate token**
6. Copy the token — shown only once

**Token expiry:** Tokens last 1 year. The token `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` expires **June 2027**.

---

## VALID SYMBOLS

Any NSE stock in NIFTY 500 or F&O universe. Examples:

**Large Cap:** RELIANCE · HDFCBANK · ICICIBANK · TCS · INFY · SBIN · BAJFINANCE · KOTAKBANK  
**Mid Cap:** CGPOWER · Dixon · KAYNES · CDSL · ANGELONE · BSE · PERSISTENT  
**FMCG:** HINDUNILVR · NESTLEIND · MARICO · DABUR · BRITANNIA  
**Pharma:** SUNPHARMA · DRREDDY · CIPLA · DIVISLAB · LUPIN  
**Auto:** MARUTI · M&M · TVSMOTOR · BAJAJ-AUTO · EICHERMOT  
**IT:** TCS · INFY · WIPRO · TECHM · HCLTECH · MPHASIS  
**Energy:** RELIANCE · NTPC · POWERGRID · TATAPOWER · ONGC  
**Defence:** HAL · BEL · BDL · GRSE · MAZDOCK  

If symbol not recognised → still try. The dashboard will show available data and mark missing fields as N/A.

---

## DASHBOARD CONTENTS

The HTML dashboard has 5 rows:

| Row | What's Inside |
|---|---|
| **Row 1** | Company overview · Live price + OHLCV · **Candlestick chart with S&R zones** · Technical summary (RSI/MACD/ADX/StochRSI/CCI/RS/Minervini) |
| **Row 2** | Moving averages (9/20/50/100/200 SMA+EMA) · Valuation metrics · Volume analysis · Risk analysis (5 categories) |
| **Row 3** | 5-year financials table · Key triggers (positive + negative) · Support & Resistance pivots · BUY/HOLD/SELL recommendation |
| **Row 4** | 8-quarter results tracker · Analyst sentiment donut chart · Notes & insights |
| **Row 5** | Price move history (1D/2D/5D/7D/1W/1M/2M/6M + CAGR targets) · PE analysis (current vs 5Y/10Y mean + sector + peers + PEG) · Entry/Exit strategy + **chart patterns detected** · **Institutional value analysis** |

### New in This Version
- **Dark neon design** — dark background with neon green/red accents
- **Candlestick chart** — OHLC candles with S&R zone overlays, 3 modes (Candle/Line/S&R)
- **9 chart patterns** auto-detected — VCP, Double Bottom, Cup & Handle, H&S, Bull/Bear Flag, Doji, Hammer, Shooting Star
- **S&R zones** — detected from swing highs/lows with confluence scoring
- **PEG ratio** — PE ÷ EPS CAGR, key growth-adjusted valuation metric
- **Institutional value score** — 0–100 score based on Revenue CAGR, PAT CAGR, ROE, PE vs history, PEG, FCF

---

## CONNECTING FROM DIFFERENT AI PLATFORMS

### Claude (Mobile App or Web)
Claude can trigger this workflow directly via its tool/API access if given the PAT token. On mobile, Claude can also guide the user to open the GitHub Actions URL and tap Run workflow.

### ChatGPT (with Code Interpreter or Actions)
Use the API call in Step 1 above inside a ChatGPT Action or function call. Configure:
- **Action URL:** `https://api.github.com`
- **Auth:** Bearer token (PAT)
- **Endpoint:** `/repos/MarketVeda/market-veda-dashboard/actions/workflows/dashboard.yml/dispatches`

### Gemini / Bard
Use the same API call via Gemini Extensions or function calling.

### Any Custom Chatbot
POST the API call from your backend server. The PAT token should be stored server-side, never exposed to frontend.

### Simple Mobile Shortcut (no AI needed)
Create an iOS Shortcut or Android HTTP Request shortcut that POSTs to the GitHub API with your PAT and a symbol input. Opens the dashboard URL in Safari/Chrome immediately after.

---

## QUICK REFERENCE

| Action | URL / Command |
|---|---|
| Trigger workflow | `POST /repos/MarketVeda/market-veda-dashboard/actions/workflows/dashboard.yml/dispatches` |
| Check status | `GET /repos/MarketVeda/market-veda-dashboard/actions/runs?per_page=1` |
| Dashboard URL | `https://marketveda.github.io/market-veda-dashboard/SYMBOL_YYYY-MM-DD.html` |
| All dashboards | `https://marketveda.github.io/market-veda-dashboard/` |
| GitHub repo | `https://github.com/MarketVeda/market-veda-dashboard` |
| GitHub Actions | `https://github.com/MarketVeda/market-veda-dashboard/actions` |

---

## IMPORTANT NOTES

1. **RSI/MACD/ADX** show N/A until 15+ trading days of EOD data accumulate in nse-market-db. This resolves automatically over time.

2. **Dashboard URL is permanent** — the GitHub Pages URL never expires. You can bookmark and share it.

3. **Each symbol generates a fresh file** named `SYMBOL_YYYY-MM-DD.html`. Running the same symbol twice on the same day overwrites the previous file.

4. **No ZIP file** — the dashboard opens directly in browser via GitHub Pages. No extraction needed.

5. **Logo is embedded** — no secrets or tokens needed at generation time. The MarketVeda logo is baked into `design.py`.

6. **Works offline** — once the HTML is open in your browser, it works fully offline (except the Chart.js CDN for the price chart).
