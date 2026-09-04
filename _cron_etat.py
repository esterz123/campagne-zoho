# -*- coding: utf-8 -*-
# Etat business reel : file restante, envois, reponses, relances, argent (hors TEST)
import json, re, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def load(p):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print('ERR load', p, e)
        return None

data = load('campagne_data.json')
state = load('campagne_state.json') or {}
fiches = data if isinstance(data, list) else data.get('fiches', data.get('prospects', list(data.values())))
sent = state.get('sent', {})

restants, envoyes, replies = [], 0, []
for i, f in enumerate(fiches):
    num = str(i)
    s = sent.get(num)
    if s:
        envoyes += 1
        if s.get('replied'):
            replies.append((num, str(f.get('entreprise', f.get('nom', '?')))[:40]))
    else:
        restants.append(num)

print('FICHES:', len(fiches), '| ENVOYES:', envoyes, '| RESTANTS:', len(restants))
print('REPLIES:', len(replies))
for n, e in replies:
    print('  #' + n, e)
rel1 = sum(1 for v in sent.values() if v.get('sent_relance1'))
rel2 = sum(1 for v in sent.values() if v.get('sent_relance2'))
print('RELANCES R1:', rel1, 'R2:', rel2)

# Argent reel (exclut TEST + auto-mahdi)
rev = load('suivi_revenus.json')
if rev:
    items = rev if isinstance(rev, list) else rev.get('paiements', list(rev.values()))
    tot = 0.0
    for p in items:
        if not isinstance(p, dict):
            continue
        note = str(p.get('note', ''))
        payeur = str(p.get('payeur', ''))
        if 'TEST' in note.upper() or 'mahdi-design' in payeur.lower():
            continue
        m = p.get('montant', 0)
        m = m if isinstance(m, (int, float)) else 0
        tot += m
        print('PAY:', p.get('date', '?'), '|', m, 'EUR |', payeur[:30], '|', note[:60])
    print('TOTAL ARGENT REEL:', round(tot, 2), 'EUR')

# Chauds: replies recents ou pending
seq = load('relances_conges.json')
if seq:
    print('CONGES/PAUSES:', len(seq) if isinstance(seq, (list, dict)) else '?')

# Aliases reponses
alias = load('reply_aliases.json')
if alias:
    print('ALIASES:', list(alias.keys())[:8] if isinstance(alias, dict) else len(alias))
