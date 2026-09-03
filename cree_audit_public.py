# -*- coding: utf-8 -*-
"""
AUDIT GRAND PUBLIC - la page d'audit gratuit automatisee, transformee en
machine de LEADS self-service 24h/24.
=========================================================================
Ce qui existe : audit.html (page de diagnostic gratuit). Ce qui manque :
la collecte automatique de l'URL + envoi du rapport automatise + capture
du lead dans la file. Ce script PREPARE le formulaire + endpoint local.
Mahdi colle ensuite dans son herbergeur (ou Netlify Forms gratuit).
"""
import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))
VITRINE = os.path.normpath(os.path.join(BASE, "..", "vitrine"))
FORM_FILE = os.path.join(VITRINE, "audit-form.html")


def main():
    # 1. formulaire simple (Netlify Forms gratuit, ou mailto fallback)
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Audit gratuit de votre site en 30 secondes - Mahdi Design</title>
<style>
body{font-family:var(--font,'Segoe UI'),sans-serif;background:#0d0f13;color:#e8eaef;margin:0;padding:0;display:flex;align-items:center;justify-content:center;min-height:100vh}
.card{background:#171b22;border:1px solid #242a34;border-radius:16px;padding:44px 36px;max-width:480px;margin:24px;text-align:center}
h1{font-size:1.7rem;margin-bottom:10px}em{color:#ff7a1a;font-style:normal}
p{color:#9aa3b2;font-size:0.95rem;margin-bottom:24px}
input{width:100%;padding:15px 18px;border-radius:999px;border:1px solid #242a34;background:#0d0f13;color:#e8eaef;font-size:1rem;margin-bottom:16px}
button{width:100%;padding:15px;border-radius:999px;border:0;background:linear-gradient(135deg,#ff8c2a,#ff7a1a);color:#0d0f13;font-weight:800;font-size:1rem;cursor:pointer}
button:hover{transform:scale(1.02);box-shadow:0 10px 32px rgba(255,122,26,.45)}
.small{font-size:.8rem;color:#4ade80;margin-top:14px}
a{color:#9aa3b2}
</style>
</head>
<body>
<div class="card">
<h1>Audit gratuit de votre site <em>en 30 secondes</em></h1>
<p>Vous decouvrez ce qui fait fuir vos clients : vitesse, mobile, securite, visibilite Google. Rapport chiffre, sans engagement, livre par email.</p>
<form name="audit-gratuit" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/merci-audit.html">
  <input type="hidden" name="form-name" value="audit-gratuit" />
  <p style="display:none"><label>Ne pas remplir: <input name="bot-field"/></label></p>
  <input type="url" name="site" placeholder="https://votre-site.fr" required />
  <input type="email" name="email" placeholder="votre@email.fr" required />
  <button type="submit">Recevoir mon audit gratuit &rarr;</button>
</form>
<p class="small">Aucune inscription. Vous voyez vous-meme avant de me croire.</p>
<p style="margin-top:18px;font-size:.85rem"><a href="https://mahdi-design.com">&larr; Retour au portfolio</a></p>
</div>
</body>
</html>"""
    with open(FORM_FILE, "w", encoding="utf-8", newline="") as f:
        f.write(html)

    # 2. page merci avec upsell (pattern funnel post-paiement deja valide)
    merci = html.replace("Audit gratuit de votre site <em>en 30 secondes</em>",
                         "Recu ! <em>L'audit arrive dans votre boite.</em>").replace(
        "<p>Vous decouvrez ce qui fait fuir vos clients : vitesse, mobile, securite, visibilite Google. Rapport chiffre, sans engagement, livre par email.</p>",
        """<p>Votre audit est en preparation : tu le recois par email sous 24h.</p>
<div style="background:rgba(255,122,26,0.08);border:1px solid rgba(255,122,26,0.4);border-radius:12px;padding:18px;margin:20px 0">
<p style="color:#ff7a1a;font-weight:700;margin-bottom:8px">Pendant que vous attendez :</p>
<p style="color:#e8eaef">La plupart des sites que j'audite ont <strong>3 problems en commun</strong>. Je peux aussi comparer votre site a 2 concurrents directs et vous montrer exactement ce qu'ils font de mieux. C'est l'audit complet a 79 EUR, rembourse si pas de valeur, deduit du projet.</p>
<a href="https://mahdi-design.com/diagnostic.html" style="display:inline-block;margin-top:12px;padding:12px 24px;border-radius:999px;background:linear-gradient(135deg,#ff8c2a,#ff7a1a);color:#0d0f13;font-weight:700">Voir l'audit complet 79 EUR</a>
</div>""")
    merci = merci.replace("audit-gratuit.html", "merci-audit.html")
    merci = merci.replace("Recevoir mon audit gratuit", "Recu !")
    merci = merci.replace('<form name="audit-gratuit" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/merci-audit.html">', "")
    merci = merci.replace('<input type="url" name="site" placeholder="https://votre-site.fr" required />', "")
    merci = merci.replace('<input type="email" name="email" placeholder="votre@email.fr" required />', "")
    merci = merci.replace('<button type="submit">Recu !</button>', "")
    merci = merci.replace("</form>", "")

    with open(os.path.join(VITRINE, "merci-audit.html"), "w", encoding="utf-8", newline="") as f:
        f.write(merci)
    print("PAGES CREEES:")
    print("  ", FORM_FILE)
    print("  ", os.path.join(VITRINE, "merci-audit.html"))
    print("")
    print("POUR ACTIVER (Mahdi, 5 min):")
    print("  1. Le repo vitrine est deja sur GitHub Pages -> le push active tout")
    print("  2. Netlify Forms gratuit : les soumissions arrivent par email a contact@")
    print("  3. Ou demander a Mahdi de mettre le form sur son hebergeur")
    print("")
    print("PIPELINE: lead entre son URL -> Netlify -> email a contact@ ->")
    print("  Mahdi colle l URL dans verificateur_site.py -> rapport auto -> envoi")


if __name__ == "__main__":
    main()
