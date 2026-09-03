# -*- coding: utf-8 -*-
"""Verification LIVE rouxel-mold.com : statut, titre, images sans alt, polices."""
import urllib.request, re, ssl, html

URL = "https://www.rouxel-mold.com/"
ctx = ssl.create_default_context()
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"})
try:
    resp = urllib.request.urlopen(req, timeout=15, context=ctx)
    raw = resp.read()
    print("STATUT HTTP:", resp.status)
    print("TAILLE:", len(raw), "octets")
    body = raw.decode("utf-8", errors="replace")
except Exception as ex:
    print("ERREUR:", ex)
    raise SystemExit(1)

title = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
print("TITRE:", html.unescape(title.group(1)).strip() if title else "ABSENT")

imgs = re.findall(r"<img\b[^>]*>", body, re.I)
no_alt = [i for i in imgs if not re.search(r"\balt\s*=\s*[\"'][^\"']+[\"']", i, re.I)]
print("IMAGES:", len(imgs), "| SANS ALT (attribut vide/absent):", len(no_alt))

polices = set(re.findall(r"font-family\s*:\s*([^;}\"]+)", body, re.I))
fam = {p.strip().strip("'\"").split(",")[0].strip() for p in polices if p.strip()}
google_fonts = set(re.findall(r"fonts\.googleapis\.com/css2?\?family=([A-Za-z+]+)", body))
print("FAMILLES font-family inline/CSS:", len(fam), sorted(fam)[:12])
print("GOOGLE FONTS chargees:", sorted(google_fonts))

viewport = bool(re.search(r"name=[\"']viewport[\"']", body, re.I))
https_ok = URL.startswith("https")
print("VIEWPORT MOBILE:", viewport, "| HTTPS:", https_ok)
# copyright fige ?
cr = re.findall(r"(?:&copy;|©)\s*(20\d{2})", body)
print("COPYRIGHT vus:", sorted(set(cr)))
# email publie ?
mails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", body))
mails = {m for m in mails if not m.lower().endswith((".png", ".jpg", ".webp"))}
print("EMAILS publies:", mails if mails else "AUCUN")
