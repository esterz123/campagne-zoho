# Etat file restante : constats presents ?bounce par boite ? nouvelles fiches
import json, collections, os
d = json.load(open('campagne_data.json', encoding='utf-8'))
s = json.load(open('campagne_state.json', encoding='utf-8'))
sent = s.get('sent', {})
rest = [e for e in d if str(e.get('num')) not in sent]

# 1) bounce par boite d'envoi
bc = collections.Counter()
for k, v in sent.items():
    if v.get('bounce'):
        bc[v.get('via', '?')] += 1
print('bounce par boite:', dict(bc))

# 2) constats_sites.json couverture
if os.path.exists('constats_sites.json'):
    cst = json.load(open('constats_sites.json', encoding='utf-8'))
    print('constats_sites entrees:', len(cst))
    couvert = sum(1 for e in rest if str(e['num']) in cst or e.get('num') in cst)
    print('restants avec constat scanne:', couvert, '/', len(rest))
else:
    print('constats_sites.json ABSENT')

# 3) nouvelles fiches >413
new = [e for e in d if int(e['num']) > 413]
newrest = [e for e in new if str(e['num']) not in sent]
print('fiches >413:', len(new), '| restantes:', len(newrest))

# 4) fiches restantes: champs utiles presents ?
have_dir = sum(1 for e in rest if e.get('dirigeant'))
have_body = sum(1 for e in rest if e.get('body'))
print('restants avec dirigeant:', have_dir, '| avec body:', have_body, '/', len(rest))

# 5) echantillon
e = rest[0]
print('ech fiche', e['num'], '| keys:', sorted(e.keys()))
