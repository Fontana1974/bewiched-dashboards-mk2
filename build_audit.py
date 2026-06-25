#!/usr/bin/env python3
"""Brand-audit QTD score + recurring themes for the store dashboards (Glenvale + Leamington).
Reads audit_raw.json (the quarter's Brand-Audit rows pulled from the Brand Audit sheet
'Brand Audit Date (NEW24/25)' — Store, Date, 5 sub-scores [Culture, Shift mgmt, Cleanliness,
Product, Maintenance], Total, Action Plan) and writes audit_themes.json:
  { store: { qtd, n, window, pillars:{name:avg}, weakest:[...], themes:[{text,count,pillar}],
             themes_status:"live"|"pending" } }
patch_newsite.audit_section() renders it on the Operations tab. If audit_raw.json is missing/empty
for a store, patch_newsite falls back to the allstores audit_qtd score and flags themes 'pending'.
Recurring themes = action-plan topics that appear in >=2 of the quarter's audits (data-driven)."""
import json, re, datetime, statistics as _st

PILLARS=["Store Culture","Shift Management","Cleanliness","Product","Maintenance"]
# Recurring-theme topic patterns (label, pillar, regex over the action-plan text).
TOPICS=[
 ("Queue calling at peak ('2 is a queue') and consistent hellos &amp; goodbyes","Store Culture",
   r"queue calling|hellos and goodbyes|hellos dipped|2 is a queue|goodbyes"),
 ("Transactions mis-keyed as 'dine in' instead of takeaway (VAT impact)","Shift Management",
   r"dine ?in|takeaway|vat"),
 ("Sticky syrup pumps / shelf residue &amp; daily wipe-downs","Cleanliness",
   r"syrup|sticky|residue|wipe"),
 ("Freezers due a defrost / floor mopping &amp; build-up","Cleanliness",
   r"defrost|mopping|build[ -]?up|floors?"),
 ("Chewing gum under tables / weekly deep-clean jobs","Cleanliness",
   r"chewing gum|weekly cleaning|deck"),
 ("Panini-fridge availability / fill under 90%","Shift Management",
   r"panini fridge|availability|90%"),
]

def _parse_date(s):
    for f in ("%m/%d/%Y","%d/%m/%Y","%Y-%m-%d"):
        try: return datetime.datetime.strptime(s.strip(),f).date()
        except: pass
    return None

def build(store, rows):
    if not rows: return None
    n=len(rows)
    totals=[r["total"] for r in rows]
    qtd=round(sum(totals)/n,2)
    pil={}
    for i,name in enumerate(PILLARS):
        vals=[r["sub"][i] for r in rows if len(r.get("sub",[]))>i]
        if vals: pil[name]=round(sum(vals)/len(vals),2)
    weakest=sorted(pil.items(), key=lambda kv: kv[1])[:2]
    weakest=[{"name":k,"avg":v} for k,v in weakest]
    dates=[_parse_date(r["date"]) for r in rows]; dates=[d for d in dates if d]
    win=""
    if dates:
        lo,hi=min(dates),max(dates)
        win=f"{lo.strftime('%b')}–{hi.strftime('%b')} {hi.year} · {n} audit{'s' if n!=1 else ''}"
    blob=" \n ".join((r.get("action","") or "") for r in rows).lower()
    themes=[]
    for label,pillar,pat in TOPICS:
        c=sum(1 for r in rows if re.search(pat, (r.get("action","") or "").lower()))
        if c>=2: themes.append({"text":label,"count":c,"pillar":pillar})
    themes.sort(key=lambda t:-t["count"])
    return {"qtd":qtd,"n":n,"window":win,"pillars":pil,"weakest":weakest,
            "themes":themes[:3],"themes_status":"live" if themes else "pending"}

def main():
    try: raw=json.load(open("audit_raw.json"))
    except (FileNotFoundError,ValueError):
        json.dump({}, open("audit_themes.json","w")); print("no audit_raw.json — wrote empty audit_themes.json"); return
    out={}
    for store,rows in (raw.get("rows") or {}).items():
        b=build(store,rows)
        if b: out[store]=b
    out["_pulled"]=raw.get("_pulled","")
    json.dump(out, open("audit_themes.json","w"), ensure_ascii=False, indent=1)
    for s in out:
        if s.startswith("_"): continue
        print(s, out[s]["qtd"], out[s]["window"], "weakest", out[s]["weakest"][0], "themes", len(out[s]["themes"]))

if __name__=="__main__": main()
