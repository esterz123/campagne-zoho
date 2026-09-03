# -*- coding: utf-8 -*-
"""Audit 3 : reserves chargeurs, dispo realiste pour la file."""
import json, os, re

os.chdir(r"C:/Users/ulamb/Bureau/prospection/github-campagne")

def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"__err__": str(e)}

data = load("campagne_data.json")
state = load("campagne_state.json")
sent = state.get("sent", {})
sent_emails = set()
for f in data:
    num = str(f.get("num"))
    if num in sent:
        to = (f.get("to") or "").lower()
        if "@" in to:
            sent_emails.add(to)

# reserves
for f in ["candidats_a_verifier.json", "candidats_agences.json", "candidats_cabinets.json",
          "candidats_bruts.json", "candidats_locaux.json", "_candidats_domains.json"]:
    d = load(f)
    if isinstance(d, dict) and "__err__" in d:
        print(f, "->", d["__err__"][:60])
        continue
    n = len(d)
    # emails dispo = emails uniques non deja envoyes
    emails = set()
    if isinstance(d, list):
        for x in d:
            if isinstance(x, dict):
                for v in x.values():
                    if isinstance(v, str) and "@" in v and "." in v.split("@")[-1]:
                        emails.add(v.lower().strip())
    print(f, "->", n, "entrees;", len(emails), "emails uniques trouves")

# prospects deja en file mais pas envoyes = 191
# dispo total approx = 191 + reserves non envoyes
db = load("domaines_bloques.json")
print("domaines_bloques:", len(db) if isinstance(db, (list, dict)) else "?")
