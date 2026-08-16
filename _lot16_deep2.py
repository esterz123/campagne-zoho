#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 16 : deep check 2e vague (omedec, baxter, batisud, gillet-stsi, nde, clickoutil, metallerie)."""
import json, re, urllib.request, urllib.error, ssl, socket, html as H

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
socket.setdefaulttimeout(10)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

TARGETS = {
    "311666077_OMEDEC": ["https://omedec.com", "https://omedec.com/contact", "https://omedec.com/contact/", "https://omedec.com/mentions-legales", "https://omedec.com/mentions-legales/"],
    "399796861_BAXTER": ["https://www.baxter-injection.com", "https://www.baxter-injection.com/contact", "https://www.baxter-injection.com/contact/", "https://www.baxter-injection.com/mentions-legales", "https://www.baxter-injection.com/mentions-legales/", "https://www.baxter-injection.com/contact.html", "https://www.baxter-injection.com/nous-contacter", "https://www.baxter-injection.com/nous-contacter/"],
    "501007652_BATISUD": ["http://batisud.org", "http://batisud.org/contact", "http://batisud.org/contact/", "http://batisud.org/mentions-legales", "http://batisud.org/mentions-legales/", "http://batisud.org/contact.html", "http://batisud.org/nous-contacter", "http://batisud.org/nous-contacter/"],
    "419168448_GILLET": ["https://gillet-decolletage.com", "https://gillet-decolletage.com/contact", "https://gillet-decolletage.com/contact/", "https://gillet-decolletage.com/mentions-legales", "https://gillet-decolletage.com/mentions-legales/", "https://gillet-decolletage.com/nous-contacter", "https://gillet-decolletage.com/nous-contacter/"],
    "419808985_NDE": ["https://sites.google.com/view/nde-crulai", "https://sites.google.com/view/nde-crulai/accueil", "https://sites.google.com/view/nde-crulai/contact"],
    "303376222_CLICKOUTIL": ["http://clickoutil.fr", "http://clickoutil.fr/mentions-legales", "http://clickoutil.fr/mentions-legales/", "http://clickoutil.fr/contact", "http://clickoutil.fr/contact/", "http://clickoutil.fr/nous-contacter", "http://clickoutil.fr/nous-contacter/"],
    "817734593_METALLERIE": ["https://metallerie.com", "https://metallerie.com/entreprise", "https://metallerie.com/contact", "https://metallerie.com/contact/"],
}

def strip_html(h):
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", H.unescape(h)).strip()

out = {}
for k, urls in TARGETS.items():
    rec = {"pages": {}}
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
            with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
                b = r.read()
            html = b.decode("utf-8", "replace")
            rec["pages"][u] = {
                "status": 200, "taille": len(b),
                "title": re.sub(r"\s+", " ", (re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) or [None, ""])[1]).strip()[:110] if re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I) else "",
                "generator": (re.search(r'name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I) or [None, ""])[1][:60],
                "viewport": bool(re.search(r'name=["\']viewport["\']', html, re.I)),
                "tables": html.lower().count("<table"),
                "copyright": re.findall(r"(?:©|&copy;|copyright)\s*(?:<[^>]+>)*\s*(\d{4})", html, re.I)[:3],
                "emails": [e for e in sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html))) if "sentry" not in e and "wixpress" not in e and not e.endswith((".png", ".jpg", ".webp", ".gif", ".svg"))][:10],
                "siren": {k.split("_")[0]: k.split("_")[0] in re.sub(r"[\s.\-\u00a0]", "", html) for k in []},
                "text": strip_html(html)[:700],
            }
            siren = k.split("_")[0]
            rec["pages"][u]["siren_ok"] = siren in re.sub(r"[\s.\-\u00a0]", "", html)
        except Exception as e:
            rec["pages"][u] = {"status": "ERR", "err": str(e)[:60]}
    out[k] = rec
    print("===", k)
    for u, p in rec["pages"].items():
        if p.get("status") == "ERR":
            print("  ", u, "-> ERR", p.get("err"))
        else:
            print("  ", u, "->", p["status"], p["taille"], "| gen:", p["generator"], "| vp:", p["viewport"], "| tables:", p["tables"], "| copy:", p["copyright"], "| siren:", p.get("siren_ok"), "| emails:", p["emails"])
            print("     TXT:", p["text"][:220].replace("\n", " "))

json.dump(out, open("_lot16_deep2_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE")
