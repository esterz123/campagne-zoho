# -*- coding: utf-8 -*-
# Vendeur: identifier prospects sous-exploites (relance2+ >= 7j sans reponse)
import json
from datetime import date

p = r"C:\Users\ulamb\Bureau\prospection\github-campagne\campagne_state.json"
d = json.load(open(p, encoding="utf-8"))
sent = d.get("sent", {})
print("nb entrees sent:", len(sent))
today = date(2026, 9, 1)

def d2(x):
    try:
        return date.fromisoformat(str(x)[:10])
    except Exception:
        return None

cands = []
for k, v in sent.items():
    r1 = v.get("sent_relance1")
    r2 = v.get("sent_relance2")
    r3 = v.get("sent_relance3")
    last = r3 or r2 or r1
    dt = d2(last) if last else None
    days = (today - dt).days if dt else -1
    if days >= 7:
        cands.append((k, str(v.get("note", ""))[:60], r1, r2, r3, days))

print("relances >=7j:", len(cands))
for c in sorted(cands, key=lambda x: -x[5])[:60]:
    print(c)

print("---notes non vides---")
for k, v in sent.items():
    n = str(v.get("note", ""))
    if n.strip():
        print(k, "->", n[:140])
