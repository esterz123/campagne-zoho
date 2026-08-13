#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATEUR DE DM URGENCE — Instagram + X (Twitter) pour sites piratés/vulnérables.
================================================================================
Pourquoi : LinkedIn est ecarte (localisation Algerie visible, peur du drop).
Instagram + X = pas de localisation visible, DM directs, zero warm-up.

Cible : les entreprises de urgence_securite.json (sites PIRATES / WP_OBSOLETE).
L'angle : URGENCE + peur (leurs clients voient le probleme) + offre simple.

Usage :
  python3 dm_urgence.py                  # genere messages_dm_urgence.json
  python3 dm_urgence.py --liste          # affiche la liste des cibles avec leur DM
  python3 dm_urgence.py --print <n>      # affiche le DM n°n (a copier-coller)

Les DM sont generes avec les vrais constats du scan (pas de blabla).
"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))


def charger_cibles():
    try:
        with open(os.path.join(BASE, "urgence_securite.json"), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Fichier urgence_securite.json introuvable. Lance d'abord : python3 scan_urgence.py")
        sys.exit(1)


def generer_dm(c, insta_handle=""):
    """Cree le DM pour une cible. Angle urgence + constat reel + offre simple."""
    nom = c.get("nom", "votre entreprise")
    probleme = c["probleme"]
    details = c.get("details", [])
    site = c.get("site") or c.get("url", "")  # url = le vrai domaine (site peut etre vide)

    if probleme == "PIRATE":
        accroche = ("Votre site %s affiche des liens de fraude et du spam "
                    "(casino, contenus en coreen/chinois) visibles par vos clients." % site)
        offre = ("Je peux nettoyer votre site et le securiser dans la semaine, "
                 "150 EUR l'intervention, puis 79 EUR/mois pour le surveiller "
                 "et le proteger. Sans engagement, je vous montre d'abord ce "
                 "que j'ai trouve.")
    elif probleme == "WP_OBSOLETE":
        accroche = ("Votre site tourne sur un WordPress obsolete, avec des "
                    "vulnerabilites connues non corrigees. Un hacker peut le "
                    "prendre en 30 minutes.")
        offre = ("Je peux le mettre a jour et le securiser : intervention "
                 "150 EUR, puis 79 EUR/mois pour les mises a jour et la "
                 "surveillance. Je vous montre d'abord les failles.")
    else:
        accroche = ("J'ai regarde votre site %s : %s" % (site, details[0] if details else "il a besoin d'une mise a jour."))
        offre = ("Je peux le moderniser et le securiser. On en parle 5 minutes ?")

    return {
        "instagram": (
            "Bonjour%s, %s\n\n"
            "%s\n\n"
            "Je suis Mahdi, je securise et modernise les sites de PME. "
            "Je peux vous montrer ce que j'ai trouve, sans engagement.\n\n"
            "Passez une bonne journee." % (
                " " + insta_handle if insta_handle else "",
                accroche, offre))
        ,
        "x": (
            "Bonjour%s, %s\n\n"
            "%s\n\n"
            "Je suis Mahdi, je securise les sites de PME. "
            "Je peux vous montrer ce que j'ai trouve, sans engagement." % (
                " " + insta_handle if insta_handle else "",
                accroche, offre))
    }


def main():
    cibles = charger_cibles()
    if not cibles:
        print("Aucune cible a probleme. Le scan n'a rien trouve ou pas encore tourne.")
        return

    args = sys.argv[1:]
    if "--liste" in args:
        for i, c in enumerate(cibles):
            email = c.get("email", "") or "pas d'email"
            print("%2d. [%s] %s | %s | email: %s" % (i, c["probleme"], c["nom"][:35], c["site"], email))
        print("\nUtilise --print <n> pour voir le DM complet d'une cible.")
        return

    if "--print" in args:
        idx = int(args[args.index("--print") + 1])
        c = cibles[idx]
        dms = generer_dm(c)
        print("=== CIBLE %d: %s (%s) ===" % (idx, c["nom"], c["site"]))
        print("\n--- INSTAGRAM ---\n" + dms["instagram"])
        print("\n--- X (TWITTER) ---\n" + dms["x"])
        return

    # Generation complete
    messages = []
    for c in cibles:
        dms = generer_dm(c)
        messages.append({
            "nom": c["nom"], "site": c.get("site") or c.get("url", ""), "email": c.get("email", ""),
            "probleme": c["probleme"], "instagram": dms["instagram"], "x": dms["x"]
        })
    with open(os.path.join(BASE, "messages_dm_urgence.json"), "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=1)
    print("%d DM d'urgence generes -> messages_dm_urgence.json" % len(messages))
    print("Pour envoyer : copie le DM, colle-le dans le DM Instagram ou X de l'entreprise.")
    print("Astuce : cherche le compte Instagram/X de l'entreprise via son site (footer/social links).")


if __name__ == "__main__":
    main()
