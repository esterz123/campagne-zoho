"""Fiche #464 suspecte (email u002f = slash echappe)."""
import json

data = {d["num"]: d for d in json.load(open("campagne_data.json")) if isinstance(d, dict)}
d = data.get(464, {})
for k in ("num", "nom", "site", "to", "subject", "dirigeant", "source"):
    print(k, "=", repr(d.get(k))[:120])
print("BODY:", repr((d.get("body") or "")[:250]))
