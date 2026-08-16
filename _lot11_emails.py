#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot11 : scan emails sur pages contact/mentions-legales des sites confirmes."""
import json, re, time, urllib.request

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

SITES = {
    111: ["https://www.sdeb.fr/", "https://www.sdeb.fr/contact", "https://www.sdeb.fr/contact/", "https://www.sdeb.fr/mentions-legales", "https://www.sdeb.fr/mentions-legales/"],
    118: ["https://www.smg-decoupage-tolerie.com/", "https://www.smg-decoupage-tolerie.com/contact", "https://www.smg-decoupage-tolerie.com/contact/", "https://www.smg-decoupage-tolerie.com/mentions-legales", "https://www.smg-decoupage-tolerie.com/mentions-legales/"],
    123: ["https://www.sare-sarl-69.fr/", "https://www.sare-sarl-69.fr/contact", "https://www.sare-sarl-69.fr/contact/", "https://www.sare-sarl-69.fr/mentions-legales", "https://www.sare-sarl-69.fr/mentions-legales/"],
    124: ["https://uma.fr/", "https://uma.fr/contact", "https://uma.fr/contact/", "https://uma.fr/mentions-legales", "https://uma.fr/mentions-legales/", "https://www.uma.fr/"],
    128: ["https://www.batisud.org", "https://www.batisud.org/contact", "https://www.batisud.org/contact/", "https://www.batisud.org/mentions-legales"],
    130: ["https://www.lg-metallerie.fr/", "https://www.lg-metallerie.fr/contact", "https://www.lg-metallerie.fr/contact/", "https://www.lg-metallerie.fr/mentions-legales"],
    132: ["https://torras.fr/", "https://torras.fr/contact", "https://torras.fr/contact/", "https://torras.fr/mentions-legales", "https://torras.fr/mentions-legales/"],
    133: ["https://metalleriefrancilienne.fr/", "https://metalleriefrancilienne.fr/contact", "https://metalleriefrancilienne.fr/contact/", "https://metalleriefrancilienne.fr/mentions-legales", "https://metalleriefrancilienne.fr/mentions-legales/"],
    137: ["https://www.soudecoup.fr/", "https://www.soudecoup.fr/contact", "https://www.soudecoup.fr/contact/", "https://www.soudecoup.fr/mentions-legales", "https://www.soudecoup.fr/mentions-legales/"],
    144: ["https://atlantiquetoleriesoudure.fr/", "https://atlantiquetoleriesoudure.fr/contact", "https://atlantiquetoleriesoudure.fr/contact/", "https://atlantiquetoleriesoudure.fr/mentions-legales", "https://atlantiquetoleriesoudure.fr/mentions-legales/"],
    146: ["https://msi-industrie.fr/", "https://msi-industrie.fr/contact", "https://msi-industrie.fr/contact/", "https://msi-industrie.fr/mentions-legales", "https://msi-industrie.fr/mentions-legales/"],
    148: ["https://www.ti-ventilation.fr/", "https://www.ti-ventilation.fr/contact", "https://www.ti-ventilation.fr/contact/", "https://www.ti-ventilation.fr/mentions-legales", "https://www.ti-ventilation.fr/mentions-legales/"],
}

def fetch(url, timeout=9):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(150000).decode("utf-8", "ignore")
    except Exception:
        return None

def emails_in(html):
    out = set()
    for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", (html or "").lower()):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".js",
                                ".css", ".svg", "schema.org", "w3.org", "sentry.io", "alpinejs",
                                "polyfill", "jquery", "email@domain", "@2x", ".webp", ".jpeg")):
            continue
        out.add(e)
    return sorted(out)

out = {}
try:
    out = json.load(open(BASE + r"\_lot11_emails_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

for idx, urls in SITES.items():
    found = set()
    for u in urls:
        h = fetch(u)
        if h:
            found.update(emails_in(h))
    out[str(idx)] = sorted(found)
    print(idx, "->", sorted(found), flush=True)
    time.sleep(0.3)

json.dump(out, open(BASE + r"\_lot11_emails_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TERMINE", flush=True)
