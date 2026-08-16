#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot12 ter : scan emails + cms + copyright sur toutes les pages internes (http+https)."""
import json, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

SITES = {
    152: "tifsas.com", 158: "camega-tolerie.com", 161: "tolerie-du-nord.fr",
    163: "cntolerie.fr", 169: "magmecanique.fr", 175: "acmg.fr", 176: "mecagemo.fr",
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
                                "sitemap", "no-reply", "noreply", "bicom")):
            continue
        out.add(e)
    return sorted(out)

results = {}
for idx, dom in SITES.items():
    home = None
    for scheme in ("https", "http"):
        home = fetch(scheme + "://" + dom)
        if home:
            break
        home = fetch(scheme + "://www." + dom)
        if home:
            break
    if not home:
        results[str(idx)] = {"domaine": dom, "erreur": "injoignable"}
        print(idx, dom, "INJOIGNABLE", flush=True)
        continue
    links = set()
    for m in re.findall(r'href=["\']([^"\']+)["\']', home):
        u = m.split("#")[0]
        if u.startswith("/") and len(u) > 1:
            links.add("http://" + dom + u)
            links.add("https://" + dom + u)
        elif dom in u and u.startswith("http"):
            links.add(u)
    html_all = home
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch, u) for u in list(links)[:40]]
        for f in futs:
            try:
                h = f.result()
            except Exception:
                continue
            if h:
                html_all += h
    low = html_all.lower()
    cms = []
    if re.search(r"wp-content|wp-includes|wordpress", low): cms.append("WordPress")
    if re.search(r"joomla|com_content", low): cms.append("Joomla")
    if re.search(r"prestashop", low): cms.append("PrestaShop")
    yrs = re.findall(r"(?:copyright|©|&copy;)\s*(?:[^\n<]{0,40}?\s)?(20[0-2][0-9])", html_all, re.I)
    years = sorted(set(int(y) for y in yrs if 1990 <= int(y) <= 2030))
    if not years:
        yrs2 = re.findall(r"\b20(0[0-9]|1[0-9])\b", html_all)
        years = sorted(set(int("20" + y) for y in yrs2))[:6]
    results[str(idx)] = {"domaine": dom, "cms": cms, "copyright": years,
                         "tables": low.count("<table"), "emails": emails_in(html_all)}
    print(idx, dom, "| CMS:", cms, "| cop:", years, "| tables:", low.count("<table"),
          "| emails:", results[str(idx)]["emails"][:8], flush=True)
    time.sleep(0.2)

json.dump(results, open(BASE + r"\_lot12_ter_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK")
