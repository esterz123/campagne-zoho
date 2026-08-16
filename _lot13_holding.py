#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : remontee holdings + verification mentions legales restantes."""
import json, re, urllib.request, urllib.parse, time

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

def api(q):
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={urllib.parse.quote(q)}&per_page=2"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode("utf-8"))

def get(url, mb=250000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.read(mb).decode("utf-8", "ignore")

print("=== HOLDINGS ===")
holdings = {
 132: "HARMONIA",
 144: "AD2C MANAGEMENT",
 123: "GAP SAS",
 112: "GROUPE EDM",
 114: "JELZA HOLDING",
 113: "HOLDING ROUGER",
 120: "TALBOT INDUSTRIE DEVELOPPEMENT",
 140: "ROGER HOLDING",
 141: "WELDING PIPELINES SERVICES",
 142: "SILENN",
 147: "MANO FINANCE",
 115: "KDMJ",
 110: "SOFIRME",
 149: "GR HOLDING",
}
hres = {}
for idx, h in holdings.items():
    try:
        j = api(h)
        for res in j.get("results", [])[:2]:
            nom = res.get("nom_complet") or res.get("nom_raison_sociale") or ""
            siren = res.get("siren")
            eff = res.get("tranche_effectif_salarie")
            drs = []
            for d in res.get("dirigeants", []):
                if d.get("type_dirigeant") == "personne physique":
                    drs.append(f"{d.get('prenoms','')} {d.get('nom','')} [{d.get('qualite','')}]")
            print(f"[{idx}] holding={h} -> {nom} siren={siren} eff={eff} dirigeants={drs}")
            hres[idx] = {"holding": h, "resolved": nom, "siren": siren, "eff": eff, "dirigeants": drs}
            break
    except Exception as e:
        print(f"[{idx}] holding={h} ERR {str(e)[:120]}")
    time.sleep(1.2)

with open(f"{BASE}/_lot13_holding_tmp.json", "w", encoding="utf-8") as f:
    json.dump(hres, f, ensure_ascii=False, indent=1)

print("\n=== MENTIONS LEGALES / PAGES CONTACT ===")
checks = {
 125: ("https://samd-aero.fr/", "401884382"),
 131: ("https://groupe-gb.fr/mentions-legales/", "397020033"),
 133: ("https://metallerie.com/mentions-legales/", "817734593"),
 135: ("https://www.gatsbysoudure.com/contactez-nous/", "813390432"),
 118: ("https://www.smg-decoupage-tolerie.com/mentions-legales/", "484871272"),
 130: ("https://lg-metallerie.fr/", "803868660"),
 128: ("https://batisud.org/", "501007652"),
 111: ("https://sdeb.fr/mentions-legales", "976720284"),
 123: ("https://sare-sarl-69.fr/", "351174081"),
 127: ("https://www.oaca.fr/mentions-legales/", "443830898"),
 129: ("https://sudmetallerie.com/mentions-legales-sud-metallerie/", "310826698"),
 137: ("https://www.soudecoup.fr/mentions-legales/", "055802995"),
}
mres = {}
for idx, (url, siren) in checks.items():
    try:
        html = get(url)
        low = html.lower()
        emails = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)))
        emails = [e for e in emails if not any(x in e.lower() for x in [".png",".jpg",".jpeg",".gif",".webp",".svg","@2x","sentry"])]
        siren_ok = siren in re.sub(r"\s", "", html)
        cps = re.findall(r"©\s*(\d{4})(?:\s*[-–—]\s*(\d{4}))?", html)[:4]
        title = re.findall(r"<title[^>]*>(.*?)</title>", html, re.I|re.S)[:1]
        print(f"[{idx}] {url} siren_ok={siren_ok} emails={emails[:6]} cp={cps} title={title}")
        mres[idx] = {"url": url, "siren_ok": siren_ok, "emails": emails[:8], "copyright": cps, "title": title}
    except Exception as e:
        print(f"[{idx}] {url} ERR {str(e)[:100]}")
        mres[idx] = {"url": url, "err": str(e)[:120]}
    time.sleep(0.8)

with open(f"{BASE}/_lot13_mentions_tmp.json", "w", encoding="utf-8") as f:
    json.dump(mres, f, ensure_ascii=False, indent=1)
print("\ndone")
