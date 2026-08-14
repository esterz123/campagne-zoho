#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHERCHEUR SITES VIA BIOS INSTAGRAM (SearXNG)
=============================================
Methode validee au dossier : chercher le handle Instagram dans les resultats
de recherche SearXNG. Le snippet de la page Instagram (bio) contient souvent
le site web du commerce. On extrait le domaine depuis le content des resultats
pointant vers instagram.com (le nom affiche + la bio y figurent).

Sortie : met a jour kit_dm_masse.json avec "website" pour les sites trouves.
Le domaine candidat est PROVISOIRE : il sera VERIFIE PAR VISION avant tout DM.

Port SearXNG : auto-detecte (le port change a chaque lancement). Priorite :
  env SEARX_PORT, puis scan 1090..1180, puis 8080.
Usage : python3 chercheur_sites_bios.py [--max N]
"""
import json, os, re, sys, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))

EXCLURE = ("instagram.com", "facebook.com", "linkedin.com", "tiktok.com", "snapchat.com",
           "societe.com", "pagesjaunes", "yelp", "infogreffe", "pappers", "kompass",
           "lefigaro", "linternaute", "tripadvisor", "planity", "118000", "justacote",
           "misterwhat", "yumpu", "mappy", "annuaire-entreprises", "gouv.fr",
           "maps.google", "google.com", "youtube.com", "pinterest", "twitter.com",
           "x.com", "booking", "youtube", "quoidonner", "sortiraparis", "airzen",
           "francebleu", "bfmtv", "leboncoin", "mon-entreprise", "wixsite", "webnode")


def detecter_port():
    """Trouve le port SearXNG en service."""
    if os.environ.get("SEARX_PORT"):
        return os.environ["SEARX_PORT"]
    for p in list(range(1090, 1181)) + [8080, 8888, 8889]:
        try:
            url = "http://127.0.0.1:%d/search?q=test&format=json" % p
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            j = json.loads(urllib.request.urlopen(req, timeout=4).read().decode())
            if isinstance(j, dict) and "results" in j:
                return str(p)
        except Exception:
            continue
    return "1090"


def searx_search(port, query, n=12):
    try:
        url = "http://127.0.0.1:%s/search?q=%s&format=json" % (port, urllib.parse.quote(query))
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0)"})
        j = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
        return j.get("results", [])
    except Exception:
        return []


def nettoyer_domaine(url):
    m = re.search(r'https?://(?:www\.)?([a-z0-9-]+\.(?:fr|com|eu|net|site|business|center|co|io|be|ch|ca|org|me))', url)
    return m.group(1).lower() if m else None


def candidats_site(port, nom, ville, handle):
    """Cherche le site depuis la bio Instagram (le site est souvent dans la bio)."""
    handle_clean = handle.strip().lstrip("@").rstrip("/").split("/")[-1]
    candidats = []
    vus = set()

    # Requete 1 : site:instagram.com/<handle> -> le snippet montre la bio (avec le site)
    q1 = 'site:instagram.com %s' % handle_clean
    for r in searx_search(port, q1):
        url = r.get("url", "").lower()
        content = r.get("content", "") or ""
        if "instagram.com" in url and handle_clean in url:
            # Extraire tout domaine de site web dans la bio/snippet
            for d in re.findall(r'(?:https?://)?(?:www\.)?([a-z0-9-]+\.(?:fr|com|eu|net|site|business|center|co|io|be|ch|ca|org|me))', content):
                d = d.lower()
                if d in vus or any(x in d for x in EXCLURE) or d == handle_clean:
                    continue
                vus.add(d)
                candidats.append(d)
        if len(candidats) >= 3:
            break

    # Requete 2 : nom commercial + ville (secours)
    if not candidats:
        slug = re.sub(r"[^a-z0-9]", "", nom.lower())
        for q2 in ['"%s" %s' % (nom[:40], ville.split()[0]), 'instagram %s' % handle_clean]:
            for r in searx_search(port, q2):
                url = r.get("url", "").lower()
                content = r.get("content", "") or ""
                if "instagram.com" in url:
                    for d in re.findall(r'(?:https?://)?(?:www\.)?([a-z0-9-]+\.(?:fr|com|eu|net|site|business|center|co|io|be|ch|ca|org|me))', content):
                        d = d.lower()
                        if d in vus or any(x in d for x in EXCLURE) or d == handle_clean:
                            continue
                        if len(slug) >= 5 and (slug[:8] in d or d[:8] in slug):
                            vus.add(d)
                            candidats.append(d)
                if len(candidats) >= 2:
                    break
            if candidats:
                break

    return candidats


def main():
    args = sys.argv[1:]
    max_n = 100000
    if "--max" in args:
        max_n = int(args[args.index("--max") + 1])

    port = detecter_port()
    print("SearXNG port: %s" % port)

    cibles = json.load(open(os.path.join(BASE, "kit_dm_masse.json"), encoding="utf-8"))
    sans_site = [c for c in cibles if not c.get("website") and c.get("instagram")][:max_n]
    print("Cibles sans site a traiter: %d" % len(sans_site))

    trouves = 0
    for i, c in enumerate(sans_site):
        handle = c.get("instagram", "").rstrip("/").split("/")[-1]
        cands = candidats_site(port, c.get("nom", ""), c.get("ville", ""), handle)
        if cands:
            # garder le candidat le plus probable (1er), stocker la liste pour verif
            c["website"] = "https://" + cands[0]
            c["website_candidats"] = cands
            c["site_provenance"] = "bios_insta"
            trouves += 1
            print("  [%3d/%3d] %s | site provisoire: %s | cands: %s" %
                  (i + 1, len(sans_site), c.get("nom", "")[:26], cands[0][:32], cands))
        else:
            c["website"] = ""
            c["website_candidats"] = []
            c["site_provenance"] = ""
        time.sleep(0.6)

    # sauvegarde (conserve les 4 deja validees)
    json.dump(cibles, open(os.path.join(BASE, "kit_dm_masse.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\nSites provisoires trouves (a VERIFIER PAR VISION): %d/%d" % (trouves, len(sans_site)))
    print("-> kit_dm_masse.json mis a jour. Chaque site doit passer la vision avant envoi.")


if __name__ == "__main__":
    sys.exit(main())
