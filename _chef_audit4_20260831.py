# -*- coding: utf-8 -*-
# Lecture seule - potentiel de personnalisation des "Bonjour," generiques
import json, io

d = json.load(io.open('campagne_data.json', encoding='utf-8'))
items = d.get('prospects') if isinstance(d, dict) else d
st = json.load(io.open('campagne_state.json', encoding='utf-8'))
sent_nums = set(int(k) for k in st.get('sent', {}).keys())

gen = [p for p in items if p['body'].split('\n')[0].strip() == 'Bonjour,']
unsent = [p for p in gen if p['num'] not in sent_nums]
print('generiques:', len(gen), '| pas encore envoyes:', len(unsent))

# le champ prospect porte-t-il un nom exploitable ?
with_name = [p for p in unsent if (p.get('prospect') or '').strip()]
print('parmi unsent, prospect non vide:', len(with_name))
for p in unsent[:15]:
    print('  num', p['num'], '| prospect:', repr(p.get('prospect'))[:80], '| to:', p.get('to'))

# verifie_dirigeants.json contient-il des noms pour ces emails ?
try:
    vd = json.load(io.open('verifie_dirigeants.json', encoding='utf-8'))
    vd_items = vd if isinstance(vd, list) else list(vd.values())
    idx = {}
    for x in vd_items:
        if isinstance(x, dict):
            e = (x.get('email') or '').lower()
            n = (x.get('dirigeant') or x.get('nom') or '').strip()
            if e and n:
                idx[e] = n
    hits = [(p['num'], idx[p['to'].lower()]) for p in unsent if p['to'].lower() in idx]
    print('dirigeants connus pour unsent generiques:', len(hits), hits[:20])
except Exception as ex:
    print('verifie_dirigeants:', ex)
