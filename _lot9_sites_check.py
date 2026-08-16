#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 9: verification approfondie d'une liste de sites candidats (faits + emails + SIREN)."""
import json, os, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0",
      "Accept-Language": "fr-FR,fr;q=0.8", "Accept": "text/html"}

def fetch(url, tries=2):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=12) as r:
                return r.read(400000).decode("utf-8", "ignore"), r.getcode(), r.geturl()
        except Exception:
            if i == tries - 1:
                return "", 0, ""
            time.sleep(1)
    return "", 0, ""

def analyse(html):
    low = html.lower()
    out = {"flags": [], "annees": [], "emails": set(), "phones": set()}
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    out["title"] = re.sub(r"\s+", " ", t.group(1)).strip()[:130] if t else ""
    gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I)
    out["generator"] = gen.group(1)[:60] if gen else ""
    mdesc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I)
    out["meta_desc"] = (mdesc.group(1)[:160] if mdesc else "")
    out["annees"] = sorted(set(re.findall(r"(?:19[89]\d|20[0-2]\d)", html)))
    # copyright explicite
    m = re.search(r"(?:©|&copy;|copyright)\s*[^0-9]{0,30}((?:19\d\d|200\d|201\d|202[0-4]))", low)
    out["copyright"] = m.group(1) if m else None
    # CMS
    for cms, pat in (("wordpress", "wp-content"), ("joomla", "joomla"), ("drupal", "drupal"),
                     ("spip", "spip"), ("typo3", "typo3"), ("prestashop", "prestashop"),
                     ("magento", "magento"), ("wix", "wixstatic"), ("jimdo", "jimdo"),
                     ("sitego", "sitego"), ("1and1", "1und1")):
        if pat in low:
            out["flags"].append(cms)
    if low.count("<table") >= 3:
        out["flags"].append("tables_html")
    if re.search(r"\.swf|application/x-shockwave|flash", low):
        out["flags"].append("flash")
    if "viewport" not in low:
        out["flags"].append("pas_de_viewport_mobile")
    if "google-analytics" not in low and "gtag" not in low and "matomo" not in low:
        out["flags"].append("pas_de_tracking")
    if re.search(r"<!--\s*#include|\.asp\b|\.aspx\b|\.php\?", low):
        out["flags"].append("techno_vieille")
    for m in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", low):
        if any(x in m for x in ("example", "wixpress", "sentry", "schema.org", "w3.org", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", "noreply", "sentry.io", ".js", ".css", "godaddy")):
            continue
        out["emails"].add(m)
    for m in re.findall(r"(?:0\d(?:[ .-]?\d{2}){4})", html):
        out["phones"].add(m)
    out["emails"] = sorted(out["emails"])
    out["phones"] = sorted(out["phones"])[:5]
    return out

CANDIDATS = [
    # (index, nom, domaine)
    ("11", "ATEMIP", "www.atemip.com"),
    ("13", "Plastique-Industries", "www.plastique-industries.fr"),
    ("20", "P.D.G. Plastiques", "www.pdg-plastiques.com"),
    ("22", "MEP Louvres", "www.groupemep.com"),
    ("22b", "MEP Louvres (alt)", "m-e-p.fr"),
    ("24", "Plastiques Faconnes du Bethunois", "www.plast-fb.com"),
    ("27", "Mousses Plastiques d'Artois", "www.mousse-plastique-artois.com"),
    ("28", "Maison du Caoutchouc et Plastique", "www.mcp-fournitures-industrielles.fr"),
    ("52", "Bourgogne Precision Mecanique", "www.bourgogneprecisionmecanique.fr"),
    ("14", "Nobel Plastiques", "www.nobelplastiques.fr"),
    ("14b", "Nobel Plastiques (alt)", "www.nobel-plastiques.fr"),
]

def check(item):
    idx, nom, dom = item
    pages = {}
    for path in ("", "/contact", "/contactez-nous", "/nous-contacter", "/mentions-legales", "/mentions_legales", "/societe", "/qui-sommes-nous", "/index.html"):
        html, code, final = fetch("https://" + dom + path)
        if code == 200 and html:
            pages[path] = analyse(html)
    res = {"index": idx, "nom": nom, "domaine": dom}
    home = pages.get("", {})
    res["title"] = home.get("title", "")
    res["home"] = home
    res["emails"] = sorted({e for p in pages.values() for e in p.get("emails", [])})
    res["phones"] = sorted({ph for p in pages.values() for ph in p.get("phones", [])})[:4]
    res["copyright"] = home.get("copyright")
    res["pages_trouvees"] = list(pages.keys())
    return res

def main():
    out = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(check, c): c for c in CANDIDATS}
        for f in as_completed(futs):
            try:
                r = f.result()
                out[r["index"] + "|" + r["domaine"]] = r
                print("=== %s | %s" % (r["index"], r["domaine"]))
                print("  title:", r["title"])
                print("  pages:", r["pages_trouvees"])
                print("  emails:", r["emails"])
                print("  phones:", r["phones"])
                print("  flags:", r["home"].get("flags"), "| copyright:", r["copyright"], "| annees:", r["home"].get("annees", [])[-8:])
            except Exception as e:
                print("ERR", e)
    json.dump(out, open(os.path.join(BASE, "_lot9_sites_check.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
