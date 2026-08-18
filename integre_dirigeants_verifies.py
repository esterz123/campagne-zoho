#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integre les 30 prospects verifies (emails_dirigeants_verifies.json) dans campagne_data.json.
Chaque entree : nom_entreprise, dirigeant (NOM PRENOM), domaine (site), emails (dict variantes).
On prend la 1re variante d'email, on dedup contre la file, on genere le message V2 + constats."""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
SRC = os.path.join(BASE, "..", "emails_dirigeants_verifies.json")

data = json.load(open(DATA, encoding="utf-8"))
src = json.load(open(SRC, encoding="utf-8"))

file_emails = {(e.get("to") or "").lower() for e in data}
file_noms = {e.get("nom", "").lower() for e in data}
next_num = max((e.get("num", 0) for e in data), default=0) + 1

ACTIVITES = {
    "simi": "plasturgie", "rouxel": "moules injection", "milmeca": "mecanique",
    "brugiere": "outillage", "usimeca": "usinage", "desjardins": "decolletage",
    "axil": "plasturgie", "fonderie": "fonderie", "tolerie": "tolerie",
    "decolletage": "decolletage", "elcam": "usinage", "atelierphysis": "atelier",
}
def activite(dom):
    for k, v in ACTIVITES.items():
        if k in dom: return v
    return "industrielle"

added = 0
for r in src:
    ems = r.get("emails", {})
    em = list(ems.values())[0] if ems else ""
    if not em: continue
    if (em.lower() in file_emails) or (r.get("nom_entreprise", "").lower() in file_noms):
        continue
    nom = r["nom_entreprise"]
    dirg = r.get("dirigeant", "")
    # nom de famille = dernier mot en MAJUSCULES
    m = re.search(r"([A-ZÀ-ÜÉÈ]+)\s*$", dirg.strip())
    nomfam = m.group(1).title() if m else dirg.split()[-1].title() if dirg else "Madame, Monsieur"
    dom = r.get("domaine", "")
    act = activite(dom)
    msg = (
        "Bonjour M. %s,\n\n"
        "Je suis Mahdi, brand designer specialise dans les PME %s francaises.\n\n"
        "Votre site %s date probablement de plusieurs annees : sur mobile il pique les yeux, "
        "Google ne le propose pas aux prospects qui cherchent votre metier, et votre identite "
        "ne rassure plus les donneurs d'ordres qui comparent.\n\n"
        "Je propose un diagnostic offert de votre site (ce qui fuit, ce que vos concurrents ont deja corrige), "
        "puis une refonte complete marque + site a partir de 2900 euros. Vous gardez votre nom, vous changez d'ere.\n\n"
        "Si vous voulez voir ce que je vois sur votre site en 2 minutes, repondez simplement a ce mail "
        "et je vous envoie le diagnostic.\n\n"
        "Cordialement,\nMahdi\nPortfolio : mahdi-design.com"
    ) % (nomfam, act, dom)
    data.append({
        "num": next_num, "nom": nom, "to": em, "prenom": "",
        "siren": "", "site": "https://" + dom if dom else "",
        "activite": act, "dirigeant": dirg,
        "subject": "Votre site %s date : diagnostic offert" % dom,
        "body": msg, "source": "dirigeants_verifies",
    })
    next_num += 1
    added += 1

json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("INTEGRE %d nouveaux prospects (total file: %d)" % (added, len(data)))
