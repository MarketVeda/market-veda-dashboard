"""
scoring.py — News Analysis, Recommendation Engine & Analyst Sentiment
"""

# Symbol → sector map, derived once from the peer lists in financials.SECTOR_PE
# so a symbol always resolves to a real sector even when financials.json carries
# no Sector/Industry field. This makes Peer-PE and Sector-PE comparisons work.
def _build_symbol_sector():
    try:
        from financials import SECTOR_PE
    except Exception:
        return {}
    m={}
    for sector,info in SECTOR_PE.items():
        if sector=="DEFAULT": continue
        for peer in (info.get("peers") or {}):
            m.setdefault(peer.upper(), sector)
    return m

_SYMBOL_SECTOR=_build_symbol_sector()


def get_sector(sym, fin=None):
    if fin:
        km=fin.get("key_metrics") or {}
        s=km.get("Sector") or km.get("sector") or km.get("Industry") or km.get("industry")
        if s: return s.upper().strip()
    mapped=_SYMBOL_SECTOR.get((sym or "").upper())
    if mapped: return mapped
    return "DIVERSIFIED"

def get_name(sym, fin=None):
    if fin:
        km=fin.get("key_metrics") or {}
        n=km.get("Company Name") or km.get("company_name") or km.get("Name")
        if n: return n.strip()
    return f"{sym.upper()} Ltd"


def sentiment(news, tech):
    ns=news.get("news_impact_score",0) if news else 0
    neg=news.get("exclude_negative",False) if news else False
    mp=tech["min"]["pass"]
    rsi=tech["rsi"] or 50
    mh=tech["macd"][2]

    sc=min(ns*3,30)+(25 if mp else 5)
    if rsi>50: sc+=min((rsi-50)*0.5,15)
    if mh and mh>0: sc+=10
    if neg: sc=max(sc-30,5)
    sc=min(max(sc,5),90)

    if sc>=65:   bp=round(sc); hp=max(5,100-round(sc)-15); sp=100-bp-hp; cons="Strong BUY"
    elif sc>=45: bp=round(sc*.7); hp=round(sc*.3); sp=100-bp-hp; cons="BUY"
    elif sc>=30: bp=30;hp=50;sp=20; cons="HOLD"
    else:        bp=15;hp=25;sp=60; cons="SELL"
    return {"bp":bp,"hp":hp,"sp":sp,"cons":cons,"anc":max(5,min(35,int(ns*1.5+8)))}


def recommend(tech, fp, news):
    ltp=tech["ltp"]
    mp=tech["min"]["pass"]
    rsi=tech["rsi"] or 50
    mh=(tech["macd"] or (None,None,None))[2]
    ns=news.get("news_impact_score",0) if news else 0
    va=fp.get("value",{})
    vs=va.get("score",50)

    sc=30+(20 if mp else 0)
    if 45<rsi<75: sc+=10
    elif rsi>=75: sc+=2
    if mh and mh>0: sc+=10
    if tech["rs"]>=1.0: sc+=10
    sc+=min(ns*1.5,15)
    sc+=round((vs-50)*0.2)  # value score contributes
    if "EXPENSIVE" in fp.get("pe",{}).get("verdict",""):  sc-=8
    sc=min(max(sc,10),95)

    act="BUY" if sc>=60 else ("HOLD" if sc>=40 else "SELL")
    ac="#00C896" if act=="BUY" else ("#F59E0B" if act=="HOLD" else "#F43F5E")

    ee=tech["ee"]; ret=tech["ret"]
    tgt=ret.get("t1y") or ee["t2"]
    sl=ee["sl"]
    up=round((tgt-ltp)/ltp*100,1) if ltp and tgt else 0
    rr=round((tgt-ltp)/(ltp-sl),1) if ltp and sl and ltp>sl and tgt>ltp else 0

    return {"action":act,"ac":ac,"conf":sc,
            "target":round(tgt,2) if tgt else None,
            "sl":round(sl,2),"up":up,"rr":rr}


def triggers(news, tech, fp):
    pos=[]; neg=[]
    if news:
        for a in (news.get("announcements") or [])[:4]:
            subj=a.get("subject",""); asc=a.get("score",0)
            if asc>=10: pos.append(f"✅ {subj[:65]}")
            elif asc<=0: neg.append(f"⚠️ {subj[:65]}")
        bm=news.get("board_meeting")
        if bm:
            bd=bm.get("meeting_date",""); bp2=bm.get("purpose","")[:45]
            pos.append(f"✅ Board meeting {bd}: {bp2}")

    mn=tech["min"]; mh=(tech["macd"] or (None,None,None))[2]
    if mn["pass"]:
        ms=mn["stage"]; mn2=mn["n"]
        pos.append(f"✅ Minervini SEPA {ms} — {mn2}/6 filters")
    if mh and mh>0: pos.append(f"✅ MACD bullish histogram +{mh:.2f}")
    elif mh and mh<0: neg.append(f"⚠️ MACD bearish histogram {mh:.2f}")

    ltp=tech["ltp"]; h52=tech["h52"]
    if h52 and ltp and h52>0:
        pf=(h52-ltp)/h52*100
        if pf<5: pos.append(f"✅ VCP setup — CMP {pf:.1f}% from 52W high ₹{h52:.1f}")
        elif pf>30: neg.append(f"⚠️ CMP {pf:.0f}% below 52W high")

    if tech["rs"]>=1.3: pos.append(f"✅ Strong RS {tech['rs']:.2f} — outperforming Nifty50")
    elif tech["rs"]<0.85: neg.append(f"⚠️ Weak RS {tech['rs']:.2f} — underperforming index")

    flags=(fp.get("value") or {})
    rc=flags.get("rev_cagr"); nc=flags.get("np_cagr")
    if rc and rc>=15: pos.append(f"✅ Revenue CAGR {rc}% (5Y)")
    if nc and nc>=15: pos.append(f"✅ PAT CAGR {nc}% (5Y)")

    pe_an=fp.get("pe",{})
    if "EXPENSIVE" in pe_an.get("verdict",""):
        pos_pe=str(pe_an.get("cur_pe","N/A")); pe5=str(pe_an.get("pe5","N/A"))
        neg.append(f"⚠️ PE {pos_pe}x expensive vs 5Y mean {pe5}x")

    sk=tech["srsi"][0] if tech["srsi"] else None
    if sk and sk>80: neg.append(f"⚠️ Stoch RSI {sk:.1f} — overbought")
    elif sk and sk<20: pos.append(f"✅ Stoch RSI {sk:.1f} — oversold reversal watch")

    rsi=tech["rsi"] or 50
    if rsi>72: neg.append(f"⚠️ RSI {rsi:.1f} — approaching overbought")
    elif rsi<30: pos.append(f"✅ RSI {rsi:.1f} — oversold zone")

    return pos[:6], neg[:4]


def risk(tech, fp):
    rsi=tech["rsi"] or 50; adx2=tech["adx"] or 20
    mn=tech["min"]; rs=tech["rs"]
    pe_an=fp.get("pe",{}); va=fp.get("value",{})
    vol=tech["ohlc"]["vol"]; avg=tech["avg20"]

    def badge(v):
        v=max(0,min(100,v))
        return ("Low","low") if v<=30 else (("Medium","med") if v<=60 else ("High","high"))

    mk=25+(30 if rsi>75 else 0)+(15 if adx2<20 else 0)-(10 if rs>=1 else 0)
    sk=20 if mn["pass"] else 50-(10 if rs>=1.2 else 0)
    ck=30; va_score=va.get("score",50)
    ck=max(10,70-int(va_score*0.4))
    fk=25+(30 if "EXPENSIVE" in pe_an.get("verdict","") else 0)-(15 if "CHEAP" in pe_an.get("verdict","") else 0)
    lk=25+(30 if avg and vol<avg*.3 else (15 if avg and vol<avg*.5 else 0))
    ov=sum([mk,sk,ck,fk,lk])/5

    return {"market":badge(mk),"sector":badge(sk),"company":badge(ck),
            "financial":badge(fk),"liquidity":badge(lk),"overall":badge(ov)}
