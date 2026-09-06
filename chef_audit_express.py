# -*- coding: utf-8 -*-
# Audit express : file reelle (join data<->state), relances dues, chauds, cash reel
import json, datetime, os
BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

d = json.load(open('campagne_data.json', encoding='utf-8'))
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st.get('sent', {})
today = datetime.date.today()

rest = [e for e in d if str(e.get('num')) not in sent]
rep = [e for e in d if sent.get(str(e.get('num')), {}).get('replied')]
print(f"fiches={len(d)} envoyes={len(sent)} restants={len(rest)} replied={len(rep)}")

due = []
for e in d:
    s = sent.get(str(e.get('num')))
    if not s or s.get('replied') or s.get('bounce'): continue
    on = s.get('on')
    if not on: continue
    try:
        d0 = datetime.date.fromisoformat(str(on)[:10])
    except Exception:
        continue
    age = (today - d0).days
    if age >= 3 and not s.get('sent_relance1'): due.append((e.get('num'), 'J3', age))
    elif age >= 7 and not s.get('sent_relance2'): due.append((e.get('num'), 'J7', age))
    elif age >= 14 and not s.get('sent_relance3'): due.append((e.get('num'), 'J14', age))
print(f"relances_dues={len(due)} J3={sum(1 for x in due if x[1]=='J3')} J7={sum(1 for x in due if x[1]=='J7')} J14={sum(1 for x in due if x[1]=='J14')}")
print("chauds:", [str(e.get('num')) + ' ' + str(e.get('entreprise', ''))[:25] for e in rep][:12])

# suivi SIMI closing (diag livre -> relance closing attend GO)
simi = [str(e.get('num')) for e in d if 'simi' in str(e.get('to', '')).lower() or 'simi' in str(e.get('entreprise', '')).lower()]
print("simi_nums:", simi, "-> state:", {n: sent.get(n) for n in simi if sent.get(n)})

if os.path.exists('suivi_revenus.json'):
    rv = json.load(open('suivi_revenus.json', encoding='utf-8'))
    ent = rv.get('entrees', [])
    real = [x for x in ent if 'TEST' not in str(x.get('note', '')).upper() and 'mahdi-design' not in str(x.get('payeur', ''))]
    print("revenus_reels:", [(x.get('date'), x.get('montant'), x.get('statut')) for x in real])

# dernier etat relances_conges (prospects en attente de retour)
if os.path.exists('relances_conges.json'):
    rc = json.load(open('relances_conges.json', encoding='utf-8'))
    print("relances_conges en attente:", [(x.get('to'), x.get('send_on')) for x in rc][:8])

# backlog pending (messages prepares attends GO)
if os.path.exists('pending_go.json'):
    pg = json.load(open('pending_go.json', encoding='utf-8'))
    print("pending_go:", pg)
