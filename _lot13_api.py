#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : API dirigeants + effectifs pour les index 110-149 de candidats_bruts.json."""
import json, urllib.request, urllib.parse, time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "C:/Users/ulamb/Bureau/prospection/github-campagne"

with open(f"{BASE}/candidats_bruts.json", encoding="utf-8") as f:
    data = json.load(f)

cibles = [(110 + i, c) for i, c in enumerate(data[110:150])]

def fetch(idx, c):
    q = urllib.parse.quote(c["siren"])
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={q}&per_page=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            j = json.loads(r.read().decode("utf-8"))
        if not j.get("results"):
            return {"index": idx, "nom": c["nom"], "siren": c["siren"], "error": "no result"}
        res = j["results"][0]
        return {
            "index": idx,
            "nom": c["nom"],
            "siren": c["siren"],
            "denomination": res.get("nom_complet") or res.get("nom_raison_sociale"),
            "sigle": res.get("sigle"),
            "tranche_effectif_salarie": res.get("tranche_effectif_salarie"),
            "tranche_effectif_salarie_unite_legale": res.get("tranche_effectif_salarie_unite_legale"),
            "dirigeants": res.get("dirigeants", []),
            "siege": (res.get("siege") or {}).get("adresse"),
            "activite": res.get("activite_principale"),
            "etat": res.get("etat_administratif"),
        }
    except Exception as e:
        return {"index": idx, "nom": c["nom"], "siren": c["siren"], "error": str(e)[:200]}

results = {}
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch, idx, c): idx for idx, c in cibles}
    for f in as_completed(futs):
        r = f.result()
        results[r["index"]] = r

with open(f"{BASE}/_lot13_api_tmp.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

for idx in sorted(results):
    r = results[idx]
    eff = r.get("tranche_effectif_salarie") or r.get("tranche_effectif_salarie_unite_legale") or "?"
    dr = r.get("dirigeants") or []
    dstr = "; ".join(f"{d.get('prenoms','')} {d.get('nom','')} [{d.get('qualite','')} / {d.get('type_dirigeant','')}]" + (f" HOLDING:{d.get('denomination','')}" if d.get('type_dirigeant')=='personne morale' else "") for d in dr[:3])
    print(f"[{idx}] {r.get('nom','')} | eff={eff} | {dstr} | err={r.get('error','')}")
