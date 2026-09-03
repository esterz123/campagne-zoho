# -*- coding: utf-8 -*-
"""Debug: que renvoient reellement Brave et DDG pour 3 candidats ?"""
import sys, re, urllib.parse
sys.path.insert(0, ".")
from chasseur_prospects import fetch, _brave_sites

for nom, ville in [("4 J CHAUDRONNERIE", "SAINTE-BLANDINE"),
                   ("A.F.U.M.E. ATELIER DE FABRICATION ET D'USINAGE MECANIQUE (A.F.U.M.E.)", "JARGEAU"),
                   ("Axil Plasturgie", "CIVRIEUX-D'AZERGUES")]:
    q = '"%s" %s' % (nom, ville)
    out = fetch("https://search.brave.com/search?q=" + urllib.parse.quote(q))
    urls = re.findall(r'(https?://[^"<> ]+)', out)
    doms = []
    for l in urls[:200]:
        m = re.match(r'https?://(?:www\.)?([^/]+)', l)
        if m and m.group(1) not in doms:
            doms.append(m.group(1))
    print("=== BRAVE", nom[:30], "len:", len(out))
    print("   doms:", doms[:15])
    print("   _brave_sites:", _brave_sites(nom, ville))
    ddg = fetch("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
    hits = [urllib.parse.unquote(m) for m in re.findall(r'uddg=([^&"]+)', ddg)[:8]]
    print("   DDG:", hits[:8])
