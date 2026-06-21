#!/usr/bin/env python3
# Rebuild App_Dashboard.html from app_data.json (Vicky's app dashboard).
# Monday refresh: run the 4 BigQuery pulls -> app_data.json -> python3 build_app.py
import json
d=json.load(open("app_data.json"))
t=open("app_template.html").read()
t=t.replace("__WK__", json.dumps(d["wk"]))
t=t.replace("__QTR__", json.dumps(d["qtr"], ensure_ascii=False))
t=t.replace("__STORE__", json.dumps(d["store"], ensure_ascii=False))
t=t.replace("__REWARDS__", json.dumps(d["rewards"], ensure_ascii=False))
open("App_Dashboard.html","w").write(t)
print("App_Dashboard.html rebuilt — wk",len(d["wk"]),"qtr",len(d["qtr"]),"store",len(d["store"]),"rewards",len(d["rewards"]))
