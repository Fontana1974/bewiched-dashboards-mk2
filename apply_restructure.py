#!/usr/bin/env python3
"""One-shot: apply ONLY the 4-tab structural restructure to the two published store pages,
preserving every live figure (the full weekly content refresh stays the runbook's job and now
carries the same restructure via patch_newsite.py). Structure-only, idempotent."""
import patch_newsite as P
TARGETS=[('Glenvale_Forecast.html','Glenvale Drive Thru','Ian'),
         ('Leamington_Parade_Forecast.html','Leamington Parade','Rich')]
def apply(fn,store,coach):
    h=open(fn,encoding='utf-8').read()
    h=P.inject_compliance(h,store)     # drop the stale half-built compliance panel (star ops=None)
    h=P.relocate_coaching(h)           # keep documented coaching on Operations (idempotent)
    h=P.restructure_tabs(h,store)      # collapse 5 tabs -> Commercial/Operations/People/Customer
    h=P.inject_audit(h,store)          # brand-audit QTD + recurring themes on Operations
    h=P.simplify_mix_table(h)          # clean the category-mix table to match the capture table
    open(fn,'w',encoding='utf-8').write(h)
    print("restructured",fn)
if __name__=='__main__':
    for t in TARGETS: apply(*t)
