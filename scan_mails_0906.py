"""Scan tous les emails non envoyes : format valide ou poubelle."""
import json, re

st = json.load(open("campagne_state.json"))["sent"]
env = set()
for k in st:
    try:
        env.add(int(k))
    except ValueError:
        pass
ok_pat = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
n = 0
for d in json.load(open("campagne_data.json")):
    if not isinstance(d, dict) or d.get("num") in env:
        continue
    n += 1
    to = d.get("to") or ""
    if not ok_pat.match(to):
        print("POUBELLE #" + str(d.get("num")), repr(to), "|", d.get("nom"), "| source:", d.get("source"))
print("non envoyes verifies:", n)
