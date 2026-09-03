# -*- coding: utf-8 -*-
"""
RESYNC SCORES PAGES DIAG - aligne le score affiche sur la page avec le
constat MESURE de constats_sites.json (l'ere preuve). Les pages 90-349
avaient un score calcule par une version anterieure du scanner : 112
divergent de >15 points. Un prospect qui lit 100/100 ici puis 40/100
dans le mail nous tuerait. On met a jour le HTML de chaque page + manifest.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
VITRINE = os.path.normpath(os.path.join(BASE, "..", "vitrine"))
DIAG_DIR = os.path.join(VITRINE, "diag")

m = json.load(open(os.path.join(BASE, "diag_pages.json"), encoding="utf-8"))
pr = json.load(open(os.path.join(BASE, "constats_sites.json"), encoding="utf-8"))

corrigees = 0
absentes = 0
for num, v in m.items():
    url = v.get("url")
    if not url:
        continue
    p = pr.get(num)
    if not p or p.get("note") is None:
        continue
    new_score = p["note"]
    if v.get("score") == new_score:
        continue
    fn = os.path.join(DIAG_DIR, "%s.html" % num)
    if not os.path.exists(fn):
        absentes += 1
        continue
    html = open(fn, encoding="utf-8").read()
    # remplacer le score affiche (pattern du template : NN/100)
    html2, n = re.subn(r">(\d{1,3})/100<", ">%d/100<" % new_score, html, count=1)
    if not n:
        html2, n = re.subn(r"(\d{1,3})/100", "%d/100" % new_score, html, count=1)
    if n:
        open(fn, "w", encoding="utf-8", newline="").write(html2)
    v["score"] = new_score
    corrigees += 1

json.dump(m, open(os.path.join(BASE, "diag_pages.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("pages recalees sur la mesure:", corrigees, "| sans fichier:", absentes)
