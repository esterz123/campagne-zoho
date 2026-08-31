# -*- coding: utf-8 -*-
# Lecture seule - anomalies de salutation (cycle chef 2026-08-31)
import json, io, re, collections

d = json.load(io.open('campagne_data.json', encoding='utf-8'))
items = d.get('prospects') if isinstance(d, dict) else d

pat = re.compile(r'^.*$', re.M)
first_lines = collections.Counter()
weird = []
for p in items:
    line1 = p['body'].splitlines()[0].strip() if p['body'].strip() else '(vide)'
    first_lines[line1] += 1
    if ('M. Monsieur' in line1) or ('Mme Madame' in line1) or ('M. Madame' in line1) \
       or line1 in ('Bonjour,', 'Bonjour', 'Bonjour .', 'Bonjour M.,') or 'Monsieur Madame' in line1:
        weird.append((p['num'], line1))

print('lignes de salutation distinctes:', len(first_lines))
for l, c in first_lines.most_common(15):
    print(f'  {c:4d}  {l}')
print('ANOMALIES:', len(weird))
for n, l in weird[:40]:
    print('  num', n, '->', l)
