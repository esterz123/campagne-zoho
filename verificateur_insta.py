#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICATEUR COMPTES INSTA — verifie chaque compte et recupere les stats.
=========================================================================
Pour chaque cible : recupere followers/posts/nom_affiche depuis la page
publique Instagram, puis VERIFIE que le nom affiche correspond a
l'entreprise (anti-mauvais-compte). Les comptes douteux sont exclus.

Sortie : kit_dm_masse.json (filtre, avec stats) + rapport des exclus.
Usage : python3 verificateur_insta.py
"""
import json, os, re, sys, time, unicodedata, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}


def sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def stats_insta(handle):
    try:
        url = "https://www.instagram.com/%s/" % handle.strip("@")
        req = urllib.request.Request(url, headers=UA)
        html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", "ignore")
        m = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        if not m:
            return None
        desc = m.group(1)
        followers = re.search(r'([\d,\.]+)\s*Followers', desc)
        posts = re.search(r'([\d,\.]+)\s*Posts', desc)
        nom = re.search(r'from\s+(.+?)\s*\(', desc)
        return {
            "followers": followers.group(1) if followers else "?",
            "posts": posts.group(1) if posts else "?",
            "nom_affiche": (nom.group(1) if nom else "").replace("&#x2728;", "")
                          .replace("&#064;", "@").strip()[:40],
        }
    except Exception:
        return None


def nom_correspond(nom_entreprise, nom_affiche):
    ne = sans_accents(nom_entreprise)
    na = sans_accents(nom_affiche)
    if not na:
        return False
    mots = [w for w in re.findall(r"[a-z]{4,}", ne)
            if w not in ("sarl", "sas", "eurl", "les", "paris", "france", "saint",
                         "sur", "concept", "studio", "services", "coiffure", "beaute",
                         "barber", "salon", "institut")]
    if mots and any(m in na for m in mots):
        return True
    return False


def main():
    dms = json.load(open(os.path.join(BASE, "kit_dm_masse.json"), encoding="utf-8"))
    bons, douteux = [], []
    for i, d in enumerate(dms):
        handle = d.get("instagram", "").rstrip("/").split("/")[-1]
        s = stats_insta(handle)
        if not s:
            douteux.append({"nom": d.get("nom"), "handle": handle, "raison": "stats indisponibles"})
        else:
            d["stats"] = s
            if nom_correspond(d.get("nom", ""), s["nom_affiche"]):
                bons.append(d)
            else:
                douteux.append({"nom": d.get("nom"), "handle": handle,
                                "raison": "nom affiche: %s" % s["nom_affiche"][:30]})
        if (i + 1) % 10 == 0:
            # sauvegarde incrementale
            json.dump(bons, open(os.path.join(BASE, "kit_dm_masse.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print("  [%d/%d] bons=%d douteux=%d" % (i + 1, len(dms), len(bons), len(douteux)))
            sys.stdout.flush()
        time.sleep(1.5)

    json.dump(bons, open(os.path.join(BASE, "kit_dm_masse.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(douteux, open(os.path.join(BASE, "insta_douteux.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("TERMINE: %d bons (confirms), %d douteux (exclus)" % (len(bons), len(douteux)))


if __name__ == "__main__":
    sys.exit(main())
