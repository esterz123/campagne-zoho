#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot12 : retry API rate-limited SIRENs (sequential, sleeps) + resolution chaines holding."""
import json, re, time, urllib.request, urllib.parse

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

def api_q(q):
    url = "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=3" % urllib.parse.quote(q)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if "429" in str(e) or "timeout" in str(e).lower():
                time.sleep(2.5 * (attempt + 1))
                continue
            return {"erreur": str(e)[:120]}
    return {"erreur": "429 persistent"}

def extract_dir(d):
    if isinstance(d, str):
        return {"nom": d, "prenoms": "", "qualite": "", "type": ""}
    return {"nom": d.get("nom") or d.get("denomination", ""), "prenoms": d.get("prenoms", ""),
            "qualite": d.get("qualite", ""), "type": d.get("type_dirigeant", "")}

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
        info = {"nom_complet": res.get("nom_complet") or res.get("nom_raison_sociale", ""),
                "categorie": res.get("categorie_entreprise", ""),
                "tranche": res.get("tranche_effectif_salarie") or "",
                "nature_juridique": res.get("nature_juridique", ""),
                "dirigeants": dirs, "commune": commune}
        # chaine holding
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
                    found = res2; break
            if found is None and j2.get("results"):
                found = j2["results"][0]
            if not found:
                break
            cur = [extract_dir(d) for d in (found.get("dirigeants") or [])]
        info["chaine_holding"] = chain
        info["dirigeants_resolus"] = cur if chain else dirs
        return siren, info
    return siren, {"erreur": "siren introuvable"}

out = json.load(open(BASE + r"\_lot12_api_tmp.json", encoding="utf-8"))
with open(BASE + r"\candidats_bruts.json", encoding="utf-8") as f:
    bruts = json.load(f)
SIRENS = [str(bruts[i]["siren"]) for i in range(150, 203)]

# 1) retry les SIREN en erreur ou sans dirigeant
todo = [s for s in SIRENS if "erreur" in out.get(s, {}) or not out.get(s, {}).get("dirigeants_resolus")]
print("RETRY:", len(todo), "SIRENs")
for k, s in enumerate(todo):
    _, info = fetch_api(s)
    out[s] = info
    json.dump(out, open(BASE + r"\_lot12_api_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    d = info.get("dirigeants_resolu" if False else "dirigeants_resolus", info.get("dirigeants", []))
    print(k, s, "| eff:", info.get("tranche", "?"), "| hold:", ";".join(info.get("chaine_holding", [])), "| dir:", "; ".join(
        (((x.get("prenoms") or "") + " " + re.sub(r"\(.*?\)", "", x.get("nom") or "")).strip() + " [" + (x.get("qualite") or "")[:20] + "/" + (x.get("type") or "")[:8] + "]") for x in d[:3]), flush=True)
    time.sleep(1.2)

# 2) resolution holding pour les personnes morales restantes (deep)
print("\nDEEP HOLDING pour PM restants:")
for s in SIRENS:
    info = out.get(s, {})
    d = info.get("dirigeants_resolus", [])
    pm = [x for x in d if x.get("type") == "personne morale" and x.get("nom")]
    if not pm:
        continue
    chain = list(info.get("chaine_holding", []))
    cur = d
    for level in range(3):
        pm = [x for x in cur if x.get("type") == "personne morale" and x.get("nom")]
        if not pm:
            break
        denom = pm[0]["nom"]
        if denom in chain:
            break
        chain.append(denom)
        j2 = api_q(denom)
        found = None
        for res2 in j2.get("results", []):
            if res2.get("nom_complet", "").lower().replace(" ", "") == denom.lower().replace(" ", ""):
                found = res2; break
        if found is None and j2.get("results"):
            found = j2["results"][0]
        if not found:
            break
        cur = [extract_dir(x) for x in (found.get("dirigeants") or [])]
        time.sleep(1.0)
    info["chaine_holding"] = chain
    info["dirigeants_resolus"] = cur
    out[s] = info
    print(s, "| hold:", ";".join(chain), "| dir:", "; ".join(
        (((x.get("prenoms") or "") + " " + re.sub(r"\(.*?\)", "", x.get("nom") or "")).strip() + " [" + (x.get("qualite") or "")[:20] + "/" + (x.get("type") or "")[:8] + "]") for x in cur[:3]), flush=True)

json.dump(out, open(BASE + r"\_lot12_api_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TERMINE", len(out))
