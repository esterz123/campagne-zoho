# -*- coding: utf-8 -*-
"""Scan campagne_data.json : prospects sans perso v2 + anomalies de fiches."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = json.load(open('campagne_data.json', encoding='utf-8'))
weird = [p for p in d if 'prospect' not in p or 'to' not in p]
print("anomalies:", len(weird))
for p in weird[:5]:
    print({k: str(v)[:60] for k, v in p.items()})

noperso = [p for p in d if 'prospect' in p and 'ligne1-v2' not in (p.get('note') or '')]
print("sans perso v2:", len(noperso))
for p in noperso[:30]:
    print(p['num'], '|', p['prospect'][:45], '|', p.get('site'), '|', (p.get('note') or '')[:70])
