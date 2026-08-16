#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot12 : scrape les pages contact/mentions des sites trouves pour emails + SIREN + signes datation."""
import json, re, time, urllib.request

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

SITES = {
    157: "tolerie-service.fr",
    158: "camega-tolerie.com",
    160: "smg-decoupage-tolerie.com",
    161: "tolerie-du-nord.fr",
    163: "cntolerie.fr",
    171: "mgf-grimaldi.fr",
    186: "fonderie-vincent.com",
    191: "ouest-injection.fr",
    193: "baxter-injection.com",
    198: "anjou-injection.fr",
    199: "injection74.fr",
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
                                "polyfill", "jquery", "email@domain", "sentry", "webpack", ".webp",
                                "bootstrap", "cloudflare", "google", "gstatic", "wp.com", "gravatar")):
            continue
        out.add(e)
    return sorted(out)

results = {}
for idx, dom in SITES.items():
    pages = [f"https://{dom}", f"https://www.{dom}",
             f"https://{dom}/contact", f"https://{dom}/contact/",
             f"https://{dom}/contact.php", f"https://{dom}/contact.html",
             f"https://{dom}/nous-contacter", f"https://{dom}/mentions-legales",
             f"https://{dom}/mentions-legales/", f"https://{dom}/mentions_legales",
             f"https://{dom}/mentions-legales.html", f"https://{dom}/legal",
             f"https://{dom}/contactez-nous", f"https://{dom}/nous-contacter/",
             f"https://{dom}/contact/contact.html", f"https://{dom}/fr/contact",
             f"https://{dom}/fr/mentions-legales", f"https://{dom}/info",
             f"https://{dom}/a-propos", f"https://{dom}/qui-sommes-nous"]
    all_html = ""
    found_emails = set()
    siren_found = []
    for u in pages:
        h = fetch(u)
        if h:
            all_html += h
            es = emails_in(h)
            found_emails.update(es)
            for s in re.findall(r"\b\d{3}[\s.\-]?\d{3}[\s.\-]?\d{3}\b", h):
                s9 = re.sub(r"\D", "", s)
                if s9 not in siren_found:
                    siren_found.append(s9)
        time.sleep(0.2)
    results[str(idx)] = {"domaine": dom, "emails": sorted(found_emails), "sirens": siren_found[:5]}
    print(idx, dom, "| emails:", sorted(found_emails)[:6], "| sirens:", siren_found[:3], flush=True)

json.dump(results, open(BASE + r"\_lot12_emails_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK")
