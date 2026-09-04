# -*- coding: utf-8 -*-
"""Structure fiches : envoyee vs restante — chef_structure_0903.py."""
import json, os

os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state["sent"]

# une fiche envoyee
for i, f in enumerate(data):
    if str(f.get("num", i)) in sent:
        print("=== FICHE ENVOYEE num=%s ===" % f.get("num", i))
        print("cles:", sorted(f.keys()))
        for k, v in f.items():
            v = str(v)
            print("  %s = %s" % (k, v[:120].replace("\n", " | ")))
        break

# une fiche restante
for i, f in enumerate(data):
    if str(f.get("num", i)) not in sent:
        print("\n=== FICHE RESTANTE num=%s ===" % f.get("num", i))
        print("cles:", sorted(f.keys()))
        for k, v in f.items():
            v = str(v)
            print("  %s = %s" % (k, v[:120].replace("\n", " | ")))
        break

# combien de restantes ont un champ corps non vide vs vide
rest = [f for i, f in enumerate(data) if str(f.get("num", i)) not in sent]
for champ in ("corps", "body", "message", "texte", "mail"):
    n_ok = sum(1 for f in rest if len(str(f.get(champ, "")).strip()) > 80)
    print("\nchamp '%s' rempli (>80c): %d/%d" % (champ, n_ok, len(rest)))
