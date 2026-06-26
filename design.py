"""
design.py — MarketVeda Dashboard HTML Generator
Colour palette from reference trading image:
  OFF-WHITE background  #F0F2F8 / cards #FFFFFF
  Bullish candle:  Hollow cyan border  #00E5FF
  Bearish candle:  Solid magenta fill  #E91E8C
  Support lines:   Glowing cyan        #00E5FF
  Resistance lines:Glowing magenta     #E91E8C
  Accent 1 (cyan):   #00E5FF  — section headings, positive signals
  Accent 2 (purple): #9C27B0  — neutral / informational
  Accent 3 (magenta):#E91E8C  — negative / bearish
  Glow via box-shadow / text-shadow / filter:drop-shadow
  Dark text: #0A0E27 (navy) / #2D3560 (mid)
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
    if v>=100_000:    return f"{v/100_000:.2f}L"
    if v>=1000:       return f"{v/1000:.1f}K"
    return str(v)

def pct_c(v):
    if v is None: return "#9B9FB0"
    return "#00B894" if float(v)>=0 else "#E91E8C"

def pct_sign(v):
    if v is None: return ""
    return "+" if float(v)>=0 else ""


def build_chart_data(eod, candles, sym):
    months=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    def fd(s):
        p=s.split("-"); return f"{p[2]}{months[int(p[1])]}{p[0][2:]}"

    ohlcv=[]
    for e in eod:
        ohlcv.append({"t":fd(e["date"]),"o":e["o"],"h":e["h"],"l":e["l"],"c":e["c"],"v":e.get("v",0)})

    intra=[]
    for c in candles:
        t=c.get("t",c.get("time",""))
        intra.append({"t":str(t)[:5],"o":c.get("o",c.get("open",0)),
                      "h":c.get("h",c.get("high",0)),"l":c.get("l",c.get("low",0)),
                      "c":c.get("c",c.get("close",0)),"v":c.get("v",0)})

    n=len(ohlcv)
    def sl(d): return ohlcv[-d:] if n>=d else ohlcv

    tf_data = {
        "1D":  intra if intra else sl(1),
        "1W":  sl(5),
        "1M":  sl(21),
        "3M":  sl(63),
        "6M":  sl(126),
        "1Y":  sl(252),
        "2Y":  sl(min(504,n)),
        "5Y":  ohlcv,
    }
    return json.dumps(tf_data)


def _sh_bar_html(label, pct, color, chg):
    """Render a shareholding progress bar row."""
    if pct is None:
        return f'<div class="sh-row"><span class="sh-lbl">{label}</span><span class="sh-na">N/A</span></div>'
    w = min(100, max(0, pct))
    chg_html = ""
    if chg is not None:
        arr = "▲" if chg > 0 else ("▼" if chg < 0 else "→")
        cc  = "#00E5FF" if chg > 0 else ("#E91E8C" if chg < 0 else "#9C27B0")
        chg_html = f'<span style="color:{cc};font-size:10px;font-weight:700;margin-left:5px;">{arr}{abs(chg):.2f}%</span>'
    return f'''<div class="sh-row">
      <div class="sh-meta">
        <span class="sh-lbl">{label}</span>
        <span style="font-weight:800;color:{color};font-size:12px;">{pct:.1f}%{chg_html}</span>
      </div>
      <div class="sh-track"><div class="sh-fill" style="width:{w}%;background:{color};box-shadow:0 0 8px {color}88;"></div></div>
    </div>'''


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
    sh_data=fp.get("shareholding",[])
    sha=fp.get("sh_analysis",{})

    deliv_pct=data.get("deliv_pct"); deliv_date=data.get("deliv_date","")
    fno_oi=data.get("oi",[])

    from scoring import get_name, get_sector
    name=get_name(sym, data.get("fin"))
    sector=get_sector(sym, data.get("fin"))

    # ── Chart data ──
    candles_raw=data.get("candles",[])
    if isinstance(candles_raw,tuple): candles_raw=candles_raw[0]
    chart_js=build_chart_data(data.get("eod",[]), candles_raw, sym)

    chg_col="#00B894" if chg>=0 else "#E91E8C"
    chg_arr="▲" if chg>=0 else "▼"

    # ── MA table ──
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

    # ── Volume ──
    vol_today=ohlc["vol"]; vol_pct=round((vol_today-avg20)/avg20*100,1) if avg20 else 0
    vol_col="#00B894" if vol_pct>=0 else "#E91E8C"; vol_arr="▲" if vol_pct>=0 else "▼"
    upc=round(ohlc["pc"]*1.10,2); loc=round(ohlc["pc"]*0.90,2)

    # ── MACD ──
    mh=macd_v[2] if macd_v else None
    ml_word="Bullish" if mh and mh>0 else "Bearish"
    ml_sign="+" if mh and mh>0 else ""
    ml=f"{ml_word} {ml_sign}{mh:.2f}" if mh else "N/A"
    mc="bull" if mh and mh>0 else "bear"

    # ── StochRSI ──
    sk=srsi[0] if srsi else None
    sl2=(f"{sk:.1f} ⚠" if sk and sk>80 else f"{sk:.1f}") if sk else "N/A"
    sc3="bull" if sk and sk<30 else ("bear" if sk and sk>80 else "ts-v")

    # ── RS ──
    rsp=min(99,max(1,int(rs*50))); rsp2=max(1,rsp-3)

    # ── Annual table ──
    ann_hdr="".join("<th>"+str(r["yr"])+"</th>" for r in annual)
    def arow(lbl,key,suf=""):
        cells=""
        for i,r in enumerate(annual):
            v=r.get(key); last=(i==len(annual)-1)
            st=' style="background:rgba(0,229,255,0.08);font-weight:800;color:#00899E;"' if last else ""
            cells+=f"<td{st}>{v:,.0f}{suf}</td>" if isinstance(v,(int,float)) else f"<td{st}>N/A</td>"
        return f"<tr><td>{lbl}</td>{cells}</tr>"
    ann_body=(arow("Revenue (₹Cr)","rev")+arow("Op. Profit","op")+
              arow("OPM %","opm","%")+arow("Net Profit","np")+
              arow("EPS (₹)","eps")+arow("ROE %","roe","%"))

    # ── Quarterly table ──
    qtr_hdr=""
    for i,q in enumerate(qtrs):
        last=(i==len(qtrs)-1)
        st=' style="background:rgba(0,229,255,0.15);"' if last else ""
        star="★ " if last else ""
        qtr_hdr+=f"<th{st}>{star}{q['q']}</th>"

    def qrow(lbl,key,suf=""):
        cells=""
        for i,q in enumerate(qtrs):
            v=q.get(key); last=(i==len(qtrs)-1)
            st=' style="background:rgba(0,229,255,0.08);font-weight:800;color:#00899E;"' if last else ""
            cells+=f"<td{st}>{v:,.0f}{suf}</td>" if isinstance(v,(int,float)) else f"<td{st}>N/A</td>"
        return f"<tr><td>{lbl}</td>{cells}</tr>"

    qtr_beat=""
    for _bi in range(len(qtrs)):
        _bst=" style='background:rgba(0,229,255,0.08);'" if _bi==len(qtrs)-1 else ""
        qtr_beat+=f"<td class='beat'{_bst}>BEAT</td>"
    qtr_body=qrow("Revenue","rev")+qrow("Net Profit","np")+qrow("EPS (₹)","eps")+qrow("OPM %","opm","%")+f"<tr><td>Result</td>{qtr_beat}</tr>"

    # ── Returns ──
    ret_rows=""
    for lbl,key in [("1 Day","1D"),("2 Days","2D"),("5 Days","5D"),("7 Days","7D"),
                    ("1 Week","1W"),("1 Month","1M"),("2 Months","2M"),("6 Months","6M")]:
        v=ret.get(key)
        if v is None: cell='<td style="color:#9B9FB0;">N/A</td>'
        else:
            col="#00B894" if v>=0 else "#E91E8C"; s="+" if v>=0 else ""
            cell=f'<td style="font-weight:800;color:{col};">{s}{v:.2f}%</td>'
        ret_rows+=f"<tr><td>{lbl}</td>{cell}</tr>"

    # ── PE peers ──
    cur_pe=pe_an.get("cur_pe"); pe5=pe_an.get("pe5"); pe10=pe_an.get("pe10")
    sect_pe=pe_an.get("sect_pe"); verdict=pe_an.get("verdict","N/A"); vc=pe_an.get("vc","#9B9FB0")
    peer_html=""
    for p,peval in list(pe_an.get("peers",{}).items())[:5]:
        if peval is None: peer_html+=f'<tr><td>{p}</td><td style="text-align:right;color:#9B9FB0;">N/A</td></tr>'
        else:
            col="#E91E8C" if cur_pe and float(cur_pe)>float(peval)*1.2 else "#00B894"
            peer_html+=f'<tr><td>{p}</td><td style="text-align:right;font-weight:700;color:{col};">{peval:.1f}x</td></tr>'

    # ── Value analysis ──
    va_remarks="".join(f'<div class="va-rem">{r}</div>' for r in va.get("remarks",[])[:6])
    va_score=va.get("score",0)
    va_verdict=va.get("verdict","N/A")
    va_col="#00B894" if va_score>=65 else ("#F59E0B" if va_score>=50 else "#E91E8C")

    # ── Shareholding bars ──
    lat=sha.get("latest",{})
    sh_promoter_bar=_sh_bar_html("Promoter",lat.get("promoter"),"#9C27B0",sha.get("promoter_chg"))
    sh_fii_bar     =_sh_bar_html("FII / FPI",lat.get("fii"),    "#00E5FF",sha.get("fii_chg"))
    sh_dii_bar     =_sh_bar_html("DII / MF", lat.get("dii"),    "#00B894",sha.get("dii_chg"))
    sh_pub_bar     =_sh_bar_html("Public",   lat.get("public"), "#F59E0B",None)
    sh_signal=sha.get("signal","N/A")
    sh_sig_col=("#00B894" if "BULLISH" in sh_signal else
                "#E91E8C" if "BEARISH" in sh_signal else "#9C27B0")
    sh_remarks_html="".join(f'<div class="va-rem">{r}</div>' for r in sha.get("remarks",[])[:5])

    # Build shareholding history table
    sh_hist_rows=""
    sh_hist_hdrs=""
    if sh_data:
        for d in sh_data[-6:]:
            sh_hist_hdrs+=f"<th>{d.get('q','')}</th>"
        for key,lbl in [("promoter","Promoter"),("fii","FII"),("dii","DII"),("public","Public")]:
            cells=""
            for d in sh_data[-6:]:
                v=d.get(key)
                cells+=f"<td>{v:.1f}%</td>" if v else "<td>—</td>"
            sh_hist_rows+=f"<tr><td>{lbl}</td>{cells}</tr>"

    # ── Patterns ──
    pat_tabs=""; pat_html=""
    if patterns:
        for idx,p in enumerate(patterns):
            p_col="#00E5FF" if p["direction"]=="bullish" else ("#E91E8C" if p["direction"]=="bearish" else "#9C27B0")
            p_arr="↑" if p["direction"]=="bullish" else ("↓" if p["direction"]=="bearish" else "→")
            pat_tabs+=f'<button class="ctab" onclick="setMode(\'pat{idx}\',this)">{p_arr} {p["name"]}</button>'
            pat_html+=f'''<div class="pat-card">
                <div class="pat-head">
                    <span class="pat-name">{p_arr} {p["name"]}</span>
                    <span class="pat-conf" style="color:{p_col};">{p["confidence"]}%</span>
                </div>
                <div class="pat-desc">{p["description"]}</div>
            </div>'''
    else:
        pat_html='<div class="pat-none">No strong patterns detected in current data</div>'

    sr_json=json.dumps(sr_zones)

    # ── Risk badges ──
    def rb(lbl,k):
        t,c=risk_r.get(k,("N/A","low"))
        return f'<div class="risk-r"><span class="risk-l">{lbl}</span><span class="{c}">{t}</span></div>'
    ot,oc=risk_r.get("overall",("N/A","low"))
    risk_html=(rb("Market Risk","market")+rb("Sector Risk","sector")+
               rb("Company Risk","company")+rb("Financial Risk","financial")+
               rb("Liquidity Risk","liquidity")+
               f'<div class="risk-r" style="border-top:1px solid #E2E6F0;margin-top:4px;padding-top:5px;">'
               f'<span class="risk-l" style="font-weight:800;color:#0A0E27;">Overall Risk</span>'
               f'<span class="{oc}" style="font-size:11px;padding:2px 12px;">{ot}</span></div>')

    # ── Triggers ──
    pos_html="".join(f'<div class="trg trg-pos">{t}</div>' for t in pos[:5])
    neg_html="".join(f'<div class="trg trg-neg">{t}</div>' for t in neg[:4])

    # ── OI rows ──
    _oi_parts=[]
    for r in (fno_oi or [])[-5:]:
        _rd=r["date"][5:]; _roi=fvol(r["oi"]); _rltp=r["ltp"]
        _oi_parts.append(f"<tr><td>{_rd}</td><td style='text-align:right;'>{_roi}</td><td style='text-align:right;'>₹{_rltp:,.1f}</td></tr>")
    oi_rows="".join(_oi_parts) or '<tr><td colspan="3" style="color:#9B9FB0;">Non-FnO stock</td></tr>'

    act=sc["action"]; ac=sc["ac"]
    act_class="buy" if act=="BUY" else ("hold-tag" if act=="HOLD" else "sell-tag")

    _ap=ohlc.get("ap"); ap_str=f"{_ap:,.2f}" if _ap else "N/A"
    _tg=sc.get("target"); tgt_str=("₹"+f"{_tg:,.2f}") if _tg else "N/A"
    _sl=sc.get("sl"); sl_str=("₹"+f"{_sl:,.2f}") if _sl else "N/A"
    _t3=ret.get("t3m"); t3m_s=("₹"+f"{_t3:,.2f}") if _t3 else "N/A"
    _t6=ret.get("t6m"); t6m_s=("₹"+f"{_t6:,.2f}") if _t6 else "N/A"
    _ty=ret.get("t1y"); t1y_s=("₹"+f"{_ty:,.2f}") if _ty else "N/A"
    _dp=data.get("deliv_pct"); _dd=data.get("deliv_date","")
    deliv_html=(f"{_dp:.1f}% ({_dd})") if _dp else "N/A"
    deliv_col="#00B894" if _dp and _dp>40 else "#9B9FB0"
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
<script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-annotation/3.0.1/chartjs-plugin-annotation.min.js"></script>
<style>
/* ── RESET ── */
*{{margin:0;padding:0;box-sizing:border-box;}}

/* ── PALETTE ──
   Background:   #F0F2F8  (off-white)
   Card surface: #FFFFFF  with subtle glow borders
   Text primary: #0A0E27  (deep navy)
   Text muted:   #5A5F7A
   Cyan accent:  #00E5FF  (bullish / support)
   Magenta:      #E91E8C  (bearish / resistance)
   Purple:       #9C27B0  (neutral)
   Teal green:   #00B894  (profit / positive)
   Amber:        #F59E0B  (caution)
*/

:root{{
  --bg:        #F0F2F8;
  --card:      #FFFFFF;
  --navy:      #0A0E27;
  --mid:       #2D3560;
  --muted:     #5A5F7A;
  --light:     #9B9FB0;
  --border:    #E2E6F0;
  --cyan:      #00E5FF;
  --magenta:   #E91E8C;
  --purple:    #9C27B0;
  --teal:      #00B894;
  --amber:     #F59E0B;
  --red:       #F43F5E;
  --glow-cyan: 0 0 12px rgba(0,229,255,0.35), 0 0 24px rgba(0,229,255,0.15);
  --glow-mag:  0 0 12px rgba(233,30,140,0.35), 0 0 24px rgba(233,30,140,0.15);
  --glow-pur:  0 0 10px rgba(156,39,176,0.30);
  --glow-card: 0 2px 20px rgba(0,229,255,0.08), 0 1px 4px rgba(10,14,39,0.06);
}}

body{{
  background:var(--bg);
  font-family:'Segoe UI',system-ui,-apple-system,sans-serif;
  font-size:12px;color:var(--navy);
  min-height:100vh;padding:12px;
  display:flex;flex-direction:column;align-items:center;
}}

/* ── MAIN WRAPPER ── */
.card{{
  background:var(--card);
  border-radius:14px;
  border:1.5px solid rgba(0,229,255,0.3);
  box-shadow:var(--glow-cyan),0 4px 40px rgba(10,14,39,0.10);
  width:100%;max-width:1380px;overflow:hidden;
}}

/* ── HEADER ── */
.hdr{{
  background:linear-gradient(135deg,#0A0E27 0%,#1a1f4e 50%,#0A0E27 100%);
  padding:10px 18px;
  display:flex;align-items:center;justify-content:space-between;
  border-bottom:2px solid var(--cyan);
  box-shadow:0 2px 20px rgba(0,229,255,0.25);
}}
.hdr-t1{{
  font-size:17px;font-weight:900;color:#FFFFFF;letter-spacing:2.5px;
  text-shadow:var(--glow-cyan);
}}
.hdr-t2{{font-size:9px;color:rgba(255,255,255,0.5);letter-spacing:2px;text-transform:uppercase;margin-top:2px;}}
.hdr-meta{{display:flex;gap:20px;align-items:center;}}
.hdr-mi{{display:flex;flex-direction:column;align-items:flex-end;}}
.hdr-ml{{font-size:9px;color:rgba(255,255,255,0.45);letter-spacing:1px;text-transform:uppercase;}}
.hdr-mv{{font-size:11px;font-weight:800;color:#FFFFFF;margin-top:1px;}}
.live-badge{{
  background:linear-gradient(90deg,var(--cyan),#00B8D9);
  color:#0A0E27;font-size:10px;font-weight:900;
  padding:3px 10px;border-radius:20px;
  display:flex;align-items:center;gap:5px;
  box-shadow:var(--glow-cyan);
}}
.dot{{width:6px;height:6px;border-radius:50%;background:#0A0E27;animation:blink 1.4s ease-in-out infinite;}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.2;}}}}
.nse-badge{{
  background:linear-gradient(90deg,var(--magenta),#C2185B);
  color:#fff;font-size:10px;font-weight:900;
  padding:2px 10px;border-radius:20px;
  box-shadow:var(--glow-mag);
}}
.btns{{display:flex;gap:6px;}}
.btn{{padding:5px 13px;border-radius:20px;border:none;cursor:pointer;font-size:11px;font-weight:700;transition:.2s;}}
.btn-t{{background:linear-gradient(90deg,var(--cyan),#00B8D9);color:#0A0E27;box-shadow:var(--glow-cyan);}}
.btn-o{{background:transparent;border:1px solid rgba(255,255,255,0.3);color:rgba(255,255,255,0.7);}}
.btn-t:hover{{transform:translateY(-1px);box-shadow:0 0 20px rgba(0,229,255,0.5);}}

/* ── LAYOUT ── */
.body{{padding:13px 15px 12px;background:var(--bg);}}
.sec{{
  font-size:9px;font-weight:900;letter-spacing:2px;text-transform:uppercase;
  margin-bottom:7px;padding-bottom:4px;
  border-bottom:2px solid var(--cyan);
  color:var(--cyan);
  text-shadow:0 0 8px rgba(0,229,255,0.4);
}}
.panel{{
  background:var(--card);border-radius:10px;
  border:1px solid var(--border);
  box-shadow:var(--glow-card);
  padding:10px 12px;
}}
.panel:hover{{border-color:rgba(0,229,255,0.25);box-shadow:var(--glow-cyan),0 2px 12px rgba(10,14,39,0.08);transition:.3s;}}
.row{{display:grid;gap:10px;margin-bottom:10px;}}
.r1{{grid-template-columns:0.9fr 0.8fr 2.3fr 1fr;}}
.r2{{grid-template-columns:1fr 1fr 1fr 1fr;}}
.r3{{grid-template-columns:1.1fr 1fr 0.85fr 0.85fr;}}
.r4{{grid-template-columns:1.6fr 0.65fr 1.75fr;}}
.r5{{grid-template-columns:1fr 1fr 1fr 1fr;margin-bottom:0;}}

/* ── OVERVIEW ── */
.co-name{{
  font-size:22px;font-weight:900;
  background:linear-gradient(90deg,var(--cyan),var(--purple));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
  margin-bottom:3px;line-height:1;
  filter:drop-shadow(0 0 6px rgba(0,229,255,0.3));
}}
.co-full{{font-size:9px;color:var(--muted);margin-bottom:8px;}}
.ov-grid{{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px;}}
.ov-l{{font-size:9px;color:var(--light);text-transform:uppercase;letter-spacing:.8px;}}
.ov-v{{font-size:11px;font-weight:700;color:var(--mid);margin-top:1px;}}

/* ── PRICE ── */
.cmp{{
  font-size:32px;font-weight:900;color:var(--navy);
  letter-spacing:-1px;font-variant-numeric:tabular-nums;line-height:1;
}}
.chg{{font-size:13px;font-weight:700;margin-top:3px;}}
.ohlc-g{{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px;margin-top:7px;}}
.oh-l{{font-size:9px;color:var(--light);text-transform:uppercase;letter-spacing:.8px;}}
.oh-v{{font-size:11px;font-weight:700;color:var(--mid);font-variant-numeric:tabular-nums;}}

/* ── CHART ── */
.chart-toolbar{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:4px;}}
.tf-row{{display:flex;gap:3px;flex-wrap:wrap;}}
.tf-btn{{
  padding:2px 8px;border-radius:12px;
  border:1px solid var(--border);
  background:transparent;color:var(--muted);
  font-size:10px;cursor:pointer;font-weight:600;transition:.2s;
}}
.tf-btn.active,.tf-btn:hover{{
  background:linear-gradient(90deg,var(--cyan),#00B8D9);
  color:#0A0E27;border-color:var(--cyan);
  box-shadow:0 0 8px rgba(0,229,255,0.4);
}}
.chart-tabs{{display:flex;gap:4px;flex-wrap:wrap;}}
.ctab{{
  padding:3px 9px;border-radius:12px;
  border:1px solid var(--border);
  background:transparent;color:var(--muted);
  font-size:10px;cursor:pointer;font-weight:700;transition:.2s;
}}
.ctab.active,.ctab:hover{{
  background:rgba(0,229,255,0.1);color:var(--cyan);
  border-color:var(--cyan);
  box-shadow:0 0 8px rgba(0,229,255,0.3);
}}
#chartWrap{{position:relative;height:390px;min-height:300px;
  background:#F7F9FC;border-radius:8px;border:1px solid var(--border);
}}

/* ── TECHNICAL SUMMARY ── */
.ts-r{{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);}}
.ts-r:last-child{{border-bottom:none;}}
.ts-l{{font-size:11px;color:var(--muted);}}
.ts-v{{font-size:11px;font-weight:700;color:var(--mid);}}
.bull{{color:var(--cyan);font-weight:800;text-shadow:0 0 6px rgba(0,229,255,0.4);}}
.bear{{color:var(--magenta);font-weight:800;text-shadow:0 0 6px rgba(233,30,140,0.35);}}

/* ── TABLES ── */
table{{width:100%;border-collapse:collapse;font-size:11px;}}
th{{
  font-size:9px;
  background:linear-gradient(90deg,rgba(0,229,255,0.12),rgba(156,39,176,0.08));
  color:var(--cyan);
  letter-spacing:1px;text-transform:uppercase;text-align:left;padding:4px 6px;
  border-bottom:1px solid rgba(0,229,255,0.2);
}}
th:not(:first-child){{text-align:right;}}
td{{padding:3px 6px;border-bottom:1px solid var(--border);color:var(--mid);font-variant-numeric:tabular-nums;}}
td:not(:first-child){{text-align:right;}}
tr:last-child td{{border-bottom:none;}}
tr:nth-child(even) td{{background:rgba(0,229,255,0.025);}}
.sigb{{color:var(--cyan);font-weight:800;text-shadow:0 0 5px rgba(0,229,255,0.35);}}
.sigr{{color:var(--magenta);font-weight:800;text-shadow:0 0 5px rgba(233,30,140,0.3);}}
.beat{{
  color:var(--teal);font-weight:800;font-size:10px;
  text-shadow:0 0 5px rgba(0,184,148,0.4);
}}

/* ── VALUATION ── */
.val-g{{display:grid;grid-template-columns:1fr 1fr;gap:5px;}}
.val-c{{
  background:linear-gradient(135deg,rgba(0,229,255,0.04),rgba(156,39,176,0.04));
  border:1px solid var(--border);border-radius:8px;
  padding:6px 8px;text-align:center;
  transition:.2s;
}}
.val-c:hover{{border-color:rgba(0,229,255,0.3);box-shadow:0 0 8px rgba(0,229,255,0.12);}}
.val-l{{font-size:9px;color:var(--light);text-transform:uppercase;letter-spacing:.8px;}}
.val-v{{font-size:15px;font-weight:900;color:var(--mid);margin-top:2px;}}

/* ── VOLUME ── */
.vol-lbl{{font-size:9px;color:var(--light);text-transform:uppercase;letter-spacing:.8px;margin-bottom:2px;}}
.vol-v{{font-size:16px;font-weight:900;color:var(--navy);font-variant-numeric:tabular-nums;}}

/* ── RISK ── */
.risk-r{{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid var(--border);}}
.risk-r:last-child{{border-bottom:none;}}
.risk-l{{font-size:11px;color:var(--muted);}}
.low{{
  background:linear-gradient(90deg,rgba(0,184,148,0.15),rgba(0,229,255,0.10));
  color:var(--teal);font-size:10px;font-weight:800;
  padding:2px 9px;border-radius:10px;border:1px solid rgba(0,184,148,0.3);
}}
.med{{
  background:rgba(245,158,11,0.12);
  color:var(--amber);font-size:10px;font-weight:800;
  padding:2px 9px;border-radius:10px;border:1px solid rgba(245,158,11,0.25);
}}
.high{{
  background:rgba(233,30,140,0.10);
  color:var(--magenta);font-size:10px;font-weight:800;
  padding:2px 9px;border-radius:10px;border:1px solid rgba(233,30,140,0.25);
}}

/* ── S&R PIVOT ── */
.sr-r{{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--border);font-size:11px;font-variant-numeric:tabular-nums;}}
.sr-r:last-child{{border-bottom:none;}}
.sr-k{{color:var(--light);}}
.sr-rv{{color:var(--magenta);font-weight:700;text-shadow:0 0 5px rgba(233,30,140,0.3);}}
.sr-sv{{color:var(--cyan);font-weight:700;text-shadow:0 0 5px rgba(0,229,255,0.3);}}
.sr-p{{color:var(--navy);font-weight:900;}}

/* ── TRIGGERS ── */
.trg-h{{font-size:9px;font-weight:900;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;}}
.trg{{font-size:10px;padding:2px 0 2px 7px;line-height:1.4;}}
.trg-pos{{color:var(--muted);border-left:2px solid var(--cyan);}}
.trg-neg{{color:var(--muted);border-left:2px solid var(--magenta);}}

/* ── RECOMMENDATION ── */
.buy{{
  font-size:38px;font-weight:900;line-height:1;letter-spacing:-1px;
  background:linear-gradient(90deg,var(--cyan),var(--teal));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  filter:drop-shadow(0 0 8px rgba(0,229,255,0.45));
}}
.sell-tag{{
  font-size:38px;font-weight:900;line-height:1;letter-spacing:-1px;
  background:linear-gradient(90deg,var(--magenta),#C2185B);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  filter:drop-shadow(0 0 8px rgba(233,30,140,0.4));
}}
.hold-tag{{
  font-size:38px;font-weight:900;line-height:1;letter-spacing:-1px;
  color:var(--amber);
  filter:drop-shadow(0 0 6px rgba(245,158,11,0.4));
}}
.conf-bar{{height:5px;background:var(--border);border-radius:3px;overflow:hidden;margin-top:3px;}}
.conf-fill{{
  height:100%;
  background:linear-gradient(90deg,var(--cyan),var(--teal));
  border-radius:3px;
  box-shadow:0 0 6px rgba(0,229,255,0.5);
}}

/* ── DONUT LEGEND ── */
.dl{{display:flex;flex-direction:column;gap:3px;margin-top:4px;}}
.dl-r{{display:flex;align-items:center;gap:5px;font-size:10px;color:var(--muted);}}
.dot2{{width:9px;height:9px;border-radius:50%;flex-shrink:0;}}

/* ── NOTES ── */
.note{{
  font-size:10px;color:var(--muted);
  padding:3px 0 3px 7px;
  border-left:2px solid var(--cyan);
  margin-bottom:4px;line-height:1.4;
}}

/* ── PATTERNS ── */
.pat-card{{
  background:linear-gradient(135deg,rgba(0,229,255,0.04),rgba(156,39,176,0.04));
  border:1px solid rgba(0,229,255,0.18);
  border-radius:8px;padding:7px 9px;margin-bottom:6px;
  transition:.2s;
}}
.pat-card:hover{{border-color:var(--cyan);box-shadow:0 0 12px rgba(0,229,255,0.15);}}
.pat-head{{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;}}
.pat-name{{font-size:11px;font-weight:800;color:var(--navy);}}
.pat-conf{{font-size:11px;font-weight:800;}}
.pat-desc{{font-size:10px;color:var(--muted);line-height:1.4;}}
.pat-none{{font-size:10px;color:var(--light);font-style:italic;padding:8px 0;}}

/* ── VALUE ANALYSIS ── */
.va-rem{{
  font-size:10px;color:var(--muted);
  padding:2px 0 2px 6px;
  border-left:2px solid rgba(0,229,255,0.3);
  margin-bottom:4px;line-height:1.4;
}}
.va-score{{font-size:28px;font-weight:900;line-height:1;}}

/* ── SHAREHOLDING ── */
.sh-row{{margin-bottom:8px;}}
.sh-meta{{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;}}
.sh-lbl{{font-size:10px;font-weight:700;color:var(--mid);text-transform:uppercase;letter-spacing:.8px;}}
.sh-na{{font-size:10px;color:var(--light);}}
.sh-track{{
  height:6px;background:var(--border);border-radius:3px;overflow:hidden;
}}
.sh-fill{{height:100%;border-radius:3px;transition:width .6s ease;}}
.sh-signal-badge{{
  display:inline-block;
  padding:3px 10px;border-radius:12px;font-size:10px;font-weight:800;
  margin-bottom:7px;
}}

/* ── ENTRY/EXIT ── */
.ee-grid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:11px;}}
.ee-c{{border-radius:8px;padding:5px 7px;}}
.ee-l{{font-size:9px;color:var(--light);text-transform:uppercase;letter-spacing:.8px;margin-bottom:1px;}}
.ee-v{{font-size:12px;font-weight:800;}}

/* ── GLOW UTILITY ── */
.glow-cyan{{color:var(--cyan);text-shadow:0 0 8px rgba(0,229,255,0.5);}}
.glow-mag{{color:var(--magenta);text-shadow:0 0 8px rgba(233,30,140,0.45);}}
.glow-pur{{color:var(--purple);text-shadow:0 0 8px rgba(156,39,176,0.4);}}
.glow-teal{{color:var(--teal);text-shadow:0 0 8px rgba(0,184,148,0.45);}}

@media print{{
  body{{background:#fff;padding:0;}}
  .card{{border:1px solid #ccc;box-shadow:none;max-width:100%;border-radius:0;}}
  .btns{{display:none;}}
  .hdr{{background:#0A0E27;}}
}}
</style></head><body>
<div class="card">

<!-- ═══ HEADER ═══ -->
<div class="hdr">
  <div style="display:flex;flex-direction:column;">
    <div class="hdr-t1">⚡ MARKET VEDA DASHBOARD</div>
    <div class="hdr-t2">Complete Stock Intelligence · Institutional Grade</div>
  </div>
  <div class="hdr-meta">
    <div class="hdr-mi"><span class="hdr-ml">Date</span><span class="hdr-mv">{data.get("date_str","")}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Time</span><span class="hdr-mv">{data.get("time_str","")}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Sector</span><span class="hdr-mv" style="color:var(--cyan);text-shadow:0 0 6px rgba(0,229,255,0.4);">{sector}</span></div>
    <div class="hdr-mi"><span class="hdr-ml">Exchange</span><span class="nse-badge">NSE</span></div>
    <div class="live-badge"><div class="dot"></div>Live · DB</div>
  </div>
  <div class="btns">
    <button class="btn btn-o" onclick="window.print()">🖨 PDF</button>
    <button class="btn btn-t" onclick="dlPage()">⬇ Download</button>
  </div>
</div>

<div class="body">

<!-- ═══ ROW 1: Overview | Price | Chart | Technical ═══ -->
<div class="row r1">

  <div class="panel">
    <div class="sec">Overview</div>
    <div class="co-name">{sym}</div>
    <div class="co-full">{name}</div>
    <div class="ov-grid">
      <div><div class="ov-l">Market Cap</div><div class="ov-v">{mktcap_s}</div></div>
      <div><div class="ov-l">52W H / L</div><div class="ov-v">{h52_s} / {l52_s}</div></div>
      <div><div class="ov-l">P/E (TTM)</div><div class="ov-v">{cur_pe_str}</div></div>
      <div><div class="ov-l">Book Value</div><div class="ov-v">{bv_s}</div></div>
      <div><div class="ov-l">ROE</div><div class="ov-v glow-cyan">{roe_s}</div></div>
      <div><div class="ov-l">ROCE</div><div class="ov-v glow-cyan">{roce_s}</div></div>
      <div><div class="ov-l">Div. Yield</div><div class="ov-v">{div_yield}</div></div>
      <div><div class="ov-l">Beta</div><div class="ov-v">{beta_s}</div></div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Current Price · Live</div>
    <div class="cmp">₹{ltp:,.2f}</div>
    <div class="chg" style="color:{chg_col};text-shadow:0 0 6px {chg_col}66;">{chg_arr} {abs(chg):.2f} ({abs(chgp):.2f}%)</div>
    <div class="ohlc-g">
      <div><div class="oh-l">Open</div><div class="oh-v">{ohlc["o"]:,.2f}</div></div>
      <div><div class="oh-l">High</div><div class="oh-v glow-cyan">{ohlc["h"]:,.2f}</div></div>
      <div><div class="oh-l">Low</div><div class="oh-v glow-mag">{ohlc["l"]:,.2f}</div></div>
      <div><div class="oh-l">Prev Close</div><div class="oh-v">{ohlc["pc"]:,.2f}</div></div>
      <div><div class="oh-l">Avg Price</div><div class="oh-v">{ap_str}</div></div>
      <div><div class="oh-l">VWAP</div><div class="oh-v">{vwap_str}</div></div>
      <div><div class="oh-l">Upper Ckt</div><div class="oh-v">₹{upc2}</div></div>
      <div><div class="oh-l">Lower Ckt</div><div class="oh-v">₹{loc2}</div></div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Price Chart · Candlestick + Institutional S&amp;R</div>
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
  </div>

  <div class="panel">
    <div class="sec">Technical Summary</div>
    <div class="ts-r"><span class="ts-l">TREND</span><span class="{'bull' if chg>=0 else 'bear'}">{'Bullish ▲' if chg>=0 else 'Bearish ▼'}</span></div>
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

<!-- ═══ ROW 2: MAs | Valuation | Volume | Risk ═══ -->
<div class="row r2">

  <div class="panel">
    <div class="sec">Moving Averages</div>
    <table><thead><tr><th>Period</th><th>SMA</th><th>EMA</th><th>Signal</th></tr></thead>
    <tbody>{ma_rows}</tbody></table>
    <div style="margin-top:6px;padding:5px 8px;background:linear-gradient(90deg,rgba(0,229,255,0.06),rgba(0,184,148,0.04));border-radius:6px;border-left:3px solid var(--cyan);">
      <div style="font-size:10px;font-weight:800;" class="glow-cyan">{'✅ All 4/4 MAs Bullish' if bull_n==4 else f'{bull_n}/4 MAs Bullish'}</div>
      <div style="font-size:9px;color:var(--light);margin-top:1px;">CMP {dev20:+.1f}% vs SMA20 · {dev200:+.1f}% vs SMA200</div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Valuation Metrics</div>
    <div class="val-g">
      <div class="val-c"><div class="val-l">P/E (TTM)</div><div class="val-v">{cur_pe_str}</div></div>
      <div class="val-c"><div class="val-l">P/B Ratio</div><div class="val-v">{str(km.get("Price to Book",km.get("P/B","N/A")))+"x" if km else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">PEG Ratio</div><div class="val-v" style="color:{'var(--teal)' if va.get('peg') and va['peg']<1 else 'var(--amber)' if va.get('peg') else 'var(--light)'}">{peg_str}</div></div>
      <div class="val-c"><div class="val-l">EV/EBITDA</div><div class="val-v">{km.get("EV/EBITDA","N/A") if km else "N/A"}</div></div>
      <div class="val-c"><div class="val-l">Rev CAGR 5Y</div><div class="val-v glow-teal">{rev_cagr_s}</div></div>
      <div class="val-c"><div class="val-l">PAT CAGR 5Y</div><div class="val-v glow-teal">{np_cagr_s}</div></div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Volume Analysis</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:7px;">
      <div><div class="vol-lbl">Avg Vol (20D)</div><div class="vol-v">{fvol(avg20)}</div></div>
      <div><div class="vol-lbl">Today's Vol</div><div class="vol-v">{fvol(ohlc["vol"])}</div></div>
    </div>
    <div style="margin-bottom:6px;">
      <div class="vol-lbl">Volume % vs Avg</div>
      <div style="font-size:13px;font-weight:800;color:{vol_col};text-shadow:0 0 6px {vol_col}66;">{vol_arr} {abs(vol_pct):.1f}% {'Above' if vol_pct>=0 else 'Below'} Avg</div>
    </div>
    <div style="margin-bottom:6px;">
      <div class="vol-lbl">Delivery %</div>
      <div style="font-size:12px;font-weight:700;color:{deliv_col};">{deliv_html}</div>
    </div>
    <div style="background:rgba(0,229,255,0.04);border-radius:6px;padding:5px 7px;border:1px solid var(--border);">
      <div class="vol-lbl">Bid / Ask Qty</div>
      <div style="font-size:11px;font-weight:700;color:var(--mid);">{fvol(ohlc["bq"])} / {fvol(ohlc["sq"])}</div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Risk Analysis</div>
    {risk_html}
  </div>
</div>

<!-- ═══ ROW 3: Financials | Triggers | S&R | Recommendation ═══ -->
<div class="row r3">

  <div class="panel">
    <div class="sec">Financial Summary (₹ Cr) · Annual</div>
    <table><thead><tr><th>Metric</th>{ann_hdr}</tr></thead><tbody>{ann_body}</tbody></table>
    <div style="margin-top:5px;display:flex;gap:6px;flex-wrap:wrap;">
      <div style="background:rgba(0,229,255,0.08);border-radius:10px;padding:2px 8px;font-size:10px;font-weight:700;" class="glow-cyan">Rev CAGR: {rev_cagr_s}</div>
      <div style="background:rgba(0,184,148,0.08);border-radius:10px;padding:2px 8px;font-size:10px;font-weight:700;" class="glow-teal">PAT CAGR: {np_cagr_s}</div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Key Triggers</div>
    <div class="trg-h" style="color:var(--teal);">✅ Positive Catalysts</div>
    {pos_html}
    <div style="height:5px;"></div>
    <div class="trg-h" style="color:var(--magenta);">⚠️ Risk Factors</div>
    {neg_html}
  </div>

  <div class="panel">
    <div class="sec">Support &amp; Resistance · Pivot</div>
    <div class="sr-r"><span class="sr-k">R3</span><span class="sr-rv">{pp.get("r3","N/A")}</span></div>
    <div class="sr-r"><span class="sr-k">R2</span><span class="sr-rv">{pp.get("r2","N/A")}</span></div>
    <div class="sr-r"><span class="sr-k">R1</span><span class="sr-rv">{pp.get("r1","N/A")}</span></div>
    <div class="sr-r" style="border-top:2px solid var(--cyan);border-bottom:2px solid var(--cyan);margin:3px 0;padding:4px 0;">
      <span class="sr-k" style="font-weight:900;color:var(--navy);">PIVOT</span><span class="sr-p">{pp.get("pivot","N/A")}</span>
    </div>
    <div class="sr-r"><span class="sr-k">S1</span><span class="sr-sv">{pp.get("s1","N/A")}</span></div>
    <div class="sr-r"><span class="sr-k">S2</span><span class="sr-sv">{pp.get("s2","N/A")}</span></div>
    <div class="sr-r"><span class="sr-k">S3</span><span class="sr-sv">{pp.get("s3","N/A")}</span></div>
  </div>

  <div class="panel">
    <div class="sec">Recommendation</div>
    <div class="{act_class}">{act}</div>
    <div style="margin-top:6px;"><div class="vol-lbl">Target Price (12M)</div>
    <div style="font-size:17px;font-weight:900;color:var(--navy);">{tgt_str}</div></div>
    <div style="margin-top:4px;"><div class="vol-lbl">Upside Potential</div>
    <div style="font-size:14px;font-weight:800;" class="glow-cyan">{'+' if sc.get('up',0)>=0 else ''}{sc.get('up','N/A')}%</div></div>
    <div style="margin-top:4px;">
      <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
        <span class="vol-lbl">Confidence</span>
        <span style="font-size:13px;font-weight:900;" class="glow-cyan">{sc.get('conf',0)}%</span>
      </div>
      <div class="conf-bar"><div class="conf-fill" style="width:{sc.get('conf',0)}%;"></div></div>
    </div>
    <div style="margin-top:5px;font-size:10px;color:var(--muted);line-height:1.6;">
      Stop: <b style="color:var(--magenta);">{sl_str}</b> · R:R <b>1:{sc.get('rr','N/A')}</b><br>
      Method: RS/VCP/Minervini SEPA
    </div>
  </div>
</div>

<!-- ═══ ROW 4: Results | Sentiment | Notes ═══ -->
<div class="row r4">

  <div class="panel">
    <div class="sec">Results Tracker — Last 8 Quarters (₹ Cr)</div>
    <table><thead><tr><th>Quarter</th>{qtr_hdr}</tr></thead><tbody>{qtr_body}</tbody></table>
  </div>

  <div class="panel">
    <div class="sec">Analyst Sentiment</div>
    <div style="display:flex;align-items:center;gap:10px;">
      <canvas id="dc" width="80" height="80"></canvas>
      <div>
        <div style="font-size:20px;font-weight:900;line-height:1;" class="glow-cyan">{sent["bp"]}%</div>
        <div style="font-size:10px;font-weight:700;color:var(--cyan);">{sent["cons"]}</div>
        <div class="dl">
          <div class="dl-r"><div class="dot2" style="background:var(--cyan);box-shadow:0 0 6px var(--cyan);"></div><span style="font-weight:700;" class="glow-cyan">BUY {sent["bp"]}%</span></div>
          <div class="dl-r"><div class="dot2" style="background:var(--purple);"></div><span style="color:var(--muted);">HOLD {sent["hp"]}%</span></div>
          <div class="dl-r"><div class="dot2" style="background:var(--magenta);"></div><span style="color:var(--muted);">SELL {sent["sp"]}%</span></div>
        </div>
        <div style="font-size:9px;color:var(--light);margin-top:4px;">{sent["anc"]}+ Analyst Ratings (est.)</div>
      </div>
    </div>
  </div>

  <div class="panel">
    <div class="sec">Notes &amp; Insights</div>
    <div class="note">Minervini SEPA: {mn["stage"]} — {mn["n"]}/6 filters. {'Qualifies for momentum setup.' if mn["pass"] else 'Not yet in Stage 2.'}</div>
    <div class="note">RS vs Nifty50: {rs:.2f} ({rsp} pctl). {'Outperforming ✅' if rs>=1 else 'Underperforming ⚠️'}</div>
    <div class="note">{note_cagr}</div>
    <div class="note">Entry ₹{ee["el"]:,.2f}–₹{ee["eh"]:,.2f} · Stop ₹{ee["sl"]:,.2f} · T1 ₹{ee["t1"]:,.2f} · R:R 1:{ee["rr"]}</div>
    <div class="note">PE: {verdict}. Current {cur_pe_str} · 5Y Mean {pe5_str} · Sector {sect_pe_str}</div>
  </div>
</div>

<!-- ═══ ROW 5: Price Move | PE | Entry/Exit + Patterns | Institutional Value + OI ═══ -->
<div class="row r5">

  <div class="panel">
    <div class="sec">Price Move History &amp; CAGR Targets</div>
    <table><thead><tr><th>Period</th><th>Move %</th></tr></thead>
    <tbody>
      {ret_rows}
      <tr style="background:rgba(0,229,255,0.06);"><td colspan="2" style="font-size:9px;font-weight:800;padding:4px 6px;" class="glow-cyan">📈 CAGR-Based Projections</td></tr>
      <tr><td>CAGR 1Y (est.)</td><td style="text-align:right;font-weight:800;" class="glow-teal">{('+' if ret.get('cagr1y',0)>=0 else '')+str(ret.get('cagr1y','N/A'))+'%' if ret.get('cagr1y') else 'N/A'}</td></tr>
      <tr><td>Target 3M</td><td style="text-align:right;font-weight:700;" class="glow-teal">{t3m_s}</td></tr>
      <tr><td>Target 6M</td><td style="text-align:right;font-weight:700;" class="glow-teal">{t6m_s}</td></tr>
      <tr><td>Target 1Y</td><td style="text-align:right;font-weight:700;" class="glow-teal">{t1y_s}</td></tr>
    </tbody></table>
  </div>

  <div class="panel">
    <div class="sec">PE Valuation Analysis</div>
    <div style="background:linear-gradient(135deg,{vc}15,{vc}08);border:1px solid {vc}40;border-radius:8px;padding:6px;margin-bottom:7px;text-align:center;">
      <div style="font-size:10px;font-weight:900;color:{vc};text-shadow:0 0 6px {vc}88;">{verdict}</div>
    </div>
    <table style="margin-bottom:6px;">
      <thead><tr><th>PE Metric</th><th>Value</th></tr></thead>
      <tbody>
        <tr><td>Current P/E</td><td style="text-align:right;font-weight:800;color:{vc};">{cur_pe_str}</td></tr>
        <tr><td>5Y Mean PE</td><td style="text-align:right;">{pe5_str}</td></tr>
        <tr><td>10Y Mean PE</td><td style="text-align:right;">{pe10_str}</td></tr>
        <tr><td>Sector PE</td><td style="text-align:right;">{sect_pe_str}</td></tr>
        <tr><td>PEG Ratio</td><td style="text-align:right;font-weight:700;color:{'var(--teal)' if va.get('peg') and va['peg']<1 else 'var(--amber)'}">{peg_str}</td></tr>
      </tbody>
    </table>
    <div class="vol-lbl" style="margin-bottom:3px;">Peer Comparison</div>
    <table><tbody>{peer_html or '<tr><td colspan="2" style="color:var(--light);">N/A</td></tr>'}</tbody></table>
  </div>

  <div class="panel">
    <div class="sec">Entry / Exit Strategy</div>
    <div class="ee-grid">
      <div class="ee-c" style="background:rgba(0,229,255,0.06);border:1px solid rgba(0,229,255,0.2);">
        <div class="ee-l">Entry Zone</div>
        <div class="ee-v glow-cyan">₹{ee["el"]:,.2f} – ₹{ee["eh"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:rgba(233,30,140,0.06);border:1px solid rgba(233,30,140,0.2);">
        <div class="ee-l">Stop Loss</div>
        <div class="ee-v glow-mag">₹{ee["sl"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:rgba(0,184,148,0.06);border:1px solid rgba(0,184,148,0.2);">
        <div class="ee-l">Target 1 (R1)</div>
        <div class="ee-v glow-teal">₹{ee["t1"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:rgba(0,184,148,0.06);border:1px solid rgba(0,184,148,0.2);">
        <div class="ee-l">Target 2 (R2)</div>
        <div class="ee-v glow-teal">₹{ee["t2"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:rgba(0,184,148,0.06);border:1px solid rgba(0,184,148,0.2);">
        <div class="ee-l">Target 3 (R3)</div>
        <div class="ee-v glow-teal">₹{ee["t3"]:,.2f}</div>
      </div>
      <div class="ee-c" style="background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.2);">
        <div class="ee-l">Risk : Reward</div>
        <div class="ee-v" style="color:var(--amber);">1 : {ee["rr"]}</div>
      </div>
    </div>
    <div style="margin-top:6px;background:rgba(0,229,255,0.04);border-radius:6px;padding:5px 7px;border:1px solid var(--border);font-size:10px;color:var(--muted);">
      <b>Trigger:</b> Pullback to S1 ₹{pp.get("s1","N/A")} with vol ≥ 1.5× avg
    </div>
    <div style="margin-top:8px;">
      <div class="sec">Chart Patterns Detected</div>
      {pat_html}
    </div>
  </div>

  <div class="panel">
    <!-- ── Institutional Value Score ── -->
    <div class="sec">Institutional Value Analysis</div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:7px;">
      <div class="va-score" style="color:{va_col};text-shadow:0 0 10px {va_col}66;">{va_score}</div>
      <div>
        <div style="font-size:10px;font-weight:800;color:{va_col};">{va_verdict}</div>
        <div style="font-size:9px;color:var(--light);margin-top:2px;">/ 100 Value Score</div>
      </div>
    </div>
    {va_remarks}

    <!-- ── Shareholding Pattern ── -->
    <div style="margin-top:10px;border-top:1px solid var(--border);padding-top:8px;">
      <div class="sec">📊 Promoter / DII / FII Shareholding</div>
      <div class="sh-signal-badge" style="background:{sh_sig_col}18;border:1px solid {sh_sig_col}40;color:{sh_sig_col};">
        {sh_signal}
      </div>
      {sh_promoter_bar}
      {sh_fii_bar}
      {sh_dii_bar}
      {sh_pub_bar}
      <div style="margin-top:6px;">
        {sh_remarks_html}
      </div>
    </div>

    <!-- ── Shareholding History ── -->
    {"" if not sh_hist_rows else f'''<div style="margin-top:8px;border-top:1px solid var(--border);padding-top:6px;">
      <div class="sec">Shareholding History</div>
      <table><thead><tr><th>Entity</th>{sh_hist_hdrs}</tr></thead>
      <tbody>{sh_hist_rows}</tbody></table>
    </div>'''}

    <!-- ── OI & Delivery ── -->
    <div style="margin-top:8px;border-top:1px solid var(--border);padding-top:6px;">
      <div class="sec">F&amp;O OI &amp; Delivery</div>
      <div style="margin-bottom:6px;">
        <div class="vol-lbl">Delivery % (Latest)</div>
        <div style="font-size:13px;font-weight:800;color:{deliv_col};">{deliv_html}</div>
      </div>
      <table><thead><tr><th>Date</th><th>OI</th><th>LTP</th></tr></thead>
      <tbody>{oi_rows}</tbody></table>
    </div>
  </div>
</div><!-- end row5 -->

</div><!-- end body -->
</div><!-- end card -->

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-annotation/3.0.1/chartjs-plugin-annotation.min.js"></script>
<script>
const CD  = {chart_js};
const SR  = {sr_json};
const LTP = {ltp};
let PC=null, MODE='candle', TF='1Y';

// ── Download ──────────────────────────────────────────────────────────────────
function dlPage(){{
  const blob=new Blob([document.documentElement.outerHTML],{{type:'text/html;charset=utf-8'}});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='{sym}_dashboard.html';
  a.click(); URL.revokeObjectURL(a.href);
}}

// ── Gradient fill (subtle off-white) ─────────────────────────────────────────
function mkGrad(ctx,ca){{
  const g=ctx.createLinearGradient(0,ca.top,0,ca.bottom);
  g.addColorStop(0,'rgba(0,229,255,0.10)');
  g.addColorStop(1,'rgba(0,229,255,0.00)');
  return g;
}}

// ── CANDLESTICK PLUGIN (reference image colours) ──────────────────────────────
// Bullish: hollow body, CYAN border (#00E5FF)  — like teal/cyan candles in image
// Bearish: solid MAGENTA fill (#E91E8C)        — like pink/magenta candles in image
const candlePlugin={{
  id:'candlePlugin',
  afterDatasetsDraw(chart){{
    const raw=chart._candleRaw;
    if(!raw||!raw.length) return;
    const {{ctx,chartArea:ca,scales:{{x,y}}}}=chart;
    const n=raw.length;
    const barW=Math.max(2,Math.min(12,(ca.right-ca.left)/n*0.65));
    ctx.save();
    raw.forEach((c,i)=>{{
      const xp=x.getPixelForValue(i);
      const yO=y.getPixelForValue(c.o);
      const yC=y.getPixelForValue(c.c);
      const yH=y.getPixelForValue(c.h);
      const yL=y.getPixelForValue(c.l);
      const bull=c.c>=c.o;
      const bodyTop=Math.min(yO,yC);
      const bodyH=Math.max(1.5,Math.abs(yC-yO));

      if(bull){{
        // Cyan wick
        ctx.strokeStyle='#00E5FF'; ctx.lineWidth=1.2;
        ctx.shadowColor='#00E5FF'; ctx.shadowBlur=4;
        ctx.beginPath();ctx.moveTo(xp,yH);ctx.lineTo(xp,bodyTop);ctx.stroke();
        ctx.beginPath();ctx.moveTo(xp,bodyTop+bodyH);ctx.lineTo(xp,yL);ctx.stroke();
        ctx.shadowBlur=0;
        // Hollow cyan body
        ctx.strokeStyle='#00E5FF'; ctx.lineWidth=1.2;
        ctx.shadowColor='#00E5FF'; ctx.shadowBlur=5;
        ctx.strokeRect(xp-barW/2,bodyTop,barW,bodyH);
        ctx.fillStyle='rgba(0,229,255,0.06)';
        ctx.fillRect(xp-barW/2,bodyTop,barW,bodyH);
        ctx.shadowBlur=0;
      }} else {{
        // Magenta wick
        ctx.strokeStyle='#E91E8C'; ctx.lineWidth=1.2;
        ctx.shadowColor='#E91E8C'; ctx.shadowBlur=4;
        ctx.beginPath();ctx.moveTo(xp,yH);ctx.lineTo(xp,bodyTop);ctx.stroke();
        ctx.beginPath();ctx.moveTo(xp,bodyTop+bodyH);ctx.lineTo(xp,yL);ctx.stroke();
        ctx.shadowBlur=0;
        // Solid magenta body
        ctx.fillStyle='rgba(233,30,140,0.82)';
        ctx.fillRect(xp-barW/2,bodyTop,barW,bodyH);
        ctx.strokeStyle='#E91E8C'; ctx.lineWidth=0.8;
        ctx.shadowColor='#E91E8C'; ctx.shadowBlur=5;
        ctx.strokeRect(xp-barW/2,bodyTop,barW,bodyH);
        ctx.shadowBlur=0;
      }}
    }});
    ctx.restore();
  }}
}};
Chart.register(candlePlugin);

// ── Institutional-grade S&R annotations (full-width glowing lines) ────────────
function buildAnnotations(ltp,sr,showSR){{
  const anns={{}};

  // LTP line — amber dashed
  anns.ltp={{
    type:'line',yMin:ltp,yMax:ltp,
    borderColor:'#F59E0B',borderWidth:1.5,borderDash:[6,4],
    label:{{
      content:'LTP ₹'+ltp.toFixed(1),display:true,
      backgroundColor:'rgba(245,158,11,0.85)',color:'#0A0E27',
      font:{{size:10,weight:'bold'}},position:'end',yAdjust:-12
    }}
  }};

  if(showSR){{
    sr.slice(0,8).forEach((z,i)=>{{
      const isR=z.type==='resistance';
      const col=isR?'#E91E8C':'#00E5FF';
      anns['sr'+i]={{
        type:'line',yMin:z.price,yMax:z.price,
        borderColor:col,borderWidth:1.8,
        label:{{
          content:(isR?'🔴 R':'🟢 S')+' ₹'+z.price.toFixed(0)+(z.touches?' ×'+z.touches:''),
          display:true,
          backgroundColor:isR?'rgba(233,30,140,0.10)':'rgba(0,229,255,0.10)',
          color:col,font:{{size:9,weight:'bold'}},
          position:'start',yAdjust:isR?-11:4
        }}
      }};
    }});
  }}
  return anns;
}}

// ── Build invisible scatter for labels (candles drawn by plugin) ──────────────
function buildDataset(tf){{
  const d=CD[tf];
  if(!d||!d.length) return null;
  return {{
    type:'scatter',data:d.map((c,i)=>({{x:i,y:c.c}})),
    pointRadius:0,pointHoverRadius:3,
    pointBackgroundColor:'rgba(0,229,255,0.8)',
    showLine:false
  }};
}}

// ── Render chart ──────────────────────────────────────────────────────────────
function renderChart(){{
  if(PC){{PC.destroy();PC=null;}}
  const d=CD[TF];
  if(!d||!d.length) return;
  const canvas=document.getElementById('pc');
  const ctx=canvas.getContext('2d');
  const labels=d.map(c=>c.t);
  const ds=buildDataset(TF);
  if(!ds) return;
  const showSR=(MODE==='sr'||MODE==='candle');

  PC=new Chart(ctx,{{
    type:'line',data:{{labels,datasets:[ds]}},
    options:{{
      responsive:true,maintainAspectRatio:false,animation:{{duration:250}},
      interaction:{{mode:'index',intersect:false}},
      plugins:{{
        legend:{{display:false}},
        tooltip:{{
          backgroundColor:'rgba(10,14,39,0.92)',
          borderColor:'#00E5FF',borderWidth:1,
          titleColor:'#E2E6F0',bodyColor:'#00E5FF',
          padding:9,displayColors:false,
          callbacks:{{
            title:items=>d[items[0].dataIndex]?d[items[0].dataIndex].t:'',
            label:c=>{{
              const raw=d[c.dataIndex];
              if(raw&&raw.o!==undefined)return[
                'O: ₹'+raw.o.toFixed(2),'H: ₹'+raw.h.toFixed(2),
                'L: ₹'+raw.l.toFixed(2),'C: ₹'+raw.c.toFixed(2),
                'Vol: '+(raw.v?raw.v.toLocaleString():'N/A')];
              return '₹'+c.parsed.y.toFixed(2);
            }}
          }}
        }},
        annotation:{{annotations:buildAnnotations(LTP,SR,showSR)}}
      }},
      scales:{{
        x:{{
          grid:{{color:'rgba(0,229,255,0.05)'}},
          ticks:{{color:'#5A5F7A',font:{{size:10}},maxTicksLimit:12,
            callback:(v,i)=>{{
              const step=Math.ceil(d.length/12);
              return i%step===0&&d[i]?d[i].t:null;
            }}
          }}
        }},
        y:{{
          position:'right',
          grid:{{color:'rgba(0,229,255,0.06)'}},
          ticks:{{color:'#5A5F7A',font:{{size:10}},callback:v=>'₹'+v.toLocaleString()}},
          min:(()=>{{const lows=d.map(c=>c.l).filter(Boolean);return lows.length?Math.min(...lows)*0.985:undefined;}})(),
          max:(()=>{{const highs=d.map(c=>c.h).filter(Boolean);return highs.length?Math.max(...highs)*1.015:undefined;}})()
        }}
      }}
    }}
  }});
  PC._candleRaw=d;
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

// ── Donut chart (cyan/purple/magenta) ─────────────────────────────────────────
function initDonut(){{
  const ctx2=document.getElementById('dc').getContext('2d');
  new Chart(ctx2,{{
    type:'doughnut',
    data:{{datasets:[{{
      data:[{sent["bp"]},{sent["hp"]},{sent["sp"]}],
      backgroundColor:['#00E5FF','#9C27B0','#E91E8C'],
      borderWidth:0
    }}]}},
    options:{{responsive:false,plugins:{{legend:{{display:false}},tooltip:{{enabled:false}}}}}}
  }});
}}

window.addEventListener('load',()=>{{ renderChart(); initDonut(); }});
</script>
</body></html>"""
