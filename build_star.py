#!/usr/bin/env python3
# Recompute star_rating.json (Grow composite — Glenvale + Leamington Parade) from live sources.
# Pillars are REALIGNED to the four store-page tabs: Commercial · Operations · People · Customer.
# Each metric is scored 0-5 by linear interpolation between anchors floor=0 / target=3 / stretch=5 (clamped);
# a pillar = the mean of its metrics; composite = mean of the four pillars.
#   Commercial = Sales YoY (4-wk) + ATV vs £6.80           (CPH actual is not auto-sourced per store -> not scored)
#   Operations = F1 race score + brand audit /5 + wastage % (lower waste better)
#   People     = RMS health + RTW%                          (lateness shown on the page but not scored; bench not per-store)
#   Customer   = Google health (QTD; falls back to the live all-time rating when the QTD feed is stale, flagged)
# GROW TARGET = 4.6 stars: a composite (or pillar) below 4.6 is OFF TARGET. The 0/3/5 per-metric anchors are kept
# (so "meeting target" on a metric = 3 stars); 4.6 is the headline Grow line, shown as a target marker + off-target state.
import json
from statistics import mean
ALL=json.load(open("allstores.json"))["rec"]
FD=json.load(open("f1_detail.json"))
SHS=json.load(open("storehealth.json"))["stores"]
SI=json.load(open("star_inputs.json"))
STORES=[k for k in SI.keys() if not k.startswith("_")]
TARGET=4.6

def up(v,f,t,s):
    if v is None: return None
    if v<=f: return 0.0
    if v<=t: return 3*(v-f)/(t-f)
    if v<=s: return 3+2*(v-t)/(s-t)
    return 5.0
def dn(v,f,t,s):
    if v is None: return None
    if v>=f: return 0.0
    if v>=t: return 3*(f-v)/(f-t)
    if v>=s: return 3+2*(t-v)/(t-s)
    return 5.0
r1=lambda x:round(x,1)
def pillar(metrics):  # metrics=[(label,valuetext,star)]; star may be None (shown, not scored)
    scored=[m[2] for m in metrics if m[2] is not None]
    return (round(mean(scored),1) if scored else 0.0)

METHOD=("Grow composite, pillars REALIGNED to the four tabs (Commercial · Operations · People · Customer). "
 "Each metric scored 0-5 between anchors floor=0/target=3/stretch=5 (clamped); pillar = mean of its metrics; "
 "composite = mean of the four pillars. Commercial = Sales YoY(-8/8/20) + ATV vs £6.80(5.5/6.8/8.0). "
 "Operations = F1 race(320/190/130, lower better) + brand audit /5(4.0/4.5/5.0) + wastage %(5/3/1, lower better). "
 "People = RMS health(1.66/3.32/5.0) + RTW%(0/80/100); lateness is shown but not scored, bench is not tracked per store. "
 "Customer = Google health(1.66/3.32/5.0), QTD or live-rating fallback when the QTD feed is stale. "
 "GROW TARGET = 4.6 stars (below 4.6 = OFF TARGET); the per-metric 0/3/5 anchors are kept, 4.6 is the headline target line.")

out={"_method":METHOD,"_window":"quarter-to-date · Q2 2026 (rebuilt weekly)","target":TARGET,"stores":{}}
log=[]
for G in STORES:
    A=ALL.get(G,{}); F=FD.get(G,{}); SH=SHS.get(G,{}); si=SI[G]
    yoy=A.get("yoy_4w"); atv=A.get("atv"); audit=A.get("audit_qtd"); waste=A.get("waste_pct")
    f1=(F.get("race_qtd") or {}).get("score"); rms=SH.get("r_avg"); rtw=A.get("sent",{}).get("rtw_rate"); late=A.get("sent",{}).get("late")
    gh=SH.get("g_health"); gbasis="QTD"
    if gh is None:
        cu=A.get("cust",{}) or {}
        if cu.get("rating") is not None:
            tgt=SH.get("g_target",15) or 15
            gh=cu["rating"]*0.5+min((cu.get("reviews",0) or 0)/tgt,1)*2.5
            gbasis=f"live {cu['rating']}★/{cu.get('reviews',0)} all-time (QTD feed stale)"
    # ---- pillar metric breakdowns ----
    commercial=[("Sales YoY (4-wk)",f"{'+' if (yoy or 0)>=0 else ''}{round(yoy,1)}%",up(yoy,-8,8,20)),
                ("ATV vs £6.80",f"£{atv}",up(atv,5.5,6.8,8.0))]
    operations=[("F1 race score",f"{round(f1)}",dn(f1,320,190,130)),
                ("Brand audit /5",f"{round(audit,2)}",up(audit,4.0,4.5,5.0)),
                ("Wastage %",f"{waste}%",dn(waste,5.0,3.0,1.0))]
    people=[("RMS health /5",f"{round(rms,2)}",up(rms,1.66,3.32,5.0)),
            ("RTW completion",f"{round(rtw)}%",up(rtw,0,80,100)),
            ("Lateness (shown, not scored)",f"{late} late",None)]
    customer=[("Google health",f"{round(gh,2)} ({gbasis})",up(gh,1.66,3.32,5.0))]
    pills=[("Commercial",commercial),("Operations",operations),("People",people),("Customer",customer)]
    P=[{"name":n,"star":pillar(ms),"target":TARGET,"on_target":pillar(ms)>=TARGET,
        "metrics":[{"label":l,"value":v,"star":(r1(s) if s is not None else None)} for (l,v,s) in ms]} for n,ms in pills]
    comp=round(mean([p["star"] for p in P]),1)
    out["stores"][G]={"composite":comp,"target":TARGET,"on_target":comp>=TARGET,"pillars":P}
    log.append((G,comp,{p["name"]:p["star"] for p in P}))
json.dump(out,open("star_rating.json","w"),indent=1,ensure_ascii=False)
for L in log: print(f"{L[0]}: composite {L[1]} (target {TARGET}, {'ON' if L[1]>=TARGET else 'OFF'} target) {L[2]}")
