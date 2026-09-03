# -*- coding: utf-8 -*-
"""Probe 2: moteurs de recherche accessibles depuis cette machine ?"""
import sys, re, urllib.parse
sys.path.insert(0, ".")
from chasseur_prospects import fetch, _brave_sites, find_site

nom, ville = "Axil Plasturgie", "CIVRIEUX-D'AZERGUES"
print("--- brave raw ---")
out = fetch("https://search.brave.com/search?q=" + urllib.parse.quote('"Axil Plasturgie" CIVRIEUX'))
print("len:", len(out))
print("--- _brave_sites ---")
print(_brave_sites(nom, ville))
print("--- find_site full ---")
print(find_site(nom, ville))
