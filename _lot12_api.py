#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot12 : API recherche-entreprises pour SIREN 150-202 (dirigeants + tranche + chaine holding)."""
import json, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

with open(BASE + r"\candidats_bruts.json", encoding="utf-8") as f:
    bruts = json.load(f)

SIRENS = [str(bruts[i]["siren"]) for i in range(150, 203)]

def api_q(q):
    url = "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=3" % urllib.parse.quote(q)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"erreur": str(e)[:120]}

def extract_dir(d):
    if isinstance(d, str):
        return {"nom": d, "prenoms": "", "qualite": "", "type": ""}
    return {
        "nom": d.get("nom") or d.get("denomination", ""),
        "prenoms": d.get("prenoms", ""),
        "qualite": d.get("qualite", ""),
        "type": d.get("type_dirigeant", ""),
    }

def fetch_api(siren):
    j = api_q(siren)
    if "erreur" in j:
        return siren, {"erreur": j["erreur"]}
    for res in j.get("results", []):
        if res.get("siren") != siren:
            continue
        siege = res.get("siege") or {}
        adr = siege.get("adresse")
        commune = adr.get("libelle_commune", "") if isinstance(adr, dict) else ""
        dirs = [extract_dir(d) for d in (res.get("dirigeants") or [])]
        info = {
            "nom_complet": res.get("nom_complet") or res.get("nom_raison_sociale", ""),
            "categorie": res.get("categorie_entreprise", ""),
            "tranche": res.get("tranche_effectif_salarie") or "",
            "nature_juridique": res.get("nature_juridique", ""),
            "dirigeants": dirs,
            "commune": commune,
        }
        # chaine holding : si dirigeant personne morale, remonter (max 3 niveaux)
        chain = []
        cur = dirs
        for level in range(3):
            pm = [d for d in cur if d.get("type") == "personne morale" and d.get("nom")]
            if not pm:
                break
            denom = pm[0]["nom"]
            chain.append(denom)
            j2 = api_q(denom)
            found = None
            for res2 in j2.get("results", []):
                if res2.get("nom_complet", "").lower().replace(" ", "") == denom.lower().replace(" ", ""):
                    found = res2
                    break
            if found is None and j2.get("results"):
                found = j2["results"][0]
            if not found:
                break
            cur = [extract_dir(d) for d in (found.get("dirigeants") or [])]
        info["chaine_holding"] = chain
        info["dirigeants_resolus"] = cur if chain else dirs
        return siren, info
    return siren, {"erreur": "siren introuvable"}

import urllib.parse
out = {}
try:
    out = json.load(open(BASE + r"\_lot12_api_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

todo = [s for s in SIRENS if s not in out]
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(fetch_api, s): s for s in todo}
    for f in as_completed(futs):
        siren, info = f.result()
        out[siren] = info
        t = info.get("tranche", "?")
        d = info.get("dirigeants_resolus", info.get("dirigeants", []))
        print(siren, "| eff:", t, "| hold:", ";".join(info.get("chaine_holding", [])), "| dir:", "; ".join(
            (((dd.get("prenoms") or "") + " " + re.sub(r"\(.*?\)", "", dd.get("nom") or "")).strip() + " (" + (dd.get("qualite") or "")[:20] + "/" + (dd.get("type") or "")[:10] + ")") for dd in d[:3]), flush=True)
        json.dump(out, open(BASE + r"\_lot12_api_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.15)
print("TERMINE API", len(out))
