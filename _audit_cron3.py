# -*- coding: utf-8 -*-
# Audit 3 : bounces recents, qualite file restante, pages diag, relance SIMI
import json, os, datetime as dt, re

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
os.chdir(BASE)

st = json.load(open("campagne_state.json", encoding="utf-8"))
sent = st.get("sent", {})
data = json.load(open("campagne_data.json", encoding="utf-8"))
by_num = {str(e.get("num")): e for e in data if isinstance(e, dict)}

# bounces par semaine
from collections import Counter
cb = Counter()
for n, e in sent.items():
    if isinstance(e, dict) and e.get("bounce"):
        on = str(e.get("on", "?"))[:7]
        cb[on] += 1
print("bounces par mois d'envoi:", dict(cb))

# bounces sur envois des 14 derniers jours
recent_b = [(n, e.get("on"), by_num.get(n, {}).get("entreprise", by_num.get(n, {}).get("nom", "?")))
            for n, e in sent.items() if isinstance(e, dict) and e.get("bounce") and str(e.get("on", "")) >= "2026-08-20"]
print("bounces depuis 20/08:", len(recent_b))
for x in sorted(recent_b, key=lambda t: str(t[1]), reverse=True)[:8]:
    print("  ", x)

# file restante : qualite
rest = [e for e in data if isinstance(e, dict) and str(e.get("num")) not in sent]
try:
    constats = json.load(open("constats_sites.json", encoding="utf-8"))
except Exception:
    constats = {}
def note(n):
    c = constats.get(str(n)) or constats.get(int(n)) if not isinstance(constats, dict) else constats.get(str(n))
    if isinstance(c, dict):
        return c.get("note"), c.get("etat", "")
    return None, ""
qual = Counter(); vivantes = []
for e in rest:
    n = str(e.get("num"))
    nt, etat = note(n)
    site = e.get("site") or e.get("url")
    if etat in ("MORT",) or (isinstance(nt, int) and nt == 0):
        qual["site_mort"] += 1
    elif etat == "BLOQUE":
        qual["bloque"] += 1
    else:
        qual["ok_ou_inconnu"] += 1
        vivantes.append(n)
print("file restante qualite:", dict(qual))

# pages diag couverture des restantes
pages_dir = r"C:\Users\ulamb\Bureau\prospection\vitrine\diag"
have = set()
if os.path.isdir(pages_dir):
    have = {f[:-5] for f in os.listdir(pages_dir) if f.endswith(".html")}
missing = [n for n in (str(e.get("num")) for e in rest) if n not in have]
print("pages diag: restantes sans page=%d / %d" % (len(missing), len(rest)))
print("exemples sans page:", missing[:12])

# relance closing SIMI : contenu + deadline
p = os.path.join(BASE, "livrable", "relance_closing_SIMI.txt")
if os.path.exists(p):
    txt = open(p, encoding="utf-8").read()
    print("=== relance_closing_SIMI.txt (726o) ===")
    print(txt[:800])
