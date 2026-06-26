"""
indicators.py — Technical Indicators + Chart Pattern Detection
All computed from raw OHLCV. No external TA library needed.
"""
import math


# ── Helpers ───────────────────────────────────────────────────────────────────
def C(s): return [x["c"] for x in s]
def H(s): return [x["h"] for x in s]
def L(s): return [x["l"] for x in s]
def O(s): return [x["o"] for x in s]
def V(s): return [x["v"] for x in s]

def ema(prices, n):
    if len(prices) < n: return [None]*len(prices)
    k = 2/(n+1)
    out = [None]*(n-1) + [sum(prices[:n])/n]
    for p in prices[n:]:
        out.append(out[-1]*(1-k)+p*k)
    return out

def sma(prices, n):
    return [None if i<n-1 else sum(prices[i-n+1:i+1])/n for i in range(len(prices))]

def last(lst):
    for v in reversed(lst):
        if v is not None: return v
    return None


# ── RSI ───────────────────────────────────────────────────────────────────────
def rsi(s, n=14):
    c=C(s)
    if len(c)<n+1: return None
    g=[max(c[i]-c[i-1],0) for i in range(1,len(c))]
    l=[max(c[i-1]-c[i],0) for i in range(1,len(c))]
    ag=sum(g[:n])/n; al=sum(l[:n])/n
    for i in range(n,len(g)):
        ag=(ag*(n-1)+g[i])/n; al=(al*(n-1)+l[i])/n
    return round(100-100/(1+ag/al),1) if al else 100.0


# ── MACD ──────────────────────────────────────────────────────────────────────
def macd(s):
    c=C(s)
    ef=ema(c,12); es=ema(c,26)
    ml=[f-sv if f and sv else None for f,sv in zip(ef,es)]
    vm=[v for v in ml if v is not None]
    if len(vm)<9: return None,None,None
    sl=ema(vm,9); mv=vm[-1]; sv=last(sl)
    return round(mv,2), round(sv,2) if sv else None, round(mv-sv,2) if sv else None


# ── ADX ───────────────────────────────────────────────────────────────────────
def adx(s, n=14):
    if len(s)<n+1: return None
    h=H(s); l=L(s); c=C(s)
    tr,pdm,ndm=[],[],[]
    for i in range(1,len(s)):
        tr.append(max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])))
        up=h[i]-h[i-1]; dn=l[i-1]-l[i]
        pdm.append(max(up,0) if up>dn else 0)
        ndm.append(max(dn,0) if dn>up else 0)
    atr=sum(tr[:n]); sp=sum(pdm[:n]); sn=sum(ndm[:n]); dx=[]
    for i in range(n,len(tr)):
        atr=atr-atr/n+tr[i]; sp=sp-sp/n+pdm[i]; sn=sn-sn/n+ndm[i]
        p=100*sp/atr if atr else 0; nn=100*sn/atr if atr else 0
        d=p+nn; dx.append(100*abs(p-nn)/d if d else 0)
    return round(sum(dx[-n:])/n,1) if len(dx)>=n else None


# ── Stochastic RSI ────────────────────────────────────────────────────────────
def stoch_rsi(s, rn=14, sn=14, k=3, d=3):
    c=C(s)
    if len(c)<rn+sn+k+d: return None,None
    rv=[]
    for i in range(rn,len(c)):
        sub=c[max(0,i-rn-14):i+1]
        g=[max(sub[j]-sub[j-1],0) for j in range(1,len(sub))]
        l=[max(sub[j-1]-sub[j],0) for j in range(1,len(sub))]
        ag=sum(g[:rn])/rn; al=sum(l[:rn])/rn
        for gi,li in zip(g[rn:],l[rn:]):
            ag=(ag*(rn-1)+gi)/rn; al=(al*(rn-1)+li)/rn
        rv.append(100-100/(1+ag/al) if al else 100)
    if len(rv)<sn: return None,None
    rk=[]
    for i in range(sn-1,len(rv)):
        w=rv[i-sn+1:i+1]; lo=min(w); hi=max(w)
        rk.append(100*(rv[i]-lo)/(hi-lo) if hi!=lo else 50)
    ks=sma(rk,k); ds=sma([v for v in ks if v is not None],d)
    return (round(last(ks),1) if last(ks) else None,
            round(last(ds),1) if last(ds) else None)


# ── CCI ───────────────────────────────────────────────────────────────────────
def cci(s, n=20):
    if len(s)<n: return None
    tp=[(x["h"]+x["l"]+x["c"])/3 for x in s[-n:]]
    m=sum(tp)/n; md=sum(abs(t-m) for t in tp)/n
    return round((tp[-1]-m)/(0.015*md),1) if md else 0


# ── VWAP ──────────────────────────────────────────────────────────────────────
def vwap(s):
    total_pv=sum((x["h"]+x["l"]+x["c"])/3*x["v"] for x in s if x.get("v"))
    total_v=sum(x["v"] for x in s if x.get("v"))
    return round(total_pv/total_v,2) if total_v else None


# ── Moving Averages ───────────────────────────────────────────────────────────
def moving_averages(s):
    c=C(s); cur=c[-1] if c else 0
    out={}
    for n in [9,20,50,100,200]:
        sv=last(sma(c,n)); ev=last(ema(c,n))
        sig="Bullish" if sv and cur>sv else ("Bearish" if sv else "N/A")
        out[n]={"sma":round(sv,2) if sv else None,
                "ema":round(ev,2) if ev else None,
                "sig":sig}
    return out


# ── Pivot Points ──────────────────────────────────────────────────────────────
def pivots(s):
    if len(s)<2: return {}
    p=s[-2]; H2,L2,C2=p["h"],p["l"],p["c"]
    pv=(H2+L2+C2)/3
    return dict(
        pivot=round(pv,2),
        r1=round(2*pv-L2,2),r2=round(pv+(H2-L2),2),r3=round(H2+2*(pv-L2),2),
        s1=round(2*pv-H2,2),s2=round(pv-(H2-L2),2),s3=round(L2-2*(H2-pv),2)
    )


# ── Support / Resistance Zones ────────────────────────────────────────────────
def sr_zones(s, window=3, min_touches=2):
    if len(s)<window*2+1: return []
    zones=[]
    h=H(s); l=L(s); c=C(s)
    cur=c[-1]

    for i in range(window, len(s)-window):
        if h[i]==max(h[i-window:i+window+1]):
            price=h[i]; touches=sum(1 for j in range(len(s)) if abs(h[j]-price)/price<0.005)
            if touches>=min_touches:
                zones.append({"price":round(price,2),"type":"resistance",
                              "touches":touches,"strength":min(touches*20,100)})

    for i in range(window, len(s)-window):
        if l[i]==min(l[i-window:i+window+1]):
            price=l[i]; touches=sum(1 for j in range(len(s)) if abs(l[j]-price)/price<0.005)
            if touches>=min_touches:
                zones.append({"price":round(price,2),"type":"support",
                              "touches":touches,"strength":min(touches*20,100)})

    merged=[]
    for z in sorted(zones,key=lambda x:x["price"]):
        if merged and abs(z["price"]-merged[-1]["price"])/merged[-1]["price"]<0.01:
            if z["touches"]>merged[-1]["touches"]: merged[-1]=z
        else:
            merged.append(z)

    above=[z for z in merged if z["price"]>cur][:4]
    below=[z for z in merged if z["price"]<=cur][-4:]
    return below+above


# ── Chart Pattern Detection ───────────────────────────────────────────────────
def detect_patterns(s):
    if len(s)<10: return []
    c=C(s); h=H(s); l=L(s); o=O(s)
    n=len(s)
    patterns=[]

    def body(i): return abs(c[i]-o[i])
    def upper_wick(i): return h[i]-max(c[i],o[i])
    def lower_wick(i): return min(c[i],o[i])-l[i]

    if n>=15:
        ranges=[h[-15+i]-l[-15+i] for i in range(15)]
        vols=[s[-15+i].get("v",0) for i in range(15)]
        contracting=all(ranges[i]>=ranges[i+1] for i in range(0,12,3))
        vol_contracting=sum(vols[:7])>sum(vols[7:]) if sum(vols[7:]) else False
        if contracting and vol_contracting:
            patterns.append({"name":"VCP (Volatility Contraction)","direction":"bullish",
                            "confidence":85,
                            "description":"Price ranges contracting with declining volume — classic pre-breakout setup. Watch for breakout above ₹"+str(round(max(h[-5:]),2))+" on 1.5× avg volume."})

    if n>=20:
        lows=l[-20:]
        min1_idx=lows.index(min(lows))
        lows2=[x if i!=min1_idx else 9999 for i,x in enumerate(lows)]
        min2_idx=lows2.index(min(lows2))
        if abs(min1_idx-min2_idx)>=5:
            diff=abs(lows[min1_idx]-lows[min2_idx])
            if diff/lows[min1_idx]<0.03:
                patterns.append({"name":"Double Bottom","direction":"bullish",
                                "confidence":78,
                                "description":f"Two lows near ₹{round(min(lows),1)} separated by {abs(min1_idx-min2_idx)} bars. Bullish reversal — neckline breakout triggers entry."})

    if n>=25:
        hs=h[-25:]
        max1_idx=hs.index(max(hs))
        if 8<=max1_idx<=16:
            left_peak=max(hs[:max1_idx-3])
            right_peak=max(hs[max1_idx+3:])
            head=hs[max1_idx]
            if left_peak<head and right_peak<head and abs(left_peak-right_peak)/head<0.04:
                patterns.append({"name":"Head & Shoulders","direction":"bearish",
                                "confidence":72,
                                "description":f"Head at ₹{round(head,1)} with shoulders near ₹{round((left_peak+right_peak)/2,1)}. Bearish reversal — neckline break confirms."})

    if n>=30:
        ch=c[-30:]
        peak_l=max(ch[:10]); bottom=min(ch[8:22]); peak_r=max(ch[20:])
        if peak_r>peak_l*0.95 and bottom<peak_l*0.85:
            handle_range=(max(ch[-8:])-min(ch[-8:]))/peak_r
            if handle_range<0.08:
                patterns.append({"name":"Cup & Handle","direction":"bullish",
                                "confidence":80,
                                "description":f"Rounded base with tight handle. Breakout target: ₹{round(peak_r*1.08,1)}. Entry on handle breakout with volume."})

    if n>=15:
        pole=c[-15:-8]; flag=c[-8:]
        pole_move=(max(pole)-min(pole))/min(pole)*100 if min(pole) else 0
        flag_range=(max(flag)-min(flag))/max(flag)*100 if max(flag) else 0
        flag_slope=(flag[-1]-flag[0])/flag[0]*100 if flag[0] else 0
        if pole_move>8 and flag_range<4 and -3<flag_slope<0.5:
            patterns.append({"name":"Bullish Flag","direction":"bullish",
                            "confidence":77,
                            "description":f"Strong {round(pole_move,1)}% pole with tight flag consolidation. Measured move target: +{round(pole_move*0.8,1)}% from breakout."})

    if n>=15:
        pole=c[-15:-8]; flag=c[-8:]
        pole_drop=(max(pole)-min(pole))/max(pole)*100 if max(pole) else 0
        flag_range=(max(flag)-min(flag))/max(flag)*100 if max(flag) else 0
        flag_slope=(flag[-1]-flag[0])/flag[0]*100 if flag[0] else 0
        if c[-15]>c[-8] and pole_drop>8 and flag_range<4 and -0.5<flag_slope<3:
            patterns.append({"name":"Bearish Flag","direction":"bearish",
                            "confidence":74,
                            "description":f"Drop of {round(pole_drop,1)}% with upward consolidation flag. Breakdown risk of -{round(pole_drop*0.7,1)}%."})

    if n>=1:
        i=-1
        if body(i)<(h[i]-l[i])*0.1 and (h[i]-l[i])>0:
            prev_trend = "up" if c[-5]>c[-10] else "down"
            patterns.append({"name":"Doji (Indecision)","direction":"neutral",
                            "confidence":60,
                            "description":f"Doji after {prev_trend}trend signals indecision. Watch next candle for direction confirmation."})

    if n>=2:
        i=-1
        if lower_wick(i)>body(i)*2 and upper_wick(i)<body(i)*0.5 and c[-5]<c[-10]:
            patterns.append({"name":"Hammer (Reversal)","direction":"bullish",
                            "confidence":70,
                            "description":"Long lower wick after downtrend — bullish reversal signal. Confirmation needed next session."})
        if upper_wick(i)>body(i)*2 and lower_wick(i)<body(i)*0.5 and c[-5]>c[-10]:
            patterns.append({"name":"Shooting Star","direction":"bearish",
                            "confidence":70,
                            "description":"Long upper wick after uptrend — bearish reversal signal. Breakdown below today's low confirms."})

    return sorted(patterns, key=lambda x:-x["confidence"])[:3]


# ── Price Returns (HISTORICAL only — NO forward projections from past CAGR) ───
def price_returns(s, ltp):
    """
    Returns historical % moves only.
    Targets (t3m/t6m/t1y) are based on pivot R1/R2/R3 — NOT CAGR extrapolation.
    Past negative CAGR does NOT mean future price will fall.
    """
    n=len(s)
    def ret(d):
        idx=n-1-d
        if idx<0 or idx>=n: return None
        b=s[idx]["c"]
        return round((ltp-b)/b*100,2) if b else None

    r={}
    for lbl,d in [("1D",1),("2D",2),("5D",5),("7D",7),
                  ("1W",5),("1M",21),("2M",42),("6M",126)]:
        r[lbl]=ret(d)

    # Historical CAGR for reference only — do NOT use for price targets
    days=min(252,n-1)
    if days>20:
        b=s[n-1-days]["c"]
        cagr=round(((ltp/b)**(252/days)-1)*100,1) if b else None
        r["cagr1y"]=cagr
    else:
        r["cagr1y"]=None

    # Price targets will be filled from entry_exit() pivot-based values
    r["t3m"]=None; r["t6m"]=None; r["t1y"]=None
    return r


# ── Entry / Exit ──────────────────────────────────────────────────────────────
def entry_exit(s, ltp):
    """
    Entry/exit levels based on pivot points and moving averages.
    Targets use R1/R2/R3 from pivot calculation — not CAGR projections.
    """
    pp=pivots(s)
    ma=moving_averages(s)
    el=pp.get("s1",ltp*0.97); eh=pp.get("pivot",ltp*0.99)
    sl=max(pp.get("s2",0), el*0.96)
    sma50=ma.get(50,{}).get("sma") or 0
    if sma50: sl=max(sl,sma50*0.97)
    t1=pp.get("r1",ltp*1.03)
    t2=pp.get("r2",ltp*1.06)
    t3=pp.get("r3",ltp*1.10)
    rr=round((t2-ltp)/(ltp-sl),1) if ltp>sl else 0
    return {"el":round(el,2),"eh":round(eh,2),"sl":round(sl,2),
            "t1":round(t1,2),"t2":round(t2,2),"t3":round(t3,2),"rr":rr}


# ── Minervini SEPA ────────────────────────────────────────────────────────────
def minervini(s):
    if not s: return {"pass":False,"stage":"Unknown","n":0,"checks":{}}
    lat=s[-1]; c=lat["c"]
    ma=moving_averages(s)
    d50=ma[50]["sma"] or 0; d150=ma[100]["sma"] or 0; d200=ma[200]["sma"] or 0
    h52=lat.get("h52",c); rs=lat.get("rs",1.0)
    checks={
        "Price > 50 DMA":   c>d50,
        "Price > 150 DMA":  c>d150,
        "Price > 200 DMA":  c>d200,
        "50 DMA > 200 DMA": d50>d200 if d50 and d200 else False,
        "Within 25% of 52W High": c>=h52*0.75 if h52 else False,
        "RS ≥ 1.0":         rs>=1.0,
    }
    n2=sum(checks.values())
    stage="Stage 2 ✅" if n2>=5 else ("Stage 1" if n2>=3 else "Stage 3/4")
    return {"pass":n2>=5,"stage":stage,"n":n2,"checks":checks}


# ── Master compute ────────────────────────────────────────────────────────────
def compute(data):
    s=data["eod"]; live=data["live"]; candles=data.get("candles",[])

    ltp_live=live.get("ltp") or live.get("last_price")
    eod_close=s[-1]["c"] if s else 0
    ltp_intra=candles[-1].get("c",0) if candles else 0
    if ltp_live and eod_close and (ltp_live>eod_close*3 or ltp_live<eod_close*0.3):
        ltp_live=None
    ltp=ltp_live or ltp_intra or eod_close

    prev=live.get("prev_close") or (s[-2]["c"] if len(s)>=2 else ltp)
    chg=round(ltp-prev,2); chgp=round(chg/prev*100,2) if prev else 0

    intra_h=max((c.get("h",0) for c in candles),default=0) if candles else 0
    intra_l=min((c.get("l",9999) for c in candles),default=9999) if candles else 9999
    intra_o=(candles[0].get("o",0) or candles[0].get("open",0)) if candles else 0
    intra_vol=sum(c.get("v",0) for c in candles) if candles else 0

    ohlc={
        "o": live.get("open") or intra_o or (s[-1]["o"] if s else 0),
        "h": live.get("high") or (intra_h if intra_h else (s[-1]["h"] if s else 0)),
        "l": live.get("low")  or (intra_l if intra_l<9999 else (s[-1]["l"] if s else 0)),
        "c": ltp, "pc": prev,
        "vol": live.get("volume") or (intra_vol if intra_vol else (s[-1]["v"] if s else 0)),
        "bq": live.get("buy_qty",0), "sq": live.get("sell_qty",0),
        "ap": live.get("avg_price",0) or ltp,
    }

    lat=s[-1] if s else {}
    ret=price_returns(s,ltp)
    ee=entry_exit(s,ltp)

    # Fill pivot-based targets into ret
    ret["t3m"]=ee["t1"]   # R1 = short-term target (~3M)
    ret["t6m"]=ee["t2"]   # R2 = medium-term target (~6M)
    ret["t1y"]=ee["t3"]   # R3 = longer-term target (~1Y)

    return {
        "ltp":ltp,"chg":chg,"chgp":chgp,"ohlc":ohlc,
        "h52":lat.get("h52",0),"l52":lat.get("l52",0),
        "rs":lat.get("rs",1.0),"avg20":lat.get("avg20",0),
        "rsi":rsi(s),"macd":macd(s),"adx":adx(s),
        "srsi":stoch_rsi(s),"cci":cci(s),
        "mas":moving_averages(s),"pp":pivots(s),
        "sr":sr_zones(s),"patterns":detect_patterns(s),
        "ret":ret,"ee":ee,
        "min":minervini(s),
        "vwap":vwap(candles) if candles else None,
    }
