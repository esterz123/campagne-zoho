#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COLLECTEUR EN MASSE — collecte de nouvelles entreprises locales (cloud).
======================================================================
API officielle recherche-entreprises (gratuite, sans cle) :
secteurs a forte presence Instagram x grandes villes francaises.
Sortie : masse_locale.json (fusionne avec l'existant, dedup par SIREN).

Chaque fiche contient : nom, siren, secteur, ville, adresse, dirigeant
(directement depuis l'API, champ dirigeants[].qualite), website.

Le dirigeant est VERIFIE : l'API ne renvoie que les dirigeants legaux
(Gerant, President, DG). Jamais de salarie, jamais de devinette.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Secteurs locaux a forte presence Insta
SECTEURS = [
    ("salon coiffure", "96.02A"),
    ("institut beaute", "96.02B"),
    ("restaurant", "56.10A"),
    ("garage auto", "45.20A"),
    ("auto-ecole", "85.53A"),
    ("boulangerie", "10.71A"),
    ("cafe bar", "56.30A"),
    ("fleuriste", "47.76Z"),
]
VILLES = [("75011", "PARIS 11"), ("75015", "PARIS 15"), ("69006", "LYON 6"),
          ("33000", "BORDEAUX"), ("59000", "LILLE"), ("31000", "TOULOUSE"),
          ("44000", "NANTES"), ("67000", "STRASBOURG"), ("13001", "MARSEILLE 1"),
          ("38000", "GRENOBLE")]

CHAÎNES = ("PAUL", "MIDAS", "FRANCK PROVOST", "HAIR CLUB", "BOULANGERIES PAUL",
           "TIMART", "MAPI", "COMPAGNIE PARISIENNE", "BRIOCHE DOREE", "MARIE BLA",
           "YVES ROCHER", "MC DONALD", "BURGER KING", "STARBUCKS", "DOMINO",
           "CARREFOUR", "LIDL", "AUCHAN")


def api_naf_cp(naf, cp, per=25):
    url = ("https://recherche-entreprises.api.gouv.fr/search?activite_principale=%s"
           "&code_postal=%s&per_page=%d" % (urllib.parse.quote(naf), cp, per))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.loads(urllib.request.urlopen(req, timeout=20).read().decode())


def physique(d):
    prenom = (d.get("prenoms") or "").split()[0] if d.get("prenoms") else ""
    nom = re.sub(r"\(.*?\)", "", d.get("nom") or "").strip()
    return f"{prenom.title()} {nom.upper()}" if prenom and nom else ""


def main():
    # Charger l'existant (fusion + dedup par SIREN)
    existant = {}
    try:
        for t in json.load(open(os.path.join(BASE, "masse_locale.json"), encoding="utf-8")):
            existant[t["siren"]] = t
    except Exception:
        pass

    n_avant = len(existant)
    nouvelles = 0
    for secteur, naf in SECTEURS:
        for cp, ville in VILLES:
            try:
                j = api_naf_cp(naf, cp)
                for r in j.get("results", []):
                    nom = r.get("nom_complet", "")
                    if any(ch in nom.upper() for ch in CHAÎNES):
                        continue
                    siren = r.get("siren")
                    if not siren or siren in existant:
                        continue
                    dir_nom = ""
                    for d in r.get("dirigeants", []):
                        p = physique(d)
                        if p:
                            dir_nom = p
                            break
                    siege = r.get("siege", {}) or {}
                    existant[siren] = {
                        "nom": nom, "siren": siren, "secteur": secteur,
                        "ville": ville, "adresse": siege.get("adresse", "")[:50],
                        "dirigeant": dir_nom, "website": r.get("website", "") or "",
                    }
                    nouvelles += 1
            except Exception:
                pass
            time.sleep(0.25)

    json.dump(list(existant.values()), open(os.path.join(BASE, "masse_locale.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("Collecte: %d nouvelles (total %d)" % (nouvelles, len(existant)))


if __name__ == "__main__":
    sys.exit(main())
