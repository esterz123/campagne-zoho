# 🚀 GUIDE : l'automatisation qui tourne SANS ton PC
## (GitHub Actions — gratuit, aucun outil à installer, tout se fait dans le navigateur)

Fais les étapes **dans l'ordre, une par une**. Dis-moi « étape suivante » entre chaque.

---

### ÉTAPE 1 — Créer le compte GitHub (2 minutes, seulement si tu n'en as pas)
1. Ouvre **https://github.com/signup**
2. Remplis : email (le tien), mot de passe, pseudo (ex : `mahdi-design`)
3. Clique les boutons verts jusqu'à la fin (vérifie l'email si demandé)

✅ Tu es connecté à GitHub. Dis-moi « étape suivante ».

---

### ÉTAPE 2 — Créer le dépôt (1 minute)
1. Ouvre **https://github.com/new**
2. « Repository name » : tape `campagne-zoho`
3. Choisis **Private** (privé — ton code reste caché)
4. Clique le bouton vert **« Create repository »**

✅ Écran gris avec des instructions en anglais = parfait. Dis-moi « étape suivante ».

---

### ÉTAPE 3 — Déposer les fichiers (2 minutes)
1. Sur l'écran gris, clique le lien bleu **« uploading an existing file »**
2. Ouvre ce dossier sur ton PC : `Bureau → prospection → github-campagne`
3. **Glisse les 4 éléments** dans la page GitHub :
   - `campagne_zoho.py`
   - `campagne_data.json`
   - `campagne_state.json`
   - le dossier `.github` (glisse-le entier, GitHub crée les sous-dossiers tout seul)
4. Clique le bouton vert **« Commit changes »**

⚠️ Ne glisse PAS `secrets_a_coller.txt` (il reste sur ton PC, c'est normal).
✅ La liste des fichiers apparaît. Dis-moi « étape suivante ».

---

### ÉTAPE 4 — Coller les 3 secrets (3 minutes)
1. Dans ton dépôt, ouvre l'onglet **Settings** (en haut, à droite)
2. Dans le menu de gauche, clique **Secrets and variables** → **Actions**
3. Clique le bouton **« New repository secret »** :
   - Name : `ZOHO_CLIENT_ID` → Value : copie depuis `secrets_a_coller.txt` (1re ligne)
   - Clique **« Add secret »**
4. Refais pareil 2 fois :
   - `ZOHO_CLIENT_SECRET` (2e ligne du fichier)
   - `ZOHO_REFRESH_TOKEN` (3e ligne du fichier)

✅ Tu vois 3 noms de secrets (valeurs cachées). Dis-moi « étape suivante ».

---

### ÉTAPE 5 — Test : « Run workflow » (1 clic)
1. Ouvre l'onglet **Actions** (en haut)
2. À gauche, clique **« Campagne emails Zoho »**
3. Clique le bouton **« Run workflow »** (à droite) puis le même bouton dans le menu déroulant
4. Attends 30 secondes : la case devient **verte** ✅

⚠️ Ce test envoie **VRAIMENT** l'email n°3 (Rouxel, contact@rouxel-mold.com) — c'est voulu, la campagne avance !
✅ Case verte = tout est bon. **Dis-moi « c'est vert » et je coupe le cron local.**

---

### APRÈS — ça tourne tout seul
- **Chaque matin à 8h30** (même PC éteint), GitHub envoie les emails du jour (2-3 max).
- L'état est sauvegardé dans le dépôt → jamais de doublon, jamais d'oubli.
- Tu peux suivre : Zoho → dossier **Envoyé**. Et me demander « statut campagne » à tout moment.
- Bouton **« Run workflow »** = envoyer tout de suite, à la main.

### En cas de problème
- Case **rouge** = erreur → clique dessus, lis le message, envoie-moi le texte.
- Mot de passe GitHub oublié → « Forgot password » sur la page de connexion.
