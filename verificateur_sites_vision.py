#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICATEUR SITES PAR VISION — capture thum.io + pre-verification automatique.
=============================================================================
Pour chaque cible avec un site provisoire (provenance bios_insta), genere une
capture thum.io du site dans un dossier captures/. Le verdict final (bon site
ou faux positif) est SAISI PAR L'AGENT via vision_analyze sur la capture.

Sortie :
  - captures/<nom>.png pour chaque site
  - un fichier candidats_a_verifier.json listant {nom, handle, site, image}
L'agent visionne chaque image, puis met a jour kit_dm_masse.json (website garde
ou vide si faux positif).

Usage : python3 verificateur_sites_vision.py [--max N]
"""
import json, os, re, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(BASE, "captures")
os.makedirs(CAP, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0"}


def slug(nom):
    return re.sub(r"[^a-z0-9]+", "_", nom.lower()).strip("_")[:40]


def capture(domain, out):
    url = "https://image.thum.io/get/width/900/noanimate/" + domain
    req = urllib.request.Request(url, headers=UA)
    data = urllib.request.urlopen(req, timeout=45).read()
    if data[:4] == b"\x89PNG":
        open(out, "wb").write(data)
        return True
    return False


def main():
    args = sys.argv[1:]
    max_n = 100000
    if "--max" in args:
        max_n = int(args[args.index("--max") + 1])

    cibles = json.load(open(os.path.join(BASE, "kit_dm_masse.json"), encoding="utf-8"))
    a_verifier = []
    n = 0
    for c in cibles:
        site = (c.get("website") or "").strip()
        if not site or c.get("site_provenance") != "bios_insta":
            continue
        if c.get("site_verifie") is True or c.get("site_verifie") is False:
            continue  # deja tranche
        n += 1
        if n > max_n:
            break
        dom = site.replace("https://", "").replace("http://", "").rstrip("/")
        out = os.path.join(CAP, slug(c.get("nom", "site")) + ".png")
        ok = capture("https://" + dom, out)
        a_verifier.append({
            "nom": c.get("nom", ""), "handle": c.get("instagram", "").rstrip("/").split("/")[-1],
            "ville": c.get("ville", ""), "site": site, "domaine": dom,
            "image": out if ok else "",
            "capture_ok": ok,
        })
        print("  %s | %s | capture:%s" % (c.get("nom", "")[:26], dom[:35], "OK" if ok else "ECHEC"))

    json.dump(a_verifier, open(os.path.join(BASE, "candidats_a_verifier.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n%d candidats captures dans captures/ + candidats_a_verifier.json" % len(a_verifier))
    print("-> Chaque image doit etre visionnee (vision_analyze) avant de valider le site.")


if __name__ == "__main__":
    sys.exit(main())
