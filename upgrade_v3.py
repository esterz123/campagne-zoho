#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regénère le corps V3 (percutant) pour tous les prospects de campagne_data.json.
V3 = preuve + urgence + CTA trivial (repondre oui). Pas de 'probablement' vague.
Garde le subject existant. Sauvegarde _bak avant ecrasement."""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
data = json.load(open(DATA, encoding="utf-8"))

def corps_v3(nomfam, act, dom):
    metier = act if act != "industrielle" else "industrielle"
    return (
        "Bonjour M. %s,\n\n"
        "Votre site %s n'apparait pas quand un donneur d'ordres cherche \"%s\" sur Google. "
        "Vos concurrents qui ont refait leur site il y a 2 ans sont devant vous sur ces requetes : "
        "c'est eux qui prennent les appels, pas vous.\n\n"
        "Je ne vous vends rien ici. Je regarde votre site 2 minutes et je vous dis exactement ce que "
        "vos prospects fuient (vitesse, mobile, confiance). C'est gratuit, sans engagement.\n\n"
        "Repondez simplement \"oui\" a ce mail et je vous envoie mes constats sous 48h.\n\n"
        "Cordialement,\nMahdi\nPortfolio : mahdi-design.com"
    ) % (nomfam, dom, metier)

import re
for e in data:
    dom = e.get("site", "").replace("https://", "").replace("http://", "").rstrip("/")
    if not dom:
        dom = (e.get("to", "").split("@")[-1] if e.get("to") else "")
    # nom de famille du dirigeant ou du nom
    dirg = e.get("dirigeant", "") or e.get("nom", "")
    m = re.search(r"([A-ZÀ-ÜÉÈ]+)\s*$", dirg.strip())
    nomfam = m.group(1).title() if m else e.get("nom", "Madame, Monsieur").split()[-1].title()
    act = e.get("activite", "industrielle")
    if act in ("", None):
        act = "industrielle"
    old = e.get("body", "")
    # V3 pour tous (sauf deja V3)
    if "n'apparait pas quand un donneur" not in old:
        e["body"] = corps_v3(nomfam, act, dom)

json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("V3 applique sur %d prospects" % len(data))
