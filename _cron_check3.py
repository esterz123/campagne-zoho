import json, io, os
os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")

# Que se passe-t-il aujourd'hui sur les 8 fiches touchees ?
s = json.load(io.open("campagne_state.json", encoding="utf-8"))
sent = s.get("sent", {})
today = "2026-09-03"
for k in ['149', '165', '129', '152', '408', '101', '201', '132']:
    print(k, "->", json.dumps(sent.get(k, {}), ensure_ascii=False)[:300])

# fiche correspondante
data = json.load(io.open("campagne_data.json", encoding="utf-8"))
fiches = data if isinstance(data, list) else data.get("fiches") or []
bynum = {str(f.get("num")): f for f in fiches}
print("\n===== fiches du jour =====")
for k in ['149', '165', '129', '152', '408', '101', '201', '132']:
    f = bynum.get(k) or {}
    print(k, f.get("prospect"), "| to:", f.get("to"), "| subj:", str(f.get("subject"))[:60])
