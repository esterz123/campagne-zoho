import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"C:\Users\ulamb\Bureau\prospection\github-campagne\campagne_data.json"
with open(p, encoding="utf-8") as f:
    data = json.load(f)
print("NB records:", len(data))
keys = set()
for d in data:
    keys.update(d.keys())
print("KEYS:", sorted(keys))
# date du jour
import datetime
today = datetime.date.today()
print("TODAY:", today.isoformat())
# candidats: relance2 7+ jours sans reponse, ou champs date/reponse
cands = []
for d in data:
    n = d.get("num")
    note = str(d.get("note", ""))
    low = note.lower()
    # detect dates in notes
    import re
    dates = re.findall(r"(\d{2})/(\d{2})", note)
    rel2 = d.get("relance2") or d.get("relance_2")
    rep = d.get("reponse") or d.get("reply")
    cands.append((n, d.get("prospect","")[:60], bool(rep), str(rel2)[:40]))
# afficher ceux avec un champ reponse
withrep = [c for c in cands if c[2]]
print("AVEC CHAMP REPONSE:", len(withrep))
for c in withrep[:20]:
    print(c)
# regarder les notes contenant 'relance' et 'j+'
cnt = 0
for d in data:
    low = str(d.get("note","")).lower()
    if "relance" in low:
        cnt += 1
print("NOTES AVEC 'relance':", cnt)
# afficher les dernieres cles des derniers records
print("--- LAST 3 records keys/values (truncated) ---")
for d in data[-3:]:
    for k, v in d.items():
        s = str(v)
        print(k, "=>", s[:180].replace("\n"," | "))
    print("=====")
