# -*- coding: utf-8 -*-
"""Diagnostic plafond 0 envoyes aujourd'hui alors que quota dispo."""
import json, os, sys, io, collections, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.chdir("C:/Users/ulamb/Bureau/prospection/github-campagne")

state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state.get("sent", {})
today = datetime.date.today().isoformat()
hier = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

# compte par boite aujourd'hui et hier
cpt_today, cpt_hier = collections.Counter(), collections.Counter()
for k, v in sent.items():
    if not isinstance(v, dict): continue
    via = v.get("via")
    for champ in ("on", "sent_relance1", "sent_relance2", "sent_relance3"):
        d = v.get(champ)
        if d == today: cpt_today[via] += 1
        if d == hier: cpt_hier[via] += 1
print("envois AUJOURD'HUI par boite:", dict(cpt_today), "total:", sum(cpt_today.values()))
print("envois HIER par boite:", dict(cpt_hier), "total:", sum(cpt_hier.values()))

# dernier jour d'activite reelle
jours = collections.Counter()
for k, v in sent.items():
    if isinstance(v, dict):
        for champ in ("on", "sent_relance1", "sent_relance2", "sent_relance3"):
            if v.get(champ): jours[v[champ]] += 1
for d in sorted(jours)[-8:]:
    print(f"  {d}: {jours[d]} envois")

# boites et max_jour (lecture du code source pour les plafonds)
src = open("campagne_zoho.py", encoding="utf-8").read()
import re
m = re.findall(r'"nom":\s*"([^"]+)"[^}]*?"max_jour":\s*(\d+)', src, re.S)
print("boites/plafonds (source):", m[:12])
# date systeme sur le runner ? comparons
print("date locale machine:", today)
