# 1) bloquer les 15 domaines sans MX (protection delivrabilite)
# 2) verifier couverture constats/preuve des fiches >413 + relances recentes
import json, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = json.load(open('campagne_data.json', encoding='utf-8'))
s = json.load(open('campagne_state.json', encoding='utf-8'))
sent = s.get('sent', {})
rk = json.load(open('_smtp_recheck_0904.json', encoding='utf-8'))

# --- 1. blocklist NOMX ---
bl = json.load(open('domaines_bloques.json', encoding='utf-8'))
blset = set(bl) if isinstance(bl, list) else set(bl.get('domaines', []))
added = []
for num, info in rk.items():
    if info['verdict'] == 'NOMX':
        dom = info['email'].split('@')[-1].lower()
        if dom not in blset:
            blset.add(dom)
            added.append((num, dom))
if isinstance(bl, list):
    bl = sorted(blset)
else:
    bl['domaines'] = sorted(blset)
json.dump(bl, open('domaines_bloques.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('domaines bloques ajoutés:', added)

# --- 2. couverture preuve fiches >413 restantes ---
cst = json.load(open('constats_sites.json', encoding='utf-8'))
new = [e for e in d if int(e['num']) > 413 and str(e['num']) not in sent]
has_cst = [e['num'] for e in new if str(e['num']) in cst or e['num'] in cst]
notes = []
for e in new:
    c = cst.get(str(e['num'])) or cst.get(e['num'])
    if isinstance(c, dict):
        notes.append((e['num'], c.get('note'), (c.get('constat') or '')[:60]))
print(f'fiches >413 restantes: {len(new)} | avec constat: {len(has_cst)}')
print('notes:', notes)

# --- 3. relances recentes (preuve terrain) ---
from collections import Counter
rel = Counter()
for k, v in sent.items():
    for tag in ('sent_relance1', 'sent_relance2', 'sent_relance3'):
        if v.get(tag):
            rel[tag] += 1
print('relances marquees:', dict(rel))

# relance1 emises sur envois vieillis d'au moins 3j mais non marques = retard
import datetime
today = datetime.date(2026, 9, 4)
due = 0
for k, v in sent.items():
    if v.get('replied') or v.get('bounce') or v.get('sent_relance1'):
        continue
    try:
        dd = datetime.date.fromisoformat(str(v.get('on', ''))[:10])
        if (today - dd).days >= 3:
            due += 1
    except Exception:
        pass
print('relances J+3 en retard (non marquées):', due)
