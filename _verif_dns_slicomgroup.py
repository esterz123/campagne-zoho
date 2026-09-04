# -*- coding: utf-8 -*-
# Verif DNS/HTTP du domaine slicom-group.com (mort ou pas aujourd'hui) + contexte GAMI dans le HTML live.
import socket, urllib.request, ssl, re, os, json

TEMP = os.environ.get("TEMP", r"C:\Users\ulamb\AppData\Local\Temp")
H = open(os.path.join(TEMP, "slicom.html"), encoding="utf-8").read()

# 1) GAMI : cite en texte sur la page ?
for m in re.finditer(r"(?i).{60}gami.{60}", H):
    print("CTX:", re.sub(r"\s+", " ", m.group(0)))

# 2) DNS A records
for dom in ["slicom-group.com", "slicom.fr", "groupe-gami.com"]:
    try:
        ips = sorted(set(i[4][0] for i in socket.getaddrinfo(dom, 443, socket.AF_INET)))
        print("A", dom, "->", ips)
    except Exception as e:
        print("A", dom, "ERR", type(e).__name__, str(e)[:60])

# 3) HTTP sur l'ancien domaine
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
for url in ["https://slicom-group.com", "http://slicom-group.com"]:
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=15, context=ctx,
        )
        print("HTTP", url, "->", r.status)
    except Exception as e:
        print("HTTP", url, "->", type(e).__name__, str(e)[:80])
print("DONE")
