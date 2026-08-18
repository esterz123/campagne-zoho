#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chasse SEARXNG locale parametree (volume, parallelisable par subagents).

Pools :
  --pool industrial : candidats_bruts.json (PME industrielles 22/24/25/28/29, hors instituts)
  --pool cabinets   : candidats_cabinets.json (expertise comptable)
  --pool agences    : candidats_agences.json (agences web)
Sortie : --out <fichier> (unique par subagent, evite les collisions).

Methode (validation 12-18/08) : site via SearXNG local (port detecte), vetuste (score>=2),
email PUBLIC sur domaine strict, dirigeant via API de l'Etat. Anti rate-limit : 1 worker,
delay 4 s, engines google>bing>ddg, une requete/candidat. ECRIT le fichier meme si partiel.
Usage : python3 chasse_searxng.py --pool industrial --start 0 --n 40 --out _lot_A.json
"""
import json, os, re, sys, time, subprocess, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import chasseur_prospects as C

SEARX = "http://127.0.0.1:14916/search"
POOL_FILES = {"industrial":"candidats_bruts.json","cabinets":"candidats_cabinets.json",
              "agences":"candidats_agences.json"}
BAD = ("wikipedia","linkedin","facebook","instagram","twitter","youtube","pappers","societe.com",
       "pagesjaunes","annuaire","data.gouv","google","mappy","118712","lefigaro","cadastre","letudiant",
       "polyvia","europages","kompass","infogreffe","verif.com","france-cadastre","monbeauvillage","mairie",
       "gowork","indeed","brignais.infoisinfo","franceenvironnement","annuaire-mairie","jobs-stages","x.com")

def searches(q):
    for engine in ("google","bing","duckduckgo"):
        url = SEARX + "?" + urllib.parse.urlencode({"q": q, "format": "json", "engines": engine})
        try:
            body = subprocess.run(["curl","-s","--max-time","12","-H","Accept: application/json",url],
                                  capture_output=True, text=True, timeout=16).stdout
            d = json.loads(body)
            res = d.get("results") or []
            if res:
                return [urllib.parse.urlsplit(r.get("url","")).netloc.replace("www.","").lower()
                        for r in res if r.get("url")]
        except Exception:
            continue
    return []

TLD_OK = (".fr", ".com", ".eu", ".net", ".info")
ACTIV = ("plasturgie","usinage","mecanique","fonderie","tolerie","decolletage","injection",
         "outillage","decoupage","chaudronnerie","moules","plastiques","plastique","precision",
         "expertise","comptable","communication","digital","web","design","agence","studio","marketing")

def valide_identite(nom, dom):
    """Gardefou d'identite (18/08) : rejette les faux sites trouves par le moteur.
    1) TLD non francais/europeen commercial (.ma/.tn/.org/.solutions...) => rejet.
    2) Aucun token du nom nettoye ni de l'activite dans le domaine => homonyme probable => rejet."""
    if not dom:
        return False
    dl = dom.lower()
    if not any(dl.endswith(t) for t in TLD_OK):
        return False
    base = re.sub(r"^(sarl|sa|sas|eurl|eu|ets\.?|les|la|le|groupe|societe|agence)\s+", "", nom.lower(), flags=re.I)
    toks = [t for t in re.split(r"[^a-z0-9]+", base) if len(t) > 2]
    root = dl.split(".")[0]
    if any(t in root or root in t for t in toks):
        return True
    if any(a in dl for a in ACTIV):
        return True
    # acronyme : Application Developpement Plasturgie 85 -> adp(85).com
    if len(toks) >= 2:
        acr = "".join(t[0] for t in toks if t[0].isalnum())
        if len(acr) >= 2 and (root.startswith(acr) or acr in root):
            return True
    return False

def find_site(nom, ville):
    for dom in searches('"%s" %s' % (nom, ville)):
        if dom and not any(b in dom for b in BAD) and "." in dom:
            if valide_identite(nom, dom):
                return dom
    base = re.sub(r"^(sarl|sa|sas|eurl|eu|ets\.?|les|la|le|groupe)\s+", "", nom.lower(), flags=re.I)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    if base:
        for tld in (".fr", ".com", ".eu"):
            if C.fetch("https://www." + base + tld):
                return base + tld
    return ""

def api_dirigeant(siren):
    try:
        d = json.load(urllib.request.urlopen(
            "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=1" % siren, timeout=15))
        ent = d.get("results",[{}])[0]
        for dd in (ent.get("dirigeants") or []):
            q2 = (dd.get("qualite") or "").upper()
            if q2 in ("PRESIDENT DE SAS","PRESIDENT","GERANT","DIRECTEUR GENERAL","ASSOCIE GERANT","GERANT ASSOCIE"):
                pren=(dd.get("prenoms") or "").strip(); nom=(dd.get("nom") or "").strip()
                if pren and nom:
                    return pren.split()[0].capitalize() + " " + nom.upper()
    except Exception:
        pass
    return ""

def main():
    pool = "industrial"
    if "--pool" in sys.argv: pool = sys.argv[sys.argv.index("--pool")+1]
    n = 40; start = 0
    if "--n" in sys.argv: n = int(sys.argv[sys.argv.index("--n")+1])
    if "--start" in sys.argv: start = int(sys.argv[sys.argv.index("--start")+1])
    out = os.path.join(BASE, "_chasse_%s.json" % pool)
    if "--out" in sys.argv: out = os.path.join(BASE, sys.argv[sys.argv.index("--out")+1])

    raw = json.load(open(os.path.join(BASE, POOL_FILES[pool]), encoding="utf-8"))
    pool_list=[]
    seen=set()
    for c in raw:
        s=c.get("siren",""); nom=(c.get("nom") or "").upper()
        if s in seen: continue
        seen.add(s)
        if pool=="industrial" and not (c.get("naf") or "").startswith(("22","24","25","28","29")): continue
        if pool=="industrial" and any(x in nom for x in ("INSTITUT","CENTRE TECHNIQUE","SYNDICAT","ASSOCIATION","UNION","HOLDING","GROUPE")): continue
        pool_list.append(c)

    data = json.load(open(os.path.join(BASE,"campagne_data.json"),encoding="utf-8"))
    part = json.load(open(os.path.join(BASE,"campagne_partenaires.json"),encoding="utf-8"))
    exdom=set()
    for e in list(data)+list(part):
        for f in ("to","cc"):
            m=re.search(r"@([A-Za-z0-9._-]+)", e.get(f) or "")
            if m: exdom.add(m.group(1).lower())

    chunk = pool_list[start:start+n]
    quals=[]
    for i,c in enumerate(chunk):
        nom=c.get("nom",""); ville=c.get("ville",""); siren=str(c.get("siren",""))
        try:
            site = find_site(nom, ville)
            if not site:
                print("  SKIP no-site | %s" % nom[:30]); time.sleep(4); continue
            html = C.fetch("https://www."+site) or C.fetch("http://"+site) or C.fetch("https://"+site)
            if not html:
                print("  SKIP no-html | %s (%s)" % (nom[:26],site)); time.sleep(4); continue
            constats, score = C.analyze(html)
            if score < 2:
                print("  SKIP site sain score=%d | %s" % (score, nom[:24])); time.sleep(4); continue
            emails=[e for e in C.find_email(site) if e.split("@")[-1]==site or e.split("@")[-1].endswith("."+site)]
            if not emails:
                print("  SKIP no-email | %s (%s)" % (nom[:24],site)); time.sleep(4); continue
            if site in exdom:
                print("  SKIP deja | %s" % nom[:24]); time.sleep(4); continue
            dirg = api_dirigeant(siren)
            rec={"pool":pool,"nom":nom,"ville":ville,"site":site,"email":emails[0],
                 "dirigeant":dirg or "A CONFIRMER","score":score,"constats":constats,
                 "siren":siren,"naf":c.get("naf")}
            quals.append(rec)
            print("  QUALIFIE | %-28s %s %s" % (nom[:28], emails[0], dirg or ""))
        except Exception as e:
            print("  ERR %s : %s" % (nom[:22], str(e)[:36]))
        time.sleep(4)

    existing=[]
    if os.path.exists(out):
        try: existing=json.load(open(out,encoding="utf-8"))
        except Exception: existing=[]
    done={r["email"] for r in existing}
    existing += [r for r in quals if r["email"] not in done]
    json.dump(existing, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== POOL %s: %d qualifies ce run | total %d | fichier %s ===" % (pool, len(quals), len(existing), out))

if __name__=="__main__":
    main()
