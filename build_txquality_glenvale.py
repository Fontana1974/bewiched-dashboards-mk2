#!/usr/bin/env python3
# Build txquality_glenvale.json for Glenvale's store "Sales" tab "Transaction quality — DT vs Dine In" block.
#   Input : txq_glenvale_raw.json  -> {days, grid:[{channel(DT|DI), daypart, txns, sales, foodtxns, retailtxns}]}
#           (one BigQuery pull, last 28 days, register-level split; see runbooks STEP 2q)
#   Output: txquality_glenvale.json -> computed per-channel + channel x daypart metrics + colours + window label
# AUTO (refreshes each run): per-channel ATV / txns-day / %-of-store / food-attach; the Channel x Daypart table.
# STATIC (manual targets/P&L — NOT sourced here): ATV target, PAT £/day current+target, food-attach targets, narratives.
import json, datetime as dt

TARGET=6.80                 # manual ATV target (£) — also drives the 18% PAT / £450-day target
FA_TGT={"DT":20,"DI":32}    # manual food-attach targets per channel
DPS=["Morning","Lunch","Afternoon","Evening"]
DPMETA={"Morning":("🌅","5am–11am"),"Lunch":("🥪","11am–2pm"),"Afternoon":("☕","2–5pm"),"Evening":("🌙","5pm+")}

raw=json.load(open("txq_glenvale_raw.json")); days=raw["days"]; g=raw["grid"]
tot_txns=sum(r["txns"] for r in g)

def atv_col(a):
    return "#1c6b3d" if a>=TARGET else ("#b7570a" if a>=TARGET-0.40 else "#c0392b")
def fa_badge(fa):
    if fa>=25: return ("#dcfce7","#1c6b3d")
    if fa>=15: return ("#fef9c3","#b7570a")
    return ("#fee2e2","#c0392b")
def signcol(v): return "#1c6b3d" if v>=0 else "#c0392b"

channels={}
for ch in ["DT","DI"]:
    rows=[r for r in g if r["channel"]==ch]
    t=sum(r["txns"] for r in rows); s=sum(r["sales"] for r in rows); f=sum(r["foodtxns"] for r in rows)
    atv=s/t; fa=100*f/t
    channels[ch]={"txns_day":round(t/days,1),"atv":round(atv,2),"food_attach":round(fa,1),
                  "pct_store":round(100*t/tot_txns),"daily_sales":round(s/days),
                  "atv_target_met":atv>=TARGET,"fa_target":FA_TGT[ch],"fa_met":fa>=FA_TGT[ch]}

grid=[]
for dp in DPS:
    for ch in ["DT","DI"]:
        r=next((x for x in g if x["daypart"]==dp and x["channel"]==ch),None)
        if not r: continue
        atv=r["sales"]/r["txns"]; tpd=r["txns"]/days; fa=100*r["foodtxns"]/r["txns"]
        gap=(atv-TARGET)*tpd
        bg,fg=fa_badge(fa)
        grid.append({"daypart":dp,"icon":DPMETA[dp][0],"hours":DPMETA[dp][1],"channel":ch,
                     "txns_day":round(tpd,1),"atv":round(atv,2),"atv_col":atv_col(atv),
                     "vs_target":round(atv-TARGET,2),"vs_col":signcol(atv-TARGET),
                     "daily_sales":round(r["sales"]/days),"food_attach":round(fa,1),
                     "fa_bg":bg,"fa_fg":fg,"gap_day":round(gap),"gap_col":signcol(gap)})

today=dt.date.today()
cur_end=today-dt.timedelta(days=((today.weekday()+1)%7))
start=cur_end-dt.timedelta(days=27)
def dlbl(d): return f"{d.day} {d.strftime('%b')}"
window=f"last 28 days ({dlbl(start)} – {dlbl(cur_end)} {cur_end.year})"

out={"_window":window,"days":days,"atv_target":TARGET,"fa_targets":FA_TGT,
     "store_daily_sales":round(sum(r['sales'] for r in g)/days),
     "channels":channels,"grid":grid,
     # STATIC manual inputs (P&L / targets) surfaced for the PAT tracker — flagged, not auto-sourced:
     "static":{"pat_day_current":354,"pat_day_current_pct":16.6,"pat_day_target":450,"pat_pct_target":18,
               "pat_basis":"April 2026 P&L basis","gap_day":96}}
json.dump(out,open("txquality_glenvale.json","w"),indent=1,ensure_ascii=False)
print("txquality_glenvale.json:",window)
for ch in ["DT","DI"]:
    c=channels[ch]; print(f"  {ch}: ATV £{c['atv']} ({'≥' if c['atv_target_met'] else '<'}£6.80) · {c['txns_day']}/day · {c['pct_store']}% · food {c['food_attach']}% (tgt {c['fa_target']}%)")
