# -*- coding: utf-8 -*-
"""Inspection 3 noms contradictoires + potentiel d'ajout de noms R1 — chef_inspect_0903.py."""
import json, re, os

os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state["sent"]
by_num = {str(f.get("num", i)): f for i, f in enumerate(data)}

# ---- 1. Les 3 fiches a noms contradictoires ----
for num in ("249", "362", "421"):
    f = by_num.get(num, {})
    prem = str(f.get("body", "")).split("\n")[0]
    print("#%s dirigeant=%r site=%r to=%r" % (num, f.get("dirigeant"), f.get("site"), f.get("to")))
    print("   1re ligne: %s" % prem[:80])

# ---- 2. Potentiel R1 : fiches restantes qui commencent par 'Bonjour,' mais ont un dirigeant ----
potentiel = []
for i, f in enumerate(data):
    num = str(f.get("num", i))
    if num in sent:
        continue
    prem = str(f.get("body", "")).split("\n")[0].strip()
    d = str(f.get("dirigeant", "")).strip()
    if prem == "Bonjour," and d and len(d) > 3:
        potentiel.append((num, d[:40], prem[:30]))
print("\nR1 'Bonjour,' AVEC dirigeant connu (ajout possible):", len(potentiel))
for num, d, p in potentiel[:15]:
    print("  #%s dirigeant=%s" % (num, d))

# format des valeurs dirigeant
print("\nechantillon formats dirigeant:")
seen = set()
for i, f in enumerate(data):
    d = str(f.get("dirigeant", "")).strip()
    if d and d not in seen and len(seen) < 12:
        seen.add(d)
        print("  %r" % d)
