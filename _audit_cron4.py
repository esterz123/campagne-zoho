# -*- coding: utf-8 -*-
# Diagnostic ecart manifest vs fichiers pages diag
import json, os

man = json.load(open(r"C:\Users\ulamb\Bureau\prospection\github-campagne\diag_pages.json", encoding="utf-8"))
d = r"C:\Users\ulamb\Bureau\prospection\vitrine\diag"
files = {f[:-5] for f in os.listdir(d) if f.endswith(".html")}
print("manifest entrees:", len(man), "| fichiers html:", len(files))

sans_fichier_url = [n for n, v in man.items() if isinstance(v, dict) and v.get("url") and n not in files]
sans_fichier_none = [n for n, v in man.items() if isinstance(v, dict) and not v.get("url") and n not in files]
print("url ok mais fichier absent:", len(sans_fichier_none), len(sans_fichier_url))
print("url=None (injoignable):", len([n for n, v in man.items() if isinstance(v, dict) and not v.get("url")]))

data = json.load(open(r"C:\Users\ulamb\Bureau\prospection\github-campagne\campagne_data.json", encoding="utf-8"))
st = json.load(open(r"C:\Users\ulamb\Bureau\prospection\github-campagne\campagne_state.json", encoding="utf-8"))["sent"]
rest = [e for e in data if isinstance(e, dict) and str(e.get("num")) not in st]
print("restantes:", len(rest))
for e in rest:
    n = str(e["num"])
    m = man.get(n)
    print("#%s manifest=%s fichier=%s site=%s" % (n, "None-entree" if m and not m.get("url") else (str(m.get("score")) if m else "ABSENT"), n in files, (e.get("site") or "")[:40]))
