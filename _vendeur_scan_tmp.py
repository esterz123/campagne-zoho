# -*- coding: utf-8 -*-
"""Scan campagne_data.json : prospects chauds ou sous-exploites pour VENDEUR cron."""
import json, datetime, io, sys

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
data = json.load(open(BASE + r"\campagne_data.json", encoding="utf-8"))
st = json.load(open(BASE + r"\campagne_state.json", encoding="utf-8"))
sent = st.get("sent", {})
today = datetime.date(2026, 8, 31)

bym = {}
for e in data:
    n = e.get("num")
    if isinstance(n, int):
        bym[n] = e

# A) relance 2 envoyee, sans reponse, 7+ jours, pas encore relance 3
rows = []
for n, v in sent.items():
    if not isinstance(v, dict):
        continue
    r2 = v.get("sent_relance2")
    if not r2 or v.get("bounce") or v.get("replied") or v.get("sent_relance3"):
        continue
    try:
        d2 = datetime.date.fromisoformat(str(r2)[:10])
    except Exception:
        continue
    days = (today - d2).days
    if days >= 7:
        num = int(n) if str(n).isdigit() else None
        e = bym.get(num, {})
        rows.append((days, n, str(r2)[:10], e.get("prospect", "?")[:48], e.get("to", "")))
rows.sort(reverse=True)
print("=== A) RELANCE2 SANS REPONSE 7J+ (pas de relance3) : %d ===" % len(rows))
for r in rows[:20]:
    print(r[0], "j | num", r[1], "| r2", r[2], "|", r[3], "|", r[4])

# B) sous-exploites : email 1 jamais envoye alors que le constat site est mauvais
print()
print("=== B) JAMAIS ENVOYES (email 1 en file) : echantillon avec constat site ===")
never = []
for n, v in sent.items():
    if not isinstance(v, dict):
        continue
    if v.get("bounce") or v.get("replied"):
        continue
    if "on" not in v:
        never.append(n)
print("count jamais envoyes:", len(never))

# constats sites pour ces nums : les plus mauvais scores d'abord
try:
    cons = json.load(open(BASE + r"\constats_sites.json", encoding="utf-8"))
except Exception:
    cons = {}
cand = []
for n in never:
    c = cons.get(n)
    if not isinstance(c, dict):
        continue
    etat = c.get("etat", "")
    note = c.get("note", None)
    if etat == "VIVANT" and note is not None and note <= 55:
        num = int(n)
        e = bym.get(num, {})
        cand.append((note, n, etat, e.get("prospect", "?")[:48], e.get("to", ""), c.get("constat", "")[:80]))
cand.sort()
print("=== C) JAMAIS ENVOYES + NOTE SITE <= 55 : %d ===" % len(cand))
for c in cand[:20]:
    print("note", c[0], "| num", c[1], "|", c[3], "|", c[4], "|", c[5])
