#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot10 : deep scan pages internes pour emails manquants."""
import json, re, time, urllib.request, urllib.parse

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

TARGETS = {
    80: "https://guillerme-decolletage.fr",
    108: "http://remo-outillage.fr",
    61: "https://usinage.com",
    68: "https://usinage-dieppois.fr",
    86: "https://www.gay-decolletage.fr",
    98: "http://fixouti.fr",
    66: "https://www.elcam-usinage.fr",
}

def fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(200000).decode("utf-8", "ignore")
    except Exception:
        return None

def emails_in(html):
    out = set()
    for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", (html or "").lower()):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".js",
                                ".css", ".svg", "schema.org", "w3.org", "sentry.io", "alpinejs",
                                "polyfill", "jquery", "email@domain", "escrow")):
            continue
        out.add(e)
    return out

def internal_links(html, base_dom):
    links = set()
    for m in re.finditer(r"href=[\"']([^\"']+)[\"']", html or "", re.I):
        u = m.group(1).strip()
        if u.startswith("mailto:") or u.startswith("tel:"):
            continue
        if "javascript" in u or u.startswith("#"):
            continue
        p = urllib.parse.urljoin("https://" + base_dom, u)
        netloc = urllib.parse.urlsplit(p).netloc.replace("www.", "")
        if netloc == base_dom.replace("www.", "") and not re.search(r"\.(png|jpe?g|gif|pdf|zip|svg|webp|ico)$", p, re.I):
            links.add(p)
    return links

out = {}
try:
    out = json.load(open(BASE + r"\_lot10_deep_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

for idx, home in TARGETS.items():
    if str(idx) in out:
        continue
    base_dom = urllib.parse.urlsplit(home).netloc.replace("www.", "")
    html_home = fetch(home)
    if not html_home:
        out[str(idx)] = {"emails": [], "pages": 0, "home": home}
        print(idx, "HOME DOWN", flush=True)
        continue
    emails = emails_in(html_home)
    links = internal_links(html_home, base_dom)
    # priorite aux pages contact/mentions
    prio = sorted([l for l in links if re.search(r"contact|mention|legal|qui-sommes|societe|infos", l, re.I)])
    others = [l for l in links if l not in prio]
    to_scan = (prio + others)[:15]
    print(idx, "|", len(links), "liens internes | scan", len(to_scan), "pages", flush=True)
    for u in to_scan:
        h = fetch(u)
        if h:
            emails |= emails_in(h)
        time.sleep(0.15)
    out[str(idx)] = {"emails": sorted(emails), "pages": len(to_scan), "home": home}
    print(idx, "-> EMAILS:", sorted(emails), flush=True)
    json.dump(out, open(BASE + r"\_lot10_deep_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TERMINE")
