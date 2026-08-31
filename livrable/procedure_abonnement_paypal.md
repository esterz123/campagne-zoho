# PROCÉDURE PAYPAL — 5 MINUTES (abonnement 69 €/mois + liens aux bons montants)

Pour Mahdi. Aucune donnée sensible ici : tout se passe dans TON compte, de ta main.
Personne (ni bot, ni agent) ne doit jamais voir tes mots de passe.

## PARTIE 1 — Le BOUTON ABONNEMENT 69 €/mois (le moteur du récurrent)

1. Va sur https://www.paypal.com → connecte-toi.
2. Menu **Pay & Get Paid** (Payer et être payé) → **PayPal Buttons** (Boutons PayPal).
   URL directe si le menu bouge : https://www.paypal.com/business/manage/fees/onboarding/
   ou cherche "PayPal Buttons" dans la barre du tableau de bord.
3. Clique **Create New Button** (Créer un bouton).
4. Type : choisis **Subscription** (Abonnement), PAS "Buy Now".
5. Nom du produit : `Pack Serenite - Site surveille et entretenu`
6. Montant : **69 EUR** / Billing frequency : **Monthly** (mensuel).
   Coche "first month free" si tu veux honorer le "premier mois offert" de l'offre.
7. Cancel and continue → active **Automatic billing** (le client se désabonne seul s'il veut,
   c'est ce qui rend le "sans engagement" crédible).
8. **Advanced Payments** : coche "Return to business after payment" si proposé.
9. **Copy Button Code** → garde le lien court `https://www.paypal.me/...` ou le code
   `cmd=_subscr-buy&plan=...`. C'est LE LIEN à mettre dans les mails de vente Sérénité.
10. Envoie-moi UNIQUEMENT ce lien public (jamais le mot de passe du compte).
    Je le branche dans closer_ia.py, repondeur.py, la vitrine et les 152 rapports.

## PARTIE 2 — Les 3 LIENS ONE-SHOT au bon montant (pour cette semaine)

Même écran PayPal Buttons, type **Buy Now**, un bouton par montant :
- `Intervention securite urgence` → **150 EUR** (FPSA et futurs piratés)
- `Acompte 30% refonte marque+site` → **870 EUR** (SIMI et refontes rentrée)
- `Refonte marque+site offre rentree` → **2900 EUR** (solde ou projet complet)

Copie chaque lien, envoie-les moi de la même façon (liens publics uniquement).
Le playbook Seller (livrable/playbook_replies_3chauds.md) a des crochets [LIEN-150],
[LIEN-870], [LIEN-2900] : dès réception je les remplace et tout est prêt à coller.

## PARTIE 3 — Pourquoi pas Stripe / facture récurrente (comparaison honnête)

| Option | Coût de départ | Récurrent automatique | Délai argent |
|--------|---------------|----------------------|--------------|
| **PayPal abonnement (cette procédure)** | 0 EUR | OUI | immédiat (compte déjà actif, testé 79 EUR le 31/08) |
| Stripe abonnement | 0 EUR mais KYC complet à re-faire | OUI | 1-7 jours (vérifications) |
| Factures récurrentes PayPal | 0 EUR | semi (relance auto par email) | immédiat |
| Renouvellement manuel par le closer | 0 EUR | non (humain chaque mois) | immédiat |

**Recommandation : Partie 1 + 2 tout de suite (PayPal, 5 min, zéro risque, compte déjà
validé par le test du 31/08).** Stripe seulement quand le volume dépassera ~30 abonnés
et que les frais PayPal (3,4 % + 0,25 €/mois) peseront vraiment.

## PARTIE 4 — Ce qui est déjà prêt côté machine

- Détection de paiement : repondeur.py reconnaît les notifs PayPal et écrit dans
  suivi_revenus.json (testé en réel le 31/08 : TESTBOUTENBOUT 79 EUR détecté).
- Un paiement récurrent PayPal génère la même notif email → il sera compté aussi.
- Le closer insérera le lien abonnement automatiquement après chaque vente diagnostic.
