#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : verification profonde des sites candidats (SIREN, emails, CMS, copyright) + pages contact."""
import json, re, urllib.request, time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

# index -> (siren, site a verifier)
SITES = {
 111: ("976720284", "https://sdeb.fr/"),
 124: ("316842012", "https://uma02.fr/"),
 125: ("401884382", "https://samd-aero.fr/"),
 126: ("966500068", "https://lenoirmetallerie.fr/"),
 127: ("443830898", "https://oaca.fr/"),
 128: ("501007652", "https://batisud.org/"),
 129: ("310826698", "https://sudmetallerie.com/"),
 130: ("803868660", "https://lg-metallerie.fr/"),
 131: ("397020033", "https://groupe-gb.fr/gb-metallerie/"),
 132: ("793224759", "https://torras.fr/"),
 133: ("817734593", "https://metallerie.com/"),
 135: ("813390432", "https://www.gatsbysoudure.com/"),
 137: ("055802995", "https://soudecoup.fr/"),
 144: ("450396296", "https://atlantiquetoleriesoudure.fr/"),
 118: ("484871272", "https://www.smg-decoupage-tolerie.com/"),
 123: ("351174081", "https://sare-sarl-69.fr/"),
 110: ("419808985", "https://www.ernst.de/en/ernst-group/global-presence/ernst-france"),
 119: ("309054054", "https://www.isil-group.com/en/companies/sep/"),
 117: ("410599864", "https://www.ernst.de/en/contact-france"),
}

def get(url, maxbytes=400000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.read(maxbytes).decode("utf-8", "ignore")

def probe_site(idx, siren, url):
    out = {"url": url, "emails": [], "siren_ok": False, "copyright": [], "cms": [], "tables": 0, "viewport": False,
           "title": "", "final": url, "err": None, "mentions_url": None}
    try:
        html = get(url)
        out["title"] = re.findall(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)[:1]
        low = html.lower()
        out["siren_ok"] = siren in re.sub(r"\s", "", html)
        out["emails"] = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)))
        out["emails"] = [e for e in out["emails"] if not any(x in e.lower() for x in [".png", ".jpg", ".gif", ".webp", ".svg", "sentry", "wixpress", "example", "domain"])]
        cps = re.findall(r"©\s*(\d{4})(?:\s*[-–—]\s*(\d{4}))?", html)
        out["copyright"] = cps[:6]
        if "wp-content" in low or "wordpress" in low: out["cms"].append("WordPress")
        if "joomla" in low: out["cms"].append("Joomla")
        if "prestashop" in low: out["cms"].append("PrestaShop")
        if "spip" in low: out["cms"].append("SPIP")
        if "wix.com" in low or "wixstatic" in low: out["cms"].append("Wix")
        if "squarespace" in low: out["cms"].append("Squarespace")
        if "webflow" in low: out["cms"].append("Webflow")
        if "oxatis" in low: out["cms"].append("Oxatis")
        if "lws" in low and "sitebuilder" in low: out["cms"].append("LWS SiteBuilder")
        gen = re.findall(r'<meta[^>]*generator[^>]*content=["\']([^"\']+)', html, re.I)
        out["generator"] = gen[:3]
        out["tables"] = low.count("<table")
        out["viewport"] = '<meta name="viewport"' in low
        # pages contact/mentions
        links = set(re.findall(r'href=["\']([^"\']+)["\']', html))
        cand = []
        for l in links:
            ll = l.lower()
            if any(k in ll for k in ["contact", "mention", "legal", "nous-contacter"]):
                if l.startswith("http"):
                    cand.append(l)
                elif l.startswith("/") or l.startswith("."):
                    from urllib.parse import urljoin
                    cand.append(urljoin(url, l))
        for c in cand[:6]:
            try:
                h2 = get(c, 250000)
                em2 = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", h2)))
                em2 = [e for e in em2 if not any(x in e.lower() for x in [".png", ".jpg", ".gif", ".webp", ".svg", "sentry", "wixpress", "example"])]
                out["emails"] = sorted(set(out["emails"] + em2))
                if siren in re.sub(r"\s", "", h2):
                    out["siren_ok"] = True
                    out["mentions_url"] = c
                if re.search(r"©\s*\d{4}", h2):
                    out["copyright"] += re.findall(r"©\s*(\d{4})(?:\s*[-–—]\s*(\d{4}))?", h2)[:3]
            except Exception:
                pass
    except Exception as e:
        out["err"] = str(e)[:150]
    return idx, out

results = {}
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(probe_site, idx, siren, url): idx for idx, (siren, url) in SITES.items()}
    for f in as_completed(futs):
        idx, r = f.result()
        results[idx] = r

with open(f"{BASE}/_lot13_verif_tmp.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

for idx in sorted(results):
    r = results[idx]
    print(f"[{idx}] {r['url']}")
    print(f"    title={r['title']} siren_ok={r['siren_ok']} err={r['err']}")
    print(f"    emails={r['emails'][:6]}")
    print(f"    copyright={r['copyright'][:4]} cms={r['cms']} gen={r.get('generator','')} tables={r['tables']} viewport={r['viewport']} mentions={r['mentions_url']}")
