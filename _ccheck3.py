import json
from collections import Counter
cd = json.load(open('campagne_data.json', encoding='utf-8'))
# structure d'un prospect
p = cd[0]
for k,v in p.items():
    print(k, ':', str(v)[:120])
print('---- prospect key sample (p avec prospect key)')
p2 = [x for x in cd if 'prospect' in x][0]
print(str(p2.get('prospect'))[:400])
# sent state
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st['sent']
print('\nSENT count:', len(sent))
# statuts internes des sent
stt = Counter(v.get('statut') or v.get('status') or '?' for v in sent.values())
print('statuts sent:', stt.most_common(15))
rk = Counter(k for v in sent.values() for k in v.keys())
print('sent subkeys:', rk.most_common(15))
