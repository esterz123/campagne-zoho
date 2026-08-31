# -*- coding: utf-8 -*-
# Lecture seule - audit personnalisation des corps (cycle chef 2026-08-31)
import json, io, collections, hashlib

d = json.load(io.open('campagne_data.json', encoding='utf-8'))
items = d.get('prospects') if isinstance(d, dict) else d

# corps identiques (groupe de templates)
h = collections.Counter(hashlib.md5(p['body'].encode()).hexdigest() for p in items)
print('corps distincts:', len(h), '/ total', len(items))
top = h.most_common(5)
for k, c in top:
    print('  template utilise', c, 'fois')

# champs 'to' vides
no_to = [p['num'] for p in items if not (p.get('to') or '').strip()]
print('to vides:', len(no_to), no_to[:10])

# prospect: contient-il un nom de societe ?
no_name = [p['num'] for p in items if not (p.get('prospect') or '').strip()]
print('prospect vide:', len(no_name), no_name[:10])

# echantillon: 3 premiers corps
for p in items[:2]:
    print('--- num', p['num'], '|', p.get('prospect'), '|', p.get('to'))
    print(p['body'][:600])
