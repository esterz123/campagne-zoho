#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot12 : verification SIREN + emails sur TOUTES les pages internes des sites candidats."""
import json, re, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

SIRENS = {
    157: "414117945", 158: "434269411", 160: "525620332", 161: "441283918",
    163: "554502476", 171: "313002214", 186: "957502164", 191: "775604945",
    193: "399796861", 198: "878798552", 199: "388781544",
    152: "315189597", 167: "352688428", 153: "392316782",
}

def fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(400000).decode("utf-8", "ignore")
    except Exception:
        return None

def emails_in(html):
    out = set()
    for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", (html or "").lower()):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".jpeg", ".gif",
                                ".js", ".css", ".svg", "schema.org", "w3.org", "sentry.io", "alpinejs",
                                "polyfill", "jquery", "email@domain", ".webp", "bootstrap", "cloudflare",
                                "google", "gstatic", "wp.com", "gravatar", "wordpress", "recrutement")):
            continue
        out.add(e)
    return sorted(out)

def internal_links(html, dom):
    links = set()
    for m in re.findall(r'href=["\']([^"\']+)["\']', html or ""):
        u = m.split("#")[0]
        if u.startswith("/") and len(u) > 1:
            links.add("https://" + dom + u)
        elif dom in u and u.startswith("http"):
            links.add(u)
    return list(links)[:40]

SITES = {152: "tifsas.com", 153: "gromy.fr", 157: "tolerie-service.fr", 158: "camega-tolerie.com",
         160: "smg-decoupage-tolerie.com", 161: "tolerie-du-nord.fr", 163: "cntolerie.fr",
         167: "dmg-decoupage.com", 171: "mgf-grimaldi.fr", 186: "fonderie-vincent.com",
         191: "ouest-injection.fr", 193: "baxter-injection.com", 198: "anjou-injection.fr",
         199: "injection74.fr"}

results = {}
for idx, dom in SITES.items():
    siren = SIRENS[idx]
    home = fetch("https://" + dom)
    if not home:
        results[str(idx)] = {"domaine": dom, "erreur": "home injoignable"}
        print(idx, dom, "HOME INJOIGNABLE", flush=True)
        continue
    pages = ["https://" + dom, "https://www." + dom] + internal_links(home, dom)
    siren_hit = False
    emails = set()
    html_all = home
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch, u) for u in pages[:35]]
        for f in futs:
            try:
                h = f.result()
            except Exception:
                continue
            if not h:
                continue
            html_all += h
            low = h.lower()
            if siren in re.sub(r"[\s.\-\u00a0]", "", low):
                siren_hit = True
            emails.update(emails_in(h))
    # scan sitemap si pas de siren
    if not siren_hit:
        sm = fetch("https://" + dom + "/sitemap.xml")
        if sm:
            urls = re.findall(r"<loc>(.*?)</loc>", sm)[:30]
            for u in urls:
                h = fetch(u)
                if h:
                    low = h.lower()
                    if siren in re.sub(r"[\s.\-\u00a0]", "", low):
                        siren_hit = True
                    emails.update(emails_in(h))
    results[str(idx)] = {"domaine": dom, "siren": siren, "siren_hit": siren_hit, "emails": sorted(emails)}
    print(idx, dom, "| SIREN", siren, "| HIT:", siren_hit, "| emails:", sorted(emails)[:8], flush=True)
    time.sleep(0.2)

json.dump(results, open(BASE + r"\_lot12_verif_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK")
