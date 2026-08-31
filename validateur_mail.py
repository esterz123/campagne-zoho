#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VALIDATEUR MAIL - contrôle les règles d'or outreach AVANT tout envoi.
=====================================================================
Règles vérifiées (issues de la chartre Mahdi, skill outreach-messages-obligatoires) :
  R1  Bonjour + nom réel (M./Mme + NOM), jamais "Bonjour," sec si un nom existe
  R2  Zéro tiret long (— –) dans sujet et corps (fait "trop IA")
  R3  Zéro apostrophe typographique U+2019 (le cloud Zoho la rejette)
  R4  "mahdi-design.com" présent dans le corps (portfolio en fin)
  R5  Le corps parle du prospect dès la 1re ligne (son site ou son nom apparaît)
  R6  Pas de promesse Google non vérifiée si un constat mesuré existe (préfixe
      "J'ai ouvert/tape" attendu quand constats_sites.json couvre le num)
Usage : python3 validateur_mail.py            -> rapport sur les non-encore-envoyés
        python3 validateur_mail.py --all      -> toute la file
Exit code 1 si au moins une violation bloquante (R2/R3/R4).
"""
import os
import re
import sys
import json

BASE = os.path.dirname(os.path.abspath(__file__))
BLOQUANTS = 0


def check(r, preuve):
    num = str(r.get("num"))
    corps = r.get("body", "")
    sujet = r.get("subject", "")
    lignes = [l.strip() for l in corps.split("\n") if l.strip()]
    pb = []
    if not lignes:
        return ["CORPS VIDE"]
    premiere = lignes[0]
    # R1 nom
    if re.match(r"^Bonjour,?$", premiere, re.I):
        pb.append("R1 salut sans nom")
    # R2 tirets longs
    if re.search(r"[\u2013\u2014]", corps + sujet):
        pb.append("R2 tiret long")
    # R3 U+2019
    if "\u2019" in corps + sujet:
        pb.append("R3 apostrophe typographique")
    # R4 portfolio
    if "mahdi-design.com" not in corps:
        pb.append("R4 portfolio absent")
    # R5 1re phrase personnalisée (nom ou domaine cités dans les 2 premières lignes)
    debut = " ".join(lignes[:2]).lower()
    dom = (r.get("site") or "").lower().replace("https://", "").replace("http://", "").replace("www.", "")
    nom = (r.get("prospect") or "").lower()[:12]
    if dom and dom.split("/")[0] not in debut and (not nom or nom.split()[0] not in debut):
        pb.append("R5 premiere ligne non personnalisee")
    # R6 preuve obligatoire si on a un constat mesuré
    if preuve and preuve.get("constat"):
        c2 = lignes[1] if len(lignes) > 1 else ""
        if not re.match(r"^J'ai (ouvert|tape|cherche|verifie|pass)", c2, re.I):
            pb.append("R6 constat mesure non injecte")
    return pb


def main():
    global BLOQUANTS
    data = json.load(open(os.path.join(BASE, "campagne_data.json"), encoding="utf-8"))
    state = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))
    preuves = {}
    p = os.path.join(BASE, "constats_sites.json")
    if os.path.exists(p):
        preuves = json.load(open(p, encoding="utf-8"))
    sent = set(str(k) for k in state.get("sent", {}))
    cible = data if "--all" in sys.argv else [r for r in data if str(r.get("num")) not in sent]
    ok = 0
    vides = 0
    par_regle = {}
    for r in cible:
        pb = check(r, preuves.get(str(r.get("num"))))
        if pb == ["CORPS VIDE"]:
            vides += 1
            continue
        if pb:
            for x in pb:
                par_regle[x.split()[0]] = par_regle.get(x.split()[0], 0) + 1
            if len([x for x in pb if x[1] in "234"]) > 0:
                BLOQUANTS += 1
            if len(par_regle) <= 8 and vides + ok < 40:
                print("num %s: %s" % (r.get("num"), "; ".join(pb)))
        else:
            ok += 1
    print("\n=== VALIDATION %d mails ===" % len(cible))
    print("CONFORMES: %d | corps vides: %d | avec alerte: %d" % (ok, vides, len(cible) - ok - vides))
    print("par regle:", dict(sorted(par_regle.items())))
    print("VIOLATIONS BLOQUANTES (R2/R3/R4): %d" % BLOQUANTS)
    return 1 if BLOQUANTS else 0


if __name__ == "__main__":
    sys.exit(main())
