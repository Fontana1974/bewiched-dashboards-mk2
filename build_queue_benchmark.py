#!/usr/bin/env python3
# Build queue_benchmark.json — our average queue time vs the competition, from the F1 "The Race" tab.
# Source CSV (the_race.csv): columns Date, Store Name, Queue average (seconds), Area Coach.
#  - Competitors are the rows where Area Coach == "Check Name" (Costa / Nero('s) / Starbucks / Coffee#1).
#  - Our stores are every other row, grouped to areas by Area Coach (Jon / Ian / Rich).
# Window: quarter-to-date (every row in the sheet is the current quarter, ~Apr–Jun). Invalid 0s excluded.
import csv, json, os, sys, statistics as st

BASE = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
rows=[]
with open(os.path.join(BASE,"the_race.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        try: q=float(r["Queue average"])
        except: continue
        if q<=0: continue
        rows.append((r["Store Name"].strip(), r["Area Coach"].strip(), q))

COMP_COACH="Check Name"
our=[q for (s,c,q) in rows if c!=COMP_COACH]
comp=[q for (s,c,q) in rows if c==COMP_COACH]
def avg(xs): return round(st.mean(xs)) if xs else None
out={
 "_source":"F1 'The Race' tab — Queue average seconds, quarter-to-date; competitors = Area Coach 'Check Name' (Costa/Nero/Starbucks/Coffee#1)",
 "_window":"this quarter to date",
 "company":{"ours":avg(our),"n_ours":len(our),"comp":avg(comp),"n_comp":len(comp)},
 "areas":{}
}
for coach in ["Jon","Ian","Rich"]:
    a=[q for (s,c,q) in rows if c==coach]
    out["areas"][coach]={"ours":avg(a),"n_ours":len(a),"comp":out["company"]["comp"],"n_comp":len(comp)}

json.dump(out, open(os.path.join(BASE,"queue_benchmark.json"),"w"), ensure_ascii=False, indent=1)
print("queue_benchmark.json written")
c=out["company"]; print(f"  COMPANY: ours {c['ours']}s (n={c['n_ours']}) vs competition {c['comp']}s (n={c['n_comp']})")
for coach,a in out["areas"].items():
    faster = "faster" if a["ours"]<a["comp"] else "slower"
    print(f"  {coach}: ours {a['ours']}s (n={a['n_ours']}) vs comp {a['comp']}s — {faster}")
