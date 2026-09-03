import json, sys
from collections import Counter

def load(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception as e:
        print('ERR', p, e); return None

s = load('campagne_state.json')
d = load('campagne_data.json')
c = load('constats_sites.json')

sent = s.get('sent', {}) if isinstance(s, dict) else {}
print('=== STATE ===')
print('top keys:', list(s.keys()) if isinstance(s, dict) else type(s))
print('sent count:', len(sent))
rep = [k for k, v in sent.items() if isinstance(v, dict) and v.get('replied')]
print('replied:', len(rep), rep[:6])
st = Counter(v.get('stage', '?') for v in sent.values() if isinstance(v, dict))
print('stages:', dict(st))
bx = Counter(v.get('box', v.get('from', '?')) for v in sent.values() if isinstance(v, dict))
print('boxes:', dict(bx))

print('=== DATA ===')
if isinstance(d, dict):
    print('data top keys:', list(d.keys())[:8])
    leads = d.get('leads', d)
    print('leads count:', len(leads))
    if isinstance(leads, list) and leads:
        print('lead sample keys:', list(leads[0].keys()))
    elif isinstance(leads, dict):
        k0 = list(leads)[0]
        print('lead sample:', k0, list(leads[k0].keys()) if isinstance(leads[k0], dict) else '')
elif isinstance(d, list):
    print('data list len:', len(d))
    if d: print('sample keys:', list(d[0].keys()))

print('=== CONSTATS ===')
print('type:', type(c), 'len:', len(c) if c else 0)
if isinstance(c, dict):
    ks = list(c)[:3]
    print('keys sample:', ks)
    v0 = c[ks[0]]
    print('entry keys:', list(v0.keys()) if isinstance(v0, dict) else v0)
    # count how many have a constat/fait
    ok = sum(1 for v in c.values() if isinstance(v, dict) and (v.get('constat') or v.get('faits') or v.get('mesures')))
    print('entries with constat/faits:', ok)
