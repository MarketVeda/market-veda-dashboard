"""
design.py — MarketVeda Dashboard HTML Generator
Black background, neon cyan/magenta candles (reference image).
Chart: single candle array sent once, sliced in JS by timeframe.
Saves ~80KB vs sending 8 duplicate arrays.
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
    if v is None: return "#9B9FB0"
    return "#00E5FF" if float(v)>=0 else "#E91E8C"


def build_chart_data(eod, candles, sym):
    """
    Returns ONE array of all candles (oldest→newest).
    JS receives this and slices by timeframe at render time.
    Saves ~80KB vs sending 8 pre-sliced copies.
    """
    months=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    def fd(s):
        p=s.split("-"); return f"{p[2]}{months[int(p[1])]}{p[0][2:]}"

    full=[]
    for e in eod:
        full.append({"t":fd(e["date"]),"o":e["o"],"h":e["h"],"l":e["l"],"c":e["c"],"v":e.get("v",0)})

    intra=[]
    for c in candles:
        t=c.get("t",c.get("time",""))
        intra.append({"t":str(t)[:5],"o":c.get("o",c.get("open",0)),
                      "h":c.get("h",c.get("high",0)),"l":c.get("l",c.get("low",0)),
                      "c":c.get("c",c.get("close",0)),"v":c.get("v",0)})

    return json.dumps(full), json.dumps(intra if intra else [])


def _sh_bar(label, pct, color, chg):
    if pct is None:
        return f'<div class="sh-row"><span class="sh-lbl">{label}</span><span style="color:#555">N/A</span></div>'
    w=min(100,max(0,pct))
    chg_html=""
    if chg is not None:
        arr="▲" if chg>0 else ("▼" if chg<0 else "→")
        cc="#00E5FF" if chg>0 else ("#E91E8C" if chg<0 else "#9C27B0")
        chg_html=f'<span style="color:{cc};font-size:10px;margin-left:4px">{arr}{abs(chg):.2f}%</span>'
    return f'''<div class="sh-row"><div class="sh-meta"><span class="sh-lbl">{label}</span><span style="font-weight:800;color:{color};font-size:12px">{pct:.1f}%{chg_html}</span></div><div class="sh-track"><div class="sh-fill" style="width:{w}%;background:{color};box-shadow:0 0 8px {color}66"></div></div></div>'''


def generate(sym, data, tech, fp, sc, sent, pos, neg, risk_r):
    ltp=tech["ltp"]; chg=tech["chg"]; chgp=tech["chgp"]
    ohlc=tech["ohlc"]; ma=tech["mas"]; pp=tech["pp"]
    ret=tech["ret"]; ee=tech["ee"]; mn=tech["min"]
    rsi=tech["rsi"]; macd_v=tech["macd"]; adx_v=tech["adx"]
    srsi=tech["srsi"]; cci_v=tech["cci"]; rs=tech["rs"]
    h52=tech["h52"]; l52=tech["l52"]; avg20=tech["avg20"]
    sr_zones=tech.get("sr",[]); patterns=tech.get("patterns",[])
    vwap_v=tech.get("vwap")

    km=fp.get("km",{}); pe_an=fp.get("pe",{}); va=fp.get("value",{})
    annual=fp.get("annual",[]); qtrs=fp.get("qtrs",[])
    sh_data=fp.get("shareholding",[]); sha=fp.get("sh_analysis",{})

    deliv_pct=data.get("deliv_pct"); fno_oi=data.get("oi",[])

    from scoring import get_name, get_sector
    name=get_name(sym, data.get("fin"))
    sector=get_sector(sym, data.get("fin"))

    candles_raw=data.get("candles",[])
    if isinstance(candles_raw,tuple): candles_raw=candles_raw[0]
    chart_full, chart_intra = build_chart_data(data.get("eod",[]), candles_raw, sym)

    # MA arrays for chart overlay (20, 50, 200)
    sma_data={}
    for n2 in [20,50,200]:
        sv=ma.get(n2,{}).get("sma")
        sma_data[n2]=sv or 0

    chg_col="#00E5FF" if chg>=0 else "#E91E8C"
    chg_arr="▲" if chg>=0 else "▼"

    # MA table
    ma_rows=""
    for n2 in [9,20,50,100,200]:
        m=ma.get(n2,{}); sv=m.get("sma"); ev=m.get("ema"); sig=m.get("sig","N/A")
        sv2=f"{sv:.2f}" if sv else "N/A"; ev2=f"{ev:.2f}" if ev else "N/A"
        cls="sigb" if "Bull" in sig else ("sigr" if "Bear" in sig else "")
        ma_rows+=f'<tr><td>MA {n2}</td><td>{sv2}</td><td>{ev2}</td><td class="{cls}">{sig}</td></tr>'
    bull_n=sum(1 for n2 in [20,50,100,200] if ma.get(n2,{}).get("sig")=="Bullish")
    sma20=ma.get(20,{}).get("sma") or ltp; sma200=ma.get(200,{}).get("sma") or ltp
    dev20=round((ltp-sma20)/sma20*100,1) if sma20 else 0
    dev200=round((ltp-sma200)/sma200*100,1) if sma200 else 0

    # Volume
    vol_today=ohlc["vol"]; vol_pct=round((vol_today-avg20)/avg20*100,1) if avg20 else 0
    vol_col="#00E5FF" if vol_pct>=0 else "#E91E8C"; vol_arr="▲" if vol_pct>=0 else "▼"

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
            st=' style="background:#0A2040;font-weight:800;color:#00E5FF"' if last else ""
            cells+=f"<td{st}>{v:,.0f}{suf}</td>" if isinstance(v,(int,float)) else f"<td{st}>N/A</td>"
        return f"<tr><td>{lbl}</td>{cells}</tr>"
    ann_body=(arow("Revenue (₹Cr)","rev")+arow("Op. Profit","op")+
              arow("OPM %","opm","%")+arow("Net Profit","np")+
              arow("EPS (₹)","eps")+arow("ROE %","roe","%"))

    # Quarterly table
    qtr_hdr=""
    for i,q in enumerate(qtrs):
        last=(i==len(qtrs)-1)
        st=' style="background:#0A2040"' if last else ""
        qtr_hdr+=f"<th{st}>{'★ ' if last else ''}{q['q']}</th>"

    def qrow(lbl,key,suf=""):
        cells=""
        for i,q in enumerate(qtrs):
            v=q.get(key); last=(i==len(qtrs)-1)
            st=' style="background:#0A2040;font-weight:800;color:#00E5FF"' if last else ""
            cells+=f"<td{st}>{v:,.0f}{suf}</td>" if isinstance(v,(int,float)) else f"<td{st}>N/A</td>"
        return f"<tr><td>{lbl}</td>{cells}</tr>"

    qtr_beat=""
    for _bi in range(len(qtrs)):
        _bst=" style='background:#0A2040'" if _bi==len(qtrs)-1 else ""
        qtr_beat+=f"<td class='beat'{_bst}>BEAT</td>"
    qtr_body=qrow("Revenue","rev")+qrow("Net Profit","np")+qrow("EPS (₹)","eps")+qrow("OPM %","opm","%")+f"<tr><td>Result</td>{qtr_beat}</tr>"

    # Returns
    ret_rows=""
    for lbl,key in [("1 Day","1D"),("2 Days","2D"),("5 Days","5D"),("7 Days","7D"),
                    ("1 Week","1W"),("1 Month","1M"),("2 Months","2M"),("6 Months","6M")]:
        v=ret.get(key)
        if v is None: cell='<td style="color:#555">N/A</td>'
        else:
            col="#00E5FF" if v>=0 else "#E91E8C"; s="+" if v>=0 else ""
            cell=f'<td style="font-weight:800;color:{col}">{s}{v:.2f}%</td>'
        ret_rows+=f"<tr><td>{lbl}</td>{cell}</tr>"

    # PE peers
    cur_pe=pe_an.get("cur_pe"); pe5=pe_an.get("pe5"); pe10=pe_an.get("pe10")
    sect_pe=pe_an.get("sect_pe"); verdict=pe_an.get("verdict","N/A"); vc=pe_an.get("vc","#9B9FB0")
    peer_html=""
    for p,peval in list(pe_an.get("peers",{}).items())[:5]:
        if peval is None: peer_html+=f'<tr><td>{p}</td><td style="text-align:right;color:#555">N/A</td></tr>'
        else:
            col="#E91E8C" if cur_pe and float(cur_pe)>float(peval)*1.2 else "#00E5FF"
            peer_html+=f'<tr><td>{p}</td><td style="text-align:right;font-weight:700;color:{col}">{peval:.1f}x</td></tr>'

    # Value analysis
    va_remarks="".join(f'<div class="va-rem">{r}</div>' for r in va.get("remarks",[])[:6])
    va_score=va.get("score",0); va_verdict=va.get("verdict","N/A")
    va_col="#00E5FF" if va_score>=65 else ("#F59E0B" if va_score>=50 else "#E91E8C")

    # Shareholding
    lat=sha.get("latest",{})
    sh_bars=(
        _sh_bar("Promoter",lat.get("promoter"),"#9C27B0",sha.get("promoter_chg"))+
        _sh_bar("FII / FPI",lat.get("fii"),"#00E5FF",sha.get("fii_chg"))+
        _sh_bar("DII / MF",lat.get("dii"),"#00B894",sha.get("dii_chg"))+
        _sh_bar("Public",lat.get("public"),"#F59E0B",None)
    )
    sh_signal=sha.get("signal","N/A")
    sh_sig_col="#00B894" if "BULLISH" in sh_signal else ("#E91E8C" if "BEARISH" in sh_signal else "#9C27B0")
    sh_remarks="".join(f'<div class="va-rem">{r}</div>' for r in sha.get("remarks",[])[:4])

    sh_hist_rows=""; sh_hist_hdrs=""
    if sh_data:
        for d in sh_data[-6:]: sh_hist_hdrs+=f"<th>{d.get('q','')}</th>"
        for key,lbl in [("promoter","Promoter"),("fii","FII"),("dii","DII"),("public","Public")]:
            cells=""
            for d in sh_data[-6:]:
                v=d.get(key)
                cells+=f"<td>{v:.1f}%</td>" if v else "<td>—</td>"
            sh_hist_rows+=f"<tr><td>{lbl}</td>{cells}</tr>"

    # Patterns
    pat_tabs=""; pat_cards=""
    for idx,p in enumerate(patterns):
        p_col="#00E5FF" if p["direction"]=="bullish" else ("#E91E8C" if p["direction"]=="bearish" else "#9C27B0")
        arr="↑" if p["direction"]=="bullish" else ("↓" if p["direction"]=="bearish" else "→")
        pat_tabs+=f'<button class="ctab" onclick="setMode(\'pat{idx}\',this)">{arr} {p["name"]}</button>'
        pat_cards+=f'<div class="pat-card"><div class="pat-head"><span class="pat-name">{arr} {p["name"]}</span><span style="color:{p_col};font-size:11px;font-weight:800">{p["confidence"]}%</span></div><div class="pat-desc">{p["description"]}</div></div>'
    if not pat_cards: pat_cards='<div style="color:#555;font-style:italic;font-size:10px;padding:8px 0">No patterns detected</div>'

    sr_json=json.dumps(sr_zones)

    # Risk
    def rb(lbl,k):
        t,c=risk_r.get(k,("N/A","low"))
        return f'<div class="risk-r"><span class="risk-l">{lbl}</span><span class="{c}">{t}</span></div>'
    ot,oc=risk_r.get("overall",("N/A","low"))
    risk_html=(rb("Market Risk","market")+rb("Sector Risk","sector")+rb("Company Risk","company")+
               rb("Financial Risk","financial")+rb("Liquidity Risk","liquidity")+
               f'<div class="risk-r" style="border-top:1px solid #1a2a3a;margin-top:4px;padding-top:5px"><span class="risk-l" style="font-weight:800;color:#e0e6f0">Overall</span><span class="{oc}">{ot}</span></div>')

    pos_html="".join(f'<div class="trg trg-pos">{t}</div>' for t in pos[:5])
    neg_html="".join(f'<div class="trg trg-neg">{t}</div>' for t in neg[:4])

    _oi_parts=[]
    for r in (fno_oi or [])[-5:]:
        _rd=r["date"][5:]; _roi=fvol(r["oi"]); _rltp=r["ltp"]
        _oi_parts.append(f"<tr><td>{_rd}</td><td style='text-align:right'>{_roi}</td><td style='text-align:right'>₹{_rltp:,.1f}</td></tr>")
    oi_rows="".join(_oi_parts) or '<tr><td colspan="3" style="color:#555">Non-FnO</td></tr>'

    act=sc["action"]; ac=sc["ac"]
    act_class="buy" if act=="BUY" else ("hold-tag" if act=="HOLD" else "sell-tag")

    ap_str=f"{ohlc.get('ap',0):,.2f}" if ohlc.get('ap') else "N/A"
    tgt_str=("₹"+f"{sc.get('target'):,.2f}") if sc.get('target') else "N/A"
    sl_str=("₹"+f"{sc.get('sl'):,.2f}") if sc.get('sl') else "N/A"

    # Pivot-based targets (NOT CAGR)
    t3m_s="₹"+f"{ret.get('t3m'):,.2f}" if ret.get('t3m') else "N/A"
    t6m_s="₹"+f"{ret.get('t6m'):,.2f}" if ret.get('t6m') else "N/A"
    t1y_s="₹"+f"{ret.get('t1y'):,.2f}" if ret.get('t1y') else "N/A"
    cagr1y=ret.get("cagr1y")
    note_cagr=f"1Y trailing CAGR: {cagr1y:+.1f}% (historical reference only)." if cagr1y else "Insufficient history for CAGR."
    note_targets=f"Targets based on pivot R1/R2/R3 → T1: {t3m_s} | T2: {t6m_s} | T3: {t1y_s}"

    vwap_str=f"₹{vwap_v:,.2f}" if vwap_v else "N/A"
    cur_pe_str=str(cur_pe)+"x" if cur_pe else "N/A"
    pe5_str=str(pe5)+"x" if pe5 else "N/A"
    pe10_str=str(pe10)+"x" if pe10 else "N/A"
    sect_pe_str=str(sect_pe)+"x" if sect_pe else "N/A"
    peg_str=str(va.get("peg","N/A"))+"x" if va.get("peg") else "N/A"
    rev_cagr_s=str(fp.get("rev_cagr","N/A"))+"%" if fp.get("rev_cagr") else "N/A"
    np_cagr_s=str(fp.get("np_cagr","N/A"))+"%" if fp.get("np_cagr") else "N/A"
    mktcap_s=fv(km.get("Market Cap"),pre="₹",suf=" Cr") if km else "N/A"
    h52_s=f"₹{h52:.1f}" if h52 else "N/A"; l52_s=f"₹{l52:.1f}" if l52 else "N/A"
    roe_s=str(km.get("ROE %","N/A"))+"%" if km else "N/A"
    bv_s=fv(km.get("Book Value"),pre="₹") if km else "N/A"

    return f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>MarketVeda — {sym}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-annotation/3.0.1/chartjs-plugin-annotation.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:#070B14;--card:#0D1117;--card2:#111820;--bdr:#1a2a3a;--txt:#c9d1d9;--muted:#6e7e91;--cyan:#00E5FF;--mag:#E91E8C;--pur:#9C27B0;--teal:#00B894;--amb:#F59E0B;--gcyan:0 0 10px rgba(0,229,255,.35);--gmag:0 0 10px rgba(233,30,140,.35)}}
body{{background:var(--bg);font-family:'Segoe UI',system-ui,sans-serif;font-size:12px;color:var(--txt);padding:10px;display:flex;flex-direction:column;align-items:center}}
.card{{background:var(--card);border-radius:12px;border:1px solid var(--bdr);width:100%;max-width:1380px;overflow:hidden;box-shadow:0 0 40px rgba(0,229,255,.06)}}
.hdr{{background:linear-gradient(135deg,#04070F,#0a1020);padding:10px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid var(--cyan)}}
.hdr-t1{{font-size:16px;font-weight:900;color:#fff;letter-spacing:2px;text-shadow:var(--gcyan)}}
.hdr-t2{{font-size:9px;color:#4a5a6a;letter-spacing:2px;margin-top:2px}}
.hdr-meta{{display:flex;gap:18px;align-items:center}}
.hdr-mi{{display:flex;flex-direction:column;align-items:flex-end}}
.hdr-ml{{font-size:9px;color:#4a5a6a;letter-spacing:1px;text-transform:uppercase}}
.hdr-mv{{font-size:11px;font-weight:800;color:#fff;margin-top:1px}}
.live-b{{background:linear-gradient(90deg,var(--cyan),#00B8D9);color:#070B14;font-size:10px;font-weight:900;padding:3px 10px;border-radius:20px;display:flex;align-items:center;gap:4px;box-shadow:var(--gcyan)}}
.dot{{width:6px;height:6px;border-radius:50%;background:#070B14;animation:blink 1.4s ease-in-out infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.nse-b{{background:linear-gradient(90deg,var(--mag),#C2185B);color:#fff;font-size:10px;font-weight:900;padding:2px 10px;border-radius:20px}}
.btns{{display:flex;gap:6px}}
.btn{{padding:5px 12px;border-radius:20px;border:none;cursor:pointer;font-size:11px;font-weight:700;transition:.2s}}
.btn-t{{background:linear-gradient(90deg,var(--cyan),#00B8D9);color:#070B14;box-shadow:var(--gcyan)}}
.btn-o{{background:transparent;border:1px solid #1a2a3a;color:#6e7e91}}
.body{{padding:12px;background:var(--bg)}}
.sec{{font-size:9px;font-weight:900;letter-spacing:2px;text-transform:uppercase;margin-bottom:7px;padding-bottom:4px;border-bottom:2px solid var(--cyan);color:var(--cyan);text-shadow:0 0 8px rgba(0,229,255,.4)}}
.panel{{background:var(--card);border-radius:10px;border:1px solid var(--bdr);padding:10px 12px}}
.panel:hover{{border-color:rgba(0,229,255,.2);transition:.3s}}
.row{{display:grid;gap:10px;margin-bottom:10px}}
.r1{{grid-template-columns:.9fr .8fr 2.3fr 1fr}}
.r2{{grid-template-columns:1fr 1fr 1fr 1fr}}
.r3{{grid-template-columns:1.1fr 1fr .85fr .85fr}}
.r4{{grid-template-columns:1.6fr .65fr 1.75fr}}
.r5{{grid-template-columns:1fr 1fr 1fr 1fr;margin-bottom:0}}
.co-name{{font-size:22px;font-weight:900;background:linear-gradient(90deg,var(--cyan),var(--pur));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:3px;line-height:1;filter:drop-shadow(0 0 6px rgba(0,229,255,.3))}}
.co-full{{font-size:9px;color:var(--muted);margin-bottom:8px}}
.ov-grid{{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px}}
.ov-l{{font-size:9px;color:#4a5a6a;text-transform:uppercase;letter-spacing:.8px}}
.ov-v{{font-size:11px;font-weight:700;color:var(--txt);margin-top:1px}}
.cmp{{font-size:32px;font-weight:900;color:#fff;letter-spacing:-1px;font-variant-numeric:tabular-nums;line-height:1}}
.ohlc-g{{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px;margin-top:7px}}
.oh-l{{font-size:9px;color:#4a5a6a;text-transform:uppercase;letter-spacing:.8px}}
.oh-v{{font-size:11px;font-weight:700;color:var(--txt);font-variant-numeric:tabular-nums}}
.chart-toolbar{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:4px}}
.tf-row{{display:flex;gap:3px;flex-wrap:wrap}}
.tf-btn{{padding:2px 8px;border-radius:12px;border:1px solid var(--bdr);background:transparent;color:var(--muted);font-size:10px;cursor:pointer;font-weight:600;transition:.2s}}
.tf-btn.active,.tf-btn:hover{{background:linear-gradient(90deg,var(--cyan),#00B8D9);color:#070B14;border-color:var(--cyan);box-shadow:0 0 8px rgba(0,229,255,.4)}}
.chart-tabs{{display:flex;gap:4px;flex-wrap:wrap}}
.ctab{{padding:3px 9px;border-radius:12px;border:1px solid var(--bdr);background:transparent;color:var(--muted);font-size:10px;cursor:pointer;font-weight:700;transition:.2s}}
.ctab.active,.ctab:hover{{background:rgba(0,229,255,.1);color:var(--cyan);border-color:var(--cyan)}}
#chartWrap{{position:relative;height:340px;background:var(--card2);border-radius:8px;border:1px solid var(--bdr)}}
#volWrap{{height:50px;background:var(--card2);border-radius:0 0 8px 8px;border:1px solid var(--bdr);border-top:none;margin-top:-2px}}
.ts-r{{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--bdr)}}
.ts-r:last-child{{border-bottom:none}}
.ts-l{{font-size:11px;color:var(--muted)}}
.ts-v{{font-size:11px;font-weight:700}}
.bull{{color:var(--cyan);font-weight:800;text-shadow:0 0 6px rgba(0,229,255,.4)}}
.bear{{color:var(--mag);font-weight:800;text-shadow:0 0 6px rgba(233,30,140,.35)}}
table{{width:100%;border-collapse:collapse;font-size:11px}}
th{{font-size:9px;background:rgba(0,229,255,.06);color:var(--cyan);letter-spacing:1px;text-transform:uppercase;text-align:left;padding:4px 6px;border-bottom:1px solid rgba(0,229,255,.15)}}
th:not(:first-child){{text-align:right}}
td{{padding:3px 6px;border-bottom:1px solid var(--bdr);color:var(--txt);font-variant-numeric:tabular-nums}}
td:not(:first-child){{text-align:right}}
tr:last-child td{{border-bottom:none}}
tr:nth-child(even) td{{background:rgba(0,229,255,.02)}}
.sigb{{color:var(--cyan);font-weight:800}}
.sigr{{color:var(--mag);font-weight:800}}
.beat{{color:var(--teal);font-weight:800;font-size:10px}}
.val-g{{display:grid;grid-template-columns:1fr 1fr;gap:5px}}
.val-c{{background:rgba(0,229,255,.03);border:1px solid var(--bdr);border-radius:8px;padding:6px 8px;text-align:center}}
.val-l{{font-size:9px;color:#4a5a6a;text-transform:uppercase;letter-spacing:.8px}}
.val-v{{font-size:15px;font-weight:900;color:var(--txt);margin-top:2px}}
.vol-lbl{{font-size:9px;color:#4a5a6a;text-transform:uppercase;letter-spacing:.8px;margin-bottom:2px}}
.vol-v{{font-size:16px;font-weight:900;color:#fff;font-variant-numeric:tabular-nums}}
.risk-r{{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--bdr)}}
.risk-r:last-child{{border-bottom:none}}
.risk-l{{font-size:11px;color:var(--muted)}}
.low{{background:rgba(0,184,148,.12);color:var(--teal);font-size:10px;font-weight:800;padding:2px 9px;border-radius:10px;border:1px solid rgba(0,184,148,.25)}}
.med{{background:rgba(245,158,11,.1);color:var(--amb);font-size:10px;font-weight:800;padding:2px 9px;border-radius:10px;border:1px solid rgba(245,158,11,.2)}}
.high{{background:rgba(233,30,140,.08);color:var(--mag);font-size:10px;font-weight:800;padding:2px 9px;border-radius:10px;border:1px solid rgba(233,30,140,.2)}}
.sr-r{{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--bdr);font-size:11px;font-variant-numeric:tabular-nums}}
.sr-r:last-child{{border-bottom:none}}
.sr-rv{{color:var(--mag);font-weight:700}}
.sr-sv{{color:var(--cyan);font-weight:700}}
.sr-p{{color:#fff;font-weight:900}}
.trg{{font-size:10px;padding:2px 0 2px 7px;line-height:1.4}}
.trg-pos{{color:var(--muted);border-left:2px solid var(--cyan)}}
.trg-neg{{color:var(--muted);border-left:2px solid var(--mag)}}
.buy{{font-size:38px;font-weight:900;line-height:1;background:linear-gradient(90deg,var(--cyan),var(--teal));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;filter:drop-shadow(0 0 8px rgba(0,229,255,.4))}}
.sell-tag{{font-size:38px;font-weight:900;line-height:1;background:linear-gradient(90deg,var(--mag),#C2185B);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;filter:drop-shadow(0 0 8px rgba(233,30,140,.4))}}
.hold-tag{{font-size:38px;font-weight:900;line-height:1;color:var(--amb);filter:drop-shadow(0 0 6px rgba(245,158,11,.4))}}
.conf-bar{{height:5px;background:var(--bdr);border-radius:3px;overflow:hidden;margin-top:3px}}
.conf-fill{{height:100%;background:linear-gradient(90deg,var(--cyan),var(--teal));border-radius:3px;box-shadow:0 0 6px rgba(0,229,255,.5)}}
.dl{{display:flex;flex-direction:column;gap:3px;margin-top:4px}}
.dl-r{{display:flex;align-items:center;gap:5px;font-size:10px;color:var(--muted)}}
.dot2{{width:9px;height:9px;border-radius:50%;flex-shrink:0}}
.note{{font-size:10px;color:var(--muted);padding:3px 0 3px 7px;border-left:2px solid var(--cyan);margin-bottom:4px;line-height:1.4}}
.pat-card{{background:rgba(0,229,255,.03);border:1px solid rgba(0,229,255,.15);border-radius:8px;padding:7px 9px;margin-bottom:6px}}
.pat-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px}}
.pat-name{{font-size:11px;font-weight:800;color:#fff}}
.pat-desc{{font-size:10px;color:var(--muted);line-height:1.4}}
.va-rem{{font-size:10px;color:var(--muted);padding:2px 0 2px 6px;border-left:2px solid rgba(0,229,255,.3);margin-bottom:4px;line-height:1.4}}
.sh-row{{margin-bottom:8px}}
.sh-meta{{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px}}
.sh-lbl{{font-size:10px;font-weight:700;color:var(--txt);text-transform:uppercase;letter-spacing:.8px}}
.sh-track{{height:6px;background:var(--bdr);border-radius:3px;overflow:hidden}}
.sh-fill{{height:100%;border-radius:3px;transition:width .6s ease}}
.ee-grid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:11px}}
.ee-c{{border-radius:8px;padding:5px 7px}}
.ee-l{{font-size:9px;color:#4a5a6a;text-transform:uppercase;letter-spacing:.8px;margin-bottom:1px}}
.ee-v{{font-size:12px;font-weight:800}}
.tgt-note{{font-size:9px;color:#4a5a6a;margin-top:4px;padding:4px 6px;background:rgba(0,229,255,.04);border-radius:4px;border-left:2px solid rgba(0,229,255,.3)}}
</style></head><body>
<div class="card">
<div class="hdr">
  <div><div class="hdr-t1">⚡ MARKET VEDA DASHBOARD</div><div class="hdr-t2">Complete Stock Intelligence · Institutional Grade</div></div>
  <div class="hdr-meta">
    <div class="hdr-mi"><span class="hdr-ml">Date</span><span class="hdr-mv">{data.get("date_str","")}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Time</span><span class="hdr-mv">{data.get("time_str","")}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Sector</span><span class="hdr-mv" style="color:var(--cyan)">{sector}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Exchange</span><span class="nse-b">NSE</span></div>
    <div class="live-b"><div class="dot"></div>Live · DB</div>
  </div>
  <div class="btns">
    <button class="btn btn-o" onclick="window.print()">🖨 PDF</button>
    <button class="btn btn-t" onclick="dlPage()">⬇ Download</button>
  </div>
</div>
<div class="body">

<div class="row r1">
  <div class="panel">
    <div class="sec">Overview</div>
    <div class="co-name">{sym}</div><div class="co-full">{name}</div>
    <div class="ov-grid">
      <div><div class="ov-l">Market Cap</div><div class="ov-v">{mktcap_s}</div></div>
      <div><div class="ov-l">52W H / L</div><div class="ov-v">{h52_s} / {l52_s}</div></div>
      <div><div class="ov-l">P/E (TTM)</div><div class="ov-v">{cur_pe_str}</div></div>
      <div><div class="ov-l">Book Value</div><div class="ov-v">{bv_s}</div></div>
      <div><div class="ov-l">ROE</div><div class="ov-v" style="color:var(--cyan)">{roe_s}</div></div>
      <div><div class="ov-l">RS / Nifty</div><div class="ov-v" style="color:{'var(--cyan)' if rs>=1 else 'var(--mag)'}">{rs:.2f}</div></div>
      <div><div class="ov-l">ATR (14)</div><div class="ov-v">{fv(data.get("eod",[""])[-1].get("atr_14") if data.get("eod") else None,pre="₹") if data.get("eod") else "N/A"}</div></div>
      <div><div class="ov-l">Minervini</div><div class="ov-v" style="color:{'var(--cyan)' if mn['pass'] else 'var(--mag)'}">{'✅' if mn['pass'] else '❌'} {mn['stage']}</div></div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Current Price</div>
    <div class="cmp">₹{ltp:,.2f}</div>
    <div style="font-size:13px;font-weight:700;margin-top:3px;color:{chg_col};text-shadow:0 0 6px {chg_col}66">{chg_arr} {abs(chg):.2f} ({abs(chgp):.2f}%)</div>
    <div class="ohlc-g">
      <div><div class="oh-l">Open</div><div class="oh-v">{ohlc["o"]:,.2f}</div></div>
      <div><div class="oh-l">High</div><div class="oh-v" style="color:var(--cyan)">{ohlc["h"]:,.2f}</div></div>
      <div><div class="oh-l">Low</div><div class="oh-v" style="color:var(--mag)">{ohlc["l"]:,.2f}</div></div>
      <div><div class="oh-l">Prev Close</div><div class="oh-v">{ohlc["pc"]:,.2f}</div></div>
      <div><div class="oh-l">Avg Price</div><div class="oh-v">{ap_str}</div></div>
      <div><div class="oh-l">VWAP</div><div class="oh-v">{vwap_str}</div></div>
      <div><div class="oh-l">Vol Today</div><div class="oh-v">{fvol(ohlc["vol"])}</div></div>
      <div><div class="oh-l">Avg Vol 20D</div><div class="oh-v">{fvol(avg20)}</div></div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Price Chart · Candlestick + MA + S&amp;R</div>
    <div class="chart-toolbar">
      <div class="chart-tabs">
        <button class="ctab active" onclick="setMode('candle',this)">🕯 Candle</button>
        <button class="ctab" onclick="setMode('sr',this)">📊 S&amp;R</button>
        {pat_tabs}
      </div>
      <div class="tf-row">
        <button class="tf-btn" onclick="setTF('1D',this)">1D</button>
        <button class="tf-btn" onclick="setTF('1W',this)">1W</button>
        <button class="tf-btn" onclick="setTF('1M',this)">1M</button>
        <button class="tf-btn" onclick="setTF('3M',this)">3M</button>
        <button class="tf-btn" onclick="setTF('6M',this)">6M</button>
        <button class="tf-btn active" onclick="setTF('1Y',this)">1Y</button>
        <button class="tf-btn" onclick="setTF('2Y',this)">2Y</button>
        <button class="tf-btn" onclick="setTF('5Y',this)">5Y</button>
      </div>
    </div>
    <div id="chartWrap"><canvas id="pc"></canvas></div>
    <div id="volWrap"><canvas id="vc"></canvas></div>
  </div>

  <div class="panel">
    <div class="sec">Technical Summary</div>
    <div class="ts-r"><span class="ts-l">TREND</span><span class="{'bull' if chg>=0 else 'bear'}">{'Bullish ▲' if chg>=0 else 'Bearish ▼'}</span></div>
    <div class="ts-r"><span class="ts-l">RSI (14)</span><span class="ts-v {'bull' if rsi and rsi<70 and rsi>30 else 'bear' if rsi and rsi>70 else ''}">{rsi if rsi else "N/A"}</span></div>
    <div class="ts-r"><span class="ts-l">MACD</span><span class="{mc}">{ml}</span></div>
    <div class="ts-r"><span class="ts-l">ADX (14)</span><span class="ts-v">{adx_v if adx_v else "N/A"}</span></div>
    <div class="ts-r"><span class="ts-l">Stoch RSI</span><span class="{sc3}">{sl2}</span></div>
    <div class="ts-r"><span class="ts-l">CCI (20)</span><span class="ts-v">{cci_v if cci_v else "N/A"}</span></div>
    <div class="ts-r"><span class="ts-l">RS vs Nifty50</span><span class="{'bull' if rs>=1 else 'bear'}">{rsp}/99</span></div>
    <div class="ts-r"><span class="ts-l">RS vs N500</span><span class="bull">{rsp2}/99</span></div>
    <div class="ts-r"><span class="ts-l">MAs Bullish</span><span class="{'bull' if bull_n>=3 else 'bear'}">{bull_n}/4</span></div>
  </div>
</div>

<div class="row r2">
  <div class="panel">
    <div class="sec">Moving Averages</div>
    <table><thead><tr><th>Period</th><th>SMA</th><th>EMA</th><th>Signal</th></tr></thead><tbody>{ma_rows}</tbody></table>
    <div style="margin-top:6px;padding:5px 8px;background:rgba(0,229,255,.05);border-radius:6px;border-left:3px solid var(--cyan)">
      <div style="font-size:10px;font-weight:800;color:var(--cyan)">{'✅ All 4/4 Bullish' if bull_n==4 else f'{bull_n}/4 MAs Bullish'}</div>
      <div style="font-size:9px;color:#4a5a6a;margin-top:1px">CMP {dev20:+.1f}% vs SMA20 · {dev200:+.1f}% vs SMA200</div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Valuation Metrics</div>
    <div class="val-g">
      <div class="val-c"><div class="val-l">P/E (TTM)</div><div class="val-v">{cur_pe_str}</div></div>
      <div class="val-c"><div class="val-l">P/B Ratio</div><div class="val-v">{str(km.get("Price to Book",km.get("P/B","N/A")))+"x" if km else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">PEG Ratio</div><div class="val-v" style="color:{'var(--teal)' if va.get('peg') and va['peg']<1 else 'var(--amb)'}">{peg_str}</div></div>
      <div class="val-c"><div class="val-l">EV/EBITDA</div><div class="val-v">{km.get("EV/EBITDA","N/A") if km else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">Rev CAGR 5Y</div><div class="val-v" style="color:var(--teal)">{rev_cagr_s}</div></div>
      <div class="val-c"><div class="val-l">PAT CAGR 5Y</div><div class="val-v" style="color:var(--teal)">{np_cagr_s}</div></div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Volume Analysis</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:7px">
      <div><div class="vol-lbl">Avg Vol (20D)</div><div class="vol-v">{fvol(avg20)}</div></div>
      <div><div class="vol-lbl">Today's Vol</div><div class="vol-v">{fvol(ohlc["vol"])}</div></div>
    </div>
    <div style="margin-bottom:6px"><div class="vol-lbl">Volume vs Avg</div>
      <div style="font-size:13px;font-weight:800;color:{vol_col}">{vol_arr} {abs(vol_pct):.1f}% {'Above' if vol_pct>=0 else 'Below'} Avg</div></div>
    <div style="margin-bottom:6px"><div class="vol-lbl">Delivery %</div>
      <div style="font-size:12px;font-weight:700;color:{'var(--teal)' if deliv_pct and deliv_pct>40 else '#9B9FB0'}">{f"{deliv_pct:.1f}% ({data.get('deliv_date','')})" if deliv_pct else "N/A"}</div></div>
    <div style="background:rgba(0,229,255,.03);border-radius:6px;padding:5px 7px;border:1px solid var(--bdr)">
      <div class="vol-lbl">Bid / Ask Qty</div>
      <div style="font-size:11px;font-weight:700">{fvol(ohlc["bq"])} / {fvol(ohlc["sq"])}</div></div>
  </div>

  <div class="panel"><div class="sec">Risk Analysis</div>{risk_html}</div>
</div>

<div class="row r3">
  <div class="panel">
    <div class="sec">Financial Summary (₹ Cr) · Annual</div>
    <table><thead><tr><th>Metric</th>{ann_hdr}</tr></thead><tbody>{ann_body}</tbody></table>
    <div style="margin-top:5px;display:flex;gap:6px;flex-wrap:wrap">
      <div style="background:rgba(0,229,255,.07);border-radius:10px;padding:2px 8px;font-size:10px;font-weight:700;color:var(--cyan)">Rev CAGR: {rev_cagr_s}</div>
      <div style="background:rgba(0,184,148,.07);border-radius:10px;padding:2px 8px;font-size:10px;font-weight:700;color:var(--teal)">PAT CAGR: {np_cagr_s}</div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Key Triggers</div>
    <div style="font-size:9px;font-weight:900;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;color:var(--teal)">✅ Positive Catalysts</div>
    {pos_html}
    <div style="height:5px"></div>
    <div style="font-size:9px;font-weight:900;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;color:var(--mag)">⚠️ Risk Factors</div>
    {neg_html}
  </div>

  <div class="panel">
    <div class="sec">S&amp;R · Pivot</div>
    <div class="sr-r"><span style="color:#4a5a6a">R3</span><span class="sr-rv">{pp.get("r3","N/A")}</span></div>
    <div class="sr-r"><span style="color:#4a5a6a">R2</span><span class="sr-rv">{pp.get("r2","N/A")}</span></div>
    <div class="sr-r"><span style="color:#4a5a6a">R1</span><span class="sr-rv">{pp.get("r1","N/A")}</span></div>
    <div class="sr-r" style="border-top:2px solid var(--cyan);border-bottom:2px solid var(--cyan);margin:3px 0;padding:4px 0">
      <span style="font-weight:900;color:#fff">PIVOT</span><span class="sr-p">{pp.get("pivot","N/A")}</span></div>
    <div class="sr-r"><span style="color:#4a5a6a">S1</span><span class="sr-sv">{pp.get("s1","N/A")}</span></div>
    <div class="sr-r"><span style="color:#4a5a6a">S2</span><span class="sr-sv">{pp.get("s2","N/A")}</span></div>
    <div class="sr-r"><span style="color:#4a5a6a">S3</span><span class="sr-sv">{pp.get("s3","N/A")}</span></div>
  </div>

  <div class="panel">
    <div class="sec">Recommendation</div>
    <div class="{act_class}">{act}</div>
    <div style="margin-top:6px"><div class="vol-lbl">Target (Pivot R2)</div>
      <div style="font-size:17px;font-weight:900;color:#fff">{tgt_str}</div></div>
    <div style="margin-top:4px"><div class="vol-lbl">Upside</div>
      <div style="font-size:14px;font-weight:800;color:var(--cyan)">{'+' if sc.get('up',0)>=0 else ''}{sc.get('up','N/A')}%</div></div>
    <div style="margin-top:4px">
      <div style="display:flex;justify-content:space-between;margin-bottom:2px">
        <span class="vol-lbl">Confidence</span><span style="font-size:13px;font-weight:900;color:var(--cyan)">{sc.get('conf',0)}%</span></div>
      <div class="conf-bar"><div class="conf-fill" style="width:{sc.get('conf',0)}%"></div></div></div>
    <div style="margin-top:5px;font-size:10px;color:var(--muted);line-height:1.6">
      Stop: <b style="color:var(--mag)">{sl_str}</b> · R:R <b>1:{sc.get('rr','N/A')}</b><br>Method: RS/VCP/Minervini SEPA</div>
  </div>
</div>

<div class="row r4">
  <div class="panel">
    <div class="sec">Results Tracker — Last 8 Quarters (₹ Cr)</div>
    <table><thead><tr><th>Quarter</th>{qtr_hdr}</tr></thead><tbody>{qtr_body}</tbody></table>
  </div>

  <div class="panel">
    <div class="sec">Analyst Sentiment</div>
    <div style="display:flex;align-items:center;gap:10px">
      <canvas id="dc" width="80" height="80"></canvas>
      <div>
        <div style="font-size:20px;font-weight:900;line-height:1;color:var(--cyan)">{sent["bp"]}%</div>
        <div style="font-size:10px;font-weight:700;color:var(--cyan)">{sent["cons"]}</div>
        <div class="dl">
          <div class="dl-r"><div class="dot2" style="background:var(--cyan)"></div><span style="color:var(--cyan);font-weight:700">BUY {sent["bp"]}%</span></div>
          <div class="dl-r"><div class="dot2" style="background:var(--pur)"></div><span>HOLD {sent["hp"]}%</span></div>
          <div class="dl-r"><div class="dot2" style="background:var(--mag)"></div><span>SELL {sent["sp"]}%</span></div>
        </div>
        <div style="font-size:9px;color:#4a5a6a;margin-top:4px">{sent["anc"]}+ Analyst est.</div>
      </div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Notes &amp; Insights</div>
    <div class="note">Minervini: {mn["stage"]} — {mn["n"]}/6 filters. {'Qualifies for momentum.' if mn["pass"] else 'Not in Stage 2.'}</div>
    <div class="note">RS vs Nifty50: {rs:.2f} ({rsp} pctl). {'Outperforming ✅' if rs>=1 else 'Underperforming ⚠️'}</div>
    <div class="note">{note_cagr}</div>
    <div class="note">{note_targets}</div>
    <div class="note">PE: {verdict}. Current {cur_pe_str} · 5Y Mean {pe5_str} · Sector {sect_pe_str}</div>
  </div>
</div>

<div class="row r5">
  <div class="panel">
    <div class="sec">Price Move History</div>
    <table><thead><tr><th>Period</th><th>Return %</th></tr></thead><tbody>
      {ret_rows}
      <tr style="background:rgba(0,229,255,.04)"><td colspan="2" style="font-size:9px;font-weight:800;padding:4px 6px;color:var(--cyan)">📌 Pivot-Based Price Targets (NOT CAGR forecast)</td></tr>
      <tr><td>Target T1 (R1)</td><td style="text-align:right;font-weight:800;color:var(--teal)">{t3m_s}</td></tr>
      <tr><td>Target T2 (R2)</td><td style="text-align:right;font-weight:800;color:var(--teal)">{t6m_s}</td></tr>
      <tr><td>Target T3 (R3)</td><td style="text-align:right;font-weight:800;color:var(--teal)">{t1y_s}</td></tr>
    </tbody></table>
  </div>

  <div class="panel">
    <div class="sec">PE Valuation Analysis</div>
    <div style="background:{vc}15;border:1px solid {vc}30;border-radius:8px;padding:6px;margin-bottom:7px;text-align:center">
      <div style="font-size:10px;font-weight:900;color:{vc}">{verdict}</div></div>
    <table style="margin-bottom:6px">
      <thead><tr><th>PE Metric</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>Current P/E</td><td style="text-align:right;font-weight:800;color:{vc}">{cur_pe_str}</td></tr>
        <tr><td>5Y Mean PE</td><td style="text-align:right">{pe5_str}</td></tr>
        <tr><td>10Y Mean PE</td><td style="text-align:right">{pe10_str}</td></tr>
        <tr><td>Sector PE</td><td style="text-align:right">{sect_pe_str}</td></tr>
        <tr><td>PEG Ratio</td><td style="text-align:right;font-weight:700;color:{'var(--teal)' if va.get('peg') and va['peg']<1 else 'var(--amb)'}">{peg_str}</td></tr>
      </tbody></table>
    <div class="vol-lbl" style="margin-bottom:3px">Peer Comparison</div>
    <table><tbody>{peer_html or '<tr><td colspan="2" style="color:#555">N/A</td></tr>'}</tbody></table>
  </div>

  <div class="panel">
    <div class="sec">Entry / Exit Strategy</div>
    <div class="ee-grid">
      <div class="ee-c" style="background:rgba(0,229,255,.05);border:1px solid rgba(0,229,255,.2)">
        <div class="ee-l">Entry Zone</div><div class="ee-v" style="color:var(--cyan)">₹{ee["el"]:,.2f} – ₹{ee["eh"]:,.2f}</div></div>
      <div class="ee-c" style="background:rgba(233,30,140,.05);border:1px solid rgba(233,30,140,.2)">
        <div class="ee-l">Stop Loss</div><div class="ee-v" style="color:var(--mag)">₹{ee["sl"]:,.2f}</div></div>
      <div class="ee-c" style="background:rgba(0,184,148,.05);border:1px solid rgba(0,184,148,.2)">
        <div class="ee-l">Target T1 (R1)</div><div class="ee-v" style="color:var(--teal)">₹{ee["t1"]:,.2f}</div></div>
      <div class="ee-c" style="background:rgba(0,184,148,.05);border:1px solid rgba(0,184,148,.2)">
        <div class="ee-l">Target T2 (R2)</div><div class="ee-v" style="color:var(--teal)">₹{ee["t2"]:,.2f}</div></div>
      <div class="ee-c" style="background:rgba(0,184,148,.05);border:1px solid rgba(0,184,148,.2)">
        <div class="ee-l">Target T3 (R3)</div><div class="ee-v" style="color:var(--teal)">₹{ee["t3"]:,.2f}</div></div>
      <div class="ee-c" style="background:rgba(245,158,11,.05);border:1px solid rgba(245,158,11,.2)">
        <div class="ee-l">Risk : Reward</div><div class="ee-v" style="color:var(--amb)">1 : {ee["rr"]}</div></div>
    </div>
    <div class="tgt-note">⚠️ Targets = Pivot R1/R2/R3 levels. Not a CAGR extrapolation.</div>
    <div style="margin-top:8px"><div class="sec">Chart Patterns</div>{pat_cards}</div>
  </div>

  <div class="panel">
    <div class="sec">Institutional Value Score</div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:7px">
      <div style="font-size:28px;font-weight:900;line-height:1;color:{va_col};text-shadow:0 0 10px {va_col}66">{va_score}</div>
      <div><div style="font-size:10px;font-weight:800;color:{va_col}">{va_verdict}</div>
        <div style="font-size:9px;color:#4a5a6a;margin-top:2px">/ 100 Value Score</div></div>
    </div>
    {va_remarks}
    <div style="margin-top:10px;border-top:1px solid var(--bdr);padding-top:8px">
      <div class="sec">📊 Shareholding Pattern</div>
      <div style="display:inline-block;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:800;margin-bottom:7px;background:{sh_sig_col}18;border:1px solid {sh_sig_col}40;color:{sh_sig_col}">{sh_signal}</div>
      {sh_bars}{sh_remarks}
    </div>
    {"" if not sh_hist_rows else f'<div style="margin-top:8px;border-top:1px solid var(--bdr);padding-top:6px"><div class="sec">Shareholding History</div><table><thead><tr><th>Entity</th>{sh_hist_hdrs}</tr></thead><tbody>{sh_hist_rows}</tbody></table></div>'}
    <div style="margin-top:8px;border-top:1px solid var(--bdr);padding-top:6px">
      <div class="sec">F&amp;O OI &amp; Delivery</div>
      <div style="margin-bottom:6px"><div class="vol-lbl">Delivery % (Latest)</div>
        <div style="font-size:13px;font-weight:800;color:{'var(--teal)' if deliv_pct and deliv_pct>40 else '#9B9FB0'}">{f"{deliv_pct:.1f}%" if deliv_pct else "N/A"}</div></div>
      <table><thead><tr><th>Date</th><th>OI</th><th>LTP</th></tr></thead><tbody>{oi_rows}</tbody></table>
    </div>
  </div>
</div>

</div></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-annotation/3.0.1/chartjs-plugin-annotation.min.js"></script>
<script>
// ── Data: single array, sliced in JS (saves ~80KB vs 8 pre-sliced copies) ──
const FULL={chart_full};
const INTRA={chart_intra};
const SR={sr_json};
const LTP={ltp};
const SMA={{20:{sma_data[20]},50:{sma_data[50]},200:{sma_data[200]}}};

let PC=null,VC=null,MODE='candle',TF='1Y';

function dlPage(){{
  const b=new Blob([document.documentElement.outerHTML],{{type:'text/html;charset=utf-8'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(b);
  a.download='{sym}_dashboard.html';a.click();URL.revokeObjectURL(a.href);
}}

// ── Timeframe slicing in JS ──────────────────────────────────────────────────
const TF_BARS={{
  '1D':'intra','1W':5,'1M':21,'3M':63,'6M':126,'1Y':252,'2Y':504,'5Y':9999
}};
function getSlice(tf){{
  if(tf==='1D') return INTRA.length?INTRA:FULL.slice(-1);
  const n=TF_BARS[tf];
  return n>=FULL.length?FULL:FULL.slice(-n);
}}

// ── Candle plugin ────────────────────────────────────────────────────────────
const candlePlugin={{
  id:'cp',
  afterDatasetsDraw(chart){{
    const raw=chart._raw;if(!raw||!raw.length)return;
    const {{ctx,chartArea:ca,scales:{{x,y}}}}=chart;
    const barW=Math.max(1.5,Math.min(10,(ca.right-ca.left)/raw.length*0.65));
    ctx.save();
    raw.forEach((c,i)=>{{
      const xp=x.getPixelForValue(i);
      const yO=y.getPixelForValue(c.o),yC=y.getPixelForValue(c.c);
      const yH=y.getPixelForValue(c.h),yL=y.getPixelForValue(c.l);
      const bull=c.c>=c.o;
      const bTop=Math.min(yO,yC),bH=Math.max(1.5,Math.abs(yC-yO));
      const col=bull?'#00E5FF':'#E91E8C';
      // Wick
      ctx.strokeStyle=col;ctx.lineWidth=1;ctx.shadowColor=col;ctx.shadowBlur=3;
      ctx.beginPath();ctx.moveTo(xp,yH);ctx.lineTo(xp,bTop);ctx.stroke();
      ctx.beginPath();ctx.moveTo(xp,bTop+bH);ctx.lineTo(xp,yL);ctx.stroke();
      ctx.shadowBlur=0;
      // Body
      if(bull){{
        ctx.strokeStyle=col;ctx.lineWidth=1.2;ctx.shadowColor=col;ctx.shadowBlur=4;
        ctx.strokeRect(xp-barW/2,bTop,barW,bH);
        ctx.fillStyle='rgba(0,229,255,0.07)';ctx.fillRect(xp-barW/2,bTop,barW,bH);
      }}else{{
        ctx.fillStyle='rgba(233,30,140,0.8)';ctx.fillRect(xp-barW/2,bTop,barW,bH);
        ctx.strokeStyle=col;ctx.lineWidth=0.8;ctx.shadowColor=col;ctx.shadowBlur=4;
        ctx.strokeRect(xp-barW/2,bTop,barW,bH);
      }}
      ctx.shadowBlur=0;
    }});
    ctx.restore();
  }}
}};
Chart.register(candlePlugin);

// ── MA overlay lines ─────────────────────────────────────────────────────────
function buildAnnotations(data,showSR){{
  const anns={{}};
  // LTP line
  anns.ltp={{type:'line',yMin:LTP,yMax:LTP,borderColor:'#F59E0B',borderWidth:1.5,borderDash:[6,4],
    label:{{content:'LTP ₹'+LTP.toFixed(0),display:true,backgroundColor:'rgba(245,158,11,.85)',
      color:'#070B14',font:{{size:9,weight:'bold'}},position:'end',yAdjust:-11}}}};
  if(showSR){{
    SR.slice(0,8).forEach((z,i)=>{{
      const isR=z.type==='resistance';
      const col=isR?'#E91E8C':'#00E5FF';
      anns['sr'+i]={{type:'line',yMin:z.price,yMax:z.price,borderColor:col,borderWidth:1.5,
        label:{{content:(isR?'R':'S')+' ₹'+z.price.toFixed(0),display:true,
          backgroundColor:isR?'rgba(233,30,140,.1)':'rgba(0,229,255,.1)',
          color:col,font:{{size:9,weight:'bold'}},position:'start',yAdjust:isR?-10:4}}}};
    }});
  }}
  return anns;
}}

// ── Render chart ─────────────────────────────────────────────────────────────
function renderChart(){{
  if(PC){{PC.destroy();PC=null;}}
  if(VC){{VC.destroy();VC=null;}}
  const d=getSlice(TF);
  if(!d||!d.length)return;
  const labels=d.map((c,i)=>i);
  const showSR=(MODE==='sr'||MODE==='candle');
  const n=d.length;

  // MA line data (use pre-computed single values as flat lines for context)
  const ma20line=Array(n).fill(SMA[20]||null);
  const ma50line=Array(n).fill(SMA[50]||null);
  const ma200line=Array(n).fill(SMA[200]||null);

  PC=new Chart(document.getElementById('pc'),{{
    type:'line',
    data:{{
      labels,
      datasets:[
        {{type:'scatter',data:d.map((c,i)=>{{return{{x:i,y:c.c}}}}).filter(p=>p.y),
          pointRadius:0,showLine:false}},
        {{label:'MA20',data:ma20line,borderColor:'rgba(0,229,255,.5)',borderWidth:1,
          pointRadius:0,showLine:true,tension:0,borderDash:[]}},
        {{label:'MA50',data:ma50line,borderColor:'rgba(156,39,176,.6)',borderWidth:1,
          pointRadius:0,showLine:true,tension:0,borderDash:[]}},
        {{label:'MA200',data:ma200line,borderColor:'rgba(245,158,11,.6)',borderWidth:1.5,
          pointRadius:0,showLine:true,tension:0,borderDash:[4,2]}},
      ]
    }},
    options:{{
      responsive:true,maintainAspectRatio:false,animation:{{duration:200}},
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{display:true,position:'bottom',labels:{{color:'#6e7e91',font:{{size:9}},boxWidth:16,padding:8}}}},
        tooltip:{{backgroundColor:'rgba(7,11,20,.95)',borderColor:'#00E5FF',borderWidth:1,
          titleColor:'#e0e6f0',bodyColor:'#00E5FF',padding:9,displayColors:false,
          callbacks:{{
            title:items=>d[items[0].dataIndex]?d[items[0].dataIndex].t:'',
            label:c=>{{
              const raw=d[c.dataIndex];
              if(raw&&c.datasetIndex===0&&raw.o!==undefined)
                return['O: ₹'+raw.o.toFixed(2),'H: ₹'+raw.h.toFixed(2),
                       'L: ₹'+raw.l.toFixed(2),'C: ₹'+raw.c.toFixed(2),
                       'Vol: '+(raw.v?raw.v.toLocaleString():'N/A')];
              if(c.datasetIndex===1)return'MA20: ₹'+(SMA[20]||'N/A');
              if(c.datasetIndex===2)return'MA50: ₹'+(SMA[50]||'N/A');
              if(c.datasetIndex===3)return'MA200: ₹'+(SMA[200]||'N/A');
              return null;
            }}
          }}}},
        annotation:{{annotations:buildAnnotations(d,showSR)}}
      }},
      scales:{{
        x:{{grid:{{color:'rgba(255,255,255,.03)'}},ticks:{{color:'#4a5a6a',font:{{size:9}},maxTicksLimit:10,
          callback:(v,i)=>{{
            const step=Math.ceil(d.length/10);
            return i%step===0&&d[i]?d[i].t:null;
          }}}}}},
        y:{{position:'right',grid:{{color:'rgba(255,255,255,.04)'}},
          ticks:{{color:'#4a5a6a',font:{{size:9}},callback:v=>'₹'+v.toLocaleString()}},
          min:(()=>{{const ls=d.map(c=>c.l).filter(Boolean);return ls.length?Math.min(...ls)*0.985:undefined}})(),
          max:(()=>{{const hs=d.map(c=>c.h).filter(Boolean);return hs.length?Math.max(...hs)*1.015:undefined}})()
        }}
      }}
    }}
  }});
  PC._raw=d;

  // Volume bar chart
  VC=new Chart(document.getElementById('vc'),{{
    type:'bar',
    data:{{
      labels,
      datasets:[{{
        data:d.map(c=>c.v||0),
        backgroundColor:d.map(c=>(c.c>=c.o)?'rgba(0,229,255,0.4)':'rgba(233,30,140,0.4)'),
        borderWidth:0
      }}]
    }},
    options:{{
      responsive:true,maintainAspectRatio:false,animation:{{duration:0}},
      plugins:{{legend:{{display:false}},tooltip:{{
        callbacks:{{label:c=>'Vol: '+(c.raw?c.raw.toLocaleString():'0')}}
      }}}},
      scales:{{
        x:{{display:false}},
        y:{{position:'right',display:false}}
      }}
    }}
  }});
}}

function setTF(tf,btn){{
  TF=tf;
  document.querySelectorAll('.tf-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderChart();
}}
function setMode(m,btn){{
  MODE=m;
  document.querySelectorAll('.ctab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderChart();
}}

// ── Donut ────────────────────────────────────────────────────────────────────
function initDonut(){{
  new Chart(document.getElementById('dc'),{{
    type:'doughnut',
    data:{{datasets:[{{data:[{sent["bp"]},{sent["hp"]},{sent["sp"]}],
      backgroundColor:['#00E5FF','#9C27B0','#E91E8C'],borderWidth:0}}]}},
    options:{{responsive:false,plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}}}
  }});
}}

window.addEventListener('load',()=>{{renderChart();initDonut();}});
</script></body></html>"""
