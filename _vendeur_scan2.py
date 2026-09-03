# -*- coding: utf-8 -*-
# VENDEUR: croise campagne_data.json + campagne_state.json pour trouver chaud/sous-exploite
import json, io, sys, datetime, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
data = json.load(io.open(BASE + r"\campagne_data.json", encoding='utf-8'))
state = json.load(io.open(BASE + r"\campagne_state.json", encoding='utf-8'))
sent = state.get('sent', {})
print("SENT keys sample:", list(sent.items())[:2])

today = datetime.date(2026, 8, 31)

def parse_date(s):
    if not s: return None
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(s))
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

# index data by num
by_num = {}
for x in data:
    by_num[str(x.get('num'))] = x

rows = []
for num, v in sent.items():
    if not isinstance(v, dict): continue
    x = by_num.get(num, {})
    on = parse_date(v.get('on'))
    r1 = parse_date(v.get('relance1_on') or v.get('sent_relance1'))
    r2 = parse_date(v.get('relance2_on') or v.get('sent_relance2'))
    r3 = parse_date(v.get('sent_relance3'))
    replied = v.get('replied')
    rows.append({
        'num': num, 'prospect': x.get('prospect'), 'to': x.get('to'),
        'on': str(on), 'r1': str(r1), 'r2': str(r2), 'r3': str(bool(r3)),
        'replied': bool(replied), 'bounce': bool(v.get('bounce')),
        'diag': bool(v.get('diag_envoye')), 'note': str(v.get('note',''))[:80],
        'keys': ','.join(sorted(v.keys()))
    })

print("=== replied ===")
for r in rows:
    if r['replied']: print(json.dumps(r, ensure_ascii=False))
print("=== bounce/diag ===")
for r in rows:
    if r['bounce'] or r['diag']: print(json.dumps(r, ensure_ascii=False))
print("=== r2 sent, no reply, >=7 days ===")
for r in rows:
    if r['r2'] != 'None' and not r['replied'] and not r['bounce']:
        d = parse_date(r['r2'])
        if d and (today - d).days >= 7:
            print(json.dumps(r, ensure_ascii=False))
print("=== state field keys survey ===")
from collections import Counter
kc = Counter()
for num, v in sent.items():
    if isinstance(v, dict): kc.update(v.keys())
print(dict(kc))
print("total sent:", len(sent), "| total data:", len(data))
