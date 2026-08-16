#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot11 : re-scan 123/124/128/130 + contenu gatsby."""
import json, re, time, urllib.request

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

def fetch(url, timeout=12, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(200000).decode("utf-8", "ignore")
        except Exception:
            time.sleep(2)
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

SITES = {
    123: ["https://www.sare-sarl-69.fr/", "https://www.sare-sarl-69.fr/contact", "https://www.sare-sarl-69.fr/mentions-legales", "https://www.sare-sarl-69.fr/contact.php"],
    124: ["https://uma.fr/", "https://uma.fr/contact", "https://uma.fr/mentions-legales", "https://www.uma.fr/"],
    128: ["https://www.batisud.org", "https://www.batisud.org/contact", "https://www.batisud.org/mentions-legales", "http://www.batisud.org/"],
    130: ["https://www.lg-metallerie.fr/", "https://www.lg-metallerie.fr/contact", "https://www.lg-metallerie.fr/mentions-legales", "http://www.lg-metallerie.fr/"],
    135: ["https://www.gatsbysoudure.com/", "http://www.gatsbysoudure.com/"],
}

out = {}
try:
    out = json.load(open(BASE + r"\_lot11_deep_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

for idx, urls in SITES.items():
    found = {}
    for u in urls:
        h = fetch(u)
        if not h:
            continue
        es = emails_in(h)
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).lower()
        title = (re.search(r"<title[^>]*>(.*?)</title>", h, re.S | re.I) or [None, ""])[1][:70] if re.search(r"<title[^>]*>(.*?)</title>", h, re.S | re.I) else ""
        found[u] = {"emails": es, "title": title, "len": len(h)}
        print(idx, u, "| len:", len(h), "|", title[:50], "|", es[:4], flush=True)
        if idx == 135:
            print("   TEXT:", t[:400], flush=True)
    if str(idx) in out and out[str(idx)]:
        out[str(idx)].update(found)
    else:
        out[str(idx)] = found
    json.dump(out, open(BASE + r"\_lot11_deep_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(0.5)
print("TERMINE", flush=True)
