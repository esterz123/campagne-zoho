#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot11 : API recherche-entreprises pour les 40 SIREN (dirigeants + tranche effectif + siege)."""
import json, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

with open(BASE + r"\candidats_bruts.json", encoding="utf-8") as f:
    bruts = json.load(f)

SIRENS = [bruts[i]["siren"] for i in range(110, 150)]

def fetch_api(siren):
    url = "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=1" % siren
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            j = json.loads(r.read().decode("utf-8"))
        for res in j.get("results", []):
            if res.get("siren") != siren:
                continue
            siege = res.get("siege") or {}
            tranche = res.get("tranche_effectif_salarie") or ""
            adr = siege.get("adresse")
            commune = adr.get("libelle_commune", "") if isinstance(adr, dict) else ""
            dirs = []
            for d in (res.get("dirigeants") or []):
                if isinstance(d, str):
                    dirs.append({"nom": d, "prenoms": "", "qualite": "", "type": ""})
                    continue
                dirs.append({
                    "nom": d.get("nom") or d.get("denomination", ""),
                    "prenoms": d.get("prenoms", ""),
                    "qualite": d.get("qualite", ""),
                    "type": d.get("type_dirigeant", ""),
                })
            return siren, {
                "nom_complet": res.get("nom_complet") or res.get("nom_raison_sociale", ""),
                "categorie": res.get("categorie_entreprise", ""),
                "tranche": tranche,
                "nature_juridique": res.get("nature_juridique", ""),
                "dirigeants": dirs,
                "commune": commune,
            }
        return siren, {"erreur": "siren introuvable"}
    except Exception as e:
        return siren, {"erreur": str(e)[:120]}

out = {}
try:
    out = json.load(open(BASE + r"\_lot11_api_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

todo = [s for s in SIRENS if s not in out]
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(fetch_api, s): s for s in todo}
    for f in as_completed(futs):
        siren, info = f.result()
        out[siren] = info
        t = info.get("tranche", "?")
        d = info.get("dirigeants", [])
        print(siren, "| eff:", t, "| dir:", "; ".join(
            (((dd.get("prenoms") or "") + " " + re.sub(r"\(.*?\)", "", dd.get("nom") or "")).strip() + " (" + (dd.get("qualite") or "")[:22] + ")") for dd in d[:3]), flush=True)
        json.dump(out, open(BASE + r"\_lot11_api_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.15)
print("TERMINE API", len(out))
