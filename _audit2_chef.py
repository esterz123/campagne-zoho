# -*- coding: utf-8 -*-
"""Audit journal boucle + relance closing + fichier chaud."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

# Journal boucle auto-amelioration
try:
    j = load("amelioration_journal.json")
    cyc = j[-1] if isinstance(j, list) else j
    print("DERNIER CYCLE JOURNAL:")
    print(json.dumps(cyc, ensure_ascii=False, indent=1)[:700])
except Exception as e:
    print("journal:", e)

print()

# Relance closing SIMI
import os
p = "livrable/relance_closing_SIMI.txt"
if os.path.exists(p):
    print("RELANCE CLOSING SIMI (premieres lignes):")
    txt = open(p, encoding="utf-8", errors="replace").read()
    print(txt[:400])
else:
    print("relance_closing_SIMI.txt: ABSENT")

print()

# Fiche 63 Gaultier: le message collab pret
d = load("campagne_data.json")
fiches = d if isinstance(d, list) else d.get("campagne", [])
f63 = next((f for f in fiches if str(f.get("num")) == "63"), None)
if f63:
    print("FICHE 63 GAULTIER:")
    for k in ("to", "dirigeant", "statut", "note", "audit_suivi"):
        v = f63.get(k)
        if v:
            print(f"  {k}: {str(v)[:150]}")

# Count sent aujourd'hui
st = load("campagne_state.json")
sent = st.get("sent", {})
auj = [n for n, s in sent.items() if isinstance(s, dict) and s.get("on") == "2026-09-03"]
print(f"\nEnvois marques ON aujourd'hui: {len(auj)} -> {auj[:15]}")
