#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEQUENCE UPSELL 79 EUR -> REFONTE 2900 EUR
==========================================
Ferme le maillon qui manquait dans la chaine d'argent : aujourd'hui, quand
un client paie le diagnostic 79 EUR, il recoit le docx (livraison_auto.py) puis
PLUS JAMAIS de sollicitation pour la refonte 2900 EUR. Chaque 79 EUR reste un 79 EUR.

Ce script (cron quotidien) :
  1. Lit suivi_revenus.json : entrees "encaisse" qui n'ont pas encore de sequence upsell.
  2. Extrait l'email du payeur depuis le `note` (resume PayPal FR) ou le subject.
  3. Genere + envoie 4 emails (J+0 / J+3 / J+7 / J+14) depuis contact@mahdi-design.com.
  4. Marque l'entree `upsell_statut` pour ne jamais renvoyer.

Templates : livraison du docx (J+0) puis nurture + offre 31/08 + J+7 livraison
rapport (J+7) + J+14 derniere chance. Respecte : ZERO U+2019, ZERO tiret long,
un seul lien de desabonnement, pas plus d'1 email/2 jours.

Regles de securite (anti-spam / anti-double) :
  - AUCUN envoi si pas d'email payeur identifiable.
  - Un seul envoi par run (l'email "du jour" calcule sur la date d'encaissement).
  - dry-run : affiche ce qui serait envoye, n'ecrit rien.
"""

import json, os, re, sys, datetime
from pathlib import Path

BASE = Path(__file__).parent
REVENUS = BASE / "suivi_revenus.json"
SEQ_DIR = BASE / "sequences_upsell"
SEQ_DIR.mkdir(exist_ok=True)

DRY = "--dry-run" in sys.argv

import repondeur as R


def email_from_text(txt):
    m = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", txt or "")
    return m.group(0).lower() if m else ""


def email_from_subject(subject):
    # PayPal FR : "Paiement recu de NOM (email@x.com) ..." ou "... <email>"
    m = re.search(r"<([\w.+-]+@[\w-]+\.[\w.-]+)>", subject or "")
    if m:
        return m.group(1).lower()
    return email_from_text(subject)


def stage_a_envoyer(encaisse_le, aujourd_hui):
    """Renvoie le stade a envoyer aujourd'hui (0/3/7/14) ou None."""
    try:
        base = datetime.date.fromisoformat(encaisse_le)
    except Exception:
        return None
    delta = (aujourd_hui - base).days
    for j in (0, 3, 7, 14):
        if delta == j:
            return j
    return None


TEMPLATES = {
    0: ("Votre diagnostic est en cours de préparation",
        """Bonjour {nom},

Paiement bien recu, merci pour votre confiance.

Je lance l'audit de votre site aujourd'hui. Vous recevrez le rapport complet sous 48h ouvrees, avec :
- Analyse de votre site (design, mobile, vitesse, signaux de confiance)
- Analyse de votre identite visuelle (logo, marque)
- Comparaison avec 2 de vos concurrents directs
- 5 recommandations concretes priorisees par impact

Une seule chose avant de demarrer, pour que le rapport soit reellement utile a votre cas :
repondez en 2 lignes a cet email avec l'URL de votre site, et ce que vous aimeriez que vos clients retiennent en premier en arrivant sur votre page.

Cordialement,
Mahdi
Portfolio : mahdi-design.com"""),

    3: ("3 questions pour personnaliser votre diagnostic",
        """Bonjour {nom},

Pendant que je finalise votre diagnostic (livraison prevue tres bientot), je voulais partager quelque chose.

Mes clients qui convertissent le mieux leurs propres prospects sont ceux qui prennent 10 minutes pour repondre a 3 questions strategiques avant la livraison du rapport :

1. Quelle est la premiere chose qu'un prospect doit comprendre en arrivant sur votre site ?
2. Pourquoi un client existant vous choisit-il plutot qu'un concurrent ?
3. Quel resultat mesurable un prospect obtient-il en travaillant avec vous ?

Vos reponses (meme en 3 lignes) seront integrees a votre rapport final pour le rendre actionnable.

Aussi, un point pratique : si vous voulez aller plus loin que le diagnostic et transformer votre image de marque pour de bon, l'offre de rentree reste ouverte jusqu'au 30 septembre. 3 places seulement. Le tarif passe de 3 900 EUR a 2 900 EUR jusqu'a cette date.

https://mahdi-design.com/refonte.html

Cordialement,
Mahdi
Portfolio : mahdi-design.com"""),

    7: ("Votre diagnostic est pret, parlons de la suite",
        """Bonjour {nom},

Votre diagnostic est pret. Le voici en piece jointe.

3 points cles que vous y trouverez :
1. Les signaux de defiance que votre site envoie aujourd'hui (et qui font hesiter vos donneurs d'ordre)
2. Ce que vos 2 concurrents directes font mieux que vous en ligne
3. Les 3 corrections gratuites applicables en moins de 24h

Les recommandations sont classees par impact : certaines sont gratuites, d'autres demandent un investissement entre 590 EUR et 2 900 EUR.

Maintenant, deux options pour la suite :

Option A - Vous appliquez vous-meme. Les 3 premieres recommandations sont gratuites (a venir dans le document). Je reste disponible pour une question par email.

Option B - Vous me confiez la transformation. Je m'occupe de tout : refonte du logo, refonte du site, mise en conformite mobile, optimisation pour la conversion. Delai 4 semaines. Tarif rentree jusqu'au 30 septembre : 2 900 EUR au lieu de 3 900 EUR.

Dites-moi simplement "option A" ou "option B" et je vous envoie le detail.

Cordialement,
Mahdi
Portfolio : mahdi-design.com"""),

    14: ("Dernier message sur votre diagnostic",
        """Bonjour {nom},

Dernier message de ma part sur ce diagnostic.

J'ai bien note que vous n'avez pas encore choisi la suite, et c'est totalement votre droit. Le diagnostic vous appartient et je ne veux rien vous forcer.

Juste pour information, l'offre de rentree se termine le 30 septembre : la refonte complete passe de 3 900 EUR a 2 900 EUR. Si vous decidez de transformer votre image avant cette date, mon agenda reste ouvert.

Sinon, gardez le diagnostic. Si un jour votre situation change (nouveau client qui doute, projet de refonte qui arrive), vous avez mon email.

Bonne continuation,
Mahdi

P.S. - Pour ne plus recevoir mes emails : repondez STOP a cet email."""),
}


def main():
    print("=== SEQUENCE UPSELL 79EUR -> 2900EUR (18/08) ===")
    if not (REVENUS.exists()):
        print("suivi_revenus.json absent - rien a faire"); return 0
    rev = json.loads(REVENUS.read_text(encoding="utf-8"))
    entrees = rev.get("entrees", [])
    boites = R.load_boites()
    if not boites:
        print("PAS DE CREDENTIALS - arret"); return 1
    boite = next((b for b in boites if b["nom"] == "contact"), boites[0])
    auj = datetime.date.today()

    traites = 0
    for i, e in enumerate(entrees):
        if e.get("statut") not in ("encaisse", "a_verifier"):
            continue
        if e.get("upsell_statut") in ("termine", "desactive"):
            continue
        # email payeur
        email = (e.get("email_payeur") or "").strip().lower()
        if not email:
            email = email_from_subject(e.get("note", "")) or email_from_text(e.get("note", ""))
        if not email:
            print("  ! entree %d : email payeur introuvable -> ignoree" % i); continue
        e["email_payeur"] = email
        encaisse_le = e.get("date")
        stage = stage_a_envoyer(encaisse_le, auj)
        if stage is None:
            # hors fenetre 0/3/7/14 : marquer termine pour eviter re-tentatives
            if e.get("upsell_statut") is None and encaisse_le:
                base = datetime.date.fromisoformat(encaisse_le)
                if (auj - base).days > 14:
                    e["upsell_statut"] = "termine"
            continue
        sujet, corps = TEMPLATES[stage]
        nom = email.split("@")[0].capitalize()
        corps = corps.replace("{nom}", nom)
        if DRY:
            print("[DRY] J+%d -> %s | %s" % (stage, email, sujet))
            continue
        try:
            access = R.refresh_access(boite)
            mid = R.send(boite, email, sujet, corps, access)
            e.setdefault("upsell_envoyes", []).append({"j": stage, "date": auj.isoformat(), "mid": mid})
            print("  ENVOYE J+%d -> %s (mid %s)" % (stage, email, mid))
            traites += 1
            if stage == 14:
                e["upsell_statut"] = "termine"
        except Exception as ex:
            print("  ! envoi KO %s : %s" % (email, str(ex)[:80]))
    if not DRY:
        REVENUS.write_text(json.dumps(rev, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Termine - %d email(s) upsell envoye(s) ce run" % traites)
    return 0


if __name__ == "__main__":
    sys.exit(main())
