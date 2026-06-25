#!/usr/bin/env python3
# Build txquality_leamington.json — Leamington Parade "Transaction quality — Eat-in vs Takeaway" block.
#   Input : txq_leamington_raw.json -> {days, grid:[{ch(EI|TA), dp, txns, sales, foodtxns}]}  (last 28d, eatin_takeaway split)
#   Leamington has NO drive-thru (single till register) and an ~87% eat-in / 13% takeaway split, so the
#   channel split here is Eat-in vs Takeaway from the POS eatin_takeaway field (not DT vs Dine-In).
# AUTO from data: per-channel ATV / txns-day / %-of-store / food attach + the Channel x Daypart table.
# STATIC (manual targets / April-2026 P&L — flagged): ATV target, food-attach targets, the PAT tracker.
import json, datetime as dt
TARGET=6.80
FA_TGT={"EI":32,"TA":20}                  # eat-in like dine-in (sit-down), takeaway like grab-and-go
LABELS={"EI":{"name":"Eat-in","icon":"☕","border":"#2a9d8f"},
        "TA":{"name":"Takeaway","icon":"🥡","border":"#457b9d"}}
ORDER=["EI","TA"]
DPS=["Morning","Lunch","Afternoon","Evening"]
DPMETA={"Morning":("🌅","5am–11am"),"Lunch":("🥪","11am–2pm"),"Afternoon":("☕","2–5pm"),"Evening":("🌙","5pm+")}
# Leamington Parade April-2026 P&L (rolling 12m sheet): turnover £32,765/mo, PAT (operating profit) £2,540/mo.
STATIC={"pat_day_current":85,"pat_day_current_pct":7.8,"pat_day_target":197,"pat_pct_target":18,
        "pat_basis":"April 2026 P&L basis","gap_day":112,"daily_sales":1092}

raw=json.load(open("txq_leamington_raw.json")); days=raw["days"]; g=raw["grid"]
tot=sum(r["txns"] for r in g)
def acol(m): return "#1c6b3d" if m else "#c0392b"
def fa_badge(fa):
    if fa>=25: return ("#dcfce7","#1c6b3d")
    if fa>=15: return ("#fef9c3","#b7570a")
    return ("#fee2e2","#c0392b")
def sgn(v): return "#1c6b3d" if v>=0 else "#c0392b"
channels={}
for ch in ORDER:
    rows=[r for r in g if r["ch"]==ch]
    t=sum(r["txns"] for r in rows); s=sum(r["sales"] for r in rows); f=sum(r["foodtxns"] for r in rows)
    atv=s/t; fa=100*f/t
    channels[ch]={"label":LABELS[ch]["name"],"icon":LABELS[ch]["icon"],"border":LABELS[ch]["border"],
                  "txns_day":round(t/days,1),"atv":round(atv,2),"food_attach":round(fa,1),
                  "pct_store":round(100*t/tot),"daily_sales":round(s/days),
                  "atv_target_met":atv>=TARGET,"fa_target":FA_TGT[ch],"fa_met":fa>=FA_TGT[ch],"sparse":t<140}
grid=[]
for dp in DPS:
    for ch in ORDER:
        r=next((x for x in g if x["dp"]==dp and x["ch"]==ch),None)
        if not r: continue
        atv=r["sales"]/r["txns"]; tpd=r["txns"]/days; fa=100*r["foodtxns"]/r["txns"]; gap=(atv-TARGET)*tpd
        bg,fg=fa_badge(fa)
        grid.append({"daypart":dp,"icon":DPMETA[dp][0],"hours":DPMETA[dp][1],"ch":ch,"chlabel":LABELS[ch]["name"],"chcol":LABELS[ch]["border"],
                     "txns_day":round(tpd,1),"atv":round(atv,2),"atv_col":acol(atv>=TARGET),
                     "vs_target":round(atv-TARGET,2),"vs_col":sgn(atv-TARGET),
                     "daily_sales":round(r["sales"]/days),"food_attach":round(fa,1),"fa_bg":bg,"fa_fg":fg,
                     "gap_day":round(gap),"gap_col":sgn(gap),"sparse":r["txns"]<60})
today=dt.date.today(); cur_end=today-dt.timedelta(days=((today.weekday()+1)%7)); start=cur_end-dt.timedelta(days=27)
dl=lambda d:f"{d.day} {d.strftime('%b')}"
out={"_window":f"last 28 days ({dl(start)} – {dl(cur_end)} {cur_end.year})","days":days,"atv_target":TARGET,
     "split":"Eat-in vs Takeaway","channels":channels,"order":ORDER,"grid":grid,"static":STATIC}
json.dump(out,open("txquality_leamington.json","w"),indent=1,ensure_ascii=False)
print("txquality_leamington.json:",out["_window"])
for ch in ORDER:
    c=channels[ch]; print(f"  {c['label']:9s}: ATV £{c['atv']} ({'≥' if c['atv_target_met'] else '<'}£6.80) · {c['txns_day']}/day · {c['pct_store']}% · food {c['food_attach']}% (tgt {c['fa_target']}%)"+("  [sparse]" if c['sparse'] else ""))
