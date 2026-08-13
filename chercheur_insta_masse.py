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
    """Cherche le compte instagram via ddgs. Retourne URL ou ''.
    FILTRE DE PERTINENCE (correctif 13/08) : le handle DOIT matcher un mot
    significatif du nom de l'entreprise, sinon c'est un faux compte
    (ex: 'popular', 'syanzhao' pour SYAN). Un DM au mauvais compte =
    catastrophe de credibilite. Jamais de match au hasard."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return ""
    try:
        # Normaliser les accents (le handle est souvent sans accent :
        # "Maîtres" -> "maitres" dans lesmaitresbarbiersperruquiers)
        def sans_accents(s):
            import unicodedata
            return "".join(c for c in unicodedata.normalize("NFD", s)
                           if unicodedata.category(c) != "Mn").lower()

        nom_norm = sans_accents(nom)
        # Mots significatifs du nom (>= 4 lettres, hors mots generiques)
        mots = [w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", nom_norm)
                if w.lower() not in ("sarl", "sas", "eurl", "snc", "sci", "les", "le",
                                     "la", "the", "des", "paris", "france", "saint",
                                     "sainte", "st", "sur", "concept", "studio", "group",
                                     "groupe", "holding", "france", "services")]
        q_variantes = [
            '"%s" %s instagram' % (nom[:40], ville),
            '%s %s instagram' % (nom[:40], ville),
        ]
        with DDGS() as ddgs:
            for q in q_variantes:
                try:
                    results = list(ddgs.text(q, max_results=10))
                except Exception:
                    results = []
                for res in results:
                    url = res.get("href", "")
                    m = re.search(r'instagram\.com/([A-Za-z0-9_.]{3,40})', url)
                    if not m:
                        continue
                    handle = sans_accents(m.group(1).split("?")[0])
                    if handle in ("explore", "accounts", "login", "reels", "p",
                                  "direct", "settings", "share", "stories", "popular"):
                        continue
                    # PERTINENCE : au moins un mot du nom dans le handle
                    if mots and any(mot in handle for mot in mots):
                        return "https://www.instagram.com/%s/" % m.group(1).split("?")[0]
                    # Fallback : le nom complet (sans accents, sans espaces) dans le handle
                    slug = re.sub(r"[^a-z0-9]", "", nom_norm)
                    if len(slug) >= 8 and slug[:12] in handle:
                        return "https://www.instagram.com/%s/" % m.group(1).split("?")[0]
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
