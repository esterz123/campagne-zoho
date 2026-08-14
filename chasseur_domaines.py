#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHASSEUR DE DOMAINES PROBABLES — trouve les vrais sites SANS moteur de recherche.
=================================================================================
Pour chaque cible sans site : genere des domaines candidats depuis le nom
commercial et le handle Instagram (ex: onatty.com, 12thsquarebarber.com,
salon-nom.fr...), teste leur existence par HTTP HEAD, et garde ceux qui
repondent avec un contenu HTML (pas un parking/404).

Les domaines trouves sont PROVISOIRES : ils seront VERIFIES PAR VISION
(screenshot thum.io) avant d'ecrire un DM (regle du dossier : domaine != entreprise).

Usage : python3 chasseur_domaines.py [--max N]
"""
import json, os, re, sys, time, socket, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

# domaines de parking/vente a ecarter d'emblee
PARKING = ("sedo.com", "afternic", "dan.com", "godaddy", "namecheap", "hugedomains",
           "shopify.com", "wixsite.com", "webnode", "sitew", "1and1", "ovh", "gandi")


def slug_net(s):
    """slug simple pour un nom commercial."""
    s = re.sub(r"[^a-z0-9]+", "", s.lower())
    return s.strip("_")


def candidats_domaines(nom, handle):
    """Genere les domaines probables : nom commercial + handle, extensions fr/com/net."""
    slugs = set()
    # nom commercial (enlever raison sociale entre parentheses, prendre le debut)
    base = re.sub(r"\(.*?\)", "", nom).strip()
    s = slug_net(base)
    if len(s) >= 4:
        slugs.add(s)
    # premier mot significatif + mot 2 si court
    mots = [w for w in re.findall(r"[a-z0-9]+", base.lower()) if len(w) >= 3]
    if mots:
        slugs.add("".join(mots[:2]))
        if len(s) > 20 and len(mots) >= 2:
            slugs.add(mots[0] + mots[1])
    # handle instagram
    h = slug_net(handle.replace("_", "").replace(".", ""))
    if len(h) >= 4:
        slugs.add(h)
    # le handle sans chiffres
    h2 = re.sub(r"[0-9]+$", "", h)
    if len(h2) >= 5:
        slugs.add(h2)

    doms = []
    for s in slugs:
        for ext in (".fr", ".com", ".net"):
            doms.append(s + ext)
    return doms[:12]


def domaine_vit(domaine):
    """Teste si le domaine repond avec du vrai HTML (pas 404/parking)."""
    for proto in ("https", "http"):
        try:
            req = urllib.request.Request(proto + "://" + domaine, headers=UA, method="GET")
            with urllib.request.urlopen(req, timeout=8) as r:
                html = r.read(60000).decode("utf-8", "ignore")
                code = r.getcode()
            if code != 200:
                continue
            low = html.lower()
            if any(p in low for p in ("buy this domain", "this domain is for sale",
                                      "domain is parked", "parked free")):
                return False
            # une vraie page : du texte + un titre
            if "<title" in low and len(re.sub(r"<[^>]+>", "", html).strip()) > 50:
                return True
        except Exception:
            continue
    return False


def main():
    args = sys.argv[1:]
    max_n = 100000
    if "--max" in args:
        max_n = int(args[args.index("--max") + 1])

    cibles = json.load(open(os.path.join(BASE, "kit_dm_masse.json"), encoding="utf-8"))
    sans_site = [c for c in cibles if not c.get("website") and c.get("instagram")][:max_n]
    print("Cibles sans site: %d" % len(sans_site))

    trouves = 0
    for i, c in enumerate(sans_site):
        handle = c.get("instagram", "").rstrip("/").split("/")[-1]
        cands = candidats_domaines(c.get("nom", ""), handle)
        vus = set()
        vivants = []
        for d in cands:
            if d in vus or any(p in d for p in PARKING):
                continue
            vus.add(d)
            if domaine_vit(d):
                vivants.append(d)
        if vivants:
            c["website"] = "https://" + vivants[0]
            c["website_candidats"] = vivants
            c["site_provenance"] = "domaines_probables"
            trouves += 1
            print("  [%3d/%3d] %s | %s" % (i + 1, len(sans_site), c.get("nom", "")[:26], vivants[:3]))
        else:
            c["website"] = ""
            c["website_candidats"] = []
        time.sleep(0.2)

    json.dump(cibles, open(os.path.join(BASE, "kit_dm_masse.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nDomaines probables trouves (A VERIFIER PAR VISION): %d/%d" % (trouves, len(sans_site)))
    print("-> kit_dm_masse.json mis a jour.")


if __name__ == "__main__":
    sys.exit(main())
