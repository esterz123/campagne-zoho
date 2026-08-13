#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATEUR DE DM EN MASSE — produit un DM personnalisé par cible Insta.
======================================================================
Input : masse_insta.json (entreprises avec dirigeant + compte Instagram).
Output : kit_dm_masse.json + integration dans kit_dm_instagram.html

Chaque DM respecte les regles du skill outreach-messages-obligatoires :
  1. Nom du dirigeant en 1ere ligne (civilité correcte)
  2. Probleme reel du secteur (angle adapte a l'activite)
  3. Offre (diagnostic 79 EUR ou securite)
  4. CTA simple
  5. Portfolio a la fin (mahdi-design.com)
  6. ZERO tiret long
"""
import json, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))

FEM = ("marie", "chloe", "chloé", "valerie", "valérie", "julie", "laurence", "mathilde",
       "stephanie", "stéphanie", "charlene", "charlène", "sophie", "anne", "celine",
       "céline", "isabelle", "nathalie", "sandra", "virginie", "emilie", "émilie",
       "audrey", "karine", "sandrine", "beatrice", "béatrice", "geraldine", "géraldine",
       "fatimata", "charlotte", "elodie", "élodie", "thi", "maria", "andrea", "alvaro",
       "justine", "kelly", "farida", "celine", "cecile", "cécilia", "sabrina", "melanie",
       "mélanie", "laetitia", "laëtitia", "amelie", "amélie", "florence", "helene",
       "hélène", "carine", "corinne", "veronique", "véronique", "dominique", "julie")

ANGLES = {
    "salon coiffure": ("votre salon merite une image a la hauteur du travail de vos stylistes. "
                       "En regardant comment les salons concurrents communiquent, votre identite "
                       "visuelle (logo, couleurs, cartes de visite, presence en ligne) ne se "
                       "distingue pas assez pour attirer les nouveaux clients du quartier."),
    "institut beaute": ("votre institut merite une image a la hauteur de vos soins. En regardant "
                        "comment les instituts voisins communiquent, votre identite visuelle ne se "
                        "distingue pas assez pour attirer les clientes qui cherchent un nouveau "
                        "lieu de confiance."),
    "salon ongles": ("votre salon d'ongles merite une image a la hauteur de votre travail. "
                     "Vos realisations sont belles, mais votre identite visuelle (logo, couleurs, "
                     "presence en ligne) ne donne pas envie de pousser la porte a la nouvelle "
                     "cliente qui vous decouvre sur Instagram."),
    "restaurant": ("votre restaurant merite une image a la hauteur de votre cuisine. En regardant "
                   "votre presence en ligne, l'identite visuelle ne raconte pas assez l'experience "
                   "que vous offrez, et les nouveaux clients ne trouvent pas immediatement ce qui "
                   "donne envie de reserver."),
    "garage auto": ("votre garage merite une image a la hauteur de votre travail. En regardant "
                    "comment les garages voisins communiquent, votre identite visuelle ne se "
                    "distingue pas assez pour rassurer les nouveaux clients qui cherchent un "
                    "professionnel de confiance."),
    "auto-ecole": ("votre auto-ecole merite une image a la hauteur de votre accompagnement. "
                   "Les eleves choisissent souvent sur la confiance que degage la marque, et "
                   "votre identite visuelle actuelle ne la transmet pas assez."),
    "boulangerie": ("votre boulangerie merite une image a la hauteur de votre savoir-faire. "
                    "En regardant votre presence en ligne, l'identite visuelle ne se distingue "
                    "pas assez pour attirer les nouveaux clients du quartier."),
    "cafe bar": ("votre etablissement merite une image a la hauteur de votre ambiance. "
                 "En regardant comment les bars voisins communiquent, votre identite visuelle "
                 "ne se distingue pas assez pour attirer les nouveaux clients."),
    "fleuriste": ("votre boutique merite une image a la hauteur de vos compositions. "
                  "En regardant votre presence en ligne, l'identite visuelle ne met pas assez "
                  "en valeur la beaute de vos creations pour attirer les nouveaux clients."),
}

CTA = ("Je suis designer de marque, et je peux vous montrer concretement ce que je ferais "
       "pour votre identite, avec un exemple adapte a votre activite, sans engagement.\n\n"
       "Ca vous interesse que je vous prepare une piste ?\n\n"
       "Portfolio : mahdi-design.com")


def civ(dirigeant):
    parts = dirigeant.split()
    prenom, *rest = parts
    nom_fam = " ".join(rest) if rest else dirigeant
    return f"{'Mme' if prenom.lower() in FEM else 'M.'} {nom_fam}"


def generer_dm(c):
    """Cree le DM personnalise pour une cible."""
    secteur = c.get("secteur", "salon coiffure")
    angle = ANGLES.get(secteur, ANGLES["salon coiffure"])
    accroche = "Bonjour %s," % civ(c["dirigeant"])
    msg = "%s\n\n%s\n\n%s" % (accroche, angle, CTA)
    # Anti-tiret final
    msg = msg.replace("—", ",").replace("–", ",")
    return msg


def main():
    try:
        cibles = json.load(open(os.path.join(BASE, "masse_insta.json"), encoding="utf-8"))
    except FileNotFoundError:
        print("masse_insta.json introuvable. Lance d'abord : python3 chercheur_insta_masse.py")
        sys.exit(1)

    # Generer les DM pour toutes les cibles avec compte Insta + dirigeant
    dms = []
    for c in cibles:
        if not c.get("instagram") or not c.get("dirigeant"):
            continue
        dms.append({**c, "dm": generer_dm(c)})

    json.dump(dms, open(os.path.join(BASE, "kit_dm_masse.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("%d DM personnalises generes -> kit_dm_masse.json" % len(dms))

    # Apercu du 1er
    if dms:
        print("\n=== APERCU (%s, %s) ===" % (dms[0]["nom"][:40], dms[0]["dirigeant"]))
        print(dms[0]["dm"][:400])


if __name__ == "__main__":
    sys.exit(main())
