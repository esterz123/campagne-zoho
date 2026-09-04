# -*- coding: utf-8 -*-
# Structure reelle d'une fiche restante
import json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open('campagne_data.json', encoding='utf-8'))
fiches = data if isinstance(data, list) else data.get('fiches', [])
for n in (104, 0, 438):
    f = fiches[n]
    print('---', n, type(f).__name__)
    if isinstance(f, dict):
        print('KEYS:', list(f.keys()))
        for k, v in list(f.items())[:14]:
            print(' ', k, '=', str(v)[:70])
    else:
        print(str(f)[:300])
