#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INJECTEUR DE PREUVES - remplace l'accusation générique par le constat mesuré.
=============================================================================
Chaque mail vierge de campagne_data.json contient une 2e ligne du type
"Votre site X n'apparait pas sur Google..." JAMAIS vérifiée. Ce script la
remplace par le constat réel sorti de verificateur_site.py (note, HTTPS,
mobile, vitesse, pages, piratage, site mort). Idempotent : un mail déjà
injecté (qui commence par "J'ai ouvert" / "J'ai tape") est sauté.

Usage : python3 injecteur_preuves.py [--dry]
"""
import os
import re
import sys
import json
import shutil
import unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
PREUVES = os.path.join(BASE, "constats_sites.json")
DRY = "--dry" in sys.argv


def clean(t):
    return (t or "").replace("\u2019", "'").replace("\u2018", "'")


def norm_dom(x):
    x = (x or "").lower().strip()
    if "@" in x:
        x = x.split("@")[-1]
    x = x.replace("https://", "").replace("http://", "").replace("www.", "")
    return x.split("/")[0].strip()


# Motifs de l'accusation NON vérifiée à remplacer (ligne 2 du corps)
CLAIM = re.compile(
    r"n'appara[iî]t pas|n'apparait|tombent sur vos concurrents|sont devant vous|"
    r"le v[oô]tre non|recherche .* sur Google", re.I)
ALREADY = re.compile(r"^J'ai (ouvert|tape|cherche|verifie|pass)", re.I)


def objet_pour(p):
    """Objet bâti sur LE fait mesuré le plus fort. Zéro affirmation gratuite.
    Retourne None = on garde l'objet d'origine (site propre ou non auditable)."""
    dom = p.get("domaine", "")
    note = p.get("note")
    if p.get("pirate"):
        return "Des liens de fraude tournent sur %s en ce moment" % dom
    if p.get("etat") == "BLOQUE" or note is None:
        return None
    if p.get("etat") != "VIVANT":
        return "Votre site %s ne s'ouvre pas ce matin" % dom
    if p.get("parking"):
        return "%s affiche une page de parking, pas votre entreprise" % dom
    if p.get("http_seul"):
        return "Chrome affiche 'non securise' sur %s" % dom
    if note < 60:
        return "J'ai audite %s ce matin: %d/100" % (dom, note)
    if p.get("mobile") is False:
        return "Votre site est illisible sur telephone, je viens de verifier"
    if p.get("temps_s") and p["temps_s"] > 3:
        return "%s met %.0f secondes a s'afficher (mesure a l'instant)" % (dom, p["temps_s"])
    return None  # site correct : objet d'origine, constat honnête dans le corps


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    if not os.path.exists(PREUVES):
        print("ERREUR: constats_sites.json absent. Lancer verificateur_site.py d'abord.")
        return 1
    preuves = json.load(open(PREUVES, encoding="utf-8"))

    injectes = 0
    conserves = 0
    sautes = 0
    objets = 0
    exemples = []
    for r in data:
        num = str(r.get("num"))
        p = preuves.get(num)
        if not p:
            continue
        body = r.get("body", "")
        lines = body.split("\n")
        # trouver la ligne d'accusation (2e ligne non vide en général)
        idx = None
        for i, ln in enumerate(lines):
            s = ln.strip()
            if not s or s.startswith("Bonjour"):
                continue
            if ALREADY.match(s):
                idx = None
                break  # déjà injecté
            # Règle 31/08 : si un constat MESURÉ existe, il remplace la 2e ligne
            # quelle que soit sa formulation d'origine (accusation non prouvée).
            if p.get("constat") or CLAIM.search(s):
                idx = i
            break
        if idx is None:
            sautes += 1
            continue
        constat = clean(p.get("constat", "")).strip()
        if not constat:
            # Site qui refuse le robot : on ne peut RIEN mesurer, donc on
            # n'affirme RIEN (règle 13/08). Formule honnête, sans Google.
            constat = ("Je suis alle voir votre site ce matin. Plutot que de vous ecrire "
                       "une longue lettre, je prefere vous montrer deux ou trois points "
                       "en direct, ca prend cinq minutes. Diagnostic gratuit, sans engagement.")
        if not constat:
            sautes += 1
            continue
        note = p.get("note")
        if note is not None and note >= 85:
            conserves += 1  # site propre, le constat dit "rien a reprocher" : utile aussi
        lines[idx] = constat
        new_body = "\n".join(lines)
        nouveau_objet = objet_pour(p)
        objet_change = False
        if nouveau_objet and clean(nouveau_objet) != clean(r.get("subject", "")):
            r["subject"] = clean(nouveau_objet)
            objet_change = True
        if new_body != body or objet_change:
            r["body"] = clean(new_body)
            injectes += 1
            if objet_change:
                objets += 1
            if len(exemples) < 3:
                exemples.append((num, p.get("domaine"), note,
                                 (r.get("subject", "")[:50] + " || " + constat[:60])))

    print("constats dispo: %d | mails injectes: %d | sites propres: %d | sautes: %d"
          % (len(preuves), injectes, conserves, sautes))
    for num, dom, note, c in exemples:
        print("  num %s (%s note %s): %s..." % (num, dom, note, c))

    if DRY:
        print("(dry-run, rien écrit)")
        return 0
    if injectes:
        shutil.copy(DATA, DATA + ".bak-preuves")
        json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("ECRIT: %s (backup .bak-preuves)" % DATA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
