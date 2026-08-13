#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCAN URGENCE SECURITE — detecte les sites piratés / vulnérables.
================================================================
Pourquoi : les entreprises au site piraté ou non maintenu ont un probleme
AIGU (peur = action immediate). C'est le levier de conversion le plus rapide :
intervention 150-300 EUR + pack securite 79 EUR/mois.

Détecte sur chaque site :
  1. LIENS DE FRAUDE / SPAM : domaines inconnus dans les href (coréen, chinois,
     pharmacie, casino) = site PIRATE
  2. WORDPRESS NON MAINTENU : wp-content/themes + version obsolete dans meta
  3. ABSENCE SSL : http:// sans redirect https (rare, signale)
  4. COPYRIGHT ANCIEN : (c) 2010-2018 dans le footer
  5. GENERATEUR WIX/WEBAZOR/1&1 = builder amateur

Sortie : urgence_securite.json — liste priorisée (PIRATE > WP_OBSOLETE > SSL_KO)
avec l'email de contact quand on l'a, pour DM/email immediat.

Usage :
  python3 scan_urgence.py            # scanne toutes les sources connues
  python3 scan_urgence.py --source dirigeants_email  # une source precise
"""
import json, os, re, sys, time, socket
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"}

# Domaines/patterns de spam connus (site pirate)
# IMPORTANT (correctif 13/08) : chaque mot-cle doit etre DELIMITE par un
# separateur de domaine (point, tiret, underscore, ou debut de domaine).
# Sans ca : "cialis" matche dans "specialiste.com", "bet" matche partout,
# "poker" dans "pokerface.fr" -> faux positifs massifs.
SEP = r"(?:^|[.\-_])"
PATTERNS_SPAM = [
    SEP + r"casino", SEP + r"poker", SEP + r"viagra", SEP + r"cialis",
    SEP + r"pharma", SEP + r"escort", SEP + r"slot", SEP + r"loto",
    r"카지노", r"온라인", r"바카라",  # coreen: casino en ligne
    r"赌场", r"赌博", r"彩票",     # chinois: casino / paris / loterie
    r"кракен", r"kraken", r"даркнет",
]
# Alertes WordPress (version obsolete = vulnérabilités connues)
WP_OLD = re.compile(r'content="WordPress\s+(\d+)\.(\d+)')
WP_LINK = re.compile(r'wp-content/themes/([a-z0-9_-]+)')


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def analyser_site(url, nom=""):
    """Analyse un site. Retourne dict {probleme, details, note}."""
    url = url if url.startswith("http") else "https://" + url
    out = {"url": url, "probleme": None, "details": [], "note": 0}
    try:
        html = fetch(url)
    except Exception:
        # retry http://
        try:
            url2 = url.replace("https://", "http://")
            html = fetch(url2)
            out["details"].append("SSL absent : le site repond en http, pas de https")
            out["note"] = max(out["note"], 2)
        except Exception:
            out["probleme"] = "INJOIGNABLE"
            out["details"].append("Le site ne repond pas (domaine mort ou bloque)")
            return out

    # 1) Liens de spam / piratage
    # IMPORTANT (correctif 13/08) : matcher les DOMAINES COMPLETS uniquement,
    # jamais le texte brut. Le mot "spécialiste" contient "cialis" (faux positif
    # massif), "bet" matche partout, "poker" dans "pokerface"... On exige un
    # domaine avec point (ex: xena-casino.gr) ET un mot-clé de fraude.
    hrefs = re.findall(r'href="(?:https?://)?([^/"\']+)', html)
    spam = []
    for d in hrefs:
        if "#" in d or d.startswith("/") or d.startswith("mailto") or "." not in d:
            continue  # ancre interne, lien relatif, mailto : jamais du spam
        d_clean = d.lower().split("/")[0]
        for p in PATTERNS_SPAM:
            if re.search(p, d_clean, re.I):
                spam.append(d)
                break
    if spam:
        out["probleme"] = "PIRATE"
        out["details"].append("Liens de fraude/spam dans le code : " + ", ".join(sorted(set(spam))[:3]))
        out["note"] = 5

    # 2) WordPress obsolete
    m = WP_OLD.search(html)
    if m:
        maj, minr = int(m.group(1)), int(m.group(2))
        if maj < 6 or (maj == 6 and minr < 6):
            out["probleme"] = out["probleme"] or "WP_OBSOLETE"
            out["details"].append("WordPress %d.%d (vulnerabilites connues non corrigees)" % (maj, minr))
            out["note"] = max(out["note"], 3)
    tm = WP_LINK.search(html)
    if tm and not m:
        out["details"].append("Theme WordPress : %s" % tm.group(1))
        # theme Divi/Bridge/Avada = template daté
        if tm.group(1).lower() in ("divi", "bridge", "avada"):
            out["details"].append("Theme Divi/Bridge/Avada (template generique date)")
            out["note"] = max(out["note"], 1)

    # 3) Builder amateur
    for b in ["wix.com", "webador", "1and1", "ionos", "site.pro", "strikingly"]:
        if b in html.lower():
            out["details"].append("Builder amateur : " + b)
            out["note"] = max(out["note"], 2)
            break

    # 4) Copyright ancien
    cp = re.search(r"©\s*(\d{4})|copyright\s*\(?c\)?\s*(\d{4})", html, re.I)
    if cp:
        annee = int(cp.group(1) or cp.group(2))
        if annee <= 2019:
            out["probleme"] = out["probleme"] or "SITE_DATÉ"
            out["details"].append("Copyright %d : site non mis a jour depuis des annees" % annee)
            out["note"] = max(out["note"], 2)

    return out


# Domaines d'annuaire/distributeurs a IGNORER (faux sites, pas l'entreprise)
FAUX_DOMAINES = {"ouest-france.fr", "laprovence.com", "master-outillage.com", "someflu.com",
                 "oaca.nat.tn", "mairiepariscentre.fr", "emploi-plasturgie.org", "mon-irrigation.com"}


def charger_sources():
    """Agrege toutes les fiches avec site + email connus."""
    fiches = {}
    # dirigeants_email.json : dict siren -> fiche
    try:
        d = json.load(open(os.path.join(BASE, "dirigeants_email.json"), encoding="utf-8"))
        for siren, f in d.items():
            if f.get("site") and f.get("site") not in ("", "N/A", "None"):
                fiches[siren] = {"nom": f.get("nom", ""), "site": f["site"],
                                 "email": f.get("email", ""), "ville": f.get("ville", "")}
    except Exception:
        pass
    # annuaire_prospects.json : liste
    try:
        a = json.load(open(os.path.join(BASE, "annuaire_prospects.json"), encoding="utf-8"))
        for f in a:
            if f.get("site"):
                fiches.setdefault(f.get("siren") or f["site"], {"nom": f.get("nom",""),
                    "site": f["site"], "email": f.get("email",""), "ville": ""})
    except Exception:
        pass
    # nouveaux_dirigeants_valides.json
    try:
        n = json.load(open(os.path.join(BASE, "nouveaux_dirigeants_valides.json"), encoding="utf-8"))
        for f in n:
            if f.get("site"):
                fiches.setdefault(f.get("siren") or f["site"], {"nom": f.get("nom",""),
                    "site": f["site"], "email": f.get("email",""), "ville": f.get("ville","")})
    except Exception:
        pass
    # campagne_data.json : la file d'envoi (sites des prospects actifs)
    try:
        c = json.load(open(os.path.join(BASE, "campagne_data.json"), encoding="utf-8"))
        for f in c:
            dom = f.get("site") or (f.get("to", "").split("@")[-1] if f.get("to") else "")
            if dom:
                fiches.setdefault(dom, {"nom": f.get("prospect", "")[:40], "site": dom,
                                        "email": f.get("to", ""), "ville": ""})
    except Exception:
        pass
    # Filtrer les domaines d'annuaires connus
    for siren in list(fiches.keys()):
        s = (fiches[siren].get("site") or "").lower()
        if any(fd in s for fd in FAUX_DOMAINES):
            del fiches[siren]
    return fiches


def main():
    fiches = charger_sources()
    print("Fiches avec site: %d" % len(fiches))
    resultats = []
    for siren, f in fiches.items():
        r = analyser_site(f["site"], f["nom"])
        if r["probleme"]:
            r.update({"nom": f["nom"], "email": f["email"], "ville": f["ville"]})
            resultats.append(r)
            print("  %-10s %-35s %s" % (r["probleme"], f["nom"][:35], f["site"]))
        time.sleep(0.4)  # courtoisie

    # Trier par gravite (note desc)
    resultats.sort(key=lambda r: r["note"], reverse=True)
    with open(os.path.join(BASE, "urgence_securite.json"), "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=1)
    print("\n%d site(s) a probleme -> urgence_securite.json" % len(resultats))
    print("PIRATES (priorite max):", sum(1 for r in resultats if r["probleme"] == "PIRATE"))
    print("WP_OBSOLETE:", sum(1 for r in resultats if r["probleme"] == "WP_OBSOLETE"))


if __name__ == "__main__":
    sys.exit(main())
