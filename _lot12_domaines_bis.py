#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot12 bis : sonde les domaines probables des candidats 150-202 non encore explores."""
import json, re, time, urllib.request, urllib.error

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

DOMAINES = {
    154: ["cta-chaudronnerie.fr", "chaudronnerie-argonne.fr", "cta-tolerie.fr", "cta51.fr", "cta-tolerie.com"],
    155: ["ctp94.fr", "carrosserie-tolerie-peinture94.fr", "ctp-94.fr"],
    159: ["tolerie-armoricaine.fr", "latoleriearmoricaine.fr"],
    165: ["tolerie-des-pyrenees.fr", "toleriedespyrenees.fr", "tolerie-pyrenees.fr"],
    166: ["mecanique-camblinoise.fr", "mg-camblinoise.fr", "camblinoise.fr"],
    168: ["durance-mecanique.fr", "dmg-meyrargues.fr", "durancemecanique.fr"],
    170: ["fonteneau-mecanique.fr", "fonteneau.fr", "fonteneaumecanique.fr"],
    172: ["gma-poligny.fr", "generale-mecanique-appliquee.fr", "mecanique-appliquee.fr"],
    173: ["gaborit-mecanique.fr", "mecanique-gaborit.fr", "smg-gaborit.fr"],
    174: ["leon-olivier.fr", "leonolivier.fr", "leon-olivier-mecanique.fr"],
    177: ["erde-mecanique.fr", "societe-erde.fr"],
    178: ["agme.fr", "agme-domont.fr", "application-mecanique-electrique.fr"],
    179: ["gmga.fr", "gmga-montmorillon.fr"],
    180: ["mgi-bayeux.fr", "mgi-mecanique.fr", "societe-mgi.fr"],
    181: ["mgo-varanges.fr", "mecanique-outillage.fr"],
    183: ["mecanique-langroise.fr", "mg-langroise.fr"],
    185: ["seba-expert.fr", "fonderie-roquevaire.fr", "sebaexpert.fr"],
    194: ["sable-injection.fr", "sableinjection.fr"],
    195: ["amiens-injection.fr", "amiensinjection.fr"],
    196: ["demo-injection.fr", "demoinjection.fr", "demo-injection.com"],
    197: ["ipv-injection.fr", "ipvinjection.fr", "ipv-injection.com"],
    201: ["creutzwald-injection.fr", "creutzwaldinjection.fr"],
}

def probe(domain):
    for scheme in ("https", "http"):
        for host in (domain, "www." + domain):
            url = "%s://%s/" % (scheme, host)
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=6) as r:
                    body = r.read(200000).decode("utf-8", "ignore")
                    return {"url": url, "status": r.status, "final": r.geturl(), "html": body}
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303, 307, 308):
                    loc = e.headers.get("Location", "")
                    if loc and loc.startswith("http"):
                        try:
                            req2 = urllib.request.Request(loc, headers=UA)
                            with urllib.request.urlopen(req2, timeout=6) as r2:
                                body = r2.read(200000).decode("utf-8", "ignore")
                                return {"url": url, "status": r2.status, "final": loc, "html": body}
                        except Exception:
                            pass
                continue
            except Exception:
                continue
    return None

out = {}
for idx, doms in DOMAINES.items():
    found = None
    for d in doms:
        p = probe(d)
        if p:
            found = {"domaine": d, **p}
            break
    if found:
        html = found["html"].lower()
        t = re.search(r"<title[^>]*>(.*?)</title>", found["html"], re.S | re.I)
        found["titre"] = t.group(1).strip()[:90] if t else ""
        found["copyright"] = re.findall(r"(?:copyright|©|&copy;)\s*[^\n<]{0,60}", found["html"], re.I)[:2]
        found["generator"] = re.findall(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', found["html"], re.I)[:2]
        found["tables"] = html.count("<table")
        found["wp"] = "wp-content" in html or "wordpress" in html
        found["emails"] = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", found["html"])))[:8]
        out[str(idx)] = found
        print(idx, "->", found["domaine"], "|", found["status"], "|", found["titre"][:50],
              "| cop:", found["copyright"], "| tables:", found["tables"], "| wp:", found["wp"],
              "| emails:", found["emails"], flush=True)
    else:
        print(idx, "-> AUCUN DOMAINE TROUVE", flush=True)
    time.sleep(0.25)

json.dump(out, open(BASE + r"\_lot12_domaines_bis_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK")
