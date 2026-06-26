"""
design.py — Complete MarketVeda Dashboard HTML Generator
- Dark neon design with teal/green accents
- Candlestick chart with S&R zones (matching reference images)
- Chart pattern tabs
- Institutional value analysis
"""
import json


def fv(v, pre="₹", suf="", na="N/A", dec=2):
    if v is None: return na
    try: return f"{pre}{float(v):,.{dec}f}{suf}"
    except: return str(v)

def fvol(v):
    if not v: return "N/A"
    v=int(v)
    if v>=10_000_000: return f"{v/10_000_000:.2f}Cr"
    if v>=100_000: return f"{v/100_000:.2f}L"
    if v>=1000: return f"{v/1000:.1f}K"
    return str(v)

def pct_c(v):
    if v is None: return "#9CA3AF"
    return "#00E87A" if float(v)>=0 else "#FF3B6B"

def pct_sign(v):
    if v is None: return ""
    return "+" if float(v)>=0 else ""


def build_chart_data(eod, candles, sym):
    months=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    def fd(s):
        p=s.split("-"); return f"{p[2]}{months[int(p[1])]}"

    # Candlestick data for EOD
    ohlcv=[]
    for e in eod:
        ohlcv.append({"t":fd(e["date"]),"o":e["o"],"h":e["h"],"l":e["l"],"c":e["c"],"v":e.get("v",0)})

    # Line data for timeframes
    cl=[(e["date"],e["c"]) for e in eod]
    n=len(cl)
    def sl(d): items=cl[-d:] if n>=d else cl; return [fd(x[0]) for x in items],[x[1] for x in items]
    l1d=[c.get("t",c.get("time",""))[:5] for c in candles]
    p1d=[c.get("c",c.get("close",0)) for c in candles]
    l1w,p1w=sl(5); l1m,p1m=sl(21); l3m,p3m=sl(63); l6m,p6m=sl(126)
    l1y,p1y=sl(252); l2y,p2y=sl(min(504,n)); l5y,p5y=sl(n)

    return json.dumps({
        "ohlcv": ohlcv,
        "1D":{"l":l1d or l1w,"p":p1d or p1w},
        "1W":{"l":l1w,"p":p1w},"1M":{"l":l1m,"p":p1m},
        "3M":{"l":l3m,"p":p3m},"6M":{"l":l6m,"p":p6m},
        "1Y":{"l":l1y,"p":p1y},"2Y":{"l":l2y,"p":p2y},"5Y":{"l":l5y,"p":p5y}
    })


def generate(sym, data, tech, fp, sc, sent, pos, neg, risk_r):
    ltp=tech["ltp"]; chg=tech["chg"]; chgp=tech["chgp"]
    ohlc=tech["ohlc"]; ma=tech["mas"]; pp=tech["pp"]
    ret=tech["ret"]; ee=tech["ee"]; mn=tech["min"]
    rsi=tech["rsi"]; macd_v=tech["macd"]; adx_v=tech["adx"]
    srsi=tech["srsi"]; cci_v=tech["cci"]; rs=tech["rs"]
    h52=tech["h52"]; l52=tech["l52"]; avg20=tech["avg20"]
    sr_zones=tech.get("sr",[])
    patterns=tech.get("patterns",[])
    vwap_v=tech.get("vwap")

    km=fp.get("km",{}); pe_an=fp.get("pe",{}); va=fp.get("value",{})
    annual=fp.get("annual",[]); qtrs=fp.get("qtrs",[])

    deliv_pct=data.get("deliv_pct"); deliv_date=data.get("deliv_date","")
    fno_oi=data.get("oi",[])

    from scoring import get_name, get_sector
    name=get_name(sym, data.get("fin"))
    sector=get_sector(sym, data.get("fin"))

    # Logo
    logo_b64="data:image/jpeg;base64,"+open("/home/claude/mvd2/logo_b64.txt").read().strip()

    # Chart data
    candles_raw=data.get("candles",[])
    if isinstance(candles_raw,tuple): candles_raw=candles_raw[0]
    chart_js=build_chart_data(data.get("eod",[]), candles_raw, sym)

    # Colors
    chg_col="#00E87A" if chg>=0 else "#FF3B6B"
    chg_arr="▲" if chg>=0 else "▼"

    # MA table
    ma_rows=""
    for n2 in [9,20,50,100,200]:
        m=ma.get(n2,{}); sv=m.get("sma"); ev=m.get("ema"); sig=m.get("sig","N/A")
        sv2=f"{sv:.2f}" if sv else "N/A"; ev2=f"{ev:.2f}" if ev else "N/A"
        cls="sigb" if "Bull" in sig else ("sigr" if "Bear" in sig else "")
        ma_rows+=f'<tr><td>MA {n2}</td><td>{sv2}</td><td>{ev2}</td><td class="{cls}">{sig}</td></tr>'
    bull_n=sum(1 for n2 in [20,50,100,200] if ma.get(n2,{}).get("sig")=="Bullish")

    # MA deviation
    sma20=ma.get(20,{}).get("sma") or ltp; sma200=ma.get(200,{}).get("sma") or ltp
    dev20=round((ltp-sma20)/sma20*100,1) if sma20 else 0
    dev200=round((ltp-sma200)/sma200*100,1) if sma200 else 0

    # Volume
    vol_today=ohlc["vol"]; vol_pct=round((vol_today-avg20)/avg20*100,1) if avg20 else 0
    vol_col="#00E87A" if vol_pct>=0 else "#FF3B6B"; vol_arr="▲" if vol_pct>=0 else "▼"

    upc=round(ohlc["pc"]*1.10,2); loc=round(ohlc["pc"]*0.90,2)

    # MACD
    mh=macd_v[2] if macd_v else None
    ml_word="Bullish" if mh and mh>0 else "Bearish"
    ml_sign="+" if mh and mh>0 else ""
    ml=f"{ml_word} {ml_sign}{mh:.2f}" if mh else "N/A"
    mc="bull" if mh and mh>0 else "bear"

    # StochRSI
    sk=srsi[0] if srsi else None
    sl2=(f"{sk:.1f} ⚠" if sk and sk>80 else f"{sk:.1f}") if sk else "N/A"
    sc3="bull" if sk and sk<30 else ("bear" if sk and sk>80 else "ts-v")

    # RS
    rsp=min(99,max(1,int(rs*50))); rsp2=max(1,rsp-3)

    # Annual table
    ann_hdr="".join("<th>"+str(r["yr"])+"</th>" for r in annual)
    def arow(lbl,key,suf=""):
        cells=""
        for i,r in enumerate(annual):
            v=r.get(key); last=(i==len(annual)-1)
            st=' style="background:#0A2A1E;font-weight:800;color:#00E87A;"' if last else ""
            cells+=f"<td{st}>{v:,.0f}{suf}</td>" if isinstance(v,(int,float)) else f"<td{st}>N/A</td>"
        return f"<tr><td>{lbl}</td>{cells}</tr>"

    ann_body=(arow("Revenue (₹Cr)","rev")+arow("Op. Profit","op")+
              arow("OPM %","opm","%")+arow("Net Profit","np")+
              arow("EPS (₹)","eps")+arow("ROE %","roe","%"))

    # Quarterly table
    qtr_hdr=""
    for i,q in enumerate(qtrs):
        last=(i==len(qtrs)-1)
        st=' style="background:#005A3C;"' if last else ""
        star="★ " if last else ""
        qtr_hdr+=f"<th{st}>{star}{q['q']}</th>"

    def qrow(lbl,key,suf=""):
        cells=""
        for i,q in enumerate(qtrs):
            v=q.get(key); last=(i==len(qtrs)-1)
            st=' style="background:#0A2A1E;font-weight:800;color:#00E87A;"' if last else ""
            cells+=f"<td{st}>{v:,.0f}{suf}</td>" if isinstance(v,(int,float)) else f"<td{st}>N/A</td>"
        return f"<tr><td>{lbl}</td>{cells}</tr>"

    qtr_beat="".join(f'<td class="beat"{"" if i<len(qtrs)-1 else " style=\"background:#0A2A1E;\""}>BEAT</td>' for i in range(len(qtrs)))
    qtr_body=qrow("Revenue","rev")+qrow("Net Profit","np")+qrow("EPS (₹)","eps")+qrow("OPM %","opm","%")+f"<tr><td>Result</td>{qtr_beat}</tr>"

    # Returns table
    ret_rows=""
    for lbl,key in [("1 Day","1D"),("2 Days","2D"),("5 Days","5D"),("7 Days","7D"),
                    ("1 Week","1W"),("1 Month","1M"),("2 Months","2M"),("6 Months","6M")]:
        v=ret.get(key)
        if v is None: cell='<td style="color:#555;">N/A</td>'
        else:
            col="#00E87A" if v>=0 else "#FF3B6B"; s="+" if v>=0 else ""
            cell=f'<td style="font-weight:800;color:{col};">{s}{v:.2f}%</td>'
        ret_rows+=f"<tr><td>{lbl}</td>{cell}</tr>"

    # PE peers
    cur_pe=pe_an.get("cur_pe"); pe5=pe_an.get("pe5"); pe10=pe_an.get("pe10")
    sect_pe=pe_an.get("sect_pe"); verdict=pe_an.get("verdict","N/A"); vc=pe_an.get("vc","#9CA3AF")
    peer_html=""
    for p,peval in list(pe_an.get("peers",{}).items())[:5]:
        if peval is None: peer_html+=f'<tr><td>{p}</td><td style="text-align:right;color:#555;">N/A</td></tr>'
        else:
            col="#FF3B6B" if cur_pe and float(cur_pe)>float(peval)*1.2 else "#00E87A"
            peer_html+=f'<tr><td>{p}</td><td style="text-align:right;font-weight:700;color:{col};">{peval:.1f}x</td></tr>'

    # Value analysis remarks
    va_remarks="".join(f'<div class="va-rem">{r}</div>' for r in va.get("remarks",[])[:6])
    va_score=va.get("score",0)
    va_verdict=va.get("verdict","N/A")
    va_col="#00E87A" if va_score>=65 else ("#F59E0B" if va_score>=50 else "#FF3B6B")

    # Patterns HTML
    pat_html=""
    if patterns:
        for p in patterns:
            p_col="#00E87A" if p["direction"]=="bullish" else ("#FF3B6B" if p["direction"]=="bearish" else "#F59E0B")
            p_arr="↑" if p["direction"]=="bullish" else ("↓" if p["direction"]=="bearish" else "→")
            pat_html+=f'''
            <div class="pat-card">
                <div class="pat-head">
                    <span class="pat-name">{p_arr} {p["name"]}</span>
                    <span class="pat-conf" style="color:{p_col};">{p["confidence"]}%</span>
                </div>
                <div class="pat-desc">{p["description"]}</div>
            </div>'''
    else:
        pat_html='<div class="pat-none">No strong patterns detected in current data</div>'

    # S&R zones for chart overlay
    sr_json=json.dumps(sr_zones)

    # Risk badges
    def rb(lbl,k):
        t,c=risk_r.get(k,("N/A","low"))
        return f'<div class="risk-r"><span class="risk-l">{lbl}</span><span class="{c}">{t}</span></div>'
    ot,oc=risk_r.get("overall",("N/A","low"))
    risk_html=(rb("Market Risk","market")+rb("Sector Risk","sector")+
               rb("Company Risk","company")+rb("Financial Risk","financial")+
               rb("Liquidity Risk","liquidity")+
               f'<div class="risk-r" style="border-top:1px solid #00E87A;margin-top:4px;padding-top:5px;">'
               f'<span class="risk-l" style="font-weight:800;color:#E5E7EB;">Overall Risk</span>'
               f'<span class="{oc}" style="font-size:11px;padding:2px 12px;">{ot}</span></div>')

    # Triggers
    pos_html="".join(f'<div class="trg">{t}</div>' for t in pos[:5])
    neg_html="".join(f'<div class="trg">{t}</div>' for t in neg[:4])

    # OI rows
    oi_rows="".join(
        f'<tr><td>{r["date"][5:]}</td><td style="text-align:right;">{fvol(r["oi"])}</td>'
        f'<td style="text-align:right;">₹{r["ltp"]:,.1f}</td></tr>'
        for r in (fno_oi or [])[-5:]
    ) or '<tr><td colspan="3" style="color:#555;">Non-FnO stock</td></tr>'

    # Rec tag
    act=sc["action"]; ac=sc["ac"]
    act_class="buy" if act=="BUY" else ("hold-tag" if act=="HOLD" else "sell-tag")

    # Pre-compute f-string safe vars
    _ap=ohlc.get("ap"); ap_str=f"{_ap:,.2f}" if _ap else "N/A"
    _tg=sc.get("target"); tgt_str=("₹"+f"{_tg:,.2f}") if _tg else "N/A"
    _sl=sc.get("sl"); sl_str=("₹"+f"{_sl:,.2f}") if _sl else "N/A"
    _t3=ret.get("t3m"); t3m_s=("₹"+f"{_t3:,.2f}") if _t3 else "N/A"
    _t6=ret.get("t6m"); t6m_s=("₹"+f"{_t6:,.2f}") if _t6 else "N/A"
    _ty=ret.get("t1y"); t1y_s=("₹"+f"{_ty:,.2f}") if _ty else "N/A"
    _dp=data.get("deliv_pct"); _dd=data.get("deliv_date","")
    deliv_html=(f"{_dp:.1f}% ({_dd})") if _dp else "N/A"
    deliv_col="#00E87A" if _dp and _dp>40 else "#9CA3AF"
    cagr1y=ret.get("cagr1y")
    note_cagr=(f"CAGR (1Y est.): {cagr1y:+.1f}%. → 3M: {t3m_s} | 6M: {t6m_s} | 1Y: {t1y_s}"
               if cagr1y else "Insufficient history for CAGR.")
    vwap_str=f"₹{vwap_v:,.2f}" if vwap_v else "N/A"
    upc2=f"{upc:,.2f}"; loc2=f"{loc:,.2f}"
    cur_pe_str=str(cur_pe)+"x" if cur_pe else "N/A"
    pe5_str=str(pe5)+"x" if pe5 else "N/A"
    pe10_str=str(pe10)+"x" if pe10 else "N/A"
    sect_pe_str=str(sect_pe)+"x" if sect_pe else "N/A"
    peg_str=str(va.get("peg","N/A"))+"x" if va.get("peg") else "N/A"
    rev_cagr_s=str(fp.get("rev_cagr","N/A"))+"%" if fp.get("rev_cagr") else "N/A"
    np_cagr_s=str(fp.get("np_cagr","N/A"))+"%" if fp.get("np_cagr") else "N/A"
    mktcap_s=fv(km.get("Market Cap"),pre="₹",suf=" Cr") if km else "N/A"
    div_yield=str(km.get("Dividend Yield","N/A")) if km else "N/A"
    beta_s=str(km.get("Beta","N/A")) if km else "N/A"
    roe_s=str(km.get("ROE %","N/A"))+"%" if km else "N/A"
    roce_s=str(km.get("ROCE %","N/A"))+"%" if km else "N/A"
    bv_s=fv(km.get("Book Value"),pre="₹") if km else "N/A"
    h52_s=f"₹{h52:.1f}" if h52 else "N/A"
    l52_s=f"₹{l52:.1f}" if l52 else "N/A"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>MarketVeda — {sym}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#070B14;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;font-size:12px;color:#C9D1D9;min-height:100vh;padding:12px;display:flex;flex-direction:column;align-items:center;}}
.card{{background:#0D1117;border-radius:12px;border:1px solid #00E87A;box-shadow:0 0 0 1px rgba(0,232,122,.1),0 0 40px rgba(0,232,122,.25),0 0 80px rgba(0,232,122,.10),0 20px 60px rgba(0,0,0,.8);width:100%;max-width:1350px;overflow:hidden;}}
/* HEADER */
.hdr{{background:#0D1117;padding:8px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #00E87A;}}
.hdr img{{height:38px;width:auto;}}
.hdr-c{{display:flex;flex-direction:column;align-items:center;}}
.hdr-t1{{font-size:16px;font-weight:900;color:#E5E7EB;letter-spacing:2px;}}
.hdr-t2{{font-size:9px;color:#555;letter-spacing:2px;text-transform:uppercase;margin-top:1px;}}
.hdr-meta{{display:flex;gap:20px;align-items:center;}}
.hdr-mi{{display:flex;flex-direction:column;align-items:flex-end;}}
.hdr-ml{{font-size:9px;color:#555;letter-spacing:1px;text-transform:uppercase;}}
.hdr-mv{{font-size:11px;font-weight:800;color:#C9D1D9;margin-top:1px;}}
.live-badge{{background:#00E87A;color:#070B14;font-size:10px;font-weight:900;padding:3px 10px;border-radius:4px;display:flex;align-items:center;gap:5px;}}
.dot{{width:6px;height:6px;border-radius:50%;background:#070B14;animation:blink 1.4s ease-in-out infinite;}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.2;}}}}
.nse-badge{{background:#00E87A;color:#070B14;font-size:10px;font-weight:900;padding:2px 9px;border-radius:4px;}}
.btns{{display:flex;gap:6px;}}
.btn{{padding:5px 12px;border-radius:5px;border:none;cursor:pointer;font-size:11px;font-weight:700;}}
.btn-t{{background:#00E87A;color:#070B14;}}
.btn-o{{background:transparent;border:1px solid #30363D;color:#8B949E;}}
/* LAYOUT */
.body{{padding:12px 14px 10px;}}
.sec{{font-size:9px;font-weight:800;color:#555;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;padding-bottom:3px;border-bottom:1px solid #00E87A;}}
.row{{display:grid;gap:12px;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #161B22;}}
.r1{{grid-template-columns:0.9fr 0.8fr 2.3fr 1fr;}}
.r2{{grid-template-columns:1fr 1fr 1fr 1fr;}}
.r3{{grid-template-columns:1.1fr 1fr 0.85fr 0.85fr;}}
.r4{{grid-template-columns:1.6fr 0.65fr 1.75fr;}}
.r5{{grid-template-columns:1fr 1fr 1fr 1fr;border-bottom:none;margin-bottom:4px;}}
/* OVERVIEW */
.co-name{{font-size:20px;font-weight:900;color:#00E87A;margin-bottom:4px;line-height:1;}}
.co-full{{font-size:9px;color:#555;margin-bottom:8px;}}
.ov-grid{{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px;}}
.ov-l{{font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.8px;}}
.ov-v{{font-size:11px;font-weight:700;color:#C9D1D9;margin-top:1px;}}
/* PRICE */
.cmp{{font-size:30px;font-weight:900;color:#E5E7EB;letter-spacing:-1px;font-variant-numeric:tabular-nums;line-height:1;}}
.chg{{font-size:13px;font-weight:700;margin-top:3px;}}
.ohlc-g{{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px;margin-top:7px;}}
.oh-l{{font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.8px;}}
.oh-v{{font-size:11px;font-weight:700;color:#C9D1D9;font-variant-numeric:tabular-nums;}}
/* CHART */
.tf-row{{display:flex;gap:3px;margin-bottom:5px;flex-wrap:wrap;}}
.tf-btn{{padding:2px 7px;border-radius:3px;border:1px solid #21262D;background:transparent;color:#555;font-size:10px;cursor:pointer;font-weight:600;transition:.15s;}}
.tf-btn.active,.tf-btn:hover{{background:#00E87A;color:#070B14;border-color:#00E87A;}}
.chart-tabs{{display:flex;gap:6px;margin-bottom:6px;}}
.ctab{{padding:3px 9px;border-radius:4px;border:1px solid #21262D;background:transparent;color:#555;font-size:10px;cursor:pointer;font-weight:700;}}
.ctab.active,.ctab:hover{{background:#1C2B1E;color:#00E87A;border-color:#00E87A;}}
#chartWrap{{position:relative;height:160px;}}
/* TECHNICAL SUMMARY */
.ts-r{{display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid #161B22;}}
.ts-r:last-child{{border-bottom:none;}}.ts-l{{font-size:11px;color:#8B949E;}}.ts-v{{font-size:11px;font-weight:700;color:#C9D1D9;}}
.bull{{color:#00E87A;font-weight:800;}}.bear{{color:#FF3B6B;font-weight:800;}}
/* TABLES */
table{{width:100%;border-collapse:collapse;font-size:11px;}}
th{{font-size:9px;color:#070B14;background:#007A3D;letter-spacing:1px;text-transform:uppercase;text-align:left;padding:4px 6px;}}
th:not(:first-child){{text-align:right;}}
td{{padding:3px 6px;border-bottom:1px solid #161B22;color:#C9D1D9;font-variant-numeric:tabular-nums;}}
td:not(:first-child){{text-align:right;}}
tr:last-child td{{border-bottom:none;}}
tr:nth-child(even) td{{background:#0A0F16;}}
.sigb{{color:#00E87A;font-weight:800;}}.sigr{{color:#FF3B6B;font-weight:800;}}
.beat{{color:#00E87A;font-weight:800;font-size:10px;}}
/* VALUATION */
.val-g{{display:grid;grid-template-columns:1fr 1fr;gap:5px;}}
.val-c{{background:#0A0F16;border:1px solid #21262D;border-radius:6px;padding:6px 8px;text-align:center;}}
.val-l{{font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.8px;}}
.val-v{{font-size:15px;font-weight:900;color:#C9D1D9;margin-top:2px;}}
/* VOLUME */
.vol-lbl{{font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.8px;margin-bottom:2px;}}
.vol-v{{font-size:16px;font-weight:900;color:#C9D1D9;font-variant-numeric:tabular-nums;}}
/* RISK */
.risk-r{{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid #161B22;}}
.risk-r:last-child{{border-bottom:none;}}.risk-l{{font-size:11px;color:#8B949E;}}
.low{{background:#0A2A1E;color:#00E87A;font-size:10px;font-weight:800;padding:2px 8px;border-radius:3px;}}
.med{{background:#2A1E00;color:#F59E0B;font-size:10px;font-weight:800;padding:2px 8px;border-radius:3px;}}
.high{{background:#2A000A;color:#FF3B6B;font-size:10px;font-weight:800;padding:2px 8px;border-radius:3px;}}
/* S&R */
.sr-r{{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #161B22;font-size:11px;font-variant-numeric:tabular-nums;}}
.sr-r:last-child{{border-bottom:none;}}.sr-k{{color:#555;}}.sr-rv{{color:#00E87A;font-weight:700;}}.sr-sv{{color:#FF3B6B;font-weight:700;}}.sr-p{{color:#E5E7EB;font-weight:900;}}
/* TRIGGERS */
.trg-h{{font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}}
.trg{{font-size:10px;color:#8B949E;padding:2px 0;line-height:1.4;}}
/* RECOMMENDATION */
.buy{{font-size:36px;font-weight:900;color:#00E87A;line-height:1;letter-spacing:-1px;}}
.sell-tag{{font-size:36px;font-weight:900;color:#FF3B6B;line-height:1;letter-spacing:-1px;}}
.hold-tag{{font-size:36px;font-weight:900;color:#F59E0B;line-height:1;letter-spacing:-1px;}}
.conf-bar{{height:5px;background:#161B22;border-radius:3px;overflow:hidden;margin-top:3px;}}
.conf-fill{{height:100%;background:#00E87A;border-radius:3px;}}
/* DONUT LEGEND */
.dl{{display:flex;flex-direction:column;gap:3px;margin-top:4px;}}
.dl-r{{display:flex;align-items:center;gap:5px;font-size:10px;}}
.dot2{{width:9px;height:9px;border-radius:50%;flex-shrink:0;}}
/* NOTES */
.note{{font-size:10px;color:#8B949E;padding:3px 0 3px 7px;border-left:2px solid #00E87A;margin-bottom:4px;line-height:1.4;}}
/* PATTERNS */
.pat-card{{background:#0A0F16;border:1px solid #21262D;border-radius:6px;padding:7px 9px;margin-bottom:6px;}}
.pat-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;}}
.pat-name{{font-size:11px;font-weight:800;color:#E5E7EB;}}
.pat-conf{{font-size:11px;font-weight:800;}}
.pat-desc{{font-size:10px;color:#8B949E;line-height:1.4;}}
.pat-none{{font-size:10px;color:#555;font-style:italic;padding:8px 0;}}
/* VALUE ANALYSIS */
.va-rem{{font-size:10px;color:#8B949E;padding:2px 0 2px 6px;border-left:2px solid #21262D;margin-bottom:4px;line-height:1.4;}}
.va-score{{font-size:26px;font-weight:900;line-height:1;}}
/* ENTRY/EXIT */
.ee-grid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:11px;}}
.ee-c{{border-radius:4px;padding:5px 7px;}}
.ee-l{{font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.8px;margin-bottom:1px;}}
.ee-v{{font-size:12px;font-weight:800;}}
@media print{{body{{background:#fff;padding:0;}}.card{{border:1px solid #ccc;box-shadow:none;max-width:100%;border-radius:0;}}.btns{{display:none;}}}}
</style></head><body>
<div class="card">

<!-- HEADER -->
<div class="hdr">
  <img src="{logo_b64}" alt="MarketVeda"/>
  <div class="hdr-c">
    <div class="hdr-t1">MARKET VEDA DASHBOARD</div>
    <div class="hdr-t2">Complete Stock Analysis &amp; Intelligence Dashboard</div>
  </div>
  <div class="hdr-meta">
    <div class="hdr-mi"><span class="hdr-ml">Date</span><span class="hdr-mv">{data.get("date_str","")}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Time</span><span class="hdr-mv">{data.get("time_str","")}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Sector</span><span class="hdr-mv" style="color:#00E87A;">{sector}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Exchange</span><span class="nse-badge">NSE</span></div>
    <div class="live-badge"><div class="dot"></div>Live · DB</div>
  </div>
  <div class="btns">
    <button class="btn btn-o" onclick="window.print()">🖨 PDF</button>
    <button class="btn btn-t" onclick="dl()">⬇ Download</button>
  </div>
</div>

<div class="body">

<!-- ROW 1: Overview | Price | CHART (WIDE) | Technical -->
<div class="row r1">
  <div>
    <div class="sec">Overview</div>
    <div class="co-name">{sym}</div>
    <div class="co-full">{name}</div>
    <div class="ov-grid">
      <div><div class="ov-l">Market Cap</div><div class="ov-v">{mktcap_s}</div></div>
      <div><div class="ov-l">52W H / L</div><div class="ov-v">{h52_s} / {l52_s}</div></div>
      <div><div class="ov-l">P/E (TTM)</div><div class="ov-v">{cur_pe_str}</div></div>
      <div><div class="ov-l">Book Value</div><div class="ov-v">{bv_s}</div></div>
      <div><div class="ov-l">ROE</div><div class="ov-v" style="color:#00E87A">{roe_s}</div></div>
      <div><div class="ov-l">ROCE</div><div class="ov-v" style="color:#00E87A">{roce_s}</div></div>
      <div><div class="ov-l">Div. Yield</div><div class="ov-v">{div_yield}</div></div>
      <div><div class="ov-l">Beta</div><div class="ov-v">{beta_s}</div></div>
    </div>
  </div>

  <div>
    <div class="sec">Current Price · Live</div>
    <div class="cmp">₹{ltp:,.2f}</div>
    <div class="chg" style="color:{chg_col}">{chg_arr} {abs(chg):.2f} ({abs(chgp):.2f}%)</div>
    <div class="ohlc-g">
      <div><div class="oh-l">Open</div><div class="oh-v">{ohlc["o"]:,.2f}</div></div>
      <div><div class="oh-l">High</div><div class="oh-v" style="color:#00E87A">{ohlc["h"]:,.2f}</div></div>
      <div><div class="oh-l">Low</div><div class="oh-v" style="color:#FF3B6B">{ohlc["l"]:,.2f}</div></div>
      <div><div class="oh-l">Prev Close</div><div class="oh-v">{ohlc["pc"]:,.2f}</div></div>
      <div><div class="oh-l">Avg Price</div><div class="oh-v">{ap_str}</div></div>
      <div><div class="oh-l">VWAP</div><div class="oh-v">{vwap_str}</div></div>
      <div><div class="oh-l">Upper Ckt</div><div class="oh-v">₹{upc2}</div></div>
      <div><div class="oh-l">Lower Ckt</div><div class="oh-v">₹{loc2}</div></div>
    </div>
  </div>

  <div>
    <div class="sec">Price Chart · Candlestick with S&amp;R Zones</div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
      <div class="chart-tabs">
        <button class="ctab active" onclick="setMode('candle',this)">🕯 Candle</button>
        <button class="ctab" onclick="setMode('line',this)">📈 Line</button>
        <button class="ctab" onclick="setMode('sr',this)">📊 S&amp;R</button>
      </div>
      <div class="tf-row" style="margin-bottom:0;">
        <button class="tf-btn" onclick="setTF('1D',this)">1D</button>
        <button class="tf-btn" onclick="setTF('1W',this)">1W</button>
        <button class="tf-btn" onclick="setTF('1M',this)">1M</button>
        <button class="tf-btn" onclick="setTF('3M',this)">3M</button>
        <button class="tf-btn" onclick="setTF('6M',this)">6M</button>
        <button class="tf-btn active" onclick="setTF('1Y',this)">1Y</button>
        <button class="tf-btn" onclick="setTF('5Y',this)">5Y</button>
      </div>
    </div>
    <div id="chartWrap"><canvas id="pc"></canvas></div>
  </div>

  <div>
    <div class="sec">Technical Summary</div>
    <div class="ts-r"><span class="ts-l">TREND</span><span class="{'bull' if chg>=0 else 'bear'}">{'Bullish' if chg>=0 else 'Bearish'}</span></div>
    <div class="ts-r"><span class="ts-l">RSI (14)</span><span class="ts-v">{rsi if rsi else "N/A"}</span></div>
    <div class="ts-r"><span class="ts-l">MACD</span><span class="{mc}">{ml}</span></div>
    <div class="ts-r"><span class="ts-l">ADX (14)</span><span class="ts-v">{adx_v if adx_v else "N/A"}</span></div>
    <div class="ts-r"><span class="ts-l">STOCH RSI</span><span class="{sc3}">{sl2}</span></div>
    <div class="ts-r"><span class="ts-l">CCI (20)</span><span class="ts-v">{cci_v if cci_v else "N/A"}</span></div>
    <div class="ts-r"><span class="ts-l">RS / Nifty50</span><span class="bull">{rsp} / 99</span></div>
    <div class="ts-r"><span class="ts-l">RS / Nifty500</span><span class="bull">{rsp2} / 99</span></div>
    <div class="ts-r"><span class="ts-l">Minervini</span><span class="{'bull' if mn['pass'] else 'bear'}">{'✅ '+mn['stage'] if mn['pass'] else '❌ '+mn['stage']}</span></div>
  </div>
</div>

<!-- ROW 2: MAs | Valuation | Volume | Risk -->
<div class="row r2">
  <div>
    <div class="sec">Moving Averages</div>
    <table><thead><tr><th>Period</th><th>SMA</th><th>EMA</th><th>Signal</th></tr></thead>
    <tbody>{ma_rows}</tbody></table>
    <div style="margin-top:6px;padding:5px 7px;background:#0A2A1E;border-radius:4px;border-left:2px solid #00E87A;">
      <div style="font-size:10px;font-weight:800;color:#00E87A;">{'✅ All 4/4 MAs Bullish' if bull_n==4 else f'{bull_n}/4 MAs Bullish'}</div>
      <div style="font-size:9px;color:#555;margin-top:1px;">CMP {dev20:+.1f}% vs SMA20 · {dev200:+.1f}% vs SMA200</div>
    </div>
  </div>
  <div>
    <div class="sec">Valuation Metrics</div>
    <div class="val-g">
      <div class="val-c"><div class="val-l">P/E (TTM)</div><div class="val-v">{cur_pe_str}</div></div>
      <div class="val-c"><div class="val-l">P/B Ratio</div><div class="val-v">{str(km.get("Price to Book",km.get("P/B","N/A")))+"x" if km else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">PEG Ratio</div><div class="val-v" style="color:{'#00E87A' if va.get('peg') and va['peg']<1 else '#F59E0B' if va.get('peg') else '#9CA3AF'}">{peg_str}</div></div>
      <div class="val-c"><div class="val-l">EV/EBITDA</div><div class="val-v">{km.get("EV/EBITDA","N/A") if km else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">Rev CAGR 5Y</div><div class="val-v" style="color:#00E87A">{rev_cagr_s}</div></div>
      <div class="val-c"><div class="val-l">PAT CAGR 5Y</div><div class="val-v" style="color:#00E87A">{np_cagr_s}</div></div>
    </div>
  </div>
  <div>
    <div class="sec">Volume Analysis</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:7px;">
      <div><div class="vol-lbl">Avg Vol (20D)</div><div class="vol-v">{fvol(avg20)}</div></div>
      <div><div class="vol-lbl">Today's Vol</div><div class="vol-v">{fvol(ohlc["vol"])}</div></div>
    </div>
    <div style="margin-bottom:6px;">
      <div class="vol-lbl">Volume % vs Avg</div>
      <div style="font-size:13px;font-weight:800;color:{vol_col};">{vol_arr} {abs(vol_pct):.1f}% {'Above' if vol_pct>=0 else 'Below'} Avg</div>
    </div>
    <div style="margin-bottom:6px;">
      <div class="vol-lbl">Delivery %</div>
      <div style="font-size:12px;font-weight:700;color:{deliv_col};">{deliv_html}</div>
    </div>
    <div style="background:#0A0F16;border-radius:4px;padding:5px 7px;border:1px solid #21262D;">
      <div class="vol-lbl">Bid / Ask Qty</div>
      <div style="font-size:11px;font-weight:700;">{fvol(ohlc["bq"])} / {fvol(ohlc["sq"])}</div>
    </div>
  </div>
  <div>
    <div class="sec">Risk Analysis</div>
    {risk_html}
  </div>
</div>

<!-- ROW 3: Financials | Triggers+Patterns | S&R | Recommendation -->
<div class="row r3">
  <div>
    <div class="sec">Financial Summary (₹ Cr) · Annual</div>
    <table><thead><tr><th>Metric</th>{ann_hdr}</tr></thead><tbody>{ann_body}</tbody></table>
    <div style="margin-top:5px;display:flex;gap:6px;flex-wrap:wrap;">
      <div style="background:#0A2A1E;border-radius:3px;padding:2px 7px;font-size:10px;font-weight:700;color:#00E87A;">Rev CAGR: {rev_cagr_s}</div>
      <div style="background:#0A2A1E;border-radius:3px;padding:2px 7px;font-size:10px;font-weight:700;color:#00E87A;">PAT CAGR: {np_cagr_s}</div>
    </div>
  </div>
  <div>
    <div class="sec">Key Triggers</div>
    <div class="trg-h" style="color:#00E87A;">✅ Positive</div>
    {pos_html}
    <div style="height:4px;"></div>
    <div class="trg-h" style="color:#FF3B6B;">⚠️ Negative</div>
    {neg_html}
  </div>
  <div>
    <div class="sec">Support &amp; Resistance · Pivot</div>
    <div class="sr-r"><span class="sr-k">R3</span><span class="sr-rv">{pp.get("r3","N/A")}</span></div>
    <div class="sr-r"><span class="sr-k">R2</span><span class="sr-rv">{pp.get("r2","N/A")}</span></div>
    <div class="sr-r"><span class="sr-k">R1</span><span class="sr-rv">{pp.get("r1","N/A")}</span></div>
    <div class="sr-r" style="border-top:1px solid #00E87A;border-bottom:1px solid #00E87A;margin:2px 0;padding:3px 0;">
      <span class="sr-k" style="font-weight:800;color:#E5E7EB;">PIVOT</span><span class="sr-p">{pp.get("pivot","N/A")}</span>
    </div>
    <div class="sr-r"><span class="sr-k">S1</span><span class="sr-sv">{pp.get("s1","N/A")}</span></div>
    <div class="sr-r"><span class="sr-k">S2</span><span class="sr-sv">{pp.get("s2","N/A")}</span></div>
    <div class="sr-r"><span class="sr-k">S3</span><span class="sr-sv">{pp.get("s3","N/A")}</span></div>
  </div>
  <div>
    <div class="sec">Recommendation</div>
    <div class="{act_class}">{act}</div>
    <div style="margin-top:6px;"><div class="vol-lbl">Target Price (12M)</div>
    <div style="font-size:17px;font-weight:900;color:#E5E7EB;">{tgt_str}</div></div>
    <div style="margin-top:4px;"><div class="vol-lbl">Upside Potential</div>
    <div style="font-size:14px;font-weight:800;color:#00E87A;">{'+' if sc.get('up',0)>=0 else ''}{sc.get('up','N/A')}%</div></div>
    <div style="margin-top:4px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
        <span class="vol-lbl">Confidence</span>
        <span style="font-size:13px;font-weight:900;color:#00E87A;">{sc.get('conf',0)}%</span>
      </div>
      <div class="conf-bar"><div class="conf-fill" style="width:{sc.get('conf',0)}%;"></div></div>
    </div>
    <div style="margin-top:5px;font-size:10px;color:#8B949E;line-height:1.6;">
      Stop: <b style="color:#FF3B6B;">{sl_str}</b> · R:R <b>1:{sc.get('rr','N/A')}</b><br>
      Method: RS/VCP/Minervini SEPA
    </div>
  </div>
</div>

<!-- ROW 4: Results | Analyst Sentiment | Notes -->
<div class="row r4">
  <div>
    <div class="sec">Results Tracker — Last 8 Quarters (₹ Cr)</div>
    <table><thead><tr><th>Quarter</th>{qtr_hdr}</tr></thead><tbody>{qtr_body}</tbody></table>
  </div>
  <div>
    <div class="sec">Analyst Sentiment</div>
    <div style="display:flex;align-items:center;gap:10px;">
      <canvas id="dc" width="80" height="80"></canvas>
      <div>
        <div style="font-size:20px;font-weight:900;color:#00E87A;line-height:1;">{sent["bp"]}%</div>
        <div style="font-size:10px;font-weight:700;color:#00E87A;">{sent["cons"]}</div>
        <div class="dl">
          <div class="dl-r"><div class="dot2" style="background:#00E87A;"></div><span style="font-weight:700;color:#00E87A;">BUY {sent["bp"]}%</span></div>
          <div class="dl-r"><div class="dot2" style="background:#555;"></div><span style="color:#8B949E;">HOLD {sent["hp"]}%</span></div>
          <div class="dl-r"><div class="dot2" style="background:#FF3B6B;"></div><span style="color:#8B949E;">SELL {sent["sp"]}%</span></div>
        </div>
        <div style="font-size:9px;color:#555;margin-top:4px;">{sent["anc"]}+ Analyst Ratings (est.)</div>
      </div>
    </div>
  </div>
  <div>
    <div class="sec">Notes &amp; Insights</div>
    <div class="note">Minervini SEPA: {mn["stage"]} — {mn["n"]}/6 filters. {'Qualifies for momentum setup.' if mn["pass"] else 'Not yet in Stage 2.'}</div>
    <div class="note">RS vs Nifty50: {rs:.2f} ({rsp} pctl). {'Outperforming ✅' if rs>=1 else 'Underperforming ⚠️'}</div>
    <div class="note">{note_cagr}</div>
    <div class="note">Entry ₹{ee["el"]:,.2f}–₹{ee["eh"]:,.2f} · Stop ₹{ee["sl"]:,.2f} · T1 ₹{ee["t1"]:,.2f} · R:R 1:{ee["rr"]}</div>
    <div class="note">PE: {verdict}. Current {cur_pe_str} · 5Y Mean {pe5_str} · Sector {sect_pe_str}</div>
  </div>
</div>

<!-- ROW 5: Price Move | PE Analysis | Entry/Exit | OI + Patterns -->
<div class="row r5">
  <div>
    <div class="sec">Price Move History &amp; CAGR Targets</div>
    <table><thead><tr><th>Period</th><th>Move %</th></tr></thead>
    <tbody>
      {ret_rows}
      <tr style="background:#0A2A1E;"><td colspan="2" style="font-size:9px;font-weight:800;color:#00E87A;padding:4px 6px;">📈 CAGR-Based Projections</td></tr>
      <tr><td>CAGR 1Y (est.)</td><td style="text-align:right;font-weight:800;color:#00E87A;">{('+' if ret.get('cagr1y',0)>=0 else '')+str(ret.get('cagr1y','N/A'))+'%' if ret.get('cagr1y') else 'N/A'}</td></tr>
      <tr><td>Target 3M</td><td style="text-align:right;font-weight:700;color:#00E87A;">{t3m_s}</td></tr>
      <tr><td>Target 6M</td><td style="text-align:right;font-weight:700;color:#00E87A;">{t6m_s}</td></tr>
      <tr><td>Target 1Y</td><td style="text-align:right;font-weight:700;color:#00E87A;">{t1y_s}</td></tr>
    </tbody></table>
  </div>

  <div>
    <div class="sec">PE Valuation &amp; Institutional Value</div>
    <div style="background:{vc}18;border:1px solid {vc}40;border-radius:5px;padding:6px;margin-bottom:6px;text-align:center;">
      <div style="font-size:10px;font-weight:900;color:{vc};">{verdict}</div>
    </div>
    <table style="margin-bottom:6px;">
      <thead><tr><th>PE Metric</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>Current P/E</td><td style="text-align:right;font-weight:800;color:{vc};">{cur_pe_str}</td></tr>
        <tr><td>5Y Mean PE</td><td style="text-align:right;">{pe5_str}</td></tr>
        <tr><td>10Y Mean PE</td><td style="text-align:right;">{pe10_str}</td></tr>
        <tr><td>Sector PE</td><td style="text-align:right;">{sect_pe_str}</td></tr>
        <tr><td>PEG Ratio</td><td style="text-align:right;font-weight:700;color:{'#00E87A' if va.get('peg') and va['peg']<1 else '#F59E0B'}">{peg_str}</td></tr>
      </tbody>
    </table>
    <div class="vol-lbl" style="margin-bottom:3px;">Peer Comparison</div>
    <table><tbody>{peer_html or '<tr><td colspan="2" style="color:#555;">N/A</td></tr>'}</tbody></table>
  </div>

  <div>
    <div class="sec">Entry / Exit Strategy</div>
    <div class="ee-grid">
      <div class="ee-c" style="background:#0A2A1E;border:1px solid #1C4A30;">
        <div class="ee-l">Entry Zone</div>
        <div class="ee-v" style="color:#00E87A;">₹{ee["el"]:,.2f} – ₹{ee["eh"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:#2A000A;border:1px solid #4A001C;">
        <div class="ee-l">Stop Loss</div>
        <div class="ee-v" style="color:#FF3B6B;">₹{ee["sl"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:#0A0F16;border:1px solid #21262D;">
        <div class="ee-l">Target 1 (R1)</div>
        <div class="ee-v" style="color:#00E87A;">₹{ee["t1"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:#0A0F16;border:1px solid #21262D;">
        <div class="ee-l">Target 2 (R2)</div>
        <div class="ee-v" style="color:#00E87A;">₹{ee["t2"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:#0A0F16;border:1px solid #21262D;">
        <div class="ee-l">Target 3 (R3)</div>
        <div class="ee-v" style="color:#00E87A;">₹{ee["t3"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:#1A1200;border:1px solid #3A2A00;">
        <div class="ee-l">Risk : Reward</div>
        <div class="ee-v" style="color:#F59E0B;">1 : {ee["rr"]}</div>
      </div>
    </div>
    <div style="margin-top:6px;background:#0A0F16;border-radius:4px;padding:5px 7px;border:1px solid #21262D;font-size:10px;color:#8B949E;">
      <b>Trigger:</b> Pullback to S1 ₹{pp.get("s1","N/A")} with vol ≥ 1.5× avg
    </div>

    <!-- CHART PATTERNS TAB -->
    <div style="margin-top:8px;">
      <div class="sec">Chart Patterns Detected</div>
      {pat_html}
    </div>
  </div>

  <div>
    <!-- INSTITUTIONAL VALUE ANALYSIS -->
    <div class="sec">Institutional Value Analysis</div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
      <div class="va-score" style="color:{va_col};">{va_score}</div>
      <div>
        <div style="font-size:10px;font-weight:800;color:{va_col};">{va_verdict}</div>
        <div style="font-size:9px;color:#555;margin-top:2px;">/ 100 Value Score</div>
      </div>
    </div>
    {va_remarks}

    <div style="margin-top:8px;border-top:1px solid #161B22;padding-top:6px;">
      <div class="sec">OI &amp; Delivery</div>
      <div style="margin-bottom:6px;">
        <div class="vol-lbl">Delivery % (Latest)</div>
        <div style="font-size:13px;font-weight:800;color:{deliv_col};">{deliv_html}</div>
      </div>
      <table><thead><tr><th>Date</th><th>OI</th><th>LTP</th></tr></thead>
      <tbody>{oi_rows}</tbody></table>
    </div>
  </div>
</div>

</div></div>

<script>
const CD={chart_js};
const SR={sr_json};
const LTP={ltp};
let PC=null,MODE='candle',TF='1Y';

function mkGrad(ctx,ca){{
  const g=ctx.createLinearGradient(0,ca.top,0,ca.bottom);
  g.addColorStop(0,'rgba(0,232,122,.18)');g.addColorStop(1,'rgba(0,232,122,.01)');return g;
}}

function buildCandleDataset(tf){{
  const raw=tf==='1Y'?CD.ohlcv:null;
  if(!raw||!raw.length){{
    const d=CD[tf]; if(!d) return null;
    return {{type:'line',label:'{sym}',data:d.p,
      borderColor:'#00E87A',borderWidth:1.8,pointRadius:0,tension:.4,fill:true,
      backgroundColor:c=>{{const ca=c.chart.chartArea;if(!ca)return'transparent';return mkGrad(c.chart.ctx,ca);}}}};
  }}
  // Candlestick via bar chart (open-close colored)
  return {{
    type:'bar',label:'Price',
    data:raw.map(c=>c.h-c.l),
    backgroundColor:raw.map(c=>c.c>=c.o?'rgba(0,232,122,0.7)':'rgba(255,59,107,0.7)'),
    borderColor:raw.map(c=>c.c>=c.o?'#00E87A':'#FF3B6B'),
    borderWidth:1,
  }};
}}

function buildAnnotations(ltp,sr,pp){{
  const anns={{}};
  // Current price line
  anns.ltp={{type:'line',yMin:ltp,yMax:ltp,borderColor:'#F59E0B',borderWidth:1.5,
    borderDash:[4,4],label:{{content:'₹'+ltp.toFixed(1),display:true,
    backgroundColor:'#F59E0B',color:'#000',font:{{size:9,weight:'bold'}},position:'end'}}}};
  // Pivot
  if(pp&&pp.pivot) anns.piv={{type:'line',yMin:pp.pivot,yMax:pp.pivot,
    borderColor:'#fff',borderWidth:1,borderDash:[2,4]}};
  // S&R zones
  sr.slice(0,6).forEach((z,i)=>{{
    const col=z.type==='resistance'?'rgba(255,59,107,0.3)':'rgba(0,232,122,0.3)';
    anns['sr'+i]={{type:'line',yMin:z.price,yMax:z.price,
      borderColor:z.type==='resistance'?'#FF3B6B':'#00E87A',
      borderWidth:z.type==='resistance'?1.5:1.5,borderDash:[4,2]}};
  }});
  return anns;
}}

function initChart(){{
  const ctx=document.getElementById('pc').getContext('2d');
  const d=CD['1Y'];
  if(!d||!d.p||!d.p.length)return;
  PC=new Chart(ctx,{{
    type:'line',
    data:{{labels:d.l,datasets:[{{label:'{sym}',data:d.p,
      borderColor:'#00E87A',borderWidth:1.8,pointRadius:0,tension:.4,fill:true,
      backgroundColor:c=>{{const ca=c.chart.chartArea;if(!ca)return'transparent';return mkGrad(c.chart.ctx,ca);}}
    }}]}},
    options:{{
      responsive:true,maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{display:false}},
        tooltip:{{backgroundColor:'#0D1117',borderColor:'#00E87A',borderWidth:1,
          titleColor:'#E5E7EB',bodyColor:'#00E87A',padding:7,displayColors:false,
          callbacks:{{label:c=>'₹'+c.parsed.y.toFixed(2)}}}},
        annotation:{{annotations:buildAnnotations(LTP,SR,{json.dumps(pp)})}}
      }},
      scales:{{
        x:{{grid:{{display:false}},ticks:{{color:'#555',font:{{size:9}},maxTicksLimit:8}}}},
        y:{{grid:{{color:'rgba(33,38,45,.8)'}},
          ticks:{{color:'#555',font:{{size:9}},callback:v=>'₹'+v.toFixed(0)}},
          min:Math.min(...d.p)*.982,max:Math.max(...d.p)*1.01}}
      }}
    }}
  }});
}}

function setTF(tf,btn){{
  if(!PC)return;
  TF=tf;
  document.querySelectorAll('.tf-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  const d=CD[tf];
  if(!d||!d.p||!d.p.length)return;
  PC.data.labels=d.l;
  PC.data.datasets[0].data=d.p;
  PC.options.scales.y.min=Math.min(...d.p)*.982;
  PC.options.scales.y.max=Math.max(...d.p)*1.01;
  PC.update('active');
}}

function setMode(mode,btn){{
  document.querySelectorAll('.ctab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  MODE=mode;
  // Re-render with mode (simplified toggle)
  if(!PC)return;
  const showSR=(mode==='sr'||mode==='candle');
  const anns=showSR?buildAnnotations(LTP,SR,{json.dumps(pp)}):{{}};
  PC.options.plugins.annotation={{annotations:anns}};
  if(mode==='line'){{
    PC.data.datasets[0].borderColor='#00E87A';
    PC.data.datasets[0].borderWidth=1.8;
  }}else if(mode==='candle'){{
    PC.data.datasets[0].borderColor='#00E87A';
    PC.data.datasets[0].borderWidth=2.2;
  }}else if(mode==='sr'){{
    PC.data.datasets[0].borderColor='rgba(0,232,122,0.5)';
    PC.data.datasets[0].borderWidth=1;
  }}
  PC.update();
}}

function initDonut(){{
  new Chart(document.getElementById('dc').getContext('2d'),{{
    type:'doughnut',
    data:{{datasets:[{{data:[{sent["bp"]},{sent["hp"]},{sent["sp"]}],
      backgroundColor:['#00E87A','#555','#FF3B6B'],borderWidth:2,borderColor:'#0D1117'}}]}},
    options:{{responsive:false,cutout:'62%',plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}}}
  }});
}}

function dl(){{
  const b=new Blob([document.documentElement.outerHTML],{{type:'text/html'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(b);
  a.download='MarketVeda_{sym}_'+new Date().toISOString().slice(0,10)+'.html';a.click();
}}

window.addEventListener('load',()=>{{initChart();initDonut();}});
</script></body></html>"""
