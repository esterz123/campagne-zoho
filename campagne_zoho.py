#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Campagne emails Zoho — envoi automatise depuis contact@mahdi-design.com
Fonctionne EN LOCAL (PC de Mahdi) ET DANS LE CLOUD (GitHub Actions, PC eteint).

Usage:
    python campagne_zoho.py            # envoi selon le quota (3/jour)
    python campagne_zoho.py 5          # quota a 5/jour
    python campagne_zoho.py --dry-run  # montre ce qui serait envoye, sans envoyer
"""
import os
import json
import sys
import time
import datetime
import urllib.request
import urllib.parse

# Chemins relatifs au script -> marche partout (local comme cloud)
BASE = os.path.dirname(os.path.abspath(__file__))
TOKENS = os.path.join(BASE, ".zoho_tokens.json")
DATA = os.path.join(BASE, "campagne_data.json")
STATE = os.path.join(BASE, "campagne_state.json")

ACCOUNT_ID = "7349712000000008002"
FROM = "contact@mahdi-design.com"
DAILY_MAX = 25  # 5 boites : contact 5/jour + 4 boites neuves 3/jour (warm-up), rotation 15/08

# ---- VERROU ANTI-ERREUR (garde-fou permanent) ----
# Un email dont le domaine est ici est un PIEGE (annuaire/scraper/mail gratuit/
# relais technique/mismatch). Le script REFUSE de l'envoyer : ca protegerait le
# domaine mahdi-design.com d'un bounce = blacklist. Liste dans domaines_bloques.json
BLOQUES = os.path.join(BASE, "domaines_bloques.json")

def load_bloquees():
    """Domaines a ne JAMAIS contacter (annuaires, scrapers, mails gratuits)."""
    try:
        with open(BLOQUES, encoding="utf-8") as f:
            j = json.load(f)
        return [d.lower() for d in j.get("bloques", [])]
    except Exception:
        return []

def domaine_bloque(to, bloquees):
    """True si l'email cible est sur un domaine piege."""
    if not to or "@" not in to:
        return True  # pas d'adresse = on ne sait pas envoyer = on bloque
    dom = to.split("@")[1].lower()
    for b in bloquees:
        if dom == b or dom.endswith("." + b):
            return True
    return False

SIG = ("Mahdi<br>"
       "Brand Designer &mdash; Identit&eacute; visuelle &amp; sites web pour PME<br>"
       "Portfolio : <a href=\"https://mahdi-design.com\">mahdi-design.com</a><br>"
       "contact@mahdi-design.com")


def body_to_html(text):
    """Convertit le corps (texte avec \\n et **bold**) en HTML lisible pour Zoho."""
    import re
    # markdown **gras** -> <strong>
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # lignes
    lines = text.split("\n")
    html = []
    para = []
    for ln in lines:
        if ln.strip() == "":
            if para:
                html.append("<p>" + "<br>".join(para) + "</p>")
                para = []
        else:
            para.append(ln)
    if para:
        html.append("<p>" + "<br>".join(para) + "</p>")
    return "\n".join(html)

