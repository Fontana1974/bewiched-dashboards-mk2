#!/usr/bin/env python3
# Recompute star_rating.json (Grow composite — Glenvale + Leamington Parade) from live sources.
# Pillars REALIGNED to the four store-page tabs: Sales · Commercial · Operations · People & Customer.
# Each metric scored 0-5 by linear interpolation between anchors floor=0 / target=3 / stretch=5 (clamped);
# a pillar = mean of its scored metrics; composite = mean of the four pillars.
#   Sales            = Sales YoY (4-wk) + ATV vs £6.80                         (the old "Commercial" pillar, renamed)
#   Commercial       = Profit after tax vs target + CPH vs per-store target    (NEW; PAT is the headline input; CPH
#                      uses each store's OWN target — Glenvale £63, Leamington £58 — and is shown-not-scored when the
#                      week's actual CPH isn't posted, so Commercial then = PAT alone, flagged)
#   Operations       = F1 race score + brand audit /5 + wastage %              (UNCHANGED)
#   People & Customer= RMS health + RTW% + Google health                       (old People + Customer MERGED;
#                      lateness shown not scored; bench not per-store)
# GROW TARGET = 4.6 stars (composite/pillar below 4.6 = OFF TARGET). The 0/3/5 per-metric anchors are KEPT
# (meeting target on a metric = 3 stars); 4.6 is the headline Grow line (target marker + off-target state). NOT rescaled.
import json
from statistics import mean
ALL=json.load(open("allstores.json"))["rec"]
FD=json.load(open("f1_detail.json"))
SHS=json.load(open("storehealth.json"))["stores"]
SI=json.load(open("star_inputs.json"))
def _txq(fn):
    try: return json.load(open(fn)).get("static",{})
    except (FileNotFoundError,ValueError): return {}
TXQ={"Glenvale Drive Thru":_txq("txquality_glenvale.json"),"Leamington Parade":_txq("txquality_leamington.json")}
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
def pillar(metrics):
    scored=[m[2] for m in metrics if m[2] is not None]
    return (round(mean(scored),1) if scored else 0.0)

METHOD=("Grow composite, pillars REALIGNED to the four tabs (Sales · Commercial · Operations · People & Customer). "
 "Each metric scored 0-5 between anchors floor=0/target=3/stretch=5 (clamped); pillar = mean of its scored metrics; "
 "composite = mean of the four pillars. Sales = Sales YoY(-8/8/20) + ATV vs £6.80(5.5/6.8/8.0). "
 "Commercial = Profit-after-tax %(0/18/24) + CPH vs each store's OWN target(target*0.85/target/target*1.08; CPH shown-not-scored "
 "when the week's actual isn't posted). Operations = F1 race(320/190/130, lower better) + brand audit /5(4.0/4.5/5.0) + wastage %(5/3/1, lower better). "
 "People & Customer = RMS health(1.66/3.32/5.0) + RTW%(0/80/100) + Google health(1.66/3.32/5.0, QTD or live-rating fallback); lateness shown not scored, bench not per-store. "
 "GROW TARGET = 4.6 stars (below 4.6 = OFF TARGET); the per-metric 0/3/5 anchors are kept, 4.6 is the headline target line.")

out={"_method":METHOD,"_window":"quarter-to-date · Q2 2026 (rebuilt weekly)","target":TARGET,"stores":{}}
log=[]
for G in STORES:
    A=ALL.get(G,{}); F=FD.get(G,{}); SH=SHS.get(G,{}); si=SI[G]; pat=TXQ.get(G,{})
    yoy=A.get("yoy_4w"); atv=A.get("atv"); audit=A.get("audit_qtd"); waste=A.get("waste_pct")
    f1=(F.get("race_qtd") or {}).get("score"); rms=SH.get("r_avg")
    rtw=A.get("sent",{}).get("rtw_rate"); late=A.get("sent",{}).get("late")
    gh=SH.get("g_health"); gbasis="QTD"
    if gh is None:
        cu=A.get("cust",{}) or {}
        if cu.get("rating") is not None:
            tgt=SH.get("g_target",15) or 15
            gh=cu["rating"]*0.5+min((cu.get("reviews",0) or 0)/tgt,1)*2.5
            gbasis=f"live {cu['rating']}★/{cu.get('reviews',0)} all-time (QTD feed stale)"
    # PAT (Profit after tax) from the txquality static block; CPH from star_inputs (per-store target).
    pat_pct=pat.get("pat_day_current_pct"); pat_cur=pat.get("pat_day_current")
    pat_tgt_pct=pat.get("pat_pct_target",18); pat_day_tgt=pat.get("pat_day_target")
    cph_a=si.get("cph_actual"); cph_t=si.get("cph_target")
    # ---- pillar metric breakdowns ----
    sales=[("Sales YoY (4-wk)",f"{'+' if (yoy or 0)>=0 else ''}{round(yoy,1)}%",up(yoy,-8,8,20)),
           ("ATV vs £6.80",f"£{atv}",up(atv,5.5,6.8,8.0))]
    patstar=up(pat_pct,0,pat_tgt_pct,pat_tgt_pct+6) if pat_pct is not None else None
    cphstar=up(cph_a,cph_t*0.85,cph_t,cph_t*1.08) if (cph_a is not None and cph_t) else None
    commercial=[("Profit after tax",(f"£{pat_cur}/day · {pat_pct}% vs {pat_tgt_pct}% target" if pat_cur is not None else "n/a"),patstar),
                (f"CPH vs £{cph_t} target",(f"£{cph_a}" if cph_a is not None else "held — provisional, shown not scored"),cphstar)]
    operations=[("F1 race score",f"{round(f1)}",dn(f1,320,190,130)),
                ("Brand audit /5",f"{round(audit,2)}",up(audit,4.0,4.5,5.0)),
                ("Wastage %",f"{waste}%",dn(waste,5.0,3.0,1.0))]
    peoplecust=[("RMS health /5",f"{round(rms,2)}",up(rms,1.66,3.32,5.0)),
                ("RTW completion",f"{round(rtw)}%",up(rtw,0,80,100)),
                ("Google health",f"{round(gh,2)} ({gbasis})",up(gh,1.66,3.32,5.0)),
                ("Lateness (shown, not scored)",f"{late} late",None)]
    pills=[("Sales",sales),("Commercial",commercial),("Operations",operations),("People & Customer",peoplecust)]
    P=[{"name":n,"star":pillar(ms),"target":TARGET,"on_target":pillar(ms)>=TARGET,
        "metrics":[{"label":l,"value":v,"star":(r1(s) if s is not None else None)} for (l,v,s) in ms]} for n,ms in pills]
    comp=round(mean([p["star"] for p in P]),1)
    # ops block for the Operations compliance panel (remote audit / compliance / coaching / RTW); None when not pulled
    ops_block=None
    if si.get("remote_audit") is not None:
        cs=si.get("coaching_cs_pct"); oc=si.get("openclose_pct")
        comp_pct=round((cs+oc)/2,1) if (cs is not None and oc is not None) else None
        ops_block={"brand_audit":audit,"remote_audit":si["remote_audit"],"remote_n":si.get("remote_n"),
                   "compliance_pct":comp_pct,"coaching_cs_pct":cs,"coaching_barista_pct":si.get("coaching_barista_pct"),
                   "openclose_pct":oc,"openclose_detail":si.get("openclose_detail",""),
                   "rtw_pct":rtw,"rtw_detail":si.get("rtw_detail","")}
    out["stores"][G]={"composite":comp,"target":TARGET,"on_target":comp>=TARGET,"pillars":P,"ops":ops_block}
    log.append((G,comp,{p["name"]:p["star"] for p in P}))
json.dump(out,open("star_rating.json","w"),indent=1,ensure_ascii=False)
for L in log: print(f"{L[0]}: composite {L[1]} (target {TARGET}, {'ON' if L[1]>=TARGET else 'OFF'} target) {L[2]}")
