# Probe 2 : structure complete etat + derniers envois + chauds
import json, re
from datetime import datetime

rev = json.load(open('suivi_revenus.json'))
print("=== SUIVI_REVENUS ===")
print("objectifs:", rev.get('objectifs'))
ent = rev.get('entrees', [])
print("entrees:", len(ent))
tot = 0.0
for r in ent:
    if isinstance(r, dict) and 'TEST' in str(r.get('note', '')):
        continue
    m = r.get('montant', r.get('montant_eur', 0))
    try:
        m = float(m)
    except Exception:
        m = 0.0
    tot += m
    print(' ', r.get('date', '?'), '|', r.get('payeur', r.get('de', '?')), '|', m, '|', str(r.get('note', ''))[:50])
print("TOTAL REEL:", tot, "EUR")

j = json.load(open('amelioration_journal.json'))
if isinstance(j, dict):
    j = j.get('cycles', j.get('journal', []))
items = j if isinstance(j, list) else list(j.values())
print("\n=== DERNIER CYCLE COMPLET ===")
print(json.dumps(items[-1], ensure_ascii=False)[:800])

st = json.load(open('campagne_state.json'))
sent = st.get('sent', {})
# dernier envoi par date
dates = []
for k, v in sent.items():
    if isinstance(v, dict):
        d = v.get('on') or v.get('date')
        if d:
            dates.append(str(d))
dates.sort()
print("\n=== ENVOIS ===")
print("derniere date d'envoi:", dates[-1] if dates else '?', "| nb avec date:", len(dates))
print("repartition 10 derniers:", dates[-10:])

rs = json.load(open('repondeur_state.json'))
print("\n=== REPONDEUR ===")
print("keys:", list(rs.keys()))
tr = rs.get('traites', [])
print("traites:", len(tr) if hasattr(tr, '__len__') else tr)

cs = json.load(open('closer_state.json'))
print("\n=== CLOSER ===")
print("keys:", list(cs.keys()))
trc = cs.get('traites', [])
print("traites:", len(trc) if hasattr(trc, '__len__') else trc)
