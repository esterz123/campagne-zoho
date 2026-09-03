import json, io, os, re
os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")

# Reponses recentes : les 'traites' du repondeur ont des timestamps ; convertir les 10 derniers
rep = json.load(io.open("repondeur_state.json", encoding="utf-8"))
tr = rep.get("traites", [])
import datetime
def ts(x):
    m = re.search(r"(\d{16,19})", x)
    return int(m.group(1))[:16]/1e9 if m else 0
recent = sorted(tr, key=ts)[-8:]
for x in recent:
    t = datetime.datetime.fromtimestamp(ts(x))
    print(t.strftime("%d/%m %H:%M"), x)

# nb traite par jour
from collections import Counter
c = Counter(datetime.datetime.fromtimestamp(ts(x)).strftime("%d/%m") for x in tr)
print("\nmessages traites par jour:", dict(sorted(c.items())[-6:]))

# y a-t-il des messages non traites en attente ?
for k in rep:
    if k != "traites":
        print("\n", k, "->", json.dumps(rep[k], ensure_ascii=False)[:600])
