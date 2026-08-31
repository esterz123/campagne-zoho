#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHASSEUR DE NOMS - remplace "Bonjour," par "Bonjour M. X," avec le VRAI dirigeant.
==================================================================================
Source : recherche-entreprises.api.gouv.fr (gratuit, sans cle, officiel).
Regle 1bis stricte : seulement si le nom est VERIFIE dirigeant (qualite President/
Gerant/DG, personne physique, chaine holding remontee max 3 niveaux). Sinon on
laisse "Bonjour," : un nom faux est pire qu'aucun nom.
Anti-doublon : ne jamais inventer, ne jamais prendre un salarie.
Idempotent, zero LLM. Usage : python3 chasseur_noms.py [--sample N] [--dry]
"""
import os
import re
import sys
import json
import time
import unicodedata
import urllib.request
import urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
CACHE = os.path.join(BASE, ".noms_cache.json")
API = "https://recherche-entreprises.api.gouv.fr/search"

PRIO = {"PRESIDENT": 0, "PRESIDENTE": 0, "DIRECTEUR GENERAL": 0, "DIRECTRICE GENERALE": 0,
        "PRESIDENT DE SAS": 0, "PRESIDENT DE SA": 0, "PRESIDENT DU DIRECTOIRE": 0,
        "GERANT": 1, "GERANTE": 1, "CO-GERANT": 1, "CO-GERANTE": 1, "GÉRANT": 1,
        "ASSOCIE GERANT": 2, "ASSOCIEE GERANTE": 2, "DIRIGEANT": 2}


def clean(t):
    return (t or "").replace("\u2019", "'").replace("\u2018", "'")


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def api_get(params, tries=2):
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mahdi-design-prospection"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())
        except Exception:
            time.sleep(1.5)
    return None


def dirigeant_de(resultat, profondeur=0):
    """Cherche une personne physique dirigeante, remonte les holdings (max 3)."""
    if not resultat or profondeur > 3:
        return None
    dirs = resultat.get("dirigeants") or []
    physiques = [d for d in dirs if d.get("type_dirigeant") == "personne physique"
                 and (d.get("nom") or d.get("prenoms"))]
    if physiques:
        best = min(physiques, key=lambda d: PRIO.get(norm(d.get("qualite") or "").upper().strip(), 9))
        if PRIO.get(norm(best.get("qualite") or "").upper().strip(), 9) < 9:
            nom = (best.get("nom") or "").strip().upper()
            prenom = (best.get("prenoms") or "").strip().title()
            qualite_up = norm(best.get("qualite") or "").upper()
            feminin = any(w in qualite_up for w in ("GERANTE", "PRESIDENTE", "DIRECTRICE", "CO-GERANTE", "ASSOCIEE"))
            if nom:
                return {"nom": nom, "prenom": prenom, "qualite": best.get("qualite"),
                        "feminin": feminin}
    morales = [d for d in dirs if d.get("type_dirigeant") == "personne morale"
               and PRIO.get(norm(d.get("qualite") or "").upper().strip(), 9) < 3]
    for dm in morales:
        siren = (dm.get("siren") or "").strip()
        if siren:
            j = api_get({"q": siren, "per_page": 1})
            time.sleep(0.45)
            if j and j.get("results"):
                got = dirigeant_de(j["results"][0], profondeur + 1)
                if got:
                    return got
    return None


def chercher(nom_entreprise, domaine):
    """Interroge l'API par nom d'entreprise, confirme par domaine si possible."""
    q = re.sub(r"\b(sas|sarl|sa|eurl|sci|sasu|sas u)\b", "", norm(nom_entreprise), flags=re.I).strip()
    q = re.sub(r"[^a-z0-9 -]", " ", q).strip()[:60]
    if len(q) < 3:
        return None
    j = api_get({"q": q, "per_page": 5})
    if not j or not j.get("results"):
        return None
    dom = (domaine or "").lower().replace("www.", "")
    dom_core = re.sub(r"\.(fr|com|net|eu|org)$", "", dom).replace("-", "") if dom else ""
    candidats = j["results"]
    if dom_core:
        # confirmation par le site : meme racine de domaine dans noms/commercials
        conf = [c for c in candidats
                if dom_core in norm(c.get("nom_complet", "")).replace("-", "")
                or any(dom_core in norm(x or "") for x in (c.get("commercials") or []))]
        if conf:
            candidats = conf
    for c in candidats:
        got = dirigeant_de(c)
        if got:
            got["siren"] = c.get("siren")
            got["enseigne"] = c.get("nom_complet", "")[:60]
            return got
    return None


def main():
    sample = None
    dry = "--dry" in sys.argv
    for i, a in enumerate(sys.argv):
        if a == "--sample" and i + 1 < len(sys.argv):
            sample = int(sys.argv[i + 1])
    data = json.load(open(DATA, encoding="utf-8"))
    state = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))
    sent = set(str(k) for k in state.get("sent", {}))
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}

    cibles = []
    for r in data:
        num = str(r.get("num"))
        if num in sent:
            continue
        lignes = r["body"].split("\n")
        if lignes[0].strip() not in ("Bonjour,", "Bonjour"):
            continue
        cibles.append((num, r))
    if sample:
        cibles = cibles[:sample]

    trouves = 0
    for k, (num, r) in enumerate(cibles, 1):
        entreprise = re.sub(r"^\d+\s*[—-]\s*", "", r.get("prospect") or "")
        if not entreprise.strip():
            # pas de raison sociale : on derive du domaine (nplast-usinage.fr -> nplast usinage)
            src = (r.get("site") or r.get("to", "") or "")
            src = re.sub(r"^https?://", "", src).replace("www.", "")
            dom = norm(src.split("@")[-1].split("/")[0])
            dom = re.sub(r"\.(fr|com|net|eu|org)$", "", dom)
            entreprise = dom.replace("-", " ").replace("_", " ").strip()
        cle = entreprise.strip().lower()[:50]
        if cle in cache:
            got = cache[cle]
        else:
            got = chercher(entreprise, r.get("site") or r.get("to", ""))
            cache[cle] = got or {}
            json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.45)
        if not got or not got.get("nom"):
            print("  [%d/%d] #%s %-30s -> pas de dirigeant verifie" % (k, len(cibles), num, entreprise[:30]))
            continue
        civ = "Mme" if got.get("feminin") else "M."
        lignes = r["body"].split("\n")
        lignes[0] = "Bonjour %s %s," % (civ, got["nom"])
        r["body"] = clean("\n".join(lignes))
        trouves += 1
        print("  [%d/%d] #%s %-30s -> %s %s (%s)" % (k, len(cibles), num, entreprise[:30], civ, got["nom"], got.get("qualite", "")[:20]))

    print("\nnoms verifies trouves: %d / %d cibles" % (trouves, len(cibles)))
    if not dry and trouves:
        json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("ECRIT:", DATA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
