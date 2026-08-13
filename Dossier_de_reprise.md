# 🎯 DOSSIER DE REPRISE — CAMPAGNE EMAIL PRO MAHDI
**Dernière mise à jour : 13/08/2026 (midi) — CORRECTIF URGENT ZOHO appliqué**

---

## 🚨 CORRECTIF URGENT (13/08 midi) — le bug des envois 404
**Symptôme** : les runs GitHub échouaient (08h01 + 09h41) avec `HTTP Error 404` → Discord alertait.
**Cause trouvée (dans le code, pas chez Zoho)** : `campagne_zoho.py` envoyait le champ `htmlContent` dans le payload API. Zoho le REFUSE (`EXTRA_KEY_FOUND_IN_JSON`) et rejette tout l'email avec 404.
**Correctif** : le HTML passe maintenant directement dans `content` (sans `htmlContent`). Vérifié en test réel : HTTP 200 + messageId. Poussé commit `7443357`.
**Leçon** : ne JAMAIS réajouter `htmlContent` dans le payload de `send_email()`. C'est documenté en commentaire dans le code.

---

## 🔒 CORRECTION CRITIQUE (13/08) — VERROU ANTI-ERREUR INSTALLÉ
**Le bug des emails piégés est CORRIGÉ à 100%, dans le code d'envoi lui-même (pas seulement un outil).**
- **Cause** : `chasseur_dirigeants.py` tombait sur des sites-annuaires/scrapers SEO (mecaniqueautofacile.com, croisieres-en-seine.fr, footballberry.com...) et récupérait des emails génériques.
- **Correctif** : `domaines_bloques.json` (70 domaines piégés : annuaires, scrapers, mails gratuits orange/gmail, relais techniques delosmail, mismatches). Le script `campagne_zoho.py` **REFUSE d'envoyer** vers tout email dont le domaine y figure.
- **`verificateur_dirigeants.py`** : l'assistant de contrôle. Vérifie chaque email, verdicts CONFIRME/DIRECTOIRE/REJETE/INCERTAIN. Sortie `verifie_dirigeants.json`.
- **File purgée** : 52 → **47** (5 emails piégés retirés : orange.fr, delosmail, bureau-vallee, segreenanjoubleu, metallerie.com).
- **Poussé sur GitHub** : le cloud (Actions) utilise la version corrigée dès le prochain run. Le PC peut rester éteint.

---

## 🎯 OBJECTIF N°1 (PRIORITÉ ABSOLUE) : GAGNER DE L'ARGENT LE PLUS VITE POSSIBLE
- Réduire le délai du premier 79 € de 2-3 semaines → **5-7 jours**
- La machine envoie + répond + relance toute seule. Mahdi confirme seulement.
- **Règle d'or : JAMAIS de tiret « — » dans les emails (virgules/points).**
- L'agent fait TOUT (chasse, emails, closing, docx). Mahdi ne remplit rien.

---

## ✅ ÉTAT ACTUEL DE LA MACHINE (12/08/2026 soir)

### File de prospects
- **52 prospects** dans `campagne_data.json` (6 envoyés, 46 restants)
- 3 envois/jour (08h30/10h30/14h Paris) via GitHub Actions
- ~15 jours pour tout envoyer au rythme actuel

### Authentification email (100% opérationnelle)
- SPF ✅ · DKIM ✅ (zmail._domainkey) · DMARC ✅ (p=none) · MX Zoho ✅
- Compte Zoho **5 boîtes** : contact@ / commercial@ / hello@ / info@ / direction@mahdi-design.com
  - Seule contact@ a un token OAuth utilisable. Les 4 autres créées mais PAS encore câblées à l'envoi.

### Relance automatique (ACCÉLÉRÉE ce soir)
- **relance1 = J+3** · **relance2 = J+7** (au lieu de J+5/J+12) — dans `followups.json`
- Logique déjà intégrée dans `campagne_zoho.py`, config via `followups.json`

### Repondeur automatique (réponses clients)
- Tourne sur GitHub Actions, toutes les heures (7h-21h), OpenRouter gratuit (50/jour)
- Lit la boîte, fait le brouillon de réponse, le met sur Discord
- Boîte actuelle : 2 messages (milmeca Mailinblack + Slicom auto) — déjà traités, rien d'urgent

### Email dirigeants (le travail de ce soir)
- **97 fiches** dans `dirigeants_email.json` (via chasse SearXNG) → **vérifiées 13/08**
- **13 emails CONFIRME** (envoyables, domaine = site officiel + SIREN vérifié) : Les Plastiques Décorés, Artois, Decolletage de Reu, Usinage Alsace, Decolletage Elbe, AG Tolerie, Drault, Axil, Fonderies Nangis, Tolerie Forezienne, Fonderie Lemer, Fonderies Larians, France Injection
- **9 INCERTAIN** (domaines réels mais SIREN non vérifiable, à confirmer à la main avant intégration) : Eberhard, Alpha Matières, Elcam, FPSA, AFM, JCM, AMD, Tolerie Remond, Millet
- **33 DIRECTOIRE + 42 REJETÉ** éliminés (annuaires/scrapers/emails piégés)
- **File : 47** après purge des 5 emails piégés
- **Leçon apprise (RENFORCÉE)** : les emails dirigeants ne se devinent JAMAIS et un email n'est envoyable QUE si son domaine = site officiel. Le vérificateur + verrou appliquent cette règle automatiquement.

---

## 📋 OUTILS / INFRA
- **SearXNG local** (Pinokio) : port actuel **12054** (varie à chaque lancement). Moteur google fiable (délai 4s anti-blocage). Le lancer via `start_searxng.py`.
- **Chasseur dirigeants** : `chasseur_dirigeants.py --start X --max Y` (écrit `dirigeants_email.json`)
- **Vérificateur IA** : `verificateur_dirigeants.py` (verdicts CONFIRME/DIRECTOIRE/REJETE/INCERTAIN, sortie `verifie_dirigeants.json`) — **à lancer avant d'intégrer de nouveaux emails à la file**
- **Verrou anti-erreur** : `domaines_bloques.json` (70 domaines piégés) — intégré à `campagne_zoho.py`, bloque l'envoi automatiquement
- **Testeur MX** : `email_tester.py --check` (vérifie le domaine, anti-bounce)
- **Testeur SMTP** : `verify_smtp.py` (PAS fiable pour décider — ne pas l'utiliser pour valider)
- **Venv docx** : `C:\Users\ulamb\Bureau\prospection\.venv-docx\Scripts\python.exe` (python-docx)
- **Livrables 79 €** : `livrable_diagnostic/` (template + exemple SIMI) · **Playbook** : `playbook_closing.md` · **Structure offres** : `structure_offres.md`
- **Messages DM** : `messages_dm.json` (32 prêts, LinkedIn/Instagram)

---

## 🎯 PROCHAINES ÉTAPES (ordre recommandé)
1. **[FAIT ce soir]** Relance accélérée J+3/J+7 — poussée sur GitHub ✅
2. **Chasse complémentaire** : les ~16 emails « trouvés sur site non encore en file » de `dirigeants_email.json` sont BEAUCOUP des faux (croisieres-en-seine, anjou-tourisme, footballberry, mecaniqueautofacile...) — **à filtrer manuellement**, n'ajouter que ceux dont le domaine = site officiel réel
3. **Remplir la file** vers 100+ (chasse GitHub fait déjà 1x/jour)
4. **Câbler les 5 boîtes** (rotation d'expéditeurs) pour monter le volume — PRUDENCE : compte de 2 jours, monter progressivement 3→6→10→15/jour pour éviter le spam. Nécessite OAuth token pour les 4 nouvelles boîtes (Admin Console Zoho).
5. **Portfolio** (à refaire sur-mesure, actuellement template Gamma qui bug)
6. **PayPal/Payoneer** : Mahdi a déjà les 2 comptes. Configurer au moment du 1er « oui » (lien paypal.me), pas avant.

---

## ⚠️ RÈGLES NON NÉGOCIABLES
- **Zéro suppression de fichiers sur le PC** sans accord de Mahdi (même pour la campagne)
- **Jamais d'email deviné** (prenom.nom@ à l'aveugle) → bounce = blacklist
- **Pas d'auto-closing / pas de promesse de prix sans validation** (risque de perte)
- **Le job Hermes de surveillance n'est PAS utile** (le repondeur GitHub le fait déjà gratuitement) — ne pas re-créer
- Les envois passent par GitHub Actions (PC peut être éteint). Le repondeur aussi.
