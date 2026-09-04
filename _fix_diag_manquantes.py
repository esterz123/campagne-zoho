#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repere les fiches ou le manifest diag_pages.json annonce une URL mais le fichier
HTML n'existe pas dans la vitrine -> les regenere via genere_pages_diag.main() en
remettant leur manifest a zero (idempotent, seuls celles-la sont rescannees)."""
import json, os

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
DIAG = r"C:\Users\ulamb\Bureau\prospection\vitrine\diag"
man = json.load(open(os.path.join(BASE, "diag_pages.json"), encoding="utf-8"))
manquants = [n for n, v in man.items() if isinstance(v, dict) and v.get("url")
             and not os.path.exists(os.path.join(DIAG, n + ".html"))]
print("fiches annoncees sans fichier:", len(manquants))
for n in manquants:
    del man[n]
json.dump(man, open(os.path.join(BASE, "diag_pages.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("manifest nettoye. Relancer genere_pages_diag.py pour regenerer.")
