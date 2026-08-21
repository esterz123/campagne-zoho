#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chasse Exa RAPIDE parametrable pour subagents/volume.
Usage: python3 exa_bulk.py "<requetes sep. par |>" "sortie.json"
Trouve des sites FR (PME/tpe), extrait l'email depuis la page (multi-workers).
Cible: entreprises avec de l'argent + potentiel de rebranding/refonte site."""
import os, sys, json, re, urllib.request, concurrent.futures, time

BASE = os.path.dirname(os.path.abspath(__file__))
EXA = "69458868-3ce4-42da-873d-43a0465dff11"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:fr|com|net|eu|org)", re.I)
BLOCK = ("gmail.com","yahoo","outlook","hotmail","orange.fr","wanadoo","free.fr","laposte",
         "example.com","@2x","@3x",".png",".jpg","sentry","wixpress","godaddy","domain.com",
         "your-domain","@email.com","@mail.com","@test","@no","@contact.fr","-site","wordpress.com","@live",
         "@wght","fonts.","googleapis","gstatic","w3.org","googlesyndication")
TYPES = (".fr",".com",".eu",".net")

def exa_search(q, n=12):
    req = urllib.request.Request("https://api.exa.ai/search",
        data=json.dumps({"query":q,"numResults":n,"type":"auto","useAutoprompt":True}).encode(),
        headers={"Content-Type":"application/json","x-api-key":EXA}, method="POST")
    return [r.get("url","") for r in json.load(urllib.request.urlopen(req,timeout=30)).get("results",[])]

def dom(u):
    return re.sub(r"^https?://(www\.)?","",u).split("/")[0].lower()

def fetch(url,t=6):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0","Accept":"text/html"})
        return urllib.request.urlopen(req,timeout=t).read().decode("utf-8","ignore")
    except Exception: return ""

def extract(path):
    idx, url = path  # (index, url)
    time.sleep(0.2*(idx % 8))  # small stagger
    base=dom(url); root=base.split(".")[0]
    urls={url, url.rstrip("/")+"/contact/", url.rstrip("/")+"/contacts/", url.rstrip("/")+"/nous-contacter/"}
    found=[]
    for u in urls:
        h=fetch(u)
        if not h: continue
        for m in EMAIL_RE.findall(h):
            m=m.lower()
            if any(b in m for b in BLOCK): continue
            mdom=m.split("@")[-1]
            if not mdom.endswith(TYPES): continue
            # email sur domaine propre (pas generique), ou incluant le nom du site
            if root in m or base in m or (mdom in base) or (len(mdom.split('.')[0])>=4 and mdom not in ("gmail.com",)):
                if m not in found: found.append(m)
        if found: break
    return (base, found[0]) if found else (base, None)

def main():
    if len(sys.argv)<3:
        print("usage: exa_bulk.py '<q1 | q2 | q3>' 'out.json' [ngroups]"); return
    queries=[q.strip() for q in sys.argv[1].split("|") if q.strip()]
    out=os.path.join(BASE,sys.argv[2])
    ngroups=int(sys.argv[3]) if len(sys.argv)>3 else 4
    # collecte
    sites={}
    for q in queries:
        try:
            for u in exa_search(q):
                d=dom(u)
                if d and not any(b in d for b in ("google","facebook","linkedin","wiki","youtube","annuaire","pagesjaunes","societe","twitter","instagram","wix","shopify","auto-ecole","notaires","avocats","mairie","commune")) and d.endswith(TYPES):
                    sites[d]=u
        except Exception: pass
    # dedup file existante
    DATA=os.path.join(BASE,"campagne_data.json")
    if os.path.exists(DATA):
        data=json.load(open(DATA,encoding="utf-8"))
        file_emails={(e.get("to") or "").lower() for e in data}
        file_doms={ (e.get("to","").split("@")[-1].lower() if e.get("to") else "") for e in data}
    else:
        file_emails=set(); file_doms=set()
    cand=[(u,d,sites[d]) for u,d in enumerate(sorted(sites)) if d not in file_doms]
    print("sites candidats:",len(cand),file=sys.stderr)
    if not cand: return
    # split en ngroups, ne garde que notre tranche si index fourni? non: on traite tout
    found={}
    idx=sorted(sites)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs={ex.submit(extract,(u,sites[u])):u for u in idx if u not in file_doms}
        done=0
        for fut in concurrent.futures.as_completed(futs):
            u=futs[fut]
            try: base,em=fut.result()
            except Exception: em=None
            if em:
                found[base]={"domaine":base,"email":em}
                print("  +",base,"->",em,flush=True)
            done+=1
    json.dump(list(found.values()), open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("== BULK LEADS:",len(found),"->",out,file=sys.stderr)

if __name__=="__main__":
    main()
