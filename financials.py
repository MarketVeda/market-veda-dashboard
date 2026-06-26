"""
financials.py — Fundamentals, PE Analysis & Institutional Value Research
Computes 5Y/8Q tables, PE vs history, value metrics, institutional-grade analysis.
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


def cagr(vals, years):
    v=[x for x in vals if x and isinstance(x,(int,float)) and x>0]
    if len(v)<2 or years<=0: return None
    return round(((v[-1]/v[0])**(1/years)-1)*100,1)


def pe_analysis(fin, cur_pe, sector, sym):
    rat=(fin.get("ratios") or {}).get("rows",{})
    pe_hist=[v for v in (rat.get("Price to Earning",{}) or rat.get("PE",{})).values()
             if isinstance(v,(int,float)) and v>0]
    pe5 =round(sum(pe_hist[-5:])/len(pe_hist[-5:]),1) if len(pe_hist)>=5 else None
    pe10=round(sum(pe_hist[-10:])/len(pe_hist[-10:]),1) if len(pe_hist)>=10 else (
         round(sum(pe_hist)/len(pe_hist),1) if pe_hist else None)
    sect_pe, peers = sector_pe_data(sector, sym)

    # Verdict
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
    """
    Institutional-grade value analysis:
    - Revenue + PAT CAGR assessment
    - Cash flow quality
    - PE vs PEG
    - Overall value score
    """
    if not annual:
        return {"score":0,"verdict":"Insufficient Data","remarks":[]}

    revs=[r["rev"] for r in annual if r.get("rev")]
    nps =[r["np"]  for r in annual if r.get("np")]
    epss=[r["eps"] for r in annual if r.get("eps")]
    roe_vals=[r["roe"] for r in annual if r.get("roe")]
    yrs=len(annual)-1 if len(annual)>1 else 1

    rev_cagr=cagr(revs,yrs); np_cagr=cagr(nps,yrs); eps_cagr=cagr(epss,yrs)
    avg_roe=round(sum(float(r) for r in roe_vals)/len(roe_vals),1) if roe_vals else None

    cur_pe=pe_an.get("cur_pe"); pe5=pe_an.get("pe5")

    # PEG ratio
    peg=None
    if cur_pe and eps_cagr and eps_cagr>0:
        peg=round(float(cur_pe)/eps_cagr,2)

    remarks=[]
    score=50  # base

    # Revenue growth
    if rev_cagr:
        if rev_cagr>=20:   remarks.append(f"✅ Revenue CAGR {rev_cagr}% (5Y) — Exceptional growth"); score+=15
        elif rev_cagr>=12: remarks.append(f"✅ Revenue CAGR {rev_cagr}% (5Y) — Strong growth"); score+=10
        elif rev_cagr>=6:  remarks.append(f"⚡ Revenue CAGR {rev_cagr}% (5Y) — Moderate growth"); score+=3
        else:              remarks.append(f"⚠️ Revenue CAGR {rev_cagr}% (5Y) — Slow growth"); score-=5

    # Profit growth
    if np_cagr:
        if np_cagr>=25:   remarks.append(f"✅ PAT CAGR {np_cagr}% (5Y) — Excellent profit growth"); score+=15
        elif np_cagr>=15: remarks.append(f"✅ PAT CAGR {np_cagr}% (5Y) — Good profit growth"); score+=8
        elif np_cagr>=5:  remarks.append(f"⚡ PAT CAGR {np_cagr}% (5Y) — Moderate profit growth"); score+=2
        else:             remarks.append(f"⚠️ PAT CAGR {np_cagr}% (5Y) — Weak profit growth"); score-=8

    # ROE
    if avg_roe:
        if avg_roe>=20:   remarks.append(f"✅ Avg ROE {avg_roe}% — High-quality business"); score+=10
        elif avg_roe>=15: remarks.append(f"⚡ Avg ROE {avg_roe}% — Decent capital efficiency"); score+=5
        else:             remarks.append(f"⚠️ Avg ROE {avg_roe}% — Below ideal (want >15%)"); score-=3

    # PE vs history
    if cur_pe and pe5:
        ratio=float(cur_pe)/float(pe5)
        if ratio<0.85:   remarks.append(f"✅ PE {cur_pe}x vs 5Y mean {pe5}x — Cheap vs history"); score+=15
        elif ratio<1.10: remarks.append(f"⚡ PE {cur_pe}x vs 5Y mean {pe5}x — Fairly priced"); score+=5
        else:            remarks.append(f"⚠️ PE {cur_pe}x vs 5Y mean {pe5}x — Expensive vs history"); score-=10

    # PEG
    if peg:
        if peg<1:        remarks.append(f"✅ PEG {peg}x (<1) — Growth available at a discount!"); score+=15
        elif peg<1.5:    remarks.append(f"⚡ PEG {peg}x (1–1.5) — Fair growth-adjusted valuation"); score+=5
        elif peg<2.5:    remarks.append(f"⚠️ PEG {peg}x (>1.5) — Paying premium for growth"); score-=5
        else:            remarks.append(f"🔴 PEG {peg}x (>2.5) — Very expensive for growth rate"); score-=15

    # FCF check
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
        "avg_roe":avg_roe,"peg":peg,
        "years":yrs,
    }


def process(fin, sym, sector):
    if not fin:
        return {"annual":[],"qtrs":[],"pe":{},
                "km":{},"value":{"score":0,"verdict":"No data","remarks":[]}}
    km=fin.get("key_metrics") or {}
    cur_pe=km.get("P/E") or km.get("P/E Ratio") or km.get("Price to Earning")
    annual=extract_annual(fin)
    qtrs=extract_quarterly(fin)
    pe=pe_analysis(fin,cur_pe,sector,sym)
    va=value_analysis(annual,km,pe)
    yrs=len(annual)-1 if len(annual)>1 else 1
    revs=[r["rev"] for r in annual if r.get("rev")]
    nps =[r["np"]  for r in annual if r.get("np")]
    return {
        "annual":annual,"qtrs":qtrs,"pe":pe,"km":km,
        "value":va,
        "rev_cagr":cagr(revs,yrs),"np_cagr":cagr(nps,yrs),
        "sector":sector,
    }
