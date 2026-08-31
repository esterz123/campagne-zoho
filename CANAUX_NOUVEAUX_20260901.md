# 3 NOUVEAUX CANAUX DE REVENUS (chasse du 01/09/2026)

Chiffres verifies : sources locales (campagne_state.json, diag_pages.json, vitrine/) + web (support-fr.comeup.com, stripe.com/fr/pricing, help.malt.com, barometre Malt).

## CANAL 1 : Gig economy (Malt + ComeUp) avec la machine comme usine de devis
Assets : 298 pages diag deja generees, 998 domaines candidats, machine 12 envois/jour.
- ComeUp : commission 20% HT (offre gratuite), Fiverr UP 20%.
- Malt : commission 10% HT (Starter), TJM webdesigner FR moyen 276-457 EUR selon anciennete.
Plan :
1. Creer 3 gigs ComeUp/Fiverr UP avec les textes deja dans CANAUX_GRATUITS.md (30 min, 0 EUR).
2. Profil Malt "Brand designer PME industrielles" + portfolio mahdi-design.com ; TJM affiche 340 EUR (moyen marche).
3. Utiliser le generateur de diag pour produire un mini-diag gratuit par prospect entrant (deja automatisé) : taux de conversion devis.
Potentiel : 2 missions/mois a 490-990 EUR net = 900-1600 EUR/mois (apres commission 20%).
1er euro : 2 a 4 semaines (delai observe marketplace).

## CANAL 2 : Productisation du diagnostic 79 EUR (self-service Stripe/PayPal)
Assets : 298 pages diag avec bouton PayPal 79 EUR DEJA injectes (verifie : 298/298, lien ncp FQYKP733699LQ), 198 envois, stock 800 prospects (998 domaines - doublons).
- Frais : PayPal NCP ~3.4% ou Stripe 1.5% + 0.25 EUR (cartes EEE, stripe.com/fr/pricing). Stripe Payment Links gratuit sans site.
Plan :
1. Creer un Stripe Payment Link 79 EUR "Diagnostic express" + un a 99 EUR avec appel de 30 min (30 min).
2. Remplacer le lien PayPal par le link Stripe sur les 298 pages (inject_pay.py modifie, 15 min) : paiement carte sans compte PayPal = moins de friction.
3. Passer le stock dormant : 651 PME jamais contactees (998 - 198 envoyes - dedup) dans la machine a 12/jour avec l offre self-serve en objet.
Potentiel : taux realiste 0.5-1% du stock en diag payant = 3 a 6 ventes/mois x 79 EUR = 240-470 EUR/mois recurrent passif ; le vrai gain = les refontes 2900 EUR derriere (1 conversion tous les 2 mois = +1450 EUR/mois moyen).
1er euro : 3 a 10 jours (paiement carte, livraison automatique du diag complet).

## CANAL 3 : Sous-traitance agences web a la commission
Assets : page partenaires.html DEJA en ligne (15% commission annoncee), 331 leads Exa + 286 leads Apify re-ciblables, machine email.
Marche : milliers d agences FR (annuaires ATLINKER, Digitiz, responsive-mind) ; beaucoup sous-traitent en marque blanche (ex Alliance Technique).
Plan :
1. Construire une liste de 200 agences web FR depuis les 3 annuaires (la machine de scraping existe deja).
2. Cibler les agences SANS designer senior (site agence moche = signal, le diag existe deja pour noter) : email d agence different du prospect PME, objet "votre production design en marque blanche".
3. Envoyer 12/jour avec la machine ; proposition : 15% sur projet signe (refonte 2900-5900 EUR = 435-885 EUR par agence convertie), renouvelable.
Potentiel : 2 agences actives x 1 projet/trimestre = 300-590 EUR/mois moyen, sans prospection PME (0 CAC).
1er euro : 4 a 8 semaines (cycle de decision agence plus long, mais clients repetes).

## Ordre recommande (cash d abord)
1. Canal 2 (Stripe link + stock dormant) : le plus rapide, tout existe deja.
2. Canal 1 (gigs) : pose les fondations en parallele, mure tout seul.
3. Canal 3 : lance la liste agences en semaine 2, recolte mois 2.
