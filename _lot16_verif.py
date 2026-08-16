#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 16 : verification directe des sites candidats (curl-like, signaux HTML)."""
import json, re, urllib.request, urllib.error, ssl, socket

BASE = r"C:/Users/ulamb/Bureau/prospection/github-campagne"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
socket.setdefaulttimeout(10)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SITES = {
    "419168448": ["https://gilletsa.com", "http://gilletsa.com"],
    "976720284": ["https://sdeb.fr", "http://sdeb.fr"],
    "351174081": ["https://sare-sarl-69.fr", "http://sare-sarl-69.fr"],
    "501007652": ["https://batisud.org", "http://batisud.org"],
    "803868660": ["https://lg-metallerie.fr", "http://lg-metallerie.fr"],
    "817734593": ["https://metallerie.com", "http://metallerie.com"],
    "320800139": ["https://tolerie-industrielle.fr", "http://tolerie-industrielle.fr"],
    "414117945": ["https://tolerie-service.fr", "http://tolerie-service.fr"],
    "434269411": ["https://camega-tolerie.com", "http://camega-tolerie.com"],
    "525620332": ["https://smg-decoupage-tolerie.com", "http://smg-decoupage-tolerie.com"],
    "957502164": ["https://fonderie-vincent.com", "http://fonderie-vincent.com"],
    "405223843": ["https://fonderies.fr", "http://fonderies.fr"],
    "399796861": ["https://baxter-injection.com", "http://baxter-injection.com"],
    "878798552": ["https://anjou-injection.fr", "http://anjou-injection.fr"],
}

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
        with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
            body = r.read()
            return r.geturl(), r.status, body
    except urllib.error.HTTPError as e:
        return url, e.code, b""
    except Exception as e:
        return url, 0, b""

out = {}
for siren, urls in SITES.items():
    rec = {"siren": siren}
    for u in urls:
        try:
            final, status, body = fetch(u)
        except Exception as e:
            final, status, body = u, 0, b""
        if status and body:
            rec["url"] = final
            rec["status"] = status
            rec["taille"] = len(body)
            try:
                html = body.decode("utf-8", errors="replace")
            except Exception:
                html = body.decode("latin-1", errors="replace")
            title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
            rec["title"] = re.sub(r"\s+", " ", title.group(1)).strip()[:120] if title else ""
            gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I) or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']generator["\']', html, re.I)
            rec["generator"] = gen.group(1).strip()[:80] if gen else ""
            years = re.findall(r"(?:©|&copy;|copyright)\s*(?:<[^>]+>)*\s*(\d{4})", html, re.I)
            years2 = re.findall(r"\b(19\d\d|20\d\d)\b", html)
            rec["copyright"] = years[:3]
            rec["viewport"] = bool(re.search(r'name=["\']viewport["\']', html, re.I))
            rec["tables"] = html.lower().count("<table")
            rec["wp"] = bool(re.search(r"wp-content|wp-includes|wordpress", html, re.I))
            rec["emails"] = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)))[:15]
            siren_norm = re.sub(r"[\s.\-\u00a0]", "", siren)
            rec["siren_sur_site"] = siren_norm in re.sub(r"[\s.\-\u00a0]", "", html)
            rec["framework"] = "WP" if rec["wp"] else ("tables" if rec["tables"] > 0 and "generator" in rec and not rec["generator"] else "html")
            break
        else:
            rec.setdefault("erreurs", []).append(f"{u} -> {status}")
    out[siren] = rec
    print(siren, rec.get("status"), rec.get("title", "")[:60], "| gen:", rec.get("generator", "")[:40], "| siren:", rec.get("siren_sur_site"), "| emails:", rec.get("emails", [])[:3], flush=True)

json.dump(out, open(BASE + "/_lot16_verif_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE")
