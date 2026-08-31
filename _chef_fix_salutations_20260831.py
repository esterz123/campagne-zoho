# -*- coding: utf-8 -*-
# Correction salutations "M. Monsieur" dans campagne_data.json (cycle chef 31/08 00h05)
# Backup .bak obligatoire avant ecriture. Remplacement sur 1re ligne uniquement.
import json, io, shutil, os

SRC = 'campagne_data.json'
BAK = 'campagne_data.json.bak_20260831_salutations'

st = json.load(io.open('campagne_state.json', encoding='utf-8'))
sent_nums = set(int(k) for k in st.get('sent', {}).keys())

d = json.load(io.open(SRC, encoding='utf-8'))
items = d.get('prospects') if isinstance(d, dict) else d

fixed = []
for p in items:
    b = p['body']
    lines = b.split('\n')
    l0 = lines[0].strip()
    new0 = None
    if 'M. Monsieur' in l0:
        new0 = 'Bonjour,'
    elif 'Mme Madame' in l0 or 'M. Madame' in l0:
        new0 = 'Bonjour,'
    if new0:
        if not os.path.exists(BAK):
            shutil.copy2(SRC, BAK)
        lines[0] = new0
        p['body'] = '\n'.join(lines)
        fixed.append((p['num'], p['num'] in sent_nums))

json.dump(d, io.open(SRC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# re-verification
d2 = json.load(io.open(SRC, encoding='utf-8'))
items2 = d2.get('prospects') if isinstance(d2, dict) else d2
restant = sum(1 for p in items2 if 'M. Monsieur' in p['body'].split('\n')[0] or 'Mme Madame' in p['body'].split('\n')[0])
print('corriges:', len(fixed))
print('  deja envoyes (historique, non rattrapable):', sum(1 for _, s in fixed if s))
print('  pas encore envoyes (proteges):', sum(1 for _, s in fixed if not s), [n for n, s in fixed if not s])
print('restant apres fix:', restant)
print('total prospects:', len(items2))
