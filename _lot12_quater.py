#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot12 quater : cible les pages contact/mentions legales probables (email + nom dirigeant)."""
import json, re, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

SITES = {
    152: "tifsas.com", 153: "gromy.fr", 157: "tolerieservice54.com", 158: "camega-tolerie.com",
    169: "magmecanique.fr", 171: "mgf-grimaldi.com", 175: "acmg.fr", 176: "mecagemo.fr",
    182: "mggc.fr", 184: "somg.fr", 190: "lory-fonderies.fr", 193: "baxter-injection.com",
}

def fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(300000).decode("utf-8", "ignore")
    except Exception:
        return None

def emails_in(html):
    out = set()
    for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", (html or "").lower()):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".jpeg", ".gif",
                                ".js", ".css", ".svg", "schema.org", "w3.org", "sentry.io", "alpinejs",
                                "polyfill", "jquery", "email@domain", ".webp", "bootstrap", "cloudflare",
                                "google", "gstatic", "wp.com", "gravatar", "wordpress", "recrutement",
                                "sitemap", "no-reply", "noreply", "bicom", "creator_embed")):
            continue
        out.add(e)
    return sorted(out)

for idx, dom in SITES.items():
    paths = ["/", "/contact", "/contact.html", "/contact.php", "/contact.htm", "/nous-contacter",
             "/mentions-legales", "/mentions_legales", "/mentions", "/legal", "/infos", "/infos.html",
             "/coordonnees", "/coordonnees.html", "/page-contact", "/contactez-nous", "/nous-joindre",
             "/entreprise", "/societe", "/equipe", "/qui-sommes-nous", "/presentation"]
    urls = []
    for scheme in ("https", "http"):
        for p in paths:
            urls.append(scheme + "://" + dom + p)
    emails = set()
    texts = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = [ex.submit(fetch, u) for u in urls]
        for f in futs:
            try:
                h = f.result()
            except Exception:
                continue
            if not h:
                continue
            emails.update(emails_in(h))
            # extraire le texte autour des mots gerant/president/directeur
            for m in re.finditer(r"(g[eé]rant|pr[eé]sident|directeur)[^<>]{0,80}", h, re.I):
                texts.append(re.sub(r"\s+", " ", m.group(0)).strip())
    print(idx, dom, "| emails:", emails, flush=True)
    if texts:
        print("   dirigeants cites:", "; ".join(dict.fromkeys(texts))[:300], flush=True)
