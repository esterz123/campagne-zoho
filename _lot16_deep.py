#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 16 : deep-check des sites (pages contact/mentions legales, emails, copyright, SIREN)."""
import json, re, urllib.request, urllib.error, ssl, socket

BASE = r"C:/Users/ulamb/Bureau/prospection/github-campagne"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
socket.setdefaulttimeout(10)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

SITES = {
    "976720284": "https://sdeb.fr",
    "351174081": "https://sare-sarl-69.fr",
    "501007652": "https://batisud.org",
    "803868660": "https://lg-metallerie.fr",
    "817734593": "https://metallerie.com",
    "414117945": "https://tolerie-service.fr",
    "434269411": "https://camega-tolerie.com",
    "525620332": "https://smg-decoupage-tolerie.com",
    "957502164": "https://fonderie-vincent.com",
    "399796861": "https://baxter-injection.com",
    "878798552": "https://anjou-injection.fr",
}
PAGES = ["/", "/contact", "/contact/", "/contact.html", "/contactez-nous", "/contactez-nous/", "/mentions-legales", "/mentions-legales/", "/mentions-légales", "/mentions-légales/", "/nous-contacter", "/nous-contacter/", "/equipe", "/equipe/", "/entreprise", "/entreprise/", "/qui-sommes-nous", "/qui-sommes-nous/"]

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
        with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
            return r.geturl(), r.status, r.read()
    except urllib.error.HTTPError as e:
        return url, e.code, b""
    except Exception:
        return url, 0, b""

out = {}
for siren, base in SITES.items():
    rec = {"siren": siren, "pages": {}}
    seen = set()
    for p in PAGES:
        if p in seen: continue
        seen.add(p)
        url = base + p
        final, status, body = fetch(url)
        if not body: 
            continue
        html = body.decode("utf-8", errors="replace")
        rec["pages"][p] = {
            "status": status,
            "taille": len(body),
            "title": re.sub(r"\s+", " ", (re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) or [None, ""])[1] if re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) else "").strip()[:100],
        }
        emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)))
        rec["pages"][p]["emails"] = [e for e in emails if "sentry" not in e and "wixpress" not in e and not e.endswith((".png", ".jpg", ".webp", ".gif", ".svg"))][:10]
        siren_norm = re.sub(r"[\s.\-\u00a0]", "", siren)
        rec["pages"][p]["siren"] = siren_norm in re.sub(r"[\s.\-\u00a0]", "", html)
        rec["pages"][p]["copyright"] = re.findall(r"(?:©|&copy;|copyright)\s*(?:<[^>]+>)*\s*(\d{4})", html, re.I)[:3]
        rec["pages"][p]["viewport"] = bool(re.search(r'name=["\']viewport["\']', html, re.I))
        rec["pages"][p]["wp"] = bool(re.search(r"wp-content|wp-includes|wordpress", html, re.I))
        # stop when we have home + one page with emails or mentions legales
    # merge: all emails found across pages
    alle = set()
    for p, info in rec["pages"].items():
        alle.update(info.get("emails", []))
    rec["emails_tous"] = sorted(alle)
    rec["siren_quelque_part"] = any(v.get("siren") for v in rec["pages"].values())
    out[siren] = rec
    print("=== ", siren, base)
    for p, info in rec["pages"].items():
        print("  ", p, info.get("status"), "|", info.get("title", "")[:60], "| siren:", info.get("siren"), "| copy:", info.get("copyright"), "| vp:", info.get("viewport"), "| wp:", info.get("wp"), "| emails:", info.get("emails", [])[:4])
    print("  TOUS EMAILS:", rec["emails_tous"])

json.dump(out, open(BASE + "/_lot16_deep_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE")
