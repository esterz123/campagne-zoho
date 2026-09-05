import json, io, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
d = json.load(io.open('campagne_data.json', encoding='utf-8'))
constats = json.load(io.open('constats_sites.json', encoding='utf-8'))
print('type constats:', type(constats).__name__, 'taille:', len(constats))
if isinstance(constats, dict):
    k = list(constats.keys())[:5]
    print('cles ex:', k)
elif isinstance(constats, list):
    print('items ex:', [list(x.keys())[:8] for x in constats[:2]])
s = json.load(io.open('campagne_state.json', encoding='utf-8'))
sent = s['sent']
# fiche ex
fiches = d if isinstance(d, list) else list(d.values())
f0 = fiches[0]
print('champs fiche:', list(f0.keys()))
# domaines dans constats
rest = [f for f in fiches if str(f.get('num')) not in sent]
import collections
kinds = collections.Counter(str(x.get('site'))[:30] if x.get('site') else 'NONE' for x in rest[:5])
print('sites restants ex:', [str(x.get('site'))[:40] for x in rest[:4]])
# bounces par date
from collections import Counter
bdates = Counter()
for k, v in sent.items():
    if v.get('bounce'):
        bdates[str(v.get('on', ''))[:7]] += 1
print('bounces par mois:', dict(bdates))
# check bounce notes
for k, v in list(sent.items()):
    if v.get('bounce'):
        print('bounce ex', k, v.get('on'), str(v.get('note'))[:50])
        break
