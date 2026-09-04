# -*- coding: utf-8 -*-
# Verif live slicom.fr : alts, mailto, robots, sitemap. Lecture seule, aucune modification.
import urllib.request, ssl, re, json, os

TEMP = os.environ.get("TEMP", r"C:\Users\ulamb\AppData\Local\Temp")
H = open(os.path.join(TEMP, "slicom.html"), encoding="utf-8").read()
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

imgs = re.findall(r"<img[^>]+>", H, re.I)
empty = [i[:100] for i in imgs if re.search(r"alt=[\"']\s*[\"']", i, re.I) or ("alt=" not in i.lower())]
print("imgs:", len(imgs), "| alt vide/absent:", len(empty))
for e in empty[:8]:
    print("   ", e)

mails = sorted(set(re.findall(r"mailto:([^\"'?>\s]+)", H, re.I)))
print("MAILTO:", mails)
print("TEL:", sorted(set(re.findall(r"(?i)tel:([+\d.()\s-]{8,20})", H)))[:5])

for path in ["robots.txt", "sitemap.xml"]:
    try:
        r = urllib.request.urlopen(
            urllib.request.Request("https://slicom.fr/" + path, headers=UA),
            timeout=20, context=ctx,
        )
        print(path, "HTTP", r.status)
    except Exception as e:
        print(path, "ERR", type(e).__name__, str(e)[:70])

# hint JSON pour la suite
out = {"imgs": len(imgs), "alt_vide": len(empty), "mailto": mails}
with open(os.path.join(TEMP, "slicom_verif.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("OK")
