# -*- coding: utf-8 -*-
# Test C : objet = score mesure. Alterne C (pair) / S standard (impair) sur les non-envoyes.
# Backup bak-objetC-0906. Idempotent : ne touche que les objets encore au standard.
import json, os, shutil, datetime
os.chdir(os.path.dirname(os.path.abspath(__file__)))

d = json.load(open('campagne_data.json', encoding='utf-8'))
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st.get('sent', {})
co = json.load(open('constats_sites.json', encoding='utf-8'))

try:
    ab = json.load(open('ab_test.json', encoding='utf-8'))
except Exception:
    ab = {}
cmap = ab.setdefault('C_test', {'date': '2026-09-06', 'num_variant': {}}).setdefault('num_variant', {})

bak = 'campagne_data.json.bak-objetC-0906'
if not os.path.exists(bak):
    shutil.copyfile('campagne_data.json', bak)

changed = 0
for e in d:
    num = str(e.get('num'))
    if num in sent:
        continue
    note = co.get(num, {}).get('note')
    if note is None:
        continue
    if num in cmap:
        continue  # deja tagge = idempotent
    domaine = str(e.get('site') or '')
    if not domaine:
        import re
        m = re.search(r'@([a-z0-9.-]+)', str(e.get('to', '')))
        m2 = re.search(r'([a-z0-9-]+\.(?:fr|com|net|org))', str(e.get('subject', '')))
        domaine = (m.group(1) if m else (m2.group(1) if m2 else ''))
    nouveau = 'Votre site : %d/100 (%s)' % (note, domaine)
    ancien = e.get('subject', '')
    if nouveau == ancien:
        continue
    # variant : pair = C (score), impair = S (standard actuel, inchangé)
    if int(num) % 2 == 0:
        e['subject'] = nouveau
    cmap[num] = 'C' if int(num) % 2 == 0 else 'S'
    changed += 1

json.dump(d, open('campagne_data.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
ab['C_test']['date'] = datetime.date.today().isoformat()
json.dump(ab, open('ab_test.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('changes=%d' % changed)
