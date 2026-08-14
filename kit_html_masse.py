#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIT HTML EN MASSE — genere kit_dm_instagram.html depuis kit_dm_masse.json.
=========================================================================
Produit le fichier cliquable : chaque cible = lien Instagram + bouton Copier
avec le DM personnalise (nom dirigeant + probleme + portfolio).

Usage :
  python3 kit_html_masse.py            # genere le kit complet
  python3 kit_html_masse.py --max 50   # limite a 50 cibles
"""
import json, os, sys, html as H

BASE = os.path.dirname(os.path.abspath(__file__))

TAGS = {
    "salon coiffure": "COIFFURE",
    "institut beaute": "BEAUTE",
    "salon ongles": "ONGLES",
    "restaurant": "RESTAURANT",
    "garage auto": "GARAGE",
    "auto-ecole": "AUTO-ECOLE",
    "boulangerie": "BOULANGERIE",
    "cafe bar": "BAR",
    "fleuriste": "FLEURISTE",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kit DM Instagram — %(count)d cibles personnalisees</title>
<style>
  body { font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #fafafa; color: #1a1a1a; }
  h1 { font-size: 1.5em; }
  .steps { background: #e8f0fe; border-radius: 10px; padding: 14px; margin: 16px 0; }
  .steps ol { margin: 8px 0 0; padding-left: 20px; }
  .cible { background: #fff; border: 1px solid #ddd; border-radius: 10px; padding: 16px; margin: 14px 0; }
  .nom { font-weight: 700; font-size: 1.05em; }
  .tag { display: inline-block; font-size: 0.72em; padding: 2px 8px; border-radius: 10px; margin-left: 8px; color: #fff; background: #e1306c; }
  .lien { margin: 8px 0; }
  .lien a { color: #e1306c; font-weight: 600; text-decoration: none; }
  .lien a.port { color: #0a66c2; margin-left: 12px; }
  .dirigeant { font-size: 0.85em; color: #555; }
  .msg { background: #f6f6f6; border-radius: 8px; padding: 12px; font-size: 0.9em; white-space: pre-wrap; margin: 8px 0; line-height: 1.45; }
  .btn { background: #e1306c; color: #fff; border: none; border-radius: 6px; padding: 8px 16px; font-size: 0.9em; cursor: pointer; }
  .copie { font-size: 0.8em; color: #666; margin-top: 4px; }
</style>
</head>
<body>
<h1>🎯 Kit DM Instagram — %(count)d cibles personnalisees</h1>
<div class="steps">
  <strong>Mode d'emploi (30 secondes par cible) :</strong>
  <ol>
    <li>Clique sur le lien Instagram (ça ouvre le profil)</li>
    <li>Touche "Message" (ou ✉️) sur le profil</li>
    <li>Clique "Copier", colle dans la boîte, envoie</li>
  </ol>
  <p style="margin:8px 0 0;font-size:0.85em;color:#444;">💡 Chaque message est personnalise (dirigeant + probleme du secteur). Espace de 2-3 min entre envois pour eviter le blocage anti-spam.</p>
</div>
%(cibles)s
<script>
function copier(id) {
  const txt = document.getElementById(id).innerText;
  navigator.clipboard.writeText(txt).then(() => {
    const copie = document.getElementById('copie' + id.slice(3));
    copie.textContent = '✅ Copié ! Colle-le dans le DM Instagram.';
    setTimeout(() => copie.textContent = '', 2500);
  });
}
</script>
</body>
</html>
"""


def generer():
    args = sys.argv[1:]
    max_n = 100000
    if "--max" in args:
        max_n = int(args[args.index("--max") + 1])

    try:
        cibles = json.load(open(os.path.join(BASE, "kit_dm_masse.json"), encoding="utf-8"))
    except FileNotFoundError:
        print("kit_dm_masse.json introuvable. Lance d'abord : python3 generateur_dm_masse.py")
        sys.exit(1)

    valides = [c for c in cibles if c.get("instagram") and c.get("dirigeant") and c.get("dm")]
    # Les DM forts (site confirme + constat) passent en tete, puis par priorite
    def cle_tri(c):
        fort = 1 if (c.get("website") and c.get("constat_site")) else 0
        prio = c.get("priorite", 9)
        return (-fort, prio if isinstance(prio, int) else 9)
    valides.sort(key=cle_tri)
    valides = valides[:max_n]

    blocs = []
    for i, c in enumerate(valides):
        nom = H.escape(c.get("nom", "?")[:60])
        insta = c.get("instagram", "")
        dir_nom = H.escape(c.get("dirigeant", "?"))
        secteur = c.get("secteur", "")
        tag = TAGS.get(secteur, secteur.upper()[:12])
        dm = H.escape(c.get("dm", ""))
        blocs.append("""<div class="cible">
  <span class="nom">%s</span>
  <span class="tag">%s</span>
  <div class="dirigeant">Dirigeant : %s</div>
  <div class="lien">📸 <a href="%s" target="_blank">%s</a> <a class="port" href="https://mahdi-design.com" target="_blank">Portfolio Mahdi Design ↗</a></div>
  <div class="msg" id="msg%d">%s</div>
  <button class="btn" onclick="copier('msg%d')">Copier</button>
  <div class="copie" id="copie%d"></div>
</div>""" % (nom, tag, dir_nom, insta, insta.replace("https://www.instagram.com/", "@").rstrip("/"),
            i, dm, i, i))

    out = TEMPLATE % {"count": len(valides), "cibles": "\n".join(blocs)}
    with open(os.path.join(BASE, "kit_dm_instagram.html"), "w", encoding="utf-8") as f:
        f.write(out)
    print("Kit genere : %d cibles -> kit_dm_instagram.html" % len(valides))


if __name__ == "__main__":
    sys.exit(generer())
