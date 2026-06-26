"""
financials.py — Fundamentals, PE Analysis, Institutional Value Research
                + Promoter/DII/FII Shareholding Analysis
Computes 5Y/8Q tables, PE vs history, value metrics, institutional-grade analysis,
and shareholding pattern changes (Promoter / DII / FII) as key price drivers.
"""

SECTOR_PE = {
    "CAPITAL GOODS":    {"pe":55,"peers":{"ABB":72,"SIEMENS":74,"BHEL":45,"BEL":50,"CGPOWER":115}},
    "IT":               {"pe":28,"peers":{"TCS":30,"INFY":25,"WIPRO":22,"TECHM":20,"HCLTECH":26}},
    "BANKING":          {"pe":14,"peers":{"HDFCBANK":18,"ICICIBANK":17,"SBIN":11,"KOTAKBANK":20}},
    "NBFC":             {"pe":20,"peers":{"BAJFINANCE":30,"CHOLAFIN":25,"MUTHOOTFIN":15}},
    "PHARMA":           {"pe":30,"peers":{"SUNPHARMA":38,"DRREDDY":25,"CIPLA":32,"DIVISLAB":40}},
    "FMCG":             {"pe":55,"peers":{"HINDUNILVR":60,"NESTLEIND":75,"MARICO":50,"DABUR":52}},
    "AUTO":             {"pe":24,"peers":{"MARUTI":28,"M&M":32,"BAJAJ-AUTO":30,"TVSMOTOR":38}},
    "AUTO ANCILLARY":   {"pe":22,"peers":{"BOSCHLTD":45,"MOTHERSON":30,"TIINDIA":35}},
    "ENERGY":           {"pe":12,"peers":{"RELIANCE":25,"ONGC":8,"BPCL":10,"IOC":7}},
    "POWER":            {"pe":20,"peers":{"NTPC":15,"POWERGRID":14,"TATAPOWER":30,"JSWENERGY":25}},
    "REALTY":           {"pe":35,"peers":{"DLF":45,"GODREJPROP":60,"LODHA":30,"PRESTIGE":28}},
    "METALS":           {"pe":12,"peers":{"TATASTEEL":10,"JSWSTEEL":15,"HINDALCO":12,"SAIL":8}},
    "CEMENT":           {"pe":28,"peers":{"ULTRACEMCO":35,"SHREECEM":32,"AMBUJACEM":28}},
    "TELECOM":          {"pe":40,"peers":{"BHARTIARTL":55,"INDUSTOWER":30}},
    "INSURANCE":        {"pe":35,"peers":{"HDFCLIFE":80,"SBILIFE":70,"ICICIPRULI":55}},
    "DEFENCE":          {"pe":48,"peers":{"HAL":48,"BEL":50,"BDL":55,"GRSE":42}},
    "CONSUMER DURABLES":{"pe":45,"peers":{"HAVELLS":55,"DIXON":90,"VOLTAS":50}},
    "CHEMICALS":        {"pe":28,"peers":{"PIDILITIND":75,"DEEPAKNTR":18,"NAVINFLUOR":30}},
    "INFRASTRUCTURE":   {"pe":22,"peers":{"LT":35,"KPIL":30,"NCC":18,"RVNL":25}},
    "DEFAULT":          {"pe":25,"peers":{}},
}

def sector_pe_data(sector, sym):
    su=(sector or "").upper()
    for k,v in SECTOR_PE.items():
        if k in su or su in k:
            return v["pe"], {p:pe for p,pe in v["peers"].items() if p!=sym.upper()}
    return SECTOR_PE["DEFAULT"]["pe"],{}


def extract_annual(fin, n=5):
    pl=fin.get("profit_loss") or {}
    hdrs=pl.get("headers",[])[-n:]
    rows=pl.get("rows",{})
    rat=(fin.get("ratios") or {}).get("rows",{})
    result=[]
    for yr in hdrs:
        result.append({
            "yr":yr,
            "rev":rows.get("Sales",{}).get(yr) or rows.get("Revenue",{}).get(yr),
            "op": rows.get("Operating Profit",{}).get(yr),
            "opm":rows.get("OPM %",{}).get(yr),
            "np": rows.get("Net Profit",{}).get(yr) or rows.get("Profit after tax",{}).get(yr),
            "eps":rows.get("EPS in Rs",{}).get(yr) or rows.get("EPS",{}).get(yr),
            "roe":rat.get("ROE %",{}).get(yr),
            "fcf":rat.get("Free Cash Flow",{}).get(yr),
        })
    return result


def extract_quarterly(fin, n=8):
    qr=fin.get("quarterly_results") or {}
    hdrs=qr.get("headers",[])[-n:]
    rows=qr.get("rows",{})
    result=[]
    for q in hdrs:
        result.append({
            "q":q,
            "rev":rows.get("Sales",{}).get(q) or rows.get("Revenue",{}).get(q),
            "np": rows.get("Net Profit",{}).get(q) or rows.get("Profit after tax",{}).get(q),
            "eps":rows.get("EPS in Rs",{}).get(q),
            "opm":rows.get("OPM %",{}).get(q),
        })
    return result


def extract_shareholding(fin, n=8):
    """
    Extract Promoter / DII / FII shareholding across last n quarters.
    Returns list of dicts with quarter and % holdings.
    Also computes trend (increasing/decreasing/stable) for each category.
    """
    sh = fin.get("shareholding") or {}
    hdrs = sh.get("headers", [])[-n:]
    rows = sh.get("rows", {})

    result = []
    for q in hdrs:
        entry = {"q": q}
        # Promoter — various field names used (screener.in uses a trailing "+")
        prom = (rows.get("Promoters+", {}).get(q) or
                rows.get("Promoters", {}).get(q) or
                rows.get("Promoter", {}).get(q) or
                rows.get("Promoter & Promoter Group", {}).get(q))
        # FII / FPI
        fii  = (rows.get("FIIs+", {}).get(q) or
                rows.get("FII", {}).get(q) or
                rows.get("FPIs", {}).get(q) or
                rows.get("Foreign Institutional Investors", {}).get(q) or
                rows.get("FII + FPI", {}).get(q))
        # DII
        dii  = (rows.get("DIIs+", {}).get(q) or
                rows.get("DII", {}).get(q) or
                rows.get("Domestic Institutional Investors", {}).get(q) or
                rows.get("Mutual Funds", {}).get(q))
        # Retail / Public
        pub  = (rows.get("Public+", {}).get(q) or
                rows.get("Public", {}).get(q) or
                rows.get("Retail", {}).get(q))

        entry["promoter"] = round(float(prom), 2) if prom else None
        entry["fii"]      = round(float(fii),  2) if fii  else None
        entry["dii"]      = round(float(dii),  2) if dii  else None
        entry["public"]   = round(float(pub),  2) if pub  else None
        result.append(entry)
    return result


def shareholding_analysis(sh_data):
    """
    Institutional-grade shareholding trend analysis.
    Bullish signals: Promoter not reducing, DII/FII increasing.
    Returns score impact, trend strings, remarks, and colour codes.
    """
    if not sh_data or len(sh_data) < 2:
        return {
            "promoter_trend": "N/A", "fii_trend": "N/A", "dii_trend": "N/A",
            "promoter_color": "#9B9FB0", "fii_color": "#9B9FB0", "dii_color": "#9B9FB0",
            "promoter_chg": None, "fii_chg": None, "dii_chg": None,
            "score_impact": 0, "remarks": [], "data": sh_data,
            "latest": {}, "signal": "NEUTRAL",
        }

    def trend(vals_raw, label):
        vals = [v for v in vals_raw if v is not None]
        if len(vals) < 2:
            return "N/A", "#9B9FB0", 0, None
        chg = round(vals[-1] - vals[0], 2)
        recent_chg = round(vals[-1] - vals[-2], 2)
        if chg > 0.5:
            return f"▲ Increasing ({chg:+.2f}%)", "#00E5FF", +8, chg
        elif chg < -0.5:
            return f"▼ Decreasing ({chg:+.2f}%)", "#E91E8C", -6, chg
        else:
            return f"→ Stable ({chg:+.2f}%)", "#9C27B0", 0, chg

    prom_vals = [d.get("promoter") for d in sh_data]
    fii_vals  = [d.get("fii")      for d in sh_data]
    dii_vals  = [d.get("dii")      for d in sh_data]

    pt, pc, ps, pchg = trend(prom_vals, "Promoter")
    ft, fc, fs, fchg = trend(fii_vals,  "FII")
    dt, dc, ds, dchg = trend(dii_vals,  "DII")

    score_impact = ps + fs + ds
    remarks = []
    latest = sh_data[-1] if sh_data else {}

    # Promoter analysis
    prom_latest = latest.get("promoter")
    if prom_latest:
        if prom_latest >= 60:
            remarks.append(f"✅ Promoter holding {prom_latest}% — High conviction, strong ownership")
        elif prom_latest >= 45:
            remarks.append(f"⚡ Promoter holding {prom_latest}% — Decent promoter confidence")
        else:
            remarks.append(f"⚠️ Promoter holding {prom_latest}% — Low promoter stake, watch closely")

    if pchg is not None:
        if pchg > 1:
            remarks.append(f"✅ Promoter BUYING — increased {pchg:+.2f}% (last {len(prom_vals)} qtrs) — Bullish signal")
        elif pchg < -1:
            remarks.append(f"⚠️ Promoter SELLING — reduced {pchg:+.2f}% — Caution signal")
        elif abs(pchg) <= 1:
            remarks.append(f"⚡ Promoter stake stable ({pchg:+.2f}%) — No major change")

    # FII analysis
    fii_latest = latest.get("fii")
    if fchg is not None:
        if fchg > 0.5:
            remarks.append(f"✅ FII ACCUMULATING — {fchg:+.2f}% increase — Smart money buying")
        elif fchg < -0.5:
            remarks.append(f"⚠️ FII REDUCING — {fchg:+.2f}% exit — Foreign outflows signal")
        else:
            remarks.append(f"⚡ FII stake stable at {fii_latest or 'N/A'}%")

    # DII analysis
    dii_latest = latest.get("dii")
    if dchg is not None:
        if dchg > 0.5:
            remarks.append(f"✅ DII BUYING — {dchg:+.2f}% increase — Domestic funds accumulating")
        elif dchg < -0.5:
            remarks.append(f"⚠️ DII REDUCING — {dchg:+.2f}% — Domestic institutional exit")
        else:
            remarks.append(f"⚡ DII stake stable at {dii_latest or 'N/A'}%")

    # Overall signal
    pos_signals = sum(1 for x in [pchg, fchg, dchg] if x is not None and x > 0.3)
    neg_signals = sum(1 for x in [pchg, fchg, dchg] if x is not None and x < -0.3)
    if pos_signals >= 2:
        signal = "BULLISH — Institutions accumulating"
    elif neg_signals >= 2:
        signal = "BEARISH — Institutions reducing"
    elif fchg is not None and fchg > 0.5 and (dchg is not None and dchg > 0):
        signal = "BULLISH — Both FII & DII buying"
    else:
        signal = "NEUTRAL — Mixed institutional activity"

    return {
        "promoter_trend": pt, "fii_trend": ft, "dii_trend": dt,
        "promoter_color": pc, "fii_color": fc, "dii_color": dc,
        "promoter_chg": pchg, "fii_chg": fchg, "dii_chg": dchg,
        "score_impact": score_impact, "remarks": remarks,
        "data": sh_data, "latest": latest, "signal": signal,
    }


def cagr(vals, years):
    v=[x for x in vals if x and isinstance(x,(int,float)) and x>0]
    if len(v)<2 or years<=0: return None
    return round(((v[-1]/v[0])**(1/years)-1)*100,2)


_MON={"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,
      "Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

def hist_pe_from_prices(eod, annual):
    """
    Derive per-financial-year average PE from our own daily price history and the
    annual EPS series (avg close over the FY / EPS for that year). Lets us show a
    5Y / 10Y mean PE even when the source ratios table has no PE history row.
    """
    import datetime
    if not eod or not annual:
        return []
    closes=[(e["date"], e["c"]) for e in eod if e.get("c")]
    if not closes:
        return []
    series=[]
    for r in annual:
        yr=str(r.get("yr","")).split(); eps=r.get("eps")
        if len(yr)!=2 or not isinstance(eps,(int,float)) or eps<=0:
            continue
        mon=_MON.get(yr[0]);
        if not mon:
            continue
        y=int(yr[1])
        end=datetime.date(y, mon, 28).isoformat()
        start=datetime.date(y-1, mon, 1).isoformat()
        vals=[c for d,c in closes if start<=d<=end]
        if vals:
            series.append(round((sum(vals)/len(vals))/eps, 2))
    return series


def pe_analysis(fin, cur_pe, sector, sym, eod=None, annual=None):
    rat=(fin.get("ratios") or {}).get("rows",{})
    pe_hist=[v for v in (rat.get("Price to Earning",{}) or rat.get("PE",{})).values()
             if isinstance(v,(int,float)) and v>0]
    # Fallback: synthesise PE history from our price + EPS data when ratios lack it
    if len(pe_hist)<2:
        pe_hist=hist_pe_from_prices(eod, annual) or pe_hist
    pe5 =round(sum(pe_hist[-5:])/len(pe_hist[-5:]),2) if len(pe_hist)>=2 else None
    pe10=round(sum(pe_hist[-10:])/len(pe_hist[-10:]),2) if len(pe_hist)>=8 else None
    sect_pe, peers = sector_pe_data(sector, sym)

    if cur_pe and pe5:
        ratio=float(cur_pe)/float(pe5)
        if ratio<0.85:    v,vc,vs="CHEAP ✅","#00C896","Undervalued vs history — potential value buy"
        elif ratio<1.10:  v,vc,vs="FAIR VALUE","#F59E0B","Trading near historical average — fairly priced"
        elif ratio<1.30:  v,vc,vs="SLIGHTLY EXPENSIVE","#F59E0B","Modest premium to history — growth must justify"
        else:             v,vc,vs="EXPENSIVE ⚠️","#F43F5E","Significant premium — high growth expectations priced in"
    elif cur_pe and sect_pe:
        ratio=float(cur_pe)/float(sect_pe)
        if ratio<0.85:   v,vc,vs="CHEAP vs Sector ✅","#00C896","Trading below sector average — potential discount"
        elif ratio<1.20: v,vc,vs="IN-LINE with Sector","#F59E0B","Fairly valued relative to peers"
        else:            v,vc,vs="PREMIUM to Sector ⚠️","#F43F5E","Premium valuation — must justify with superior growth"
    else:
        v,vc,vs="N/A","#9CA3AF","Insufficient PE history"

    return {"cur_pe":cur_pe,"pe5":pe5,"pe10":pe10,"sect_pe":sect_pe,
            "peers":peers,"verdict":v,"vc":vc,"vs":vs}


def value_analysis(annual, km, pe_an):
    if not annual:
        return {"score":0,"verdict":"Insufficient Data","remarks":[]}

    revs=[r["rev"] for r in annual if r.get("rev")]
    nps =[r["np"]  for r in annual if r.get("np")]
    epss=[r["eps"] for r in annual if r.get("eps")]
    roe_vals=[r["roe"] for r in annual if r.get("roe")]
    yrs=len(annual)-1 if len(annual)>1 else 1

    rev_cagr=cagr(revs,yrs); np_cagr=cagr(nps,yrs); eps_cagr=cagr(epss,yrs)
    avg_roe=round(sum(float(r) for r in roe_vals)/len(roe_vals),2) if roe_vals else None

    cur_pe=pe_an.get("cur_pe"); pe5=pe_an.get("pe5")

    peg=None
    if cur_pe and eps_cagr and eps_cagr>0:
        peg=round(float(cur_pe)/eps_cagr,2)

    remarks=[]; score=50

    if rev_cagr:
        if rev_cagr>=20:   remarks.append(f"✅ Revenue CAGR {rev_cagr}% (5Y) — Exceptional growth"); score+=15
        elif rev_cagr>=12: remarks.append(f"✅ Revenue CAGR {rev_cagr}% (5Y) — Strong growth"); score+=10
        elif rev_cagr>=6:  remarks.append(f"⚡ Revenue CAGR {rev_cagr}% (5Y) — Moderate growth"); score+=3
        else:              remarks.append(f"⚠️ Revenue CAGR {rev_cagr}% (5Y) — Slow growth"); score-=5

    if np_cagr:
        if np_cagr>=25:   remarks.append(f"✅ PAT CAGR {np_cagr}% (5Y) — Excellent profit growth"); score+=15
        elif np_cagr>=15: remarks.append(f"✅ PAT CAGR {np_cagr}% (5Y) — Good profit growth"); score+=8
        elif np_cagr>=5:  remarks.append(f"⚡ PAT CAGR {np_cagr}% (5Y) — Moderate profit growth"); score+=2
        else:             remarks.append(f"⚠️ PAT CAGR {np_cagr}% (5Y) — Weak profit growth"); score-=8

    if avg_roe:
        if avg_roe>=20:   remarks.append(f"✅ Avg ROE {avg_roe}% — High-quality business"); score+=10
        elif avg_roe>=15: remarks.append(f"⚡ Avg ROE {avg_roe}% — Decent capital efficiency"); score+=5
        else:             remarks.append(f"⚠️ Avg ROE {avg_roe}% — Below ideal (want >15%)"); score-=3

    if cur_pe and pe5:
        ratio=float(cur_pe)/float(pe5)
        if ratio<0.85:   remarks.append(f"✅ PE {cur_pe}x vs 5Y mean {pe5}x — Cheap vs history"); score+=15
        elif ratio<1.10: remarks.append(f"⚡ PE {cur_pe}x vs 5Y mean {pe5}x — Fairly priced"); score+=5
        else:            remarks.append(f"⚠️ PE {cur_pe}x vs 5Y mean {pe5}x — Expensive vs history"); score-=10

    if peg:
        if peg<1:        remarks.append(f"✅ PEG {peg}x (<1) — Growth available at a discount!"); score+=15
        elif peg<1.5:    remarks.append(f"⚡ PEG {peg}x (1–1.5) — Fair growth-adjusted valuation"); score+=5
        elif peg<2.5:    remarks.append(f"⚠️ PEG {peg}x (>1.5) — Paying premium for growth"); score-=5
        else:            remarks.append(f"🔴 PEG {peg}x (>2.5) — Very expensive for growth rate"); score-=15

    fcfs=[r.get("fcf") for r in annual if r.get("fcf") and isinstance(r.get("fcf"),(int,float)) and r["fcf"]>0]
    if len(fcfs)>=3:
        remarks.append(f"✅ Positive FCF in {len(fcfs)}/{len(annual)} years — Self-funding growth"); score+=8
    elif len(fcfs)>=1:
        remarks.append(f"⚡ FCF positive in {len(fcfs)} years — Improving cash generation")

    score=max(0,min(100,score))

    if score>=80:    verdict="STRONG BUY 💚 (Institutional Grade)"
    elif score>=65:  verdict="BUY 🟢 (Attractive Valuation)"
    elif score>=50:  verdict="HOLD 🟡 (Fair Value)"
    elif score>=35:  verdict="REDUCE 🟠 (Expensive)"
    else:            verdict="AVOID 🔴 (Overvalued / Deteriorating)"

    return {
        "score":score,"verdict":verdict,"remarks":remarks,
        "rev_cagr":rev_cagr,"np_cagr":np_cagr,"eps_cagr":eps_cagr,
        "avg_roe":avg_roe,"peg":peg,"years":yrs,
    }


def process(fin, sym, sector, eod=None):
    if not fin:
        return {
            "annual":[],"qtrs":[],"pe":{},"km":{},
            "value":{"score":0,"verdict":"No data","remarks":[]},
            "shareholding":[],"sh_analysis":{
                "promoter_trend":"N/A","fii_trend":"N/A","dii_trend":"N/A",
                "promoter_color":"#9B9FB0","fii_color":"#9B9FB0","dii_color":"#9B9FB0",
                "promoter_chg":None,"fii_chg":None,"dii_chg":None,
                "score_impact":0,"remarks":[],"data":[],"latest":{},"signal":"N/A",
            }
        }
    km=fin.get("key_metrics") or {}
    # Prefer the actual reported screener PE ("Stock P/E") over any fallback value
    cur_pe=(km.get("Stock P/E") or km.get("P/E") or
            km.get("P/E Ratio") or km.get("Price to Earning"))
    annual=extract_annual(fin)
    qtrs=extract_quarterly(fin)
    pe=pe_analysis(fin,cur_pe,sector,sym,eod,annual)
    va=value_analysis(annual,km,pe)
    sh_data=extract_shareholding(fin)
    sh_analysis=shareholding_analysis(sh_data)

    # Incorporate shareholding score into value score
    combined_score = min(100, max(0, va["score"] + sh_analysis["score_impact"]))
    va["score"] = combined_score
    if combined_score >= 80:    va["verdict"] = "STRONG BUY 💚 (Institutional Grade)"
    elif combined_score >= 65:  va["verdict"] = "BUY 🟢 (Attractive Valuation)"
    elif combined_score >= 50:  va["verdict"] = "HOLD 🟡 (Fair Value)"
    elif combined_score >= 35:  va["verdict"] = "REDUCE 🟠 (Expensive)"
    else:                       va["verdict"] = "AVOID 🔴 (Overvalued / Deteriorating)"

    yrs=len(annual)-1 if len(annual)>1 else 1
    revs=[r["rev"] for r in annual if r.get("rev")]
    nps =[r["np"]  for r in annual if r.get("np")]
    return {
        "annual":annual,"qtrs":qtrs,"pe":pe,"km":km,
        "value":va,
        "rev_cagr":cagr(revs,yrs),"np_cagr":cagr(nps,yrs),
        "sector":sector,
        "shareholding":sh_data,
        "sh_analysis":sh_analysis,
    }
