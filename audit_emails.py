"""Audit des emails de TOUTE la file : corrompus, suspects, hors format (lecture seule)."""
import json, re

data = [d for d in json.load(open("campagne_data.json")) if isinstance(d, dict)]
print("FICHES:", len(data))
pat_ok = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
for d in data:
    to = d.get("to") or ""
    if not pat_ok.match(to):
        print("SUSPECT #" + str(d.get("num")), repr(to)[:60], "| src:", d.get("source"))
print("FIN AUDIT")
