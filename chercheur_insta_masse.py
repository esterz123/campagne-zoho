#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHERCHEUR INSTA EN MASSE — trouve le compte Instagram de chaque entreprise.
==========================================================================
Utilise ddgs (DuckDuckGo, gratuit) pour chercher "<nom> <ville> instagram"
sur un lot d'entreprises. Extrait le 1er lien instagram.com/<compte> fiable.

Sortie : masse_insta.json — entreprises avec compte Instagram trouve.

Usage :
  python3 chercheur_insta_masse.py --max 100     # traite 100 entreprises
  python3 chercheur_insta_masse.py --secteur salon_coiffure
"""
import json, os, re, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))

def charger():
    with open(os.path.join(BASE, "masse_locale.json"), encoding="utf-8") as f:
        return json.load(f)

def chercher_insta(nom, ville):
    """Cherche le compte instagram via ddgs. Retourne URL ou ''."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return ""
    try:
        q = '"%s" %s instagram' % (nom[:40], ville)
        with DDGS() as ddgs:
            for res in ddgs.text(q, max_results=5):
                url = res.get("href", "")
                m = re.search(r'instagram\.com/([A-Za-z0-9_.]{3,40})', url)
                if m:
                    handle = m.group(1).split("?")[0]
                    if handle.lower() not in ("explore", "accounts", "login", "reels", "p",
                                              "direct", "settings", "share", "stories"):
                        return "https://www.instagram.com/%s/" % handle
    except Exception:
        pass
    return ""


def main():
    args = sys.argv[1:]
    max_n = 100000
    secteur_filter = None
    for i, a in enumerate(args):
        if a == "--max" and i + 1 < len(args):
            max_n = int(args[i + 1])
        if a == "--secteur" and i + 1 < len(args):
            secteur_filter = args[i + 1]

    toutes = charger()
    # Charger deja trouve
    deja = {}
    try:
        deja = {t["siren"]: t for t in json.load(open(os.path.join(BASE, "masse_insta.json"), encoding="utf-8"))}
    except Exception:
        pass

    # Filtrer : avec dirigeant, pas deja traite
    cibles = [t for t in toutes if t.get("dirigeant") and t["siren"] not in deja]
    if secteur_filter:
        cibles = [t for t in cibles if secteur_filter in t.get("secteur", "")]
    cibles = cibles[:max_n]

    print("A chercher: %d entreprises" % len(cibles))
    trouves = 0
    for i, t in enumerate(cibles):
        insta = chercher_insta(t["nom"], t["ville"])
        if insta:
            deja[t["siren"]] = {**t, "instagram": insta}
            trouves += 1
            print("  [%3d/%3d] %s | %s" % (i + 1, len(cibles), t["nom"][:35], insta))
        else:
            print("  [%3d/%3d] %s | (pas trouve)" % (i + 1, len(cibles), t["nom"][:35]))
        time.sleep(1.2)  # courtoisie DDG

    json.dump(list(deja.values()), open(os.path.join(BASE, "masse_insta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nTotal avec compte Insta: %d" % len(deja))
    print("-> masse_insta.json")


if __name__ == "__main__":
    sys.exit(main())
