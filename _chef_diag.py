# -*- coding: utf-8 -*-
import json, collections, os, datetime
os.chdir(r'C:\Users\ulamb\Bureau\prospection\github-campagne')

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

state = load('campagne_state.json')
sent = state['sent']

# bounces: dates + champs
b = {n: v for n, v in sent.items() if isinstance(v, dict) and v.get('bounce')}
print('bounce champs possibles:', sorted({k for v in b.values() for k in v}))
dates = collections.Counter(str(v.get('bounce'))[:10] if v.get('bounce') else str(v.get('on'))[:10] for v in b.values())
print('bounce par date:', dict(sorted(dates.items())))

# exemples
for n, v in list(b.items())[:5]:
    print(n, json.dumps(v, ensure_ascii=False)[:300])

# bounce par boite
boites = collections.Counter(str(v.get('via','?')) for v in b.values())
print('bounce par boite:', dict(boites))

# bounce par date d'envoi original
orig = collections.Counter(str(v.get('on'))[:10] for v in b.values())
print('bounce par date envoi original:', dict(sorted(orig.items())))
