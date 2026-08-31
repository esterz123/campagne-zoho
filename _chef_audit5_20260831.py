# -*- coding: utf-8 -*-
# Lecture seule - contenu des 132 unsent generiques : accusations non verifiees ?
import json, io, re, collections

d = json.load(io.open('campagne_data.json', encoding='utf-8'))
items = d.get('prospects') if isinstance(d, dict) else d
st = json.load(io.open('campagne_state.json', encoding='utf-8'))
sent_nums = set(int(k) for k in st.get('sent', {}).keys())

gen_unsent = [p for p in items if p['body'].split('\n')[0].strip() == 'Bonjour,' and p['num'] not in sent_nums]
print('gen unsent:', len(gen_unsent))

# motifs d'accusation
pat_google = sum(1 for p in gen_unsent if "n'apparait pas" in p['body'] or "apparait pas" in p['body'])
pat_lent = sum(1 for p in gen_unsent if 'lent' in p['body'].lower())
pat_pirate = sum(1 for p in gen_unsent if 'pirat' in p['body'].lower())
pat_vieux = sum(1 for p in gen_unsent if 'vieux' in p['body'].lower() or 'date' in p['body'].lower())
print('accusation Google:', pat_google, '| site lent:', pat_lent, '| piratage:', pat_pirate)
print()
print('=== exemple num', gen_unsent[0]['num'], gen_unsent[0]['to'])
print(gen_unsent[0]['body'])
print()
print('=== exemple num', gen_unsent[40]['num'], gen_unsent[40]['to'])
print(gen_unsent[40]['body'])
