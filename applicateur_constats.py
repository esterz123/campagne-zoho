#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APPLICATEUR DE CONSTATS — ecrit les DM a constat reel pour les sites vision_confirme.
====================================================================================
Usage : python3 applicateur_constats.py  -> applique CONSTATS du dict ci-dessous
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "kit_dm_masse.json")

# constat par website — a remplir apres chaque batch de vision
CONSTATS = {
    "https://epilnet.fr": "votre page d'accueil est epuree et le logo est lisible, mais aucun tarif, aucun avis client ni resultat avant/apres n'y figure. Pour une prestation a forte valeur comme l'epilation definitive, une cliente doit appeler ou prendre RDV avant de connaitre le moindre prix : c'est un frein a la decision face a la concurrence qui affiche tout.",
    "https://le20barbershop.fr": "le site met en avant vos deux adresses du 6e (Croix-Rousse et Franklin Roosevelt), mais ne montre ni tarifs, ni horaires, ni avis clients. Un client qui hesite entre plusieurs barbershops reserve chez celui qui affiche ses prix et ses preuves.",
}

def appliquer():
    d = json.load(open(PATH, encoding="utf-8"))
    n = 0
    for x in d:
        w = x.get("website") or ""
        if w in CONSTATS and (x.get("site_provenance") in ("vision_confirme", "vision_probable")):
            constat = CONSTATS[w]
            nom_prop = (x.get("dirigeant") or "").strip()
            salutation = f"Bonjour {nom_prop}," if nom_prop else "Bonjour,"
            x["constat_site"] = constat
            x["dm"] = (
                f"{salutation}\n\n"
                f"Je suis designer de marque, et en regardant votre site {w.replace('https://', '')} : {constat} "
                f"Concretement, ca vous coute des clients qui hesitent.\n\n"
                f"Je peux vous preparer un diagnostic complet en 48h (79 EUR, rembourse si vous n'y trouvez pas de valeur) : "
                f"analyse de votre image, de votre site et des actions concretes pour convertir plus de visiteurs en clients.\n\n"
                f"Vous etes disponible pour un echange de 15 minutes cette semaine ?"
            )
            n += 1
    json.dump(d, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"DM reecrits pour {n} sites (constats appliques).")

if __name__ == "__main__":
    appliquer()
