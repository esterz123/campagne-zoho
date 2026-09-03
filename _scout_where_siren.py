# -*- coding: utf-8 -*-
"""Ou est le SIREN sur afume.fr / abag.fr ?"""
import sys, re
sys.path.insert(0, ".")
from chasseur_prospects import fetch

for dom, siren in [("afume.fr", "419763099"), ("abag.fr", "404048704")]:
    for path in ["/", "/mentions-legales", "/contact", "/a-propos", "/mentions_legales", "/qui-sommes-nous"]:
        for pref in ["https://www.", "https://"]:
            html = fetch(pref + dom + path, tries=1)
            if not html:
                continue
            t = re.sub(r"\s+", " ", html)
            sp = re.sub(r"(\d{3})(?=\d)", r"\1 ", siren)
            hit = siren in t or sp in t
            title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
            print("%s%s %s len=%d SIREN=%s titre=%s" % (
                pref, dom, path, len(html), "OUUI" if hit else "non",
                (title.group(1).strip()[:60] if title else "?")))
            break
