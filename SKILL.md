# SKILL: MarketVeda Dashboard Generator

**Repo:** `github.com/MarketVeda/market-veda-dashboard`
**When to use:** User asks for a stock dashboard, stock analysis, or "give me SYMBOL dashboard"

---

## What This Does

Generates a complete HTML dashboard for any NSE stock symbol by triggering a GitHub Actions workflow. The workflow fetches live data, computes all indicators, and produces a self-contained HTML file (~160 KB) the user downloads and opens.

Works for any symbol in NIFTY500 or FnO universe.

---

## How to Trigger (GitHub Actions API)

```bash
curl -X POST \
  -H "Authorization: token GITHUB_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/MarketVeda/market-veda-dashboard/actions/workflows/dashboard.yml/dispatches \
  -d '{"ref":"main","inputs":{"symbol":"SYMBOL_HERE"}}'
```

Replace `SYMBOL_HERE` with the NSE symbol (e.g. `CGPOWER`, `RELIANCE`, `HDFCBANK`).

---

## How to Check Status

```bash
curl -H "Authorization: token GITHUB_PAT" \
  https://api.github.com/repos/MarketVeda/market-veda-dashboard/actions/runs?per_page=1
```

Look for `"status": "completed"` and `"conclusion": "success"`.

---

## How to Get the Download URL

```bash
# Get run ID from status check, then:
curl -H "Authorization: token GITHUB_PAT" \
  https://api.github.com/repos/MarketVeda/market-veda-dashboard/actions/runs/RUN_ID/artifacts
```

Returns artifact download URL. Artifact name: `MarketVeda-SYMBOL`.

---

## Simpler: Tell the User to Do It From GitHub Web UI

If API triggering is not available, give the user these steps:
1. Open `github.com/MarketVeda/market-veda-dashboard`
2. Click **Actions** → **dashboard** → **Run workflow**
3. Enter symbol (e.g. `TITAN`)
4. Click **Run workflow**
5. Wait ~60 seconds → click completed run → **Artifacts** → download

---

## What the Dashboard Contains

5 rows of panels:

**Row 1:** Overview | Live Price + OHLCV | Interactive Chart (1D–5Y) | Technical Summary (RSI/MACD/ADX/StochRSI/CCI/Minervini)

**Row 2:** Moving Averages (20/50/100/200 SMA+EMA) | Valuation Metrics | Volume Analysis | Risk Analysis (5 categories)

**Row 3:** 5-Year Financial Summary | Key Triggers (positive/negative) | Support & Resistance (S3–R3 pivots) | BUY/HOLD/SELL Recommendation

**Row 4:** 8-Quarter Results Tracker | Analyst Sentiment (donut chart) | Notes

**Row 5 (NEW):** Price Move History (1D/2D/5D/7D/1W/1M/2M/6M + CAGR targets) | PE Analysis (current vs 5Y/10Y mean, sector, peers) | Entry/Exit Strategy | OI & Delivery

---

## Important Notes

- **No symbol hardcoding.** Works for any NSE symbol. Company name and sector are read dynamically from `financials.json`.
- **No secrets required.** Logo is embedded in `build.py`. No `MARKETVEDA_LOGO_B64` secret needed.
- **No local machine.** Everything runs on GitHub Actions. User only needs a browser.
- **Artifact expires in 24 hours.** User should download immediately after generation.
- **Data freshness:** Live price from latest hourly snapshot. EOD data from last market close. Financials updated 4:30 PM IST daily.

---

## Example User Requests → Action

| User says | Claude does |
|---|---|
| "give me CGPOWER dashboard" | Trigger workflow with symbol=CGPOWER |
| "dashboard for Reliance" | Trigger workflow with symbol=RELIANCE |
| "analyse HDFCBANK for me" | Trigger workflow with symbol=HDFCBANK |
| "stock report for Titan" | Trigger workflow with symbol=TITAN |
| "generate dashboard" (no symbol) | Ask: "Which NSE symbol?" |
