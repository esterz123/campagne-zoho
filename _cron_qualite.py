# -*- coding: utf-8 -*-
# Qualite file: adresses poubelle (rgpd/dpo/privacy), restants avec vraies cles, chauds SIMI/Gaultier
import json, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open('campagne_data.json', encoding='utf-8'))
fiches = data if isinstance(data, list) else data.get('fiches', [])
state = json.load(open('campagne_state.json', encoding='utf-8'))
sent = state.get('sent', {})

BAD = ('donneespersonnelles', 'rgpd', 'dpo@', 'privacy@', 'privacy.', 'abuse@', 'postmaster@', 'webmaster@', 'no-reply@', 'noreply@')
junk_total, junk_envoye, junk_restant = [], [], []
restants_vierges = []
for i, f in enumerate(fiches):
    if not isinstance(f, dict):
        continue
    to = str(f.get('to', '')).lower()
    num = str(i)
    isjunk = any(b in to for b in BAD)
    if isjunk:
        junk_total.append(num)
        (junk_envoye if num in sent else junk_restant).append(num)
    if num not in sent and not str(f.get('body', '')).strip():
        restants_vierges.append(num)

print('JUNK ADRESSES total:', len(junk_total), '| deja envoyes (quota brule):', len(junk_envoye), junk_envoye[:20])
print('JUNK restants (a nettoyer):', len(junk_restant), junk_restant[:20])
print('RESTANTS body VIERGE (vrai):', len(restants_vierges), restants_vierges[:15])

# Chauds
for num, label in (('63', 'GAULTIER'), ):
    s = sent.get(num, {})
    print('---', label, '#' + num, 'replied:', s.get('replied'), '| on:', s.get('on'))
# SIMI = prospect 1, cherche ses cles
for i, f in enumerate(fiches):
    if isinstance(f, dict) and 'simi.fr' in str(f.get('to', '')):
        print('SIMI fiche num(str):', str(i), '| state:', sent.get(str(i), {}))
        break

# Relances closing pretes ?
for p in ('livrable/relance_closing_SIMI.txt', 'relances_closing.json', 'messages_livraison.json'):
    print(p, 'existe:', os.path.exists(p))

# Journal boucle amelioration (dernier diagnostic)
try:
    j = json.load(open('amelioration_journal.json', encoding='utf-8'))
    cyc = j[-1] if isinstance(j, list) else j
    print('DERNIER CYCLE BOUCLE:', json.dumps(cyc, ensure_ascii=False)[:400])
except Exception as e:
    print('journal:', e)
