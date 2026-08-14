#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REECRITURE DM A FAITS VERIFIES — constats 100% verifies (HTML reel + vision fullpage).
======================================================================================
REGLE D'OR : AUCUN constat negatif ("il n'y a pas X") sans preuve. On ne parle que
de ce qui est VERIFIE : elements presents (design, reservation, prix, horaires, avis)
et on pose une question de conversion.
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "kit_dm_masse.json")

# constats VERIFIES (HTML + vision) par website
CONSTATS = {
    # Lenoir : WP 5.3.2 verifie (generateur origine) + contact present
    "https://lenoirhandiconcept.com": "j'ai remarqué que votre site tourne sur WordPress 5.3.2, une version sortie fin 2019 qui ne reçoit plus de correctifs de sécurité depuis plusieurs années. Pour une entreprise qui accompagne des personnes en situation de handicap, c'est un risque sérieux : un site vulnérable peut être piraté, et vos clients ont besoin de vous faire confiance.",
    # Skinarium : design elegant (vision) + reservation presente (HTML: 'reserv')
    "https://skinarium.fr": "votre site est très élégant et soigné, avec un système de réservation bien intégré. En tant que designer, je me suis demandé : est-ce que tous vos visiteurs qui hésitent entre plusieurs instituts deviennent vraiment des clients, ou repartent-ils vers un concurrent avant de réserver ?",
    # Cryo-Spirit : tarifs + rdv + horaires presents (HTML verifie), design moderne (vision) mais logo lotus volumineux
    "https://cryospirit.fr": "votre site affiche clairement vos tarifs, vos horaires et votre système de rendez-vous : c'est un vrai point fort. J'ai juste remarqué que votre identité visuelle (grand logo lotus beige) reste dans un style spa très traditionnel, alors que votre centre propose une technologie moderne : le message visuel ne vend pas encore toute la modernité de votre offre.",
    # 12th : boutons prendre rendez-vous sur 3 salons + horaires (HTML) + design reussi (vision)
    "https://12thsquarebarber.com": "votre site est très réussi : design moderne, vos trois salons bien présentés, avec un bouton de prise de rendez-vous sur chacun et vos horaires visibles. En tant que designer, je me suis demandé : est-ce que votre site raconte aussi bien votre savoir-faire qu'il organise vos réservations ? C'est souvent là que se joue la différence avec un concurrent.",
    # Christian Gilles : rdv present (HTML), hero photo daté (vision)
    "https://christiangilles.fr": "votre site est simple et épuré, avec une prise de rendez-vous en ligne. J'ai remarqué que la page d'accueil repose surtout sur une grande photo sans identité de marque affirmée : un client qui vous découvre ne retient pas encore clairement votre nom ni votre style, alors que votre savoir-faire mérite d'être mis en avant.",
    # Avakian : histoire 1928 (dossier) + prix presents (HTML: 100€)
    "https://oceane-avakian.com/en/pages/a-propos": "j'ai découvert l'histoire de votre famille dans la coiffure depuis 1928 : c'est un héritage exceptionnel, et votre page tarifs est claire et bien faite. En tant que designer, je me suis demandé : est-ce que votre identité visuelle raconte cette histoire avec la force qu'elle mérite ? C'est un atout que très peu de salons peuvent revendiquer.",
    # Epil Net : prix + planity + temoignage presents (HTML) — constat positif
    "https://epilnet.fr": "votre site est bien structuré : prix affichés, prise de rendez-vous via Planity et témoignages clients présents. Vous avez l'essentiel en place. En tant que designer, je me suis demandé : est-ce que votre page d'accueil donne aussi envie et rassure autant qu'elle informe ? C'est là que se joue la différence entre un site qui convertit et un site qui documente.",
    # Lhoest : tarifs + rdv + horaires + avis presents (HTML)
    "https://lhoestclinic.fr": "votre site est haut de gamme : tarifs, horaires, prise de rendez-vous et avis clients sont bien présents. En tant que designer, j'ai juste remarqué qu'un bandeau cookies imposant masque une partie de votre contenu à l'arrivée : vos visiteurs voient la protection avant votre offre, ce qui peut freiner l'élan avant même de découvrir vos prestations.",
    # O'Natty : design premium, logo beau (vision fullpage)
    "https://onatty.com": "votre site est très soigné : belle identité visuelle, logo élégant et lisible, univers cohérent avec votre marque. En tant que designer, je me suis demandé : est-ce que votre site pousse les visiteurs à réserver, ou les laisse-t-il admirer sans agir ? C'est souvent le dernier maillon qui transforme une belle image en clients concrets.",
    # Le 20 : prix 24/27/31€ + rdv presents (HTML) + 2 adresses 6e
    "https://le20barbershop.fr": "votre site affiche clairement vos tarifs (dès 24 €), vos deux adresses du 6e arrondissement et la prise de rendez-vous en ligne : c'est un vrai point fort. En tant que designer, je me suis demandé : est-ce que votre image de marque donne aussi envie de venir chez vous qu'elle facilite la réservation ? C'est ce qui vous distingue des autres barbershops du quartier.",
    # Thai Bien Etre : design daté (vision) — on garde le constat visuel (pas d'affirmation d'absence)
    "https://thaibienetre.fr": "votre site a une ambiance chaleureuse et un logo lotus identifiable. J'ai remarqué que le style visuel (boutons carrés, palette or/marron) évoque les débuts des années 2000 : c'est un décalage avec la qualité des soins que vous proposez, et un client moderne pourrait hésiter avant de réserver un massage premium.",
    # Luna Ongle : annuaire sans vrai site (vision) — constat sur la presence en ligne
    "https://lunaongle.com": "quand on vous cherche, on tombe sur des fiches d'annuaire qui se répètent, avec peu d'éléments qui montrent la qualité de votre travail. Vos ongleries lyonnaises méritent une vitrine qui donne envie : c'est souvent elle qui fait la différence quand une cliente compare plusieurs adresses avant de réserver.",
}

def appliquer():
    d = json.load(open(PATH, encoding="utf-8"))
    n = 0
    for x in d:
        w = x.get("website") or ""
        if w in CONSTATS and (x.get("site_provenance") in ("vision_confirme", "vision_probable", "constat_valide_dossier")):
            constat = CONSTATS[w]
            nom_prop = (x.get("dirigeant") or "").strip()
            salutation = f"Bonjour {nom_prop}," if nom_prop else "Bonjour,"
            site_clair = w.replace("https://", "").replace("http://", "").rstrip("/")
            x["constat_site"] = constat
            x["dm"] = (
                f"{salutation}\n\n"
                f"Je suis designer de marque, et en regardant votre site {site_clair} : {constat} "
                f"Concrètement, c'est ce qui transforme un visiteur en client.\n\n"
                f"Je peux vous préparer un diagnostic complet en 48h (79 EUR, remboursé si vous n'y trouvez pas de valeur) : "
                f"analyse de votre image, de votre site et des actions concrètes pour convertir plus de visiteurs en clients.\n\n"
                f"Vous êtes disponible pour un échange de 15 minutes cette semaine ?"
            )
            n += 1
    json.dump(d, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"DM reecrits avec faits verifies : {n} sites")

if __name__ == "__main__":
    appliquer()
