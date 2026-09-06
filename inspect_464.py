"""Inspecte la fiche corrompue #464 (lecture seule)."""
import json

data = {d["num"]: d for d in json.load(open("campagne_data.json")) if isinstance(d, dict)}
d = data.get(464, {})
for k in ("num", "nom", "site", "to", "subject", "siren", "dirigeant", "source"):
    v = d.get(k)
    print(k, "=", repr(v)[:120])
st = json.load(open("campagne_state.json"))["sent"].get("464")
print("ETAT:", json.dumps(st, ensure_ascii=False)[:300])
