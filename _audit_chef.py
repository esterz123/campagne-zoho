# -*- coding: utf-8 -*-
"""Audit chiffres campagne : etat reel, file, relances, revenus."""
import json, datetime, os, re

os.chdir(os.path.dirname(os.path.abspath(__file__)))
today = datetime.date.today().isoformat()

def load(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception as e:
        print(f"!! {p}: {e}")
        return None

st = load('campagne_state.json') or {}
data = load('campagne_data.json') or []
sent = st.get('sent', {})

env_today = sorted([k for k, v in sent.items() if v.get('on') == today], key=int)
replied = [k for k, v in sent.items() if v.get('replied')]
restants = [d for d in data if str(d.get('num')) not in sent]
rel1 = [k for k, v in sent.items() if v.get('sent_relance1')]
rel2 = [k for k, v in sent.items() if v.get('sent_relance2')]

print(f"=== ETAT {today} ===")
print(f"envoyes total : {len(sent)}")
print(f"envoyes ce jour: {len(env_today)} -> {env_today[:40]}")
print(f"file restante : {len(restants)}")
print(f"replied       : {len(replied)} -> {sorted(replied, key=int)[:20]}")
print(f"relance1      : {len(rel1)} | relance2: {len(rel2)}")

# jours des derniers envois
jours = {}
for v in sent.values():
    d = v.get('on')
    if d:
        jours[d] = jours.get(d, 0) + 1
print("envois par jour (7 derniers):")
for d in sorted(jours)[-7:]:
    print(f"  {d}: {jours[d]}")

# revenus reels
rev = load('suivi_revenus.json')
if rev:
    ent = rev if isinstance(rev, list) else rev.get('paiements', rev.get('entrees', []))
    reel = [e for e in ent if 'TEST' not in str(e.get('note', '')).upper()
            and 'mahdi-design' not in str(e.get('payeur', '')).lower()]
    total = 0
    print(f"=== REVENUS REELS: {len(reel)} ===")
    for e in reel[-12:]:
        m = str(e.get('montant', ''))
        try:
            total += float(re.sub(r'[^\d.]', '', m) or 0)
        except Exception:
            pass
        print(f"  {e.get('date')} | {m} | {str(e.get('payeur'))[:30]} | {str(e.get('note'))[:70]}")
    print(f"total cash reel cumule: {total:.2f} EUR")

# suivi journal boucle
j = load('amelioration_journal.json')
if j:
    cyc = j if isinstance(j, list) else j.get('cycles', [])
    print(f"=== BOUCLE: {len(cyc)} cycles ===")
    for c in cyc[-3:]:
        print(f"  {c.get('ts', c.get('date'))} | diag: {str(c.get('diagnostic'))[:100]} | action: {str(c.get('action'))[:100]}")
