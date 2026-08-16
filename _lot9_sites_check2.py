#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 9 batch 2: verification des nouveaux sites trouves."""
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
    out = {"flags": [], "annees": [], "emails": set()}
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    out["title"] = re.sub(r"\s+", " ", t.group(1)).strip()[:130] if t else ""
    gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I)
    out["generator"] = gen.group(1)[:60] if gen else ""
    out["annees"] = sorted(set(re.findall(r"(?:19[89]\d|20[0-2]\d)", html)))
    m = re.search(r"(?:©|&copy;|copyright)\s*[^0-9]{0,30}((?:19\d\d|200\d|201\d|202[0-4]))", low)
    out["copyright"] = m.group(1) if m else None
    for cms, pat in (("wordpress", "wp-content"), ("joomla", "joomla"), ("drupal", "drupal"),
                     ("spip", "spip"), ("typo3", "typo3"), ("prestashop", "prestashop"),
                     ("magento", "magento"), ("wix", "wixstatic"), ("jimdo", "jimdo")):
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
    if re.search(r"\.asp\b|\.aspx\b|\.php\?", low):
        out["flags"].append("techno_vieille")
    if re.search(r"html4|transitional//en|xhtml", low):
        out["flags"].append("doctype_vieux")
    if "charset=windows" in low or "charset=iso-8859" in low:
        out["flags"].append("encodage_vieux")
    for m in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", low):
        if any(x in m for x in ("example", "wixpress", "sentry", "schema.org", "w3.org", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", "noreply", ".js", ".css")):
            continue
        out["emails"].add(m)
    out["emails"] = sorted(out["emails"])
    # texte visible (stripped) pour verifier contenu
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.I|re.S)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    out["texte"] = txt[:600]
    return out

CANDIDATS = [
    ("20", "PDG Plastiques", "www.pdg-plastiques.com", "http"),
    ("32", "Mecanique Baumoise de Precision", "www.mbp-usinage.fr", "https"),
    ("33", "MPI Issoirienne", "www.mpi-mecanique.com", "https"),
    ("36", "OMP Outillage", "www.omp-usinage.fr", "https"),
    ("37", "SOMEP", "somep.eu", "https"),
    ("41", "Kantemir", "www.kantemir.com", "https"),
    ("43", "Premetec", "www.premetec.fr", "https"),
    ("47", "Precision Industrielle Mecanique", "prime-sas.com", "https"),
    ("53", "Roch Mecanique", "rochmecanique.fr", "https"),
    ("52", "BPM Longvic", "www.bourgogneprecisionmecanique.fr", "http"),
]

def check(item):
    idx, nom, dom, proto = item
    pages = {}
    for path in ("", "/contact", "/contactez-vous", "/nous-contacter", "/mentions-legales", "/mentions_legales", "/societe", "/qui-sommes-nous", "/a-propos"):
        html, code, final = fetch(proto + "://" + dom + path)
        if code == 200 and html:
            pages[path] = analyse(html)
    res = {"index": idx, "nom": nom, "domaine": dom, "proto": proto}
    home = pages.get("", {})
    res["title"] = home.get("title", "")
    res["home"] = home
    res["emails"] = sorted({e for p in pages.values() for e in p.get("emails", [])})
    res["pages_trouvees"] = list(pages.keys())
    return res

def main():
    out = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(check, c): c for c in CANDIDATS}
        for f in as_completed(futs):
            try:
                r = f.result()
                out[r["index"]] = r
                print("=== %s | %s://%s" % (r["index"], r["proto"], r["domaine"]))
                print("  title:", r["title"])
                print("  pages:", r["pages_trouvees"])
                print("  emails:", r["emails"])
                print("  flags:", r["home"].get("flags"), "| copyright:", r["home"].get("copyright"), "| annees:", r["home"].get("annees", [])[-8:])
                print("  texte:", r["home"].get("texte", "")[:200])
            except Exception as e:
                print("ERR", e)
    json.dump(out, open(os.path.join(BASE, "_lot9_sites_check2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
