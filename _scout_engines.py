# -*- coding: utf-8 -*-
"""Quel moteur de recherche est encore vivant ?"""
import sys, re, urllib.parse
sys.path.insert(0, ".")
from chasseur_prospects import fetch

q = "Axil Plasturgie CIVRIEUX"
tests = {
    "brave": "https://search.brave.com/search?q=" + urllib.parse.quote(q),
    "ddg-html": "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q),
    "ddg-lite": "https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(q),
    "bing": "https://www.bing.com/search?q=" + urllib.parse.quote(q),
    "mojeek": "https://www.mojeek.com/search?q=" + urllib.parse.quote(q),
    "startpage": "https://www.startpage.com/sp/search?query=" + urllib.parse.quote(q),
    "ecosia": "https://www.ecosia.org/search?q=" + urllib.parse.quote(q),
}
for name, url in tests.items():
    out = fetch(url, tries=1)
    doms = []
    for l in re.findall(r'https?://(?:www\.)?([a-z0-9-]+\.[a-z.]{2,})', out.lower()):
        if any(x in l for x in ("brave", "duckduckgo", "bing", "mojeek", "startpage", "ecosia", "w3.org", "microsoft")):
            continue
        if l not in doms:
            doms.append(l)
    print("%-10s len=%-7d doms=%s" % (name, len(out), doms[:6]))
