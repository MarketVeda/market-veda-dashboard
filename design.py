"""
design.py — MarketVeda Dashboard
Palette: white card on dark outer — teal #00C896 accent (CGPOWER reference)
Chart: full-width, DMAs 10/20/50/100/200, volume bars, TFs 1M-5Y
"""
import json

def fv(v,pre="₹",suf="",na="N/A",dec=2):
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

def _sh_bar(label,pct,col,chg):
    if pct is None:
        return f'<div class="sh-row"><span class="sh-lbl">{label}</span><span style="color:#9CA3AF">N/A</span></div>'
    w=min(100,max(0,pct))
    cd=""
    if chg is not None:
        a="▲" if chg>0 else ("▼" if chg<0 else "→")
        cc="#00C896" if chg>0 else ("#F43F5E" if chg<0 else "#9CA3AF")
        cd=f'<span style="color:{cc};font-size:9px;margin-left:3px">{a}{abs(chg):.2f}%</span>'
    return f'<div class="sh-row"><div class="sh-meta"><span class="sh-lbl">{label}</span><span style="font-weight:800;color:{col};font-size:11px">{pct:.1f}%{cd}</span></div><div class="sh-track"><div class="sh-fill" style="width:{w}%;background:{col}"></div></div></div>'

def build_chart(eod):
    mn=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    def fd(s): p=s.split("-"); return f"{p[2]}{mn[int(p[1])]}{p[0][2:]}"
    arr=[]
    for e in eod:
        arr.append({"t":fd(e["date"]),"o":e["o"],"h":e["h"],"l":e["l"],"c":e["c"],"v":e.get("v",0)})
    return json.dumps(arr)

def generate(sym,data,tech,fp,sc,sent,pos,neg,risk_r):
    ltp=tech["ltp"]; chg=tech["chg"]; chgp=tech["chgp"]
    ohlc=tech["ohlc"]; ma=tech["mas"]; pp=tech["pp"]
    ret=tech["ret"]; ee=tech["ee"]; mn=tech["min"]
    rsi_v=tech["rsi"]; macd_v=tech["macd"]; adx_v=tech["adx"]
    srsi=tech["srsi"]; cci_v=tech["cci"]; rs=tech["rs"]
    h52=tech["h52"]; l52=tech["l52"]; avg20=tech["avg20"]
    sr_zones=tech.get("sr",[]); patterns=tech.get("patterns",[])
    vwap_v=tech.get("vwap"); atr14=data["live"].get("atr_14")

    km=fp.get("km",{}); pe_an=fp.get("pe",{}); va=fp.get("value",{})
    annual=fp.get("annual",[]); qtrs=fp.get("qtrs",[])
    sh_data=fp.get("shareholding",[]); sha=fp.get("sh_analysis",{})
    deliv_pct=data.get("deliv_pct"); fno_oi=data.get("oi",[])

    from scoring import get_name,get_sector
    name=get_name(sym,data.get("fin"))
    sector=get_sector(sym,data.get("fin"))

    chart_full=build_chart(data.get("eod",[]))
    sr_json=json.dumps(sr_zones)

    # MA values for chart overlay
    sma_vals={n2:ma.get(n2,{}).get("sma") or 0 for n2 in [10,20,50,100,200]}

    # Colors
    cc="#00C896" if chg>=0 else "#F43F5E"
    ca="▲" if chg>=0 else "▼"

    # MA table rows
    ma_rows=""
    for n2 in [9,20,50,100,200]:
        m=ma.get(n2,{}); sv=m.get("sma"); ev=m.get("ema"); sig=m.get("sig","N/A")
        cls="sigb" if "Bull" in (sig or "") else ("sigr" if "Bear" in (sig or "") else "")
        ma_rows+=f'<tr><td>MA {n2}</td><td>{"N/A" if not sv else f"{sv:.2f}"}</td><td>{"N/A" if not ev else f"{ev:.2f}"}</td><td class="{cls}">{sig}</td></tr>'
    bull_n=sum(1 for n2 in [20,50,100,200] if ma.get(n2,{}).get("sig")=="Bullish")
    sma20=ma.get(20,{}).get("sma") or ltp; sma200=ma.get(200,{}).get("sma") or ltp
    dev20=round((ltp-sma20)/sma20*100,1) if sma20 else 0
    dev200=round((ltp-sma200)/sma200*100,1) if sma200 else 0

    # Volume
    vol_today=ohlc["vol"]; vol_pct=round((vol_today-avg20)/avg20*100,1) if avg20 else 0
    vc2="#00C896" if vol_pct>=0 else "#F43F5E"

    # MACD
    mh=macd_v[2] if macd_v else None
    ml=f"{'Bullish +' if mh and mh>0 else 'Bearish '}{mh:.2f}" if mh else "N/A"
    mc="bull" if mh and mh>0 else "bear"

    # StochRSI
    sk=srsi[0] if srsi else None
    sl2=f"{sk:.1f}{'⚠' if sk and sk>80 else ''}" if sk else "N/A"
    sc3="bull" if sk and sk<30 else ("bear" if sk and sk>80 else "ts-v")

    # RS percentile
    rsp=min(99,max(1,int(rs*50)))

    # Annual table
    ann_hdr="".join(f"<th>{r['yr']}</th>" for r in annual)
    def arow(lbl,key,suf=""):
        cells=""
        for i,r in enumerate(annual):
            v=r.get(key); last=(i==len(annual)-1)
            st=' style="background:#E6FAF5;font-weight:800;color:#009B77"' if last else ""
            cells+=f"<td{st}>{v:,.0f}{suf}</td>" if isinstance(v,(int,float)) else f"<td{st}>N/A</td>"
        return f"<tr><td>{lbl}</td>{cells}</tr>"
    ann_body=(arow("Revenue (₹Cr)","rev")+arow("Op.Profit","op")+
              arow("OPM %","opm","%")+arow("Net Profit","np")+
              arow("EPS (₹)","eps")+arow("ROE %","roe","%"))

    # Quarterly
    qtr_hdr="".join(f"<th{'  style=\"background:#007A5E\"' if i==len(qtrs)-1 else ''}>{q['q']}</th>" for i,q in enumerate(qtrs))
    def qrow(lbl,key,suf=""):
        cells=""
        for i,q in enumerate(qtrs):
            v=q.get(key); last=(i==len(qtrs)-1)
            st=' style="background:#E6FAF5;font-weight:800;color:#009B77"' if last else ""
            cells+=f"<td{st}>{v:,.0f}{suf}</td>" if isinstance(v,(int,float)) else f"<td{st}>N/A</td>"
        return f"<tr><td>{lbl}</td>{cells}</tr>"
    qtr_beat="".join(f'<td class="beat"{"  style=\"background:#E6FAF5\"" if i==len(qtrs)-1 else ""}>BEAT</td>' for i in range(len(qtrs)))
    qtr_body=qrow("Revenue","rev")+qrow("Net Profit","np")+qrow("EPS (₹)","eps")+qrow("OPM %","opm","%")+f"<tr><td>Result</td>{qtr_beat}</tr>"

    # Returns table
    ret_rows=""
    for lbl,key in [("1 Day","1D"),("2 Days","2D"),("5 Days","5D"),("7 Days","7D"),
                    ("1 Week","1W"),("1 Month","1M"),("2 Months","2M"),("6 Months","6M")]:
        v=ret.get(key)
        if v is None: cell='<td style="color:#9CA3AF">N/A</td>'
        else:
            col="#00C896" if v>=0 else "#F43F5E"; s2="+" if v>=0 else ""
            cell=f'<td style="font-weight:800;color:{col}">{s2}{v:.2f}%</td>'
        ret_rows+=f"<tr><td>{lbl}</td>{cell}</tr>"

    # PE
    cur_pe=pe_an.get("cur_pe"); pe5=pe_an.get("pe5"); pe10=pe_an.get("pe10")
    sect_pe=pe_an.get("sect_pe"); verdict=pe_an.get("verdict","N/A"); vc3=pe_an.get("vc","#9CA3AF")
    peer_html="".join(
        f'<tr><td>{p}</td><td style="text-align:right;font-weight:700;color:{"#F43F5E" if cur_pe and peval and float(cur_pe)>float(peval)*1.2 else "#00C896"}">{peval:.1f}x</td></tr>'
        for p,peval in list(pe_an.get("peers",{}).items())[:5] if peval
    ) or '<tr><td colspan="2" style="color:#9CA3AF">N/A</td></tr>'

    # Value analysis
    va_score=va.get("score",0); va_verdict=va.get("verdict","N/A")
    va_col="#00C896" if va_score>=65 else ("#F59E0B" if va_score>=50 else "#F43F5E")
    va_remarks="".join(f'<div class="va-rem">{r}</div>' for r in va.get("remarks",[])[:6])

    # Shareholding
    lat=sha.get("latest",{})
    sh_bars=(
        _sh_bar("Promoter",lat.get("promoter"),"#111827",sha.get("promoter_chg"))+
        _sh_bar("FII / FPI",lat.get("fii"),"#00C896",sha.get("fii_chg"))+
        _sh_bar("DII / MF",lat.get("dii"),"#009B77",sha.get("dii_chg"))+
        _sh_bar("Public",lat.get("public"),"#9CA3AF",None)
    )
    sh_signal=sha.get("signal","N/A")
    sh_sc="#00C896" if "BULL" in sh_signal else ("#F43F5E" if "BEAR" in sh_signal else "#F59E0B")
    sh_remarks="".join(f'<div class="va-rem">{r}</div>' for r in sha.get("remarks",[])[:4])
    sh_hist_hdrs="".join(f"<th>{d.get('q','')}</th>" for d in sh_data[-6:])
    sh_hist_rows="".join(
        f'<tr><td>{lbl}</td>'+"".join(f"<td>{d.get(key):.1f}%</td>" if d.get(key) else "<td>—</td>" for d in sh_data[-6:])+f"</tr>"
        for key,lbl in [("promoter","Promoter"),("fii","FII"),("dii","DII"),("public","Public")]
    )

    # Patterns
    pat_html=""
    for p in patterns:
        pc2="#00C896" if p["direction"]=="bullish" else ("#F43F5E" if p["direction"]=="bearish" else "#F59E0B")
        ar="↑" if p["direction"]=="bullish" else ("↓" if p["direction"]=="bearish" else "→")
        pat_html+=f'<div class="pat-card"><div class="pat-head"><span class="pat-name">{ar} {p["name"]}</span><span style="color:{pc2};font-size:10px">{p["confidence"]}%</span></div><div class="pat-desc">{p["description"]}</div></div>'
    if not pat_html: pat_html='<div style="color:#9CA3AF;font-size:10px;padding:4px 0">No patterns detected</div>'

    # Risk
    def rb(lbl,k):
        t,c=risk_r.get(k,("N/A","low"))
        cls="rlow" if c=="low" else ("rmed" if c=="med" else "rhigh")
        return f'<div class="risk-r"><span class="risk-l">{lbl}</span><span class="{cls}">{t}</span></div>'
    ot,oc=risk_r.get("overall",("N/A","low")); ocls="rlow" if oc=="low" else ("rmed" if oc=="med" else "rhigh")
    risk_html=(rb("Market","market")+rb("Sector","sector")+rb("Company","company")+
               rb("Financial","financial")+rb("Liquidity","liquidity")+
               f'<div class="risk-r" style="border-top:1px solid #E5E7EB;margin-top:3px;padding-top:4px"><span class="risk-l" style="font-weight:800">Overall</span><span class="{ocls}">{ot}</span></div>')

    pos_html="".join(f'<div class="trg pos">{t}</div>' for t in pos[:5])
    neg_html="".join(f'<div class="trg neg">{t}</div>' for t in neg[:4])

    oi_rows="".join(
        f"<tr><td>{r['date'][5:]}</td><td style='text-align:right'>{fvol(r['oi'])}</td><td style='text-align:right'>₹{r['ltp']:,.1f}</td></tr>"
        for r in (fno_oi or [])[-5:]
    ) or '<tr><td colspan="3" style="color:#9CA3AF">Non-FnO</td></tr>'

    act=sc["action"]
    act_col="#00C896" if act=="BUY" else ("#F59E0B" if act=="HOLD" else "#F43F5E")
    t1s=f"₹{ret.get('t3m'):,.2f}" if ret.get('t3m') else "N/A"
    t2s=f"₹{ret.get('t6m'):,.2f}" if ret.get('t6m') else "N/A"
    t3s=f"₹{ret.get('t1y'):,.2f}" if ret.get('t1y') else "N/A"
    cagr1y=ret.get("cagr1y")

    # SMA json for chart
    sma_json=json.dumps({str(k):v for k,v in sma_vals.items()})

    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>MarketVeda — {sym}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0F0F0F;font-family:'Segoe UI',system-ui,sans-serif;font-size:12px;color:#111827;padding:12px;display:flex;flex-direction:column;align-items:center}}
.card{{background:#fff;border-radius:14px;border:2px solid #00C896;box-shadow:0 0 0 1px rgba(0,200,150,.15),0 0 35px rgba(0,200,150,.28),0 0 80px rgba(0,200,150,.10),0 20px 60px rgba(0,0,0,.5);width:100%;max-width:1380px;overflow:hidden}}
.hdr{{background:#fff;padding:9px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #00C896}}
.hdr-t1{{font-size:16px;font-weight:900;color:#111827;letter-spacing:1.5px}}
.hdr-t2{{font-size:9px;color:#9CA3AF;letter-spacing:2px;margin-top:1px}}
.hdr-meta{{display:flex;gap:18px;align-items:center}}
.hdr-mi{{display:flex;flex-direction:column;align-items:flex-end}}
.hdr-ml{{font-size:9px;color:#9CA3AF;letter-spacing:1px;text-transform:uppercase}}
.hdr-mv{{font-size:11px;font-weight:800;color:#111827;margin-top:1px}}
.live-b{{background:#00C896;color:#fff;font-size:10px;font-weight:800;padding:3px 10px;border-radius:4px;display:flex;align-items:center;gap:4px}}
.dot{{width:6px;height:6px;border-radius:50%;background:#fff;animation:blink 1.4s ease-in-out infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.nse-b{{background:#00C896;color:#fff;font-size:10px;font-weight:800;padding:2px 10px;border-radius:4px}}
.btns{{display:flex;gap:6px}}
.btn{{padding:5px 12px;border-radius:4px;border:none;cursor:pointer;font-size:11px;font-weight:700}}
.btn-t{{background:#00C896;color:#fff}}
.btn-o{{background:transparent;border:1px solid #E5E7EB;color:#6B7280}}
.body{{padding:12px 14px}}
.sec{{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;padding-bottom:3px;border-bottom:2px solid #00C896;color:#009B77}}
.panel{{background:#fff;border-radius:8px;border:1px solid #E5E7EB;padding:10px 12px;box-shadow:0 1px 4px rgba(0,200,150,.06)}}
.panel:hover{{border-color:#00C896;box-shadow:0 0 12px rgba(0,200,150,.15);transition:.3s}}
.row{{display:grid;gap:10px;margin-bottom:10px}}
.r1{{grid-template-columns:.9fr .8fr 2.5fr 1fr}}
.r2{{grid-template-columns:1fr 1fr 1fr 1fr}}
.r3{{grid-template-columns:1.1fr 1fr .85fr .85fr}}
.r4{{grid-template-columns:1.6fr .65fr 1.75fr}}
.r5{{grid-template-columns:1fr 1fr 1fr 1fr;margin-bottom:0}}
.co-name{{font-size:22px;font-weight:900;color:#00C896;margin-bottom:3px;line-height:1;text-shadow:0 0 12px rgba(0,200,150,.3)}}
.co-full{{font-size:9px;color:#9CA3AF;margin-bottom:8px}}
.ov-grid{{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px}}
.ov-l{{font-size:9px;color:#9CA3AF;text-transform:uppercase;letter-spacing:.8px}}
.ov-v{{font-size:11px;font-weight:700;color:#111827;margin-top:1px}}
.cmp{{font-size:32px;font-weight:900;color:#111827;letter-spacing:-1px;line-height:1;font-variant-numeric:tabular-nums}}
.ohlc-g{{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px;margin-top:7px}}
.oh-l{{font-size:9px;color:#9CA3AF;text-transform:uppercase;letter-spacing:.8px}}
.oh-v{{font-size:11px;font-weight:700;color:#111827;font-variant-numeric:tabular-nums}}
/* CHART */
.chart-toolbar{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:4px}}
.tf-row{{display:flex;gap:3px;flex-wrap:wrap}}
.tf-btn{{padding:2px 8px;border-radius:3px;border:1px solid #E5E7EB;background:transparent;color:#9CA3AF;font-size:10px;cursor:pointer;font-weight:600;transition:.15s}}
.tf-btn.active,.tf-btn:hover{{background:#00C896;color:#fff;border-color:#00C896;box-shadow:0 0 8px rgba(0,200,150,.35)}}
#chartWrap{{position:relative;height:360px;background:#F4FDFB;border-radius:6px;border:1px solid #D1FAF0}}
#volWrap{{height:55px;background:#F4FDFB;border-radius:0 0 6px 6px;border:1px solid #D1FAF0;border-top:none;margin-top:-2px}}
/* TECH */
.ts-r{{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid #F3F4F6}}
.ts-r:last-child{{border-bottom:none}}
.ts-l{{font-size:11px;color:#374151}}
.ts-v{{font-size:11px;font-weight:700;color:#111827}}
.bull{{color:#00C896;font-weight:800}}
.bear{{color:#F43F5E;font-weight:800}}
table{{width:100%;border-collapse:collapse;font-size:11px}}
th{{font-size:9px;color:#fff;background:#009B77;letter-spacing:1px;text-transform:uppercase;text-align:left;padding:4px 6px}}
th:not(:first-child){{text-align:right}}
td{{padding:3px 6px;border-bottom:1px solid #F3F4F6;color:#111827;font-variant-numeric:tabular-nums}}
td:not(:first-child){{text-align:right}}
tr:last-child td{{border-bottom:none}}
tr:nth-child(even) td{{background:#F4FDFB}}
.sigb{{color:#00C896;font-weight:800}}
.sigr{{color:#F43F5E;font-weight:800}}
.beat{{color:#00C896;font-weight:800;font-size:10px}}
.val-g{{display:grid;grid-template-columns:1fr 1fr;gap:5px}}
.val-c{{background:#F4FDFB;border:1px solid #D1FAF0;border-radius:6px;padding:6px 8px;text-align:center}}
.val-l{{font-size:9px;color:#9CA3AF;text-transform:uppercase;letter-spacing:.8px}}
.val-v{{font-size:15px;font-weight:900;color:#111827;margin-top:2px}}
.vol-lbl{{font-size:9px;color:#9CA3AF;text-transform:uppercase;letter-spacing:.8px;margin-bottom:2px}}
.vol-v{{font-size:16px;font-weight:900;color:#111827;font-variant-numeric:tabular-nums}}
.risk-r{{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid #F3F4F6}}
.risk-r:last-child{{border-bottom:none}}
.risk-l{{font-size:11px;color:#374151}}
.rlow{{background:#E6FAF5;color:#009B77;font-size:10px;font-weight:800;padding:2px 8px;border-radius:4px}}
.rmed{{background:#FEF9EE;color:#D97706;font-size:10px;font-weight:800;padding:2px 8px;border-radius:4px}}
.rhigh{{background:#FFF0F3;color:#F43F5E;font-size:10px;font-weight:800;padding:2px 8px;border-radius:4px}}
.sr-r{{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #F3F4F6;font-size:11px}}
.sr-r:last-child{{border-bottom:none}}
.trg{{font-size:10px;padding:2px 0 2px 6px;line-height:1.4;margin-bottom:2px}}
.trg.pos{{border-left:2px solid #00C896;color:#374151}}
.trg.neg{{border-left:2px solid #F43F5E;color:#374151}}
.conf-bar{{height:5px;background:#E5E7EB;border-radius:3px;overflow:hidden;margin-top:3px}}
.conf-fill{{height:100%;background:#00C896;border-radius:3px;box-shadow:0 0 6px rgba(0,200,150,.5)}}
.pat-card{{background:#F4FDFB;border:1px solid #D1FAF0;border-radius:6px;padding:6px 8px;margin-bottom:5px}}
.pat-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:2px}}
.pat-name{{font-size:11px;font-weight:800;color:#111827}}
.pat-desc{{font-size:10px;color:#6B7280;line-height:1.4}}
.va-rem{{font-size:10px;color:#374151;padding:2px 0 2px 5px;border-left:2px solid #D1FAF0;margin-bottom:3px;line-height:1.4}}
.sh-row{{margin-bottom:7px}}
.sh-meta{{display:flex;justify-content:space-between;align-items:center;margin-bottom:2px}}
.sh-lbl{{font-size:10px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.8px}}
.sh-track{{height:5px;background:#E5E7EB;border-radius:3px;overflow:hidden}}
.sh-fill{{height:100%;border-radius:3px}}
.ee-grid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:11px}}
.ee-c{{border-radius:6px;padding:5px 7px;border:1px solid #E5E7EB}}
.ee-l{{font-size:9px;color:#9CA3AF;text-transform:uppercase;letter-spacing:.8px;margin-bottom:1px}}
.ee-v{{font-size:12px;font-weight:800;color:#111827}}
.tgt-note{{font-size:9px;color:#9CA3AF;margin-top:4px;padding:3px 6px;background:#F4FDFB;border-radius:4px;border-left:2px solid #D1FAF0}}
.dl{{display:flex;flex-direction:column;gap:3px;margin-top:4px}}
.dl-r{{display:flex;align-items:center;gap:5px;font-size:10px;color:#374151}}
.dot2{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.note{{font-size:10px;color:#374151;padding:3px 0 3px 6px;border-left:2px solid #00C896;margin-bottom:4px;line-height:1.4}}
</style></head><body>
<div class="card">
<div class="hdr">
  <div><div class="hdr-t1">⚡ MARKET VEDA</div><div class="hdr-t2">Complete Stock Intelligence · Institutional Grade</div></div>
  <div class="hdr-meta">
    <div class="hdr-mi"><span class="hdr-ml">Date</span><span class="hdr-mv">{data.get("date_str","")}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Time</span><span class="hdr-mv">{data.get("time_str","")}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Sector</span><span class="hdr-mv" style="color:#00C896">{sector}</span></div>
    <div class="nse-b">NSE</div>
    <div class="live-b"><div class="dot"></div>Live</div>
  </div>
  <div class="btns">
    <button class="btn btn-o" onclick="window.print()">🖨 PDF</button>
    <button class="btn btn-t" onclick="dlPage()">⬇ Save</button>
  </div>
</div>
<div class="body">

<div class="row r1">
  <div class="panel">
    <div class="sec">Overview</div>
    <div class="co-name">{sym}</div><div class="co-full">{name}</div>
    <div class="ov-grid">
      <div><div class="ov-l">Market Cap</div><div class="ov-v">{fv(km.get("Market Cap"),pre="₹",suf=" Cr") if km else "N/A"}</div></div>
      <div><div class="ov-l">52W H / L</div><div class="ov-v">{"₹"+str(h52)+" / ₹"+str(l52) if h52 else "N/A"}</div></div>
      <div><div class="ov-l">P/E (TTM)</div><div class="ov-v">{str(km.get("P/E","N/A"))+"x" if km and km.get("P/E") else "N/A"}</div></div>
      <div><div class="ov-l">Book Value</div><div class="ov-v">{fv(km.get("Book Value"),pre="₹") if km else "N/A"}</div></div>
      <div><div class="ov-l">ROE</div><div class="ov-v" style="color:#00C896">{str(km.get("ROE %","N/A"))+"%" if km and km.get("ROE %") else "N/A"}</div></div>
      <div><div class="ov-l">RS / Nifty</div><div class="ov-v" style="color:{'#00C896' if rs>=1 else '#F43F5E'}">{rs:.2f}</div></div>
      <div><div class="ov-l">ATR (14)</div><div class="ov-v">{fv(atr14,pre="₹") if atr14 else "N/A"}</div></div>
      <div><div class="ov-l">Minervini</div><div class="ov-v" style="color:{'#00C896' if mn['pass'] else '#F43F5E'}">{'✅' if mn['pass'] else '❌'} {mn['stage']}</div></div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Current Price</div>
    <div class="cmp">₹{ltp:,.2f}</div>
    <div style="font-size:13px;font-weight:700;margin-top:3px;color:{cc}">{ca} {abs(chg):.2f} ({abs(chgp):.2f}%)</div>
    <div class="ohlc-g">
      <div><div class="oh-l">Open</div><div class="oh-v">{ohlc["o"]:,.2f}</div></div>
      <div><div class="oh-l">High</div><div class="oh-v" style="color:#00C896">{ohlc["h"]:,.2f}</div></div>
      <div><div class="oh-l">Low</div><div class="oh-v" style="color:#F43F5E">{ohlc["l"]:,.2f}</div></div>
      <div><div class="oh-l">Prev Close</div><div class="oh-v">{ohlc["pc"]:,.2f}</div></div>
      <div><div class="oh-l">VWAP</div><div class="oh-v">{fv(vwap_v,pre="₹") if vwap_v else "N/A"}</div></div>
      <div><div class="oh-l">Vol Today</div><div class="oh-v">{fvol(ohlc["vol"])}</div></div>
      <div><div class="oh-l">Avg Vol 20D</div><div class="oh-v">{fvol(avg20)}</div></div>
      <div><div class="oh-l">P/B</div><div class="oh-v">{str(km.get("Price to Book","N/A"))+"x" if km and km.get("Price to Book") else "N/A"}</div></div>
    </div>
  </div>

  <div class="panel" style="padding:10px 12px">
    <div class="sec">Price Chart · Candlestick + Volume + DMA Overlays</div>
    <div class="chart-toolbar">
      <div class="tf-row">
        <button class="tf-btn active" onclick="setTF('1M',this)">1M</button>
        <button class="tf-btn" onclick="setTF('2M',this)">2M</button>
        <button class="tf-btn" onclick="setTF('3M',this)">3M</button>
        <button class="tf-btn" onclick="setTF('6M',this)">6M</button>
        <button class="tf-btn" onclick="setTF('1Y',this)">1Y</button>
        <button class="tf-btn" onclick="setTF('2Y',this)">2Y</button>
        <button class="tf-btn" onclick="setTF('5Y',this)">5Y</button>
      </div>
      <div style="font-size:9px;color:#9CA3AF;display:flex;gap:8px;flex-wrap:wrap">
        <span style="color:#00C896">— DMA10</span>
        <span style="color:#009B77">— DMA20</span>
        <span style="color:#F59E0B">— DMA50</span>
        <span style="color:#374151">— DMA100</span>
        <span style="color:#F43F5E">— DMA200</span>
      </div>
    </div>
    <div id="chartWrap"><canvas id="pc"></canvas></div>
    <div id="volWrap"><canvas id="vc"></canvas></div>
  </div>

  <div class="panel">
    <div class="sec">Technical Summary</div>
    <div class="ts-r"><span class="ts-l">Trend</span><span class="{'bull' if chg>=0 else 'bear'}">{'Bullish ▲' if chg>=0 else 'Bearish ▼'}</span></div>
    <div class="ts-r"><span class="ts-l">RSI (14)</span><span class="ts-v {'bull' if rsi_v and 30<rsi_v<70 else 'bear' if rsi_v and rsi_v>70 else ''}">{rsi_v if rsi_v else "N/A"}</span></div>
    <div class="ts-r"><span class="ts-l">MACD</span><span class="{mc}">{ml}</span></div>
    <div class="ts-r"><span class="ts-l">ADX (14)</span><span class="ts-v">{adx_v if adx_v else "N/A"}</span></div>
    <div class="ts-r"><span class="ts-l">Stoch RSI</span><span class="{sc3}">{sl2}</span></div>
    <div class="ts-r"><span class="ts-l">CCI (20)</span><span class="ts-v">{cci_v if cci_v else "N/A"}</span></div>
    <div class="ts-r"><span class="ts-l">RS Percentile</span><span class="{'bull' if rs>=1 else 'bear'}">{rsp}/99</span></div>
    <div class="ts-r"><span class="ts-l">MAs Bullish</span><span class="{'bull' if bull_n>=3 else 'bear'}">{bull_n}/4</span></div>
    <div class="ts-r"><span class="ts-l">CMP vs SMA20</span><span class="{'bull' if dev20>=0 else 'bear'}">{dev20:+.1f}%</span></div>
    <div class="ts-r"><span class="ts-l">CMP vs SMA200</span><span class="{'bull' if dev200>=0 else 'bear'}">{dev200:+.1f}%</span></div>
  </div>
</div>

<div class="row r2">
  <div class="panel">
    <div class="sec">Moving Averages</div>
    <table><thead><tr><th>Period</th><th>SMA</th><th>EMA</th><th>Signal</th></tr></thead><tbody>{ma_rows}</tbody></table>
    <div style="margin-top:5px;padding:4px 7px;background:#F4FDFB;border-radius:5px;border-left:3px solid #00C896;font-size:10px">
      <span style="font-weight:800;color:#00C896">{bull_n}/4 MAs Bullish</span> · SMA20 {dev20:+.1f}% · SMA200 {dev200:+.1f}%
    </div>
  </div>
  <div class="panel">
    <div class="sec">Valuation Metrics</div>
    <div class="val-g">
      <div class="val-c"><div class="val-l">P/E (TTM)</div><div class="val-v">{str(km.get("P/E","N/A"))+"x" if km and km.get("P/E") else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">P/B Ratio</div><div class="val-v">{str(km.get("Price to Book","N/A"))+"x" if km and km.get("Price to Book") else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">PEG</div><div class="val-v" style="color:{'#00C896' if va.get('peg') and va['peg']<1 else '#F59E0B'}">{str(va.get('peg','N/A'))+"x" if va.get('peg') else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">EV/EBITDA</div><div class="val-v">{km.get("EV/EBITDA","N/A") if km else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">Rev CAGR 5Y</div><div class="val-v" style="color:#00C896">{str(fp.get("rev_cagr","N/A"))+"%" if fp.get("rev_cagr") else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">PAT CAGR 5Y</div><div class="val-v" style="color:#00C896">{str(fp.get("np_cagr","N/A"))+"%" if fp.get("np_cagr") else "N/A"}</div></div>
    </div>
  </div>
  <div class="panel">
    <div class="sec">Volume Analysis</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px">
      <div><div class="vol-lbl">Avg Vol 20D</div><div class="vol-v">{fvol(avg20)}</div></div>
      <div><div class="vol-lbl">Today's Vol</div><div class="vol-v">{fvol(ohlc["vol"])}</div></div>
    </div>
    <div style="margin-bottom:5px"><div class="vol-lbl">vs Average</div>
      <div style="font-size:13px;font-weight:800;color:{vc2}">{'▲' if vol_pct>=0 else '▼'} {abs(vol_pct):.1f}% {'Above' if vol_pct>=0 else 'Below'}</div></div>
    <div><div class="vol-lbl">Delivery %</div>
      <div style="font-size:12px;font-weight:700;color:{'#00C896' if deliv_pct and deliv_pct>40 else '#9CA3AF'}">{f"{deliv_pct:.1f}%" if deliv_pct else "N/A"}</div></div>
  </div>
  <div class="panel"><div class="sec">Risk Analysis</div>{risk_html}</div>
</div>

<div class="row r3">
  <div class="panel">
    <div class="sec">Financial Summary (₹ Cr) · Annual</div>
    <table><thead><tr><th>Metric</th>{ann_hdr}</tr></thead><tbody>{ann_body}</tbody></table>
    <div style="margin-top:5px;display:flex;gap:6px;flex-wrap:wrap">
      <div style="background:#E6FAF5;border-radius:8px;padding:2px 8px;font-size:10px;font-weight:700;color:#009B77">Rev CAGR: {str(fp.get("rev_cagr","N/A"))+"%" if fp.get("rev_cagr") else "N/A"}</div>
      <div style="background:#E6FAF5;border-radius:8px;padding:2px 8px;font-size:10px;font-weight:700;color:#009B77">PAT CAGR: {str(fp.get("np_cagr","N/A"))+"%" if fp.get("np_cagr") else "N/A"}</div>
    </div>
  </div>
  <div class="panel">
    <div class="sec">Key Triggers</div>
    <div style="font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;color:#00C896">✅ Positive</div>
    {pos_html}
    <div style="height:4px"></div>
    <div style="font-size:9px;font-weight:800;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;color:#F43F5E">⚠️ Risks</div>
    {neg_html}
  </div>
  <div class="panel">
    <div class="sec">S&amp;R · Pivot</div>
    <div class="sr-r"><span style="color:#9CA3AF">R3</span><span style="font-weight:700;color:#F43F5E">{pp.get("r3","N/A")}</span></div>
    <div class="sr-r"><span style="color:#9CA3AF">R2</span><span style="font-weight:700;color:#F43F5E">{pp.get("r2","N/A")}</span></div>
    <div class="sr-r"><span style="color:#9CA3AF">R1</span><span style="font-weight:700;color:#F43F5E">{pp.get("r1","N/A")}</span></div>
    <div class="sr-r" style="border-top:2px solid #00C896;border-bottom:2px solid #00C896;margin:3px 0;padding:4px 0">
      <span style="font-weight:900">PIVOT</span><span style="font-weight:900;color:#111827">{pp.get("pivot","N/A")}</span></div>
    <div class="sr-r"><span style="color:#9CA3AF">S1</span><span style="font-weight:700;color:#00C896">{pp.get("s1","N/A")}</span></div>
    <div class="sr-r"><span style="color:#9CA3AF">S2</span><span style="font-weight:700;color:#00C896">{pp.get("s2","N/A")}</span></div>
    <div class="sr-r"><span style="color:#9CA3AF">S3</span><span style="font-weight:700;color:#00C896">{pp.get("s3","N/A")}</span></div>
  </div>
  <div class="panel">
    <div class="sec">Recommendation</div>
    <div style="font-size:42px;font-weight:900;line-height:1;color:{act_col};text-shadow:0 0 15px {act_col}44">{act}</div>
    <div style="margin-top:6px"><div class="vol-lbl">Target (Pivot R2)</div>
      <div style="font-size:17px;font-weight:900;color:#111827">{f"₹{sc.get('target'):,.2f}" if sc.get("target") else "N/A"}</div></div>
    <div style="margin-top:4px"><div class="vol-lbl">Upside</div>
      <div style="font-size:14px;font-weight:800;color:#00C896">{'+' if sc.get('up',0)>=0 else ''}{sc.get('up','N/A')}%</div></div>
    <div style="margin-top:4px">
      <div style="display:flex;justify-content:space-between;margin-bottom:2px">
        <span class="vol-lbl">Confidence</span><span style="font-size:13px;font-weight:900;color:#00C896">{sc.get('conf',0)}%</span></div>
      <div class="conf-bar"><div class="conf-fill" style="width:{sc.get('conf',0)}%"></div></div></div>
    <div style="margin-top:5px;font-size:10px;color:#6B7280">SL: <b style="color:#F43F5E">{f"₹{sc.get('sl'):,.2f}" if sc.get("sl") else "N/A"}</b> · R:R <b>1:{sc.get('rr','N/A')}</b></div>
  </div>
</div>

<div class="row r4">
  <div class="panel">
    <div class="sec">Results Tracker — Last 8 Quarters</div>
    <table><thead><tr><th>Quarter</th>{qtr_hdr}</tr></thead><tbody>{qtr_body}</tbody></table>
  </div>
  <div class="panel">
    <div class="sec">Analyst Sentiment</div>
    <div style="display:flex;align-items:center;gap:10px">
      <canvas id="dc" width="80" height="80"></canvas>
      <div>
        <div style="font-size:20px;font-weight:900;color:#00C896">{sent["bp"]}%</div>
        <div style="font-size:10px;font-weight:700;color:#00C896">{sent["cons"]}</div>
        <div class="dl">
          <div class="dl-r"><div class="dot2" style="background:#00C896"></div><span>BUY {sent["bp"]}%</span></div>
          <div class="dl-r"><div class="dot2" style="background:#009B77"></div><span>HOLD {sent["hp"]}%</span></div>
          <div class="dl-r"><div class="dot2" style="background:#F43F5E"></div><span>SELL {sent["sp"]}%</span></div>
        </div>
      </div>
    </div>
  </div>
  <div class="panel">
    <div class="sec">Notes &amp; Insights</div>
    <div class="note">Minervini: {mn["stage"]} — {mn["n"]}/6 filters. {'Qualifies for momentum.' if mn["pass"] else 'Not in Stage 2.'}</div>
    <div class="note">RS vs Nifty50: {rs:.2f} ({rsp} pctl). {'Outperforming ✅' if rs>=1 else 'Underperforming ⚠️'}</div>
    <div class="note">1Y trailing CAGR: {f"{cagr1y:+.1f}%" if cagr1y else "N/A"} (historical only)</div>
    <div class="note">Targets = Pivot R1/R2/R3: {t1s} / {t2s} / {t3s}</div>
    <div class="note">PE: {verdict} — {pe_an.get("vs","")}</div>
  </div>
</div>

<div class="row r5">
  <div class="panel">
    <div class="sec">Price Move History</div>
    <table><thead><tr><th>Period</th><th>Return %</th></tr></thead><tbody>
    {ret_rows}
    <tr style="background:#F4FDFB"><td colspan="2" style="font-size:9px;font-weight:800;padding:4px 6px;color:#009B77">📌 Pivot-Based Targets</td></tr>
    <tr><td>T1 (R1)</td><td style="text-align:right;font-weight:800;color:#00C896">{t1s}</td></tr>
    <tr><td>T2 (R2)</td><td style="text-align:right;font-weight:800;color:#00C896">{t2s}</td></tr>
    <tr><td>T3 (R3)</td><td style="text-align:right;font-weight:800;color:#00C896">{t3s}</td></tr>
    </tbody></table>
  </div>
  <div class="panel">
    <div class="sec">PE Valuation Analysis</div>
    <div style="background:{vc3}18;border:1px solid {vc3}30;border-radius:6px;padding:5px;margin-bottom:6px;text-align:center;font-size:10px;font-weight:900;color:{vc3}">{verdict}</div>
    <table style="margin-bottom:5px">
      <thead><tr><th>PE Metric</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>Current P/E</td><td style="text-align:right;font-weight:800;color:{vc3}">{str(cur_pe)+"x" if cur_pe else "N/A"}</td></tr>
        <tr><td>5Y Mean PE</td><td style="text-align:right">{str(pe5)+"x" if pe5 else "N/A"}</td></tr>
        <tr><td>10Y Mean PE</td><td style="text-align:right">{str(pe10)+"x" if pe10 else "N/A"}</td></tr>
        <tr><td>Sector PE</td><td style="text-align:right">{str(sect_pe)+"x" if sect_pe else "N/A"}</td></tr>
        <tr><td>PEG Ratio</td><td style="text-align:right;font-weight:700;color:{'#00C896' if va.get('peg') and va['peg']<1 else '#F59E0B'}">{str(va.get('peg','N/A'))+"x" if va.get('peg') else "N/A"}</td></tr>
      </tbody></table>
    <div class="vol-lbl" style="margin-bottom:2px">Peer Comparison</div>
    <table><tbody>{peer_html}</tbody></table>
  </div>
  <div class="panel">
    <div class="sec">Entry / Exit Strategy</div>
    <div class="ee-grid">
      <div class="ee-c" style="background:#E6FAF5;border-color:#D1FAF0"><div class="ee-l">Entry Zone</div><div class="ee-v" style="color:#009B77">₹{ee["el"]:,.2f}–₹{ee["eh"]:,.2f}</div></div>
      <div class="ee-c" style="background:#FFF0F3;border-color:#FECDD3"><div class="ee-l">Stop Loss</div><div class="ee-v" style="color:#F43F5E">₹{ee["sl"]:,.2f}</div></div>
      <div class="ee-c" style="background:#E6FAF5;border-color:#D1FAF0"><div class="ee-l">T1 (R1)</div><div class="ee-v" style="color:#009B77">₹{ee["t1"]:,.2f}</div></div>
      <div class="ee-c" style="background:#E6FAF5;border-color:#D1FAF0"><div class="ee-l">T2 (R2)</div><div class="ee-v" style="color:#009B77">₹{ee["t2"]:,.2f}</div></div>
      <div class="ee-c" style="background:#E6FAF5;border-color:#D1FAF0"><div class="ee-l">T3 (R3)</div><div class="ee-v" style="color:#009B77">₹{ee["t3"]:,.2f}</div></div>
      <div class="ee-c" style="background:#FEF9EE;border-color:#FDE68A"><div class="ee-l">R:R Ratio</div><div class="ee-v" style="color:#D97706">1:{ee["rr"]}</div></div>
    </div>
    <div class="tgt-note">⚠️ Targets = Pivot R1/R2/R3 — not CAGR forecast</div>
    <div style="margin-top:8px"><div class="sec">Chart Patterns</div>{pat_html}</div>
  </div>
  <div class="panel">
    <div class="sec">Institutional Value Score</div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
      <div style="font-size:28px;font-weight:900;color:{va_col};text-shadow:0 0 10px {va_col}44">{va_score}</div>
      <div><div style="font-size:10px;font-weight:800;color:{va_col}">{va_verdict}</div><div style="font-size:9px;color:#9CA3AF;margin-top:1px">/ 100</div></div>
    </div>
    {va_remarks}
    <div style="margin-top:8px;border-top:1px solid #E5E7EB;padding-top:7px">
      <div class="sec">Shareholding Pattern</div>
      <div style="display:inline-block;padding:2px 9px;border-radius:10px;font-size:10px;font-weight:800;margin-bottom:6px;background:{sh_sc}18;border:1px solid {sh_sc}35;color:{sh_sc}">{sh_signal}</div>
      {sh_bars}{sh_remarks}
    </div>
    {"" if not sh_hist_rows else f'<div style="margin-top:7px;border-top:1px solid #E5E7EB;padding-top:6px"><div class="sec">Shareholding History</div><table><thead><tr><th>Entity</th>{sh_hist_hdrs}</tr></thead><tbody>{sh_hist_rows}</tbody></table></div>'}
    <div style="margin-top:7px;border-top:1px solid #E5E7EB;padding-top:6px">
      <div class="sec">F&amp;O OI &amp; Delivery</div>
      <div style="margin-bottom:5px"><div class="vol-lbl">Delivery %</div>
        <div style="font-size:13px;font-weight:800;color:{'#00C896' if deliv_pct and deliv_pct>40 else '#9CA3AF'}">{f"{deliv_pct:.1f}%" if deliv_pct else "N/A"}</div></div>
      <table><thead><tr><th>Date</th><th>OI</th><th>LTP</th></tr></thead><tbody>{oi_rows}</tbody></table>
    </div>
  </div>
</div>
</div></div>

<script>
const FULL={chart_full};
const SR={sr_json};
const LTP={ltp};
const SMA={sma_json};
const PC_VAL={ohlc["pc"]};

// Compute SMAs from raw data
function computeSMA(data, n){{
  const out=Array(data.length).fill(null);
  for(let i=n-1;i<data.length;i++){{
    let s=0; for(let j=i-n+1;j<=i;j++) s+=data[j].c;
    out[i]=parseFloat((s/n).toFixed(2));
  }}
  return out;
}}

let PC=null,VC=null,TF='1M';
const TF_BARS={{'1M':21,'2M':42,'3M':63,'6M':126,'1Y':252,'2Y':504,'5Y':9999}};

function dlPage(){{
  const b=new Blob([document.documentElement.outerHTML],{{type:'text/html;charset=utf-8'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(b);
  a.download='{sym}_dashboard.html';a.click();URL.revokeObjectURL(a.href);
}}

// Candle plugin
const CP={{
  id:'cp',
  afterDatasetsDraw(chart){{
    const raw=chart._raw; if(!raw||!raw.length) return;
    const {{ctx,chartArea:ca,scales:{{x,y}}}}=chart;
    const n=raw.length;
    const barW=Math.max(1.5,Math.min(10,(ca.right-ca.left)/n*0.65));
    ctx.save();
    raw.forEach((c,i)=>{{
      const xp=x.getPixelForValue(i);
      const yO=y.getPixelForValue(c.o),yC=y.getPixelForValue(c.c);
      const yH=y.getPixelForValue(c.h),yL=y.getPixelForValue(c.l);
      const bull=c.c>=c.o;
      const bT=Math.min(yO,yC),bH=Math.max(1.5,Math.abs(yC-yO));
      const col=bull?'#00C896':'#F43F5E';
      ctx.strokeStyle=col;ctx.lineWidth=1;
      ctx.shadowColor=col;ctx.shadowBlur=2;
      ctx.beginPath();ctx.moveTo(xp,yH);ctx.lineTo(xp,bT);ctx.stroke();
      ctx.beginPath();ctx.moveTo(xp,bT+bH);ctx.lineTo(xp,yL);ctx.stroke();
      ctx.shadowBlur=0;
      if(bull){{
        ctx.strokeStyle=col;ctx.lineWidth=1.2;ctx.shadowColor=col;ctx.shadowBlur=4;
        ctx.strokeRect(xp-barW/2,bT,barW,bH);
        ctx.fillStyle='rgba(0,200,150,0.08)';ctx.fillRect(xp-barW/2,bT,barW,bH);
      }}else{{
        ctx.fillStyle='rgba(244,63,94,0.75)';ctx.fillRect(xp-barW/2,bT,barW,bH);
        ctx.strokeStyle=col;ctx.lineWidth=0.8;ctx.shadowColor=col;ctx.shadowBlur=3;
        ctx.strokeRect(xp-barW/2,bT,barW,bH);
      }}
      ctx.shadowBlur=0;
    }});
    ctx.restore();
  }}
}};
Chart.register(CP);

function renderChart(){{
  if(PC){{PC.destroy();PC=null;}}
  if(VC){{VC.destroy();VC=null;}}
  const n=TF_BARS[TF]; const d=n>=FULL.length?FULL:FULL.slice(-n);
  if(!d.length) return;
  const labels=d.map((_,i)=>i);

  // Compute all DMAs from sliced data
  const dma10=computeSMA(d,10);
  const dma20=computeSMA(d,20);
  const dma50=computeSMA(d,50);
  const dma100=computeSMA(d,100);
  const dma200=computeSMA(d,200);

  PC=new Chart(document.getElementById('pc'),{{
    type:'line',
    data:{{
      labels,
      datasets:[
        {{type:'scatter',data:d.map((c,i)=>{{return{{x:i,y:c.c}}}}).filter(p=>p.y),pointRadius:0,showLine:false}},
        {{label:'DMA10', data:dma10,borderColor:'#00C896',borderWidth:1.2,pointRadius:0,showLine:true,tension:0,spanGaps:true}},
        {{label:'DMA20', data:dma20,borderColor:'#009B77',borderWidth:1.2,pointRadius:0,showLine:true,tension:0,spanGaps:true}},
        {{label:'DMA50', data:dma50,borderColor:'#F59E0B',borderWidth:1.5,pointRadius:0,showLine:true,tension:0,spanGaps:true}},
        {{label:'DMA100',data:dma100,borderColor:'#374151',borderWidth:1.2,pointRadius:0,showLine:true,tension:0,spanGaps:true}},
        {{label:'DMA200',data:dma200,borderColor:'#F43F5E',borderWidth:1.5,pointRadius:0,showLine:true,tension:0,spanGaps:true}},
      ]
    }},
    options:{{
      responsive:true,maintainAspectRatio:false,animation:{{duration:200}},
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{display:true,position:'bottom',labels:{{color:'#6B7280',font:{{size:9}},boxWidth:14,padding:8}}}},
        tooltip:{{backgroundColor:'rgba(17,24,39,.95)',borderColor:'#00C896',borderWidth:1,
          titleColor:'#fff',bodyColor:'#00C896',padding:8,displayColors:false,
          callbacks:{{
            title:items=>d[items[0].dataIndex]?d[items[0].dataIndex].t:'',
            label:c=>{{
              const raw=d[c.dataIndex];
              if(c.datasetIndex===0&&raw&&raw.o!==undefined)
                return['O: ₹'+raw.o.toFixed(2),'H: ₹'+raw.h.toFixed(2),'L: ₹'+raw.l.toFixed(2),'C: ₹'+raw.c.toFixed(2),'Vol: '+(raw.v?raw.v.toLocaleString():'N/A')];
              const labs=['','DMA10','DMA20','DMA50','DMA100','DMA200'];
              const v=c.parsed.y; return v?labs[c.datasetIndex]+': ₹'+v.toFixed(2):null;
            }}
          }}}},
        annotation:{{annotations:{{ltp:{{type:'line',yMin:LTP,yMax:LTP,borderColor:'#F59E0B',borderWidth:1.5,borderDash:[5,4],
          label:{{content:'LTP ₹'+LTP.toFixed(0),display:true,backgroundColor:'rgba(245,158,11,.9)',color:'#fff',font:{{size:9,weight:'bold'}},position:'end',yAdjust:-11}}}}}}}}
      }},
      scales:{{
        x:{{grid:{{color:'rgba(0,0,0,.04)'}},ticks:{{color:'#9CA3AF',font:{{size:9}},maxTicksLimit:10,
          callback:(v,i)=>{{const step=Math.ceil(d.length/10);return i%step===0&&d[i]?d[i].t:null;}}}}}},
        y:{{position:'right',grid:{{color:'rgba(0,200,150,.06)'}},
          ticks:{{color:'#9CA3AF',font:{{size:9}},callback:v=>'₹'+v.toLocaleString()}},
          min:(()=>{{const ls=d.map(c=>c.l).filter(Boolean);return ls.length?Math.min(...ls)*0.985:undefined}})(),
          max:(()=>{{const hs=d.map(c=>c.h).filter(Boolean);return hs.length?Math.max(...hs)*1.015:undefined}})()
        }}
      }}
    }}
  }});
  PC._raw=d;

  VC=new Chart(document.getElementById('vc'),{{
    type:'bar',
    data:{{labels,datasets:[{{data:d.map(c=>c.v||0),
      backgroundColor:d.map(c=>c.c>=c.o?'rgba(0,200,150,0.4)':'rgba(244,63,94,0.4)'),borderWidth:0}}]}},
    options:{{responsive:true,maintainAspectRatio:false,animation:{{duration:0}},
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>'Vol: '+(c.raw?c.raw.toLocaleString():'0')}}}}}},
      scales:{{x:{{display:false}},y:{{position:'right',display:false}}}}
    }}
  }});
}}

function setTF(tf,btn){{
  TF=tf;
  document.querySelectorAll('.tf-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderChart();
}}

new Chart(document.getElementById('dc'),{{
  type:'doughnut',
  data:{{datasets:[{{data:[{sent["bp"]},{sent["hp"]},{sent["sp"]}],
    backgroundColor:['#00C896','#009B77','#F43F5E'],borderWidth:0}}]}},
  options:{{responsive:false,plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}}}
}});

window.addEventListener('load',renderChart);
</script></body></html>"""
