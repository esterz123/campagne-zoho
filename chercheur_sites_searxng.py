#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHERCHEUR SITES VIA SEARXNG LOCAL — trouve le vrai site web de chaque compte.
============================================================================
Utilise SearXNG (http://127.0.0.1:1161) pour trouver le site officiel d'un
commerce, puis scan_urgence analyse le site trouve (WordPress, SSL, date).

Sortie : met a jour masse_insta.json avec "website" reel + "constat_site".

Usage : python3 chercheur_sites_searxng.py [--max N]
"""
import json, os, re, sys, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
SEARX = "http://127.0.0.1:1161"

EXCLURE = ("instagram.com", "facebook.com", "linkedin.com", "tiktok.com", "snapchat.com",
           "societe.com", "pagesjaunes", "yelp", "infogreffe", "pappers", "kompass",
           "lefigaro", "linternaute", "tripadvisor", "planity", "118000", "justacote",
           "kelest", "dnb.com", "repreneurs", "telephoneannuaire", "acte-deces",
           "verif.com", "treatwell", "maps.google", "google.com", "youtube.com",
           "pinterest", "twitter.com", "x.com", "booking", "quotidien", "journal",
           "creationprototype", "quoidonner", "sortiraparis", "airzen", "soyonsfutiles",
           "vertbobo", "fr-fr", "francebleu", "bfmtv", "leboncoin")


def searx_search(query, n=12):
    try:
        url = SEARX + "/search?q=%s&format=json" % urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0)"})
        j = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
        return j.get("results", [])
    except Exception:
        return []


def trouver_site(nom, ville, handle):
    """Trouve le vrai site web. Priorite : nom commercial + ville."""
    # Requetes candidates (du plus precis au plus large)
    queries = [
        '"%s" %s' % (nom[:40], ville.split()[0]),
        '"%s" %s' % (nom[:40], "Bordeaux" if "BORDEAUX" in ville else ville.split()[0]),
    ]
    # Si le nom est une raison sociale (LMBP), essayer le handle insta
    if len(nom) < 15:
        queries.append('instagram %s' % handle)
    vus = set()
    for q in queries:
        for r in searx_search(q):
            url = r.get("url", "")
            m = re.search(r'https?://(?:www\.)?([a-z0-9-]+\.(?:fr|com|eu|net|site|business|center|co|io))', url)
            if not m:
                continue
            domaine = m.group(1).lower()
            if domaine in vus or any(x in url.lower() for x in EXCLURE):
                continue
            vus.add(domaine)
            # ne garder que si le domaine a un rapport avec le nom ou le handle
            slug_nom = re.sub(r"[^a-z0-9]", "", nom.lower())
            slug_handle = re.sub(r"[^a-z0-9]", "", handle.lower())
            racine = domaine.split(".")[0]
            if (slug_nom and len(slug_nom) >= 5 and slug_nom[:8] in racine) or \
               (slug_handle and len(slug_handle) >= 5 and slug_handle[:8] in racine) or \
               (slug_nom and len(slug_nom) >= 5 and racine in slug_nom) or \
               (slug_handle and len(slug_handle) >= 5 and racine in slug_handle):
                return "https://" + domaine
    return ""


def main():
    args = sys.argv[1:]
    max_n = 100000
    if "--max" in args:
        max_n = int(args[args.index("--max") + 1])

    # Charger les cibles avec compte Insta
    try:
        cibles = json.load(open(os.path.join(BASE, "masse_insta.json"), encoding="utf-8"))
    except FileNotFoundError:
        print("masse_insta.json introuvable")
        sys.exit(1)

    avec_insta = [c for c in cibles if c.get("instagram")][:max_n]
    print("Cibles avec compte Insta: %d" % len(avec_insta))

    # Charger scan_urgence pour l'analyse des sites
    sys.path.insert(0, BASE)
    import scan_urgence as S

    trouves = 0
    analyses = 0
    for i, c in enumerate(avec_insta):
        handle = c.get("instagram", "").rstrip("/").split("/")[-1]
        site = trouver_site(c.get("nom", ""), c.get("ville", ""), handle)
        if site:
            c["website"] = site
            trouves += 1
            try:
                r = S.analyser_site(site)
                if r.get("probleme") and r["probleme"] not in ("OK", "", None):
                    c["constat_site"] = r
                    analyses += 1
                    print("  [%3d/%3d] %s | %s | %s" % (i + 1, len(avec_insta), c.get("nom", "")[:28], site[:35], r["probleme"]))
                else:
                    print("  [%3d/%3d] %s | %s | sain" % (i + 1, len(avec_insta), c.get("nom", "")[:28], site[:35]))
            except Exception:
                print("  [%3d/%3d] %s | %s | ?" % (i + 1, len(avec_insta), c.get("nom", "")[:28], site[:35]))
        else:
            c["website"] = ""
        time.sleep(0.8)

    json.dump(cibles, open(os.path.join(BASE, "masse_insta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nSites trouves: %d/%d | avec constat: %d" % (trouves, len(avec_insta), analyses))
    print("-> masse_insta.json mis a jour")


if __name__ == "__main__":
    sys.exit(main())
