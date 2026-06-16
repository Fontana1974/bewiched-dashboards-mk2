import json
# Google live (Q2-to-date) raw->canon
g_raw={"Train Station":(98,4.969),"Burton":(16,4.938),"Corby":(10,4.8),"Glenvale Drive Thru":(34,4.676),"Billing Drive Thru":(14,5.0),"Olney":(2,5.0),"Attleborough":(1,5.0)}
g_map={"Train Station":"Wellingborough Train Station","Burton":"Burton Latimer","Corby":"Corby","Glenvale Drive Thru":"Glenvale Drive Thru","Billing Drive Thru":"Billing Drive Thru","Olney":"Olney","Attleborough":"Attleborough"}
# RMS Q2-to-date raw->canon
rms_raw={"Corby":(60,3.533),"Glenvale Drive Thru":(51,3.294),"Npton Grosvenor":(28,4.679),"Kettering":(24,4.583),"Balsall":(36,4.917),"Npton Drive Thru":(41,4.146),"Fletton":(15,4.333),"Rugby":(62,4.919),"Market Harborough":(14,4.286),"Rothwell":(16,4.25),"W'boro Market St":(11,4.636),"Lakes":(19,3.368),"Peterborough":(19,4.789),"Leamington Parade":(120,4.692),"Lower Heathcote":(18,4.222),"Burton":(18,4.889),"Train Station":(13,1.846),"Higham":(8,4.625),"Billing Drive Thru":(22,4.818),"Olney":(3,5.0),"Attleborough":(32,4.688)}
rms_map={"Corby":"Corby","Glenvale Drive Thru":"Glenvale Drive Thru","Npton Grosvenor":"Northampton","Kettering":"Kettering","Balsall":"HOE Balsall Common","Npton Drive Thru":"Northampton Drive-Thru","Fletton":"Peterborough Fletton Quays","Rugby":"Rugby","Market Harborough":"Market Harborough","Rothwell":"Rothwell","W'boro Market St":"Wellingborough","Lakes":"Rushden Lakes","Peterborough":"Peterborough Bridge Street","Leamington Parade":"Leamington Parade","Lower Heathcote":"Lower Heathcote","Burton":"Burton Latimer","Train Station":"Wellingborough Train Station","Higham":"Higham Ferrers","Billing Drive Thru":"Billing Drive Thru","Olney":"Olney","Attleborough":"Attleborough"}
targets={"Northampton Drive-Thru":49,"Kettering":24,"Burton Latimer":10,"Rothwell":12,"Northampton":15,"Wellingborough":18,"Wellingborough Train Station":10,"Rushden Lakes":49,"Peterborough Fletton Quays":15,"Higham Ferrers":10,"Peterborough Bridge Street":18,"Lower Heathcote":8,"Leamington Parade":15,"Market Harborough":24,"Rugby":25,"Corby":25,"Glenvale Drive Thru":49,"HOE Balsall Common":15,"Billing Drive Thru":49,"Attleborough":15,"Olney":10}
OLNEY_DEFAULT=True
stores=["Attleborough","Billing Drive Thru","Burton Latimer","Corby","Glenvale Drive Thru","HOE Balsall Common","Higham Ferrers","Kettering","Leamington Parade","Lower Heathcote","Market Harborough","Northampton","Northampton Drive-Thru","Olney","Peterborough Bridge Street","Peterborough Fletton Quays","Rothwell","Rugby","Rushden Lakes","Wellingborough","Wellingborough Train Station"]
g_canon={g_map[k]:v for k,v in g_raw.items()}
rms_canon={rms_map[k]:v for k,v in rms_raw.items()}
def grag(h):
    return 'green' if h>=3.32 else 'red'
def rrag(a):
    return 'green' if a>=4.5 else ('amber' if a>=4.0 else 'red')
out={"_basis":"Quarter-to-date (Q2 2026: 1 Apr - 16 Jun). NOT last week.","_updated":"2026-06-16",
     "_google_formula":"google_health = avg_star*0.5 + min(reviews/quarterly_target,1)*2.5 ; green>=3.32",
     "_rms_formula":"rms_avg = quarterly mean shift rating (1-5); green>=4.5 amber>=4.0 red<4.0",
     "_google_feed_note":"Reviews scraper only live for 7 stores; 14 stale since ~Jul 2025 -> google_health null (shown as no-feed).",
     "targets":targets,"stores":{}}
print("%-28s | %-22s | %-22s"%("STORE","GOOGLE (n/target avg -> h RAG)","RMS (n avg -> RAG)"))
for s in stores:
    rec={}
    if s in g_canon:
        n,avg=g_canon[s]; tgt=targets.get(s)
        vol=min(n/tgt,1.0); h=round(avg*0.5+vol*2.5,2)
        rec["g_n"]=n; rec["g_avg"]=avg; rec["g_target"]=tgt; rec["g_health"]=h; rec["g_rag"]=grag(h); rec["g_stale"]=False
        gtxt="%d/%d %.2f* -> %.2f %s"%(n,tgt,avg,h,grag(h))
    else:
        rec["g_n"]=None; rec["g_health"]=None; rec["g_rag"]="na"; rec["g_stale"]=True
        gtxt="stale feed (no Q2 data)"
    if s in rms_canon:
        n,avg=rms_canon[s]; rec["r_n"]=n; rec["r_avg"]=round(avg,2); rec["r_rag"]=rrag(avg)
        rtxt="%d %.2f -> %s"%(n,avg,rrag(avg))
    else:
        rec["r_n"]=None; rec["r_avg"]=None; rec["r_rag"]="na"; rtxt="no data"
    out["stores"][s]=rec
    print("%-28s | %-22s | %-22s"%(s+("*" if s=="Olney" else ""),gtxt,rtxt))
json.dump(out,open('storehealth.json','w'),indent=1)
print("\n* Olney target defaulted to 10 (no target provided) - CONFIRM")
