# -*- coding: utf-8 -*-
"""Audit etat reel de la campagne : join data<->state, verites terrain."""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

st = json.load(open('campagne_state.json', encoding='utf-8'))
d = json.load(open('campagne_data.json', encoding='utf-8'))
sent = st.get('sent', {})

print('=== ETAT CAMPAGNE ===')
print('fiches:', len(d), '| envoyes (cles sent):', len(sent))

# GO Gaultier : marqueur
gk = [k for k in st.keys() if 'gaultier' in str(k).lower()]
print('cles racine gaultier:', gk if gk else 'AUCUNE')
for k, v in sent.items():
    if isinstance(v, dict) and 'gaultier' in json.dumps(v, ensure_ascii=False).lower():
        print('  sent[%s] = %s' % (k, json.dumps(v, ensure_ascii=False)))

# Reponses
reps = [k for k, v in sent.items() if isinstance(v, dict) and v.get('replied')]
print('replied:', len(reps), reps[:10])

# Bounces
bounces = [k for k, v in sent.items() if isinstance(v, dict) and v.get('bounce')]
print('bounces marques:', len(bounces))

# Relances
r1 = [k for k, v in sent.items() if isinstance(v, dict) and v.get('sent_relance1')]
r2 = [k for k, v in sent.items() if isinstance(v, dict) and v.get('sent_relance2')]
print('relance1 faites:', len(r1), '| relance2 faites:', len(r2))

# Cash
try:
    rev = json.load(open('suivi_revenus.json', encoding='utf-8'))
    ent = [e for e in rev.get('entrees', []) if 'TEST' not in str(e.get('note', '')).upper() and 'mahdi-design' not in str(e.get('source', ''))]
    print('revenus reel:', len(ent), 'entrees | total:', sum(e.get('montant', 0) for e in ent))
except Exception as ex:
    print('suivi_revenus:', ex)

# Kill switch
print('PAUSE_ENVOIS existe:', os.path.exists('PAUSE_ENVOIS'))
print('SEND_LOCK existe:', os.path.exists('SEND_LOCK'))

# Fiches restantes (join)
rest = [e for e in d if str(e.get('num')) not in sent]
print('file restante (join):', len(rest))
