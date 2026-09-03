import json, io, os
os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")

# 1. Combien de fiches envoyees selon campagne_state.sent
s = json.load(io.open("campagne_state.json", encoding="utf-8"))
sent = s.get("sent", {})
n_sent = len(sent)
dates = sorted(v.get("on", "?") for v in sent.values())
print("sent count:", n_sent, "| premier:", dates[0] if dates else "-", "| dernier:", dates[-1] if dates else "-")

# relances du jour?
import datetime
today = "2026-09-03"
rel_today = [k for k, v in sent.items() if any(str(x).startswith(today) for x in v.values() if isinstance(x, str))]
print("fiches touchees aujourd'hui via sent:", rel_today[:20], "total:", len(rel_today))

# 2. campagne_data : structure reelle
data = json.load(io.open("campagne_data.json", encoding="utf-8"))
fiches = data if isinstance(data, list) else data.get("fiches") or data.get("prospects") or []
if isinstance(fiches, dict):
    fiches = list(fiches.values())
keys = set()
for f in fiches[:50]:
    keys.update(f.keys())
print("champs fiches:", sorted(keys))
print("total fiches:", len(fiches))

# 3. journal d'amelioration (dernier rapport bot)
j = json.load(io.open("amelioration_journal.json", encoding="utf-8"))
jl = j if isinstance(j, list) else j.get("entrees") or j.get("journal") or []
print("\n===== journal (5 dernieres) =====")
for e in (jl if isinstance(jl, list) else [])[-5:]:
    print(json.dumps(e, ensure_ascii=False)[:400])
