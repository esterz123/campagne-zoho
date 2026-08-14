#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATEUR DM PERSONNALISE — chaque DM cite les FAITS REELS du compte.
=====================================================================
Contrairement aux templates par secteur, chaque message utilise les
stats reelles du compte Instagram de la cible (followers, posts) et son
activite precise pour creer un message UNIQUE.

Angles selon les stats reelles :
  - Compte avec beaucoup de posts mais peu de followers -> potentiel sous-exploite
  - Compte avec beaucoup de followers -> belle communaute, identite a la hauteur ?
  - Compte avec peu de posts -> presence en ligne quasi inexistante
  - Compte sans activite -> opportunite de se distinguer

Chaque DM respecte le skill outreach-messages-obligatoires :
  1. Nom du dirigeant en 1ere ligne
  2. Fait reel du compte (chiffres verifies)
  3. Probleme/opportunite concret
  4. Offre (diagnostic 79 EUR remboursable)
  5. CTA + portfolio
  6. ZERO tiret long

Usage : python3 generateur_dm_perso.py
"""
import json, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))

FEM = ("marie", "chloe", "chloé", "valerie", "valérie", "julie", "laurence", "mathilde",
       "stephanie", "stéphanie", "charlene", "charlène", "sophie", "anne", "celine",
       "céline", "isabelle", "nathalie", "sandra", "virginie", "emilie", "émilie",
       "audrey", "karine", "sandrine", "beatrice", "béatrice", "geraldine", "géraldine",
       "fatimata", "charlotte", "elodie", "élodie", "thi", "maria", "andrea", "alvaro",
       "justine", "kelly", "farida", "cecile", "cécilia", "sabrina", "melanie", "mélanie",
       "laetitia", "laëtitia", "amelie", "amélie", "florence", "helene", "hélène",
       "carine", "corinne", "veronique", "véronique", "dominique", "sandy", "aurore",
       "saerom", "yosra", "mitali", "sophie", "bich", "iasmina", "xiaoying", "marion",
       "setsuko", "stephanie", "farida", "sylvaine", "vanille", "evelyne", "vanessa")


def civ(dirigeant):
    parts = dirigeant.split()
    prenom, *rest = parts
    nom_fam = " ".join(rest) if rest else dirigeant
    return "%s %s" % ("Mme" if prenom.lower() in FEM else "M.", nom_fam)


def nb_vers_chiffre(s):
    """'8,915' -> 'pres de 9000' ; '67' -> '67'"""
    try:
        n = int(s.replace(",", "").replace(".", ""))
    except Exception:
        return s
    if n >= 10000:
        return "plus de %d" % (n // 1000 * 1000)
    if n >= 1000:
        return "pres de %d" % (n // 100 * 100)
    return str(n)


def generer_dm(d):
    """DM UNIQUE base sur les stats reelles du compte."""
    dir_nom = d.get("dirigeant", "")
    stats = d.get("stats", {})
    followers = stats.get("followers", "?")
    posts = stats.get("posts", "?")
    nom_affiche = stats.get("nom_affiche", "")
    secteur = d.get("secteur", "")

    try:
        n_followers = int(followers.replace(",", "").replace(".", ""))
    except Exception:
        n_followers = -1
    try:
        n_posts = int(posts.replace(",", "").replace(".", ""))
    except Exception:
        n_posts = -1

    # ==== Angle selon les stats reelles ====
    if 0 <= n_followers <= 100:
        angle = ("votre compte Instagram est encore discret (%s abonnes, %s publications). "
                 "C'est dommage car c'est aujourd'hui la premiere chose que vos futurs clients "
                 "regardent avant de vous choisir, et un compte qui ne tourne pas donne "
                 "l'impression d'un salon moins actif qu'il ne l'est reellement." % (nb_vers_chiffre(followers), nb_vers_chiffre(posts)))
    elif n_posts == 0:
        angle = ("votre compte Instagram ne publie pas encore, alors que vos clientes le "
                 "consultent pour juger votre travail avant de reserver. Chaque realisation "
                 "que vous montrez est une cliente qui vous choisit plutot qu'un concurrent.")
    elif n_followers > 5000:
        angle = ("vous avez deja une belle communaute (%s abonnes), c'est un vrai actif. "
                 "Mais une communaute ne convertit que si l'identite visuelle et la coherence "
                 "des publications donnent envie de passer a l'action, et c'est souvent ce "
                 "qui manque dans ce secteur." % nb_vers_chiffre(followers))
    else:
        angle = ("votre compte a %s abonnes et %s publications. C'est une base, mais sans "
                 "une identite visuelle qui marque et un message clair, ces abonnes ne se "
                 "transforment pas en clients qui poussent la porte." % (nb_vers_chiffre(followers), nb_vers_chiffre(posts)))

    offre = ("Je suis designer de marque, et je peux vous montrer concretement ce que je "
             "ferais pour rendre votre presence en ligne aussi soignee que votre travail, "
             "avec un exemple adapte a votre activite. Si vous voulez, je vous prepare un "
             "diagnostic complet en 48h (79 EUR, rembourse si vous n'y trouvez pas de "
             "valeur), vous gardez le document dans tous les cas.\n\n"
             "Ca vous interesse que je vous prepare une piste ?\n\n"
             "Portfolio : mahdi-design.com")

    msg = "Bonjour %s,\n\n%s\n\n%s" % (civ(dir_nom), angle, offre)
    msg = msg.replace("—", ",").replace("–", ",")
    return msg


def main():
    dms = json.load(open(os.path.join(BASE, "kit_dm_masse.json"), encoding="utf-8"))
    dms = [d for d in dms if d.get("stats") and d.get("dirigeant")]
    for d in dms:
        d["dm"] = generer_dm(d)
    json.dump(dms, open(os.path.join(BASE, "kit_dm_masse.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("%d DM PERSONNALISES (stats reelles) generes" % len(dms))
    # Verifier que les messages sont uniques
    corps = [d["dm"][:60] for d in dms]
    uniques = len(set(corps))
    print("Debut de messages differents: %d/%d" % (uniques, len(dms)))
    if dms:
        print("\n=== APERCU (%s) ===" % dms[0]["nom"][:40])
        print(dms[0]["dm"][:350])


if __name__ == "__main__":
    sys.exit(main())
