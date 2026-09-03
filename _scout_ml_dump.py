# -*- coding: utf-8 -*-
"""Que contient la page mentions-legales de afume.fr ?"""
import sys, re
sys.path.insert(0, ".")
from chasseur_prospects import fetch

html = fetch("https://www.afume.fr/mentions-legales", tries=2)
txt = re.sub(r"<[^>]+>", " ", html)
txt = re.sub(r"\s+", " ", txt)
# tous les groupes de >=8 chiffres
nums = re.findall(r"\d[\d .]{6,}\d", txt)
print("NOMBRES:", nums[:15])
# autour de "SIREN/SIRET/RCS/TVA"
for kw in ("SIREN", "SIRET", "RCS", "TVA", "099", "419"):
    for m in re.finditer(kw, txt, re.I):
        print(kw, "->", txt[max(0, m.start()-40):m.start()+80].strip())
        break
