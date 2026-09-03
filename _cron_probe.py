# Probe lecture-seule : journal, revenus, file (aucune ecriture)
import json
j = json.load(open('amelioration_journal.json'))
if isinstance(j, dict):
    j = j.get('cycles', j.get('journal', []))
items = j if isinstance(j, list) else list(j.values())
print("=== JOURNAL (6 derniers) ===")
for c in items[-6:]:
    if isinstance(c, dict):
        print(c.get('ts', '?'), '|', c.get('pire_facteur') or c.get('facteur', '?'), '|', str(c.get('action'))[:110])
    else:
        print(str(c)[:130])

print()
rev = json.load(open('suivi_revenus.json'))
print("=== REVENUS REELS ===")
tot = 0.0
n = 0
if isinstance(rev, list):
    for r in rev:
        if isinstance(r, dict):
            if 'TEST' in str(r.get('note', '')):
                continue
            m = r.get('montant', r.get('montant_eur', 0))
            try:
                m = float(m)
            except Exception:
                m = 0.0
            tot += m
            n += 1
            print(r.get('date', '?'), '|', r.get('payeur', r.get('de', '?')), '|', m, '|', str(r.get('note', ''))[:40])
elif isinstance(rev, dict):
    print('keys:', list(rev.keys())[:15])
print("TOTAL REEL:", tot, "EUR sur", n, "entrees")

print()
data = json.load(open('campagne_data.json'))
st = json.load(open('campagne_state.json'))
sent = st.get('sent', {})
pros = [d for d in data if d.get('type', 'prospect') == 'prospect']
rest = [d for d in pros if str(d.get('num')) not in sent]
print("=== FILE === prospects:", len(pros), "| envoyes:", len(sent), "| RESTANTS:", len(rest))

# chauds : reponses
rep = [k for k, v in sent.items() if v == 'replied' or (isinstance(v, dict) and v.get('status') == 'replied')]
print("replied dans state:", len(rep), rep[:10])

# conges / pauses
try:
    cg = json.load(open('relances_conges.json'))
    print("conges:", len(cg) if isinstance(cg, list) else list(cg.keys())[:10])
except Exception as e:
    print("conges:", e)

import os
print()
print("PAUSE_ENVOIS existe:", os.path.exists('PAUSE_ENVOIS'))
print("SEND_LOCK existe:", os.path.exists('SEND_LOCK'))
