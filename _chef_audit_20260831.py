# -*- coding: utf-8 -*-
# Lecture seule - audit hygiene campagne_data.json (cycle chef 2026-08-31 00:05)
import json, io, re, collections

d = json.load(io.open('campagne_data.json', encoding='utf-8'))
items = d.get('prospects') if isinstance(d, dict) else d
if items is None:
    print('KEYS:', list(d.keys()))
    raise SystemExit
print('n=', len(items))
print('sample keys:', sorted(items[0].keys()))

# 1) apostrophes U+2019 / accents problmatiques restantes
bad_apos = [i for i, p in enumerate(items) if '\u2019' in json.dumps(p, ensure_ascii=False)]
print('U+2019 restants:', len(bad_apos))

# 2) corps de mail vides ou trop courts
empty_body = []
for i, p in enumerate(items):
    body = p.get('body') or p.get('corps') or p.get('message') or ''
    if len(body.strip()) < 50:
        empty_body.append((i, p.get('id', p.get('numero')), p.get('email', ''), len(body.strip())))
print('corps vides/courts (<50):', len(empty_body))
for e in empty_body[:10]:
    print('  ', e)

# 3) doublons email
emails = [ (p.get('email') or '').strip().lower() for p in items ]
dups = [e for e, c in collections.Counter(emails).items() if c > 1 and e]
print('emails dupliques:', len(dups))
for e in dups[:10]:
    print('  ', e)

# 4) champs manquants critiques
missing = collections.Counter()
for p in items:
    for f in ('email', 'site', 'body'):
        v = p.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            missing[f] += 1
print('champs manquants:', dict(missing))
