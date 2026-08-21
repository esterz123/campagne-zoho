#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UN SEUL run Apify contact-info-scraper avec toutes les URLs candidats (robuste rate-limit)."""
import os, sys, json, time, subprocess, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("APIFY_TOKEN","apify_api_2znUUXJQKjxgbdfZTOmw2lsfMCvoM54eENBM")
ACTOR = "vdrmota~contact-info-scraper"
OUT = os.path.join(BASE,"_apify_contact_leads.json")

def main():
    sites = json.load(open(os.path.join(BASE,"_candidats_domains.json"),encoding="utf-8"))
    data = json.load(open(os.path.join(BASE,"campagne_data.json"),encoding="utf-8"))
    file_doms = {(e.get("to","").split("@")[-1].lower() if e.get("to") else "") for e in data}
    urls=[]
    for d,u in sites.items():
        if d not in file_doms:
            urls.append("https://"+d)
    print("URLs a traiter:",len(urls),file=sys.stderr)
    if not urls: return

    inp={"startUrls":[{"url":u} for u in urls],"maxDepth":0}
    r=subprocess.run(["curl","-s","--max-time","60","-X","POST",
        f"https://api.apify.com/v2/acts/{ACTOR}/runs?token={TOKEN}",
        "-H","Content-Type: application/json","-d",json.dumps(inp)],capture_output=True,text=True,timeout=70)
    try:
        rid=json.loads(r.stdout)["data"]["id"]
    except Exception as e:
        print("START ERR:",r.stdout[:300],file=sys.stderr); return
    print("RUN:",rid,file=sys.stderr)

    st=None
    for _ in range(90):
        time.sleep(8)
        s=subprocess.run(["curl","-s","--max-time","20",f"https://api.apify.com/v2/actor-runs/{rid}?token={TOKEN}"],capture_output=True,text=True,timeout=30)
        try: st=json.loads(s.stdout)["data"]["status"]
        except: continue
        if st in ("SUCCEEDED","FAILED","TIMED-OUT","ABORTED"): break
    print("status:",st,file=sys.stderr)
    if st!="SUCCEEDED":
        print("RUN non reussi",file=sys.stderr); return

    s=subprocess.run(["curl","-s","--max-time","20",f"https://api.apify.com/v2/actor-runs/{rid}?token={TOKEN}"],capture_output=True,text=True,timeout=30)
    ds=json.loads(s.stdout)["data"]["defaultDatasetId"]
    g=subprocess.run(["curl","-s","--max-time","60",f"https://api.apify.com/v2/datasets/{ds}/items?token={TOKEN}&clean=true"],capture_output=True,text=True,timeout=70)
    items=json.loads(g.stdout)
    results=[]
    for it in items:
        u=it.get("url") or ""; em=(it.get("emails") or ["",""])[0]
        dom=u.replace("https://","").replace("http://","").split("/")[0].lower()
        if em and "@" in em:
            results.append({"domaine":dom,"email":em.lower()})
            print("  +",dom,"->",em,flush=True)
    json.dump(results,open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("== APIFY CONTACT LEADS:",len(results),file=sys.stderr)

if __name__=="__main__":
    main()
