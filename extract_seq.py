#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extraction emails SEQUENTIELLE robuste sur _candidats_domains.json.
1 site a la fois + delai + retries (pas de parallilisme massif qui throttle).
Sauvegarde incrementale -> _exa_bulk_leads.json
Usage: python3 extract_seq.py [offset] [step]"""
import os, sys, json, re, urllib.request, time, random

BASE = os.path.dirname(os.path.abspath(__file__))
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:fr|com|net|eu)", re.I)
BLOCK = ("gmail.com","yahoo","outlook","hotmail","orange.fr","wanadoo","free.fr","laposte",
         "example.com","@2x","@3x",".png",".jpg","sentry","wixpress","godaddy","domain.com",
         "your-domain","@email.com","@mail.com","@test","@no","@contact.fr","-site","wordpress.com","@live",
         "@wght","fonts.","googleapis","gstatic","w3.org","googlesyndication","@schema")
TYPES = (".fr",".com",".eu",".net")
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0","Accept":"text/html"}

def fetch(url,t=7):
    try:
        req=urllib.request.Request(url,headers=UA)
        return urllib.request.urlopen(req,timeout=t).read().decode("utf-8","ignore")
    except Exception: return ""

def get_email(url):
    base=url.replace("https://","").replace("http://","").split("/")[0].lower()
    root=base.split(".")[0]
    pages=[url, url.rstrip("/")+"/contact/", url.rstrip("/")+"/contact", url.rstrip("/")+"/contacts/",
           url.rstrip("/")+"/nous-contacter/", url.rstrip("/")+"/#contact"]
    seen=[]
    for p in pages:
        for attempt in range(3):
            h=fetch(p)
            if h: break
            time.sleep(1.0+attempt)
        if not h: continue
        for m in EMAIL_RE.findall(h):
            m=m.lower()
            if any(b in m for b in BLOCK): continue
            mdom=m.split("@")[-1]
            if not mdom.endswith(TYPES): continue
            if root in m or base in m or mdom in base:
                if m not in seen: seen.append(m)
        if seen: break
        time.sleep(0.4)
    return seen[0] if seen else None

def main():
    off=int(sys.argv[1]) if len(sys.argv)>1 else 0
    step=int(sys.argv[2]) if len(sys.argv)>2 else 999
    sites=json.load(open(os.path.join(BASE,"_candidats_domains.json"),encoding="utf-8"))
    doms=sorted(sites)
    doms=doms[off:off+step]
    # dedup file existante
    DATA=os.path.join(BASE,"campagne_data.json")
    data=json.load(open(DATA,encoding="utf-8"))
    file_emails={(e.get("to") or "").lower() for e in data}
    file_doms={(e.get("to","").split("@")[-1].lower() if e.get("to") else "") for e in data}
    outpath=os.path.join(BASE,"_exa_bulk_leads.json")
    results=json.load(open(outpath,encoding="utf-8")) if os.path.exists(outpath) else []
    known={r["domaine"] for r in results}
    print("a traiter [%d:%d] sur %d candidats"%(off,off+step,len(doms)),file=sys.stderr)
    for i,d in enumerate(doms):
        if d in known or d in file_doms: continue
        em=get_email(sites[d])
        if em and em not in file_emails:
            results.append({"domaine":d,"email":em})
            file_emails.add(em)
            json.dump(results, open(outpath,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
            print("  +",d,"->",em,flush=True)
        else:
            # 28/08 : marquer les domaines SANS email (ou doublon) pour ne JAMAIS les re-scanner
            results.append({"domaine":d,"email":"","scan":"2026-08-28"})
            known.add(d)
            print("  -",d,"(sans email, marque scanne)",flush=True)
        time.sleep(0.4+random.random()*0.5)
        if (i+1)%15==0:
            json.dump(results, open(outpath,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
            print("  ...%d/%d, %d leads jusqu'ici"%(i+1,len(doms),len(results)),flush=True)
    json.dump(results, open(outpath,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("== TOTAL SEQUENTIEL LEADS:",len(results),file=sys.stderr)

if __name__=="__main__":
    main()
