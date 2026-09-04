# -*- coding: utf-8 -*-
# Croisement bounces <-> blacklist <-> fiches restantes (pieges quota)
import json

st = json.load(open('campagne_state.json', encoding='utf-8'))
data = json.load(open('campagne_data.json', encoding='utf-8'))
sent = st.get('sent', {})

bounces = [n for n, v in sent.items() if isinstance(v, dict) and v.get('bounce')]

def dom(n):
    for p in data:
        if str(p.get('num')) == n:
            to = str(p.get('to', '')).lower()
            if '@' in to:
                return to.split('@')[-1].strip()
    return None

doms_bounce = {dom(n) for n in bounces if dom(n)}
try:
    blocked = set(json.load(open('domaines_bloques.json', encoding='utf-8')))
except Exception as e:
    blocked = set()
    print('bloques file err:', e)

print('bounces:', len(bounces), '| domaines bounced:', len(doms_bounce), '| blacklist:', len(blocked))

restants = [str(p.get('num')) for p in data if str(p.get('num')) not in sent]
pieges = []
for n in restants:
    d = dom(n)
    if d and (d in doms_bounce or d in blocked):
        pieges.append((n, d))
print('FICHES RESTANTES SUR DOMAINE MORT:', len(pieges))
for n, d in pieges[:15]:
    print('  #' + n, d)
