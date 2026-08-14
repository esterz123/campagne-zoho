#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POST-FILTRE ANTI-PARKING + SCREENSHOTS — apres chasseur_domaines.py.
====================================================================
Re-verifie chaque domaine trouve : si le HTML sent le parking/vente de
domaine (ExpiredDomains, Sedo, Afternic, marketplaces...), on ecarte.
Les survivants recoivent une capture thum.io dans captures/ pour la VISION.

Usage : python3 postfiltre_captures.py
"""
import json, os, re, sys, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(BASE, "captures")
os.makedirs(CAP, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0"}

# marqueurs forts de parking / vente de domaine
PARKING_MOTS = (
    "expired domain", "domain marketplace", "domain broker", "acquire this domain",
    "this domain is for sale", "buy this domain", "domain is parked", "parked free",
    "sedo", "afternic", "dan.com", "hugedomains", "godaddy", "namecheap",
    "domain for sale", "domains for sale", "domain name for sale", "premium domain",
    "expireddomains", "undeveloped", "bodis", "parkingcrew", "above.com", "buy now",
    "checkout.secureserver", "domain sales", "buy domain", "sell your domain",
    "start a business today", "shopify", "wix site builder", "create your website",
    "get your domain", "make an offer", "available for purchase",
)
# marqueurs de vrais sites de salons/beaute (bonus)
BONUS_MOTS = ("coiffure", "salon", "ongle", "institut", "beaute", "beauté", "barber",
              "nail", "hair", "spa", "esthetic", "esthétique", "barbier", "perruque",
              "rendez-vous", "rendezvous", "reserver", "réservation", "tarif", "horaires")


def sent_parking(html):
    low = html.lower()
    # si marqueurs parking -> parking
    hits = [m for m in PARKING_MOTS if m in low]
    # si aucun texte reel (page vide) -> parking
    texte = re.sub(r"<[^>]+>", " ", html)
    texte = re.sub(r"\s+", " ", texte).strip()
    if len(texte) < 30:
        return True, "page vide"
    if hits:
        return True, "parking (%s)" % hits[0]
    return False, ""


def main():
    cibles = json.load(open(os.path.join(BASE, "kit_dm_masse.json"), encoding="utf-8"))
    a_visionner = []
    for c in cibles:
        site = (c.get("website") or "").strip()
        if not site or c.get("site_provenance") != "domaines_probables":
            continue
        dom = site.replace("https://", "").replace("http://", "").rstrip("/")
        try:
            req = urllib.request.Request("https://" + dom, headers=UA)
            html = urllib.request.urlopen(req, timeout=10).read(80000).decode("utf-8", "ignore")
            park, raison = sent_parking(html)
        except Exception as e:
            park, raison = True, "inaccessible (%s)" % str(e)[:40]
        if park:
            c["website"] = ""
            c["website_candidats"] = []
            print("  EKARTE %s | %s (%s)" % (c.get("nom", "")[:24], dom[:35], raison))
            continue
        # screenshot pour vision
        slug = re.sub(r"[^a-z0-9]+", "_", c.get("nom", "site").lower()).strip("_")[:40]
        out = os.path.join(CAP, "cand_" + slug + ".png")
        try:
            req = urllib.request.Request("https://image.thum.io/get/width/900/noanimate/" + dom,
                                         headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=45).read()
            if data[:4] == b"\x89PNG":
                open(out, "wb").write(data)
                a_visionner.append({"nom": c.get("nom", ""), "ville": c.get("ville", ""),
                                    "handle": c.get("instagram", "").rstrip("/").split("/")[-1],
                                    "site": site, "domaine": dom, "image": out})
                print("  GARDEE  %s | %s -> %s" % (c.get("nom", "")[:24], dom[:35], out.split("\\")[-1]))
            else:
                c["website"] = ""
        except Exception as e:
            c["website"] = ""
            print("  EKARTE %s | %s (capture impossible)" % (c.get("nom", "")[:24], dom[:35]))
        time.sleep(0.5)

    json.dump(cibles, open(os.path.join(BASE, "kit_dm_masse.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(a_visionner, open(os.path.join(BASE, "candidats_a_verifier.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n%d candidats survivants -> vision obligatoire (candidats_a_verifier.json)" % len(a_visionner))


if __name__ == "__main__":
    sys.exit(main())
