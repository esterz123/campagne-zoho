# -*- coding: utf-8 -*-
"""Audit qualite de la file restante (non envoyes) : charset, portfolio, prix, doublons ouverture."""
import json, re

data = json.load(open('campagne_data.json', encoding='utf-8'))
state = json.load(open('campagne_state.json', encoding='utf-8'))
sent = state['sent']
restants = [e for e in data if e.get('type', 'prospect') == 'prospect' and str(e['num']) not in sent]

bad_u2019, bad_dash, no_pf, prix, doublons = [], [], [], [], []
for e in restants:
    subj = str(e.get('subject', ''))
    body = str(e.get('body', ''))
    all_txt = subj + body
    if '\u2019' in all_txt:
        bad_u2019.append(e['num'])
    if '\u2014' in all_txt or '\u2013' in all_txt:
        bad_dash.append(e['num'])
    if 'Portfolio' not in body:
        no_pf.append(e['num'])
    low = body.lower()
    if '2900' in low or '3900' in low or '79 eur' in low or '69 eur' in low:
        prix.append(e['num'])
    m = re.search(r'@([a-z0-9.-]+)', str(e.get('to', '')).lower())
    if m and low[:600].count(m.group(1)) >= 2:
        doublons.append(e['num'])

print('restants:', len(restants))
print('U+2019:', len(bad_u2019), bad_u2019[:8])
print('tiret long:', len(bad_dash), bad_dash[:8])
print('sans Portfolio:', len(no_pf), no_pf[:8])
print('avec prix (interdit 1er contact):', len(prix), prix[:8])
print('doublon domaine 1re ouverture:', len(doublons), doublons[:8])
