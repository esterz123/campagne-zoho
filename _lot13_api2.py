#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : reprise API dirigeants pour les index en erreur (429)."""
import json, urllib.request, urllib.parse, time

BASE = "C:/Users/ulamb/Bureau/prospection/github-campagne"

with open(f"{BASE}/_lot13_api_tmp.json", encoding="utf-8") as f:
    results = json.load(f)

with open(f"{BASE}/candidats_bruts.json", encoding="utf-8") as f:
    data = json.load(f)

def fetch(idx, siren, nom):
    q = urllib.parse.quote(siren)
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={q}&per_page=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        j = json.loads(r.read().decode("utf-8"))
    if not j.get("results"):
        return {"index": idx, "nom": nom, "siren": siren, "error": "no result"}
    res = j["results"][0]
    return {
        "index": idx, "nom": nom, "siren": siren,
        "denomination": res.get("nom_complet") or res.get("nom_raison_sociale"),
        "sigle": res.get("sigle"),
        "tranche_effectif_salarie": res.get("tranche_effectif_salarie"),
        "tranche_effectif_salarie_unite_legale": res.get("tranche_effectif_salarie_unite_legale"),
        "dirigeants": res.get("dirigeants", []),
        "siege": (res.get("siege") or {}).get("adresse"),
        "activite": res.get("activite_principale"),
        "etat": res.get("etat_administratif"),
    }

todo = []
for idx, r in results.items():
    if r.get("error") or not r.get("dirigeants"):
        todo.append((int(idx), r["siren"], r["nom"]))

print(f"{len(todo)} a relancer")
for idx, siren, nom in todo:
    for attempt in range(3):
        try:
            r = fetch(idx, siren, nom)
            results[str(idx)] = r
            dr = r.get("dirigeants") or []
            eff = r.get("tranche_effectif_salarie") or r.get("tranche_effectif_salarie_unite_legale") or "?"
            dstr = "; ".join(f"{d.get('prenoms','')} {d.get('nom','')} [{d.get('qualite','')} / {d.get('type_dirigeant','')}]" + (f" HOLDING:{d.get('denomination','')}" if d.get('type_dirigeant')=='personne morale' else "") for d in dr[:4])
            print(f"[{idx}] {nom} | eff={eff} | {dstr}")
            break
        except Exception as e:
            if attempt == 2:
                print(f"[{idx}] {nom} | ERR {str(e)[:100]}")
            time.sleep(2 + attempt * 2)
    time.sleep(1.2)

with open(f"{BASE}/_lot13_api_tmp.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print("saved")
