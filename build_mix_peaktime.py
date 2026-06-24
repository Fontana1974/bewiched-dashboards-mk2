#!/usr/bin/env python3
# Build mix_peaktime.json for the COMPANY dashboard "Mix & opportunity" tab.
#   Inputs  (written by the weekly BigQuery pulls, see the runbooks STEP 2p):
#     peak_cat_raw.json    -> [{cat, dp, s}]              category x daypart sales, last 4 weeks, company-wide
#     peak_bakery_raw.json -> [{prod, peak_dp, share, peak_hr, units, sales}]  per bakery product, last 4 weeks
#   Output:
#     mix_peaktime.json    -> {_window, _dayparts, categories{cat:{peak,share,gap,soft,total}}, bakery[...]}
# Dayparts (established): Morning 5-11am, Lunch 11am-2pm, Afternoon 2-5pm, Evening 5pm+.
# Headless / no Chrome. gen_company.py reads mix_peaktime.json to render the Peak-time column + Bakery table.
import json, datetime as dt
from collections import defaultdict

CATS=["Hot drinks","Cold drinks","Milkshakes","Food","Bakery","Other & retail"]
SPARSE=40            # < ~10/week over 4 weeks => too sparse to call a clear peak (left off the table)
SOFT_GAP=4           # peak within this many pp of the runner-up daypart => flagged as a soft/close call

def _load(fn):
    d=json.load(open(fn))
    return d.get("results", d) if isinstance(d, dict) else d

# ---- category peaks ----
cat=defaultdict(dict)
for r in _load("peak_cat_raw.json"):
    cat[r["cat"]][r["dp"]]=float(r["s"])
categories={}
for c in CATS:
    if not cat.get(c): continue
    tot=sum(cat[c].values()); peak=max(cat[c],key=cat[c].get)
    ordered=sorted(cat[c].values(),reverse=True)
    share=round(100*cat[c][peak]/tot)
    gap=round(100*(ordered[0]-ordered[1])/tot) if len(ordered)>1 else 100
    categories[c]={"peak":peak,"share":share,"gap":gap,"soft":gap<SOFT_GAP,"total":round(tot)}

# ---- bakery per product ----
def hr_lbl(h):
    h=int(h); ap="am" if h<12 else "pm"; hh=h if 1<=h<=12 else (h-12 if h>12 else 12)
    return f"{hh}{ap}"
bakery=[]
for r in sorted(_load("peak_bakery_raw.json"), key=lambda x:-int(x["units"])):
    bakery.append({"name":r["prod"],"peak":r["peak_dp"],"share":int(r["share"]),
                   "hour":hr_lbl(r["peak_hr"]),"units":int(r["units"]),"sales":int(r["sales"]),
                   "sparse":int(r["units"])<SPARSE})

# ---- window label: 4-week trailing window to the last complete Mon-Sun week (robust Sun & Mon runs) ----
today=dt.date.today()
cur_end=today - dt.timedelta(days=((today.weekday()+1)%7))   # last complete Sunday (=today if Sunday)
start=cur_end - dt.timedelta(days=27)
def dlbl(d): return f"{d.day} {d.strftime('%b')}"
window=f"last 4 weeks ({dlbl(start)} – {dlbl(cur_end)} {cur_end.year})"

out={"_window":window,
     "_dayparts":"Morning 5–11am · Lunch 11am–2pm · Afternoon 2–5pm · Evening 5pm+",
     "categories":categories,"bakery":bakery}
json.dump(out, open("mix_peaktime.json","w"), indent=1, ensure_ascii=False)
print("mix_peaktime.json written:", window,
      "| categories:", len(categories), "| bakery solid:",
      sum(1 for b in bakery if not b["sparse"]), "sparse:", sum(1 for b in bakery if b["sparse"]))
