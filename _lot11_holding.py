#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot11 : re-fetch SIREN manquants (429) + remontee holdings."""
import json, re, time, urllib.request

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

with open(BASE + r"\candidats_bruts.json", encoding="utf-8") as f:
    bruts = json.load(f)

SIRENS = [bruts[i]["siren"] for i in range(110, 150)]

def fetch_api(siren, tries=4):
    url = "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=1" % siren
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                j = json.loads(r.read().decode("utf-8"))
            for res in j.get("results", []):
                if res.get("siren") != siren:
                    continue
                siege = res.get("siege") or {}
                adr = siege.get("adresse")
                commune = adr.get("libelle_commune", "") if isinstance(adr, dict) else ""
                dirs = []
                for d in (res.get("dirigeants") or []):
                    if isinstance(d, str):
                        dirs.append({"nom": d, "prenoms": "", "qualite": "", "type": ""})
                        continue
                    dirs.append({"nom": d.get("nom") or d.get("denomination", ""),
                                 "prenoms": d.get("prenoms", ""),
                                 "qualite": d.get("qualite", ""),
                                 "type": d.get("type_dirigeant", "")})
                return siren, {"nom_complet": res.get("nom_complet") or "",
                               "categorie": res.get("categorie_entreprise", ""),
                               "tranche": res.get("tranche_effectif_salarie") or "",
                               "nature_juridique": res.get("nature_juridique", ""),
                               "dirigeants": dirs, "commune": commune}
            return siren, {"erreur": "introuvable"}
        except Exception as e:
            if "429" in str(e) and a < tries - 1:
                time.sleep(6 * (a + 1))
                continue
            return siren, {"erreur": str(e)[:100]}
    return siren, {"erreur": "429 persistant"}

out = {}
try:
    out = json.load(open(BASE + r"\_lot11_api_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

missing = [s for s in SIRENS if "erreur" in (out.get(s) or {})]
print("re-fetch:", missing, flush=True)
for s in missing:
    siren, info = fetch_api(s)
    out[siren] = info
    if "erreur" not in info:
        print(siren, "| eff:", info.get("tranche"), "|", "; ".join(
            (((dd.get("prenoms") or "") + " " + re.sub(r"\(.*?\)", "", dd.get("nom") or "")).strip() + " [" + (dd.get("type") or "")[:8] + " " + (dd.get("qualite") or "")[:20] + "]") for dd in info.get("dirigeants", [])[:3]), flush=True)
    else:
        print(siren, "| ERREUR:", info.get("erreur"), flush=True)
    json.dump(out, open(BASE + r"\_lot11_api_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(1)

# --- remontee holdings ---
HOLDINGS = ["JELZA HOLDING", "GAP SAS", "HOLDING ROUGER", "WELDING PIPELINES SERVICES",
            "AD2C MANAGEMENT", "CRISALYNE", "SOFIRME", "GROUPE EDM", "BMA"]
print("\n--- REMONTEE HOLDINGS ---")
for name in HOLDINGS:
    try:
        url = "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=5" % urllib.parse.quote(name)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            j = json.loads(r.read().decode("utf-8"))
        for res in j.get("results", []):
            n = res.get("nom_complet") or ""
            if name.lower() in n.lower():
                pers = [d for d in (res.get("dirigeants") or []) if isinstance(d, dict) and d.get("type_dirigeant") == "personne physique"]
                print(name, "|", res.get("siren"), "|", n[:50], "| tranche:", res.get("tranche_effectif_salarie"), "| dir:",
                      "; ".join((d.get("prenoms", "") + " " + re.sub(r"\(.*?\)", "", d.get("nom") or "")).strip() + " (" + (d.get("qualite") or "")[:20] + ")" for d in pers[:3]) or "AUCUNE PERSONNE PHYSIQUE", flush=True)
                break
        time.sleep(1)
    except Exception as e:
        print(name, "| ERREUR", str(e)[:80], flush=True)
print("TERMINE", flush=True)
