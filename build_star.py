#!/usr/bin/env python3
# Recompute star_rating.json (Glenvale Grow composite — TEST, Glenvale only) from live sources.
# Pillar inputs come from the Monday-refreshed JSONs (allstores.json, f1_detail.json, storehealth.json);
# the 3 slow-moving compliance/remote sub-metrics come from star_inputs.json (refreshed by the documented
# Monday pulls — remote-assessment tab, HRP coaching checklist, Process Street open/close). Keep last on miss.
# Anchors/weights are FIXED config below (mirrors the _method string). Glenvale-only by design.
import json, datetime
G="Glenvale Drive Thru"
A=json.load(open("allstores.json"))["rec"][G]
F=json.load(open("f1_detail.json")).get(G,{})
SH=json.load(open("storehealth.json"))["stores"].get(G,{})
SI=json.load(open("star_inputs.json"))[G]

def up(v,f,t,s):   # higher-better: 0 at floor, 3 at target, 5 at stretch (clamped)
    if v<=f: return 0.0
    if v<=t: return 3*(v-f)/(t-f)
    if v<=s: return 3+2*(v-t)/(s-t)
    return 5.0
def dn(v,f,t,s):   # lower-better: f>t>s
    if v>=f: return 0.0
    if v>=t: return 3*(f-v)/(f-t)
    if v>=s: return 3+2*(t-v)/(t-s)
    return 5.0
r1=lambda x:round(x,1)

# ---- live pillar inputs ----
sales_yoy = A.get("yoy_4w")               # QTD-ish (4-week) YoY %
brand_audit = A.get("audit_qtd")          # /5 QTD
f1_score = (F.get("race_qtd") or {}).get("score")  # QTD avg race score (lower better)
google_h = SH.get("g_health")             # Google health composite QTD
rms = SH.get("r_avg")                     # avg shift rating QTD
rtw = A.get("sent",{}).get("rtw_rate")    # RTW % QTD
# ---- slow-moving specials (star_inputs.json) ----
remote = SI["remote_audit"]; remote_n=SI.get("remote_n")
coaching = (SI["coaching_cs_pct"]+SI["coaching_barista_pct"])/2
openclose = SI["openclose_pct"]

# ---- pillar stars ----
sales = up(sales_yoy,-8,8,20)
customer = 0.5*up(google_h,1.66,3.32,5.0) + 0.5*dn(f1_score,320,190,130)
people = 0.5*up(rms,1.66,3.32,5.0) + 0.5*up(rtw,0,80,100)
compliance_star = 0.5*up(coaching,50,85,100) + 0.5*up(openclose,50,85,100)
operations = (up(brand_audit,4.0,4.5,5.0) + up(remote,50,85,100) + compliance_star)/3
composite = (sales+operations+customer+people)/4

out={
 "_method": json.load(open("star_rating.json")).get("_method",""),
 "_window": "quarter-to-date · Q2 2026 (rebuilt weekly)",
 "stores": {G:{
   "composite": r1(composite),
   "pillars": [
     {"name":"Sales","star":r1(sales),"qtd":f"{'+' if sales_yoy>=0 else ''}{round(sales_yoy,1)}% YoY","target":"target +8%"},
     {"name":"Operations","star":r1(operations),"qtd":f"audit {round(brand_audit,2)} + remote {round(remote)} + compliance {round((coaching+openclose)/2)}%","target":"equal-thirds: audit·remote·compliance"},
     {"name":"Customer","star":r1(customer),"qtd":f"Google health {round(google_h,2)} + F1 {round(f1_score)}","target":"Google health + F1 race (50/50)"},
     {"name":"People","star":r1(people),"qtd":f"{round(rms,2)} RMS + {round(rtw)}% RTW","target":"RMS health + RTW% (50/50)"}
   ],
   "ops": {
     "brand_audit": round(brand_audit,2), "remote_audit": round(remote), "remote_n": remote_n,
     "compliance_pct": round((coaching+openclose)/2), "coaching_cs_pct": SI["coaching_cs_pct"],
     "coaching_barista_pct": SI["coaching_barista_pct"], "open_pct": SI["open_pct"], "close_pct": SI["close_pct"],
     "openclose_pct": openclose, "openclose_detail": SI.get("openclose_detail",""),
     "rtw_pct": round(rtw), "rtw_detail": SI.get("rtw_detail","")
   }
 }}
}
json.dump(out, open("star_rating.json","w"), indent=1)
p=out["stores"][G]
print("composite", p["composite"], "| pillars", {x["name"]:x["star"] for x in p["pillars"]})
print("inputs: salesYoY",sales_yoy,"audit",round(brand_audit,2),"f1",f1_score,"google_h",google_h,"rms",rms,"rtw",rtw,"remote",remote,"coaching",coaching,"openclose",openclose)
