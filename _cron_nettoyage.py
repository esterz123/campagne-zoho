# -*- coding: utf-8 -*-
# Exclut #429 (adresse poubelle) de la file + audit fiches 415-439 (moulin)
import json, os, shutil
os.chdir(os.path.dirname(os.path.abspath(__file__)))

BAD = ('donneespersonnelles', 'rgpd', 'dpo@', 'privacy@', 'privacy.', 'abuse@', 'postmaster@', 'webmaster@', 'no-reply@', 'noreply@')

shutil.copy('campagne_state.json', 'campagne_state.json.bak-excl429-0903')
st = json.load(open('campagne_state.json', encoding='utf-8'))
if '429' not in st.get('sent', {}):
    st['sent']['429'] = {
        'manual': True,
        'note': 'Exclu par Chef 03/09: adresse poubelle (donneespersonnelles@) - jamais un decideur. Reversible: retirer cette cle.',
    }
    json.dump(st, open('campagne_state.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('#429 EXCLU (backup: campagne_state.json.bak-excl429-0903)')
else:
    print('#429 deja en state:', st['sent']['429'])

data = json.load(open('campagne_data.json', encoding='utf-8'))
fiches = data if isinstance(data, list) else data.get('fiches', [])
print('--- AUDIT FICHES 414-438 (nouvelles) ---')
junk, gros = [], []
for i in range(414, len(fiches)):
    f = fiches[i]
    if not isinstance(f, dict):
        continue
    to = str(f.get('to', '')).lower()
    site = str(f.get('site', '')).lower()
    tag = ''
    if any(b in to for b in BAD):
        junk.append(str(i)); tag = 'JUNK'
    if any(d in site for d in ('laforet', 'century21', 'orpi', 'fnac', 'cdiscount', 'castorama', 'leroymerlin')):
        gros.append(str(i)); tag += ' GROSSE-MARQUE'
    if tag:
        print('#' + str(i), to[:45], '|', site[:45], '|', tag)
print('JUNK nouvelles:', junk, '| GROSSES MARQUES:', gros)
print('TOTAL nouvelles fiches:', len(fiches) - 414)
