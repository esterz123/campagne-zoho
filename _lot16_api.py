#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 16 : interroge recherche-entreprises.api.gouv.fr pour chaque SIREN de la 2e moitie."""
import json, time, urllib.request, urllib.parse, sys

BASE = r"C:/Users/ulamb/Bureau/prospection/github-campagne"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

src = json.load(open(BASE + "/_lot16_source_tmp.json", encoding="utf-8"))
out = {}
for i, e in enumerate(src):
    siren = e["siren"]
    url = "https://recherche-entreprises.api.gouv.fr/search?q=" + siren + "&per_page=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        res = data.get("results", [])
        if res:
            r0 = res[0]
            out[siren] = {
                "nom": r0.get("nom_complet"),
                "siren": r0.get("siren"),
                "tranche_effectif_salarie": r0.get("tranche_effectif_salarie"),
                "effectif_min": r0.get("effectif_min"),
                "effectif_max": r0.get("effectif_max"),
                "dirigeants": [{"nom": d.get("nom"), "qualite": d.get("qualite")} for d in r0.get("dirigeants", [])],
                "site_officiel": r0.get("site_officiel"),
                "activite": r0.get("activite_principale"),
                "libelle_activite": r0.get("libelle_activite_principale"),
            }
        else:
            out[siren] = {"nom": e["nom"], "siren": siren, "vide": True}
    except Exception as ex:
        out[siren] = {"nom": e["nom"], "siren": siren, "erreur": str(ex)}
    print(i, siren, out[siren].get("nom", "?"), out[siren].get("tranche_effectif_salarie"), flush=True)
    time.sleep(0.6)

json.dump(out, open(BASE + "/_lot16_dirigeants_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK", len(out))
