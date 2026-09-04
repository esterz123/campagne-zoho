# -*- coding: utf-8 -*-
# Envois du jour + couverture preuve des nouvelles fiches + trace du bug '0'
import json, os, re
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def load(p):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print('ERR load', p, e)
        return None

state = load('campagne_state.json') or {}
sent = state.get('sent', {})
# Envois du jour 2026-09-03
auj = [n for n, v in sent.items() if str(v.get('on', '')).startswith('2026-09-03')]
hier = [n for n, v in sent.items() if str(v.get('on', '')).startswith('2026-09-02')]
print('ENVOIS AUJOURDHUI (03/09):', len(auj), auj[:30])
print('ENVOIS HIER (02/09):', len(hier))

data = load('campagne_data.json')
fiches = data if isinstance(data, list) else data.get('fiches', [])
constats = load('constats_sites.json') or {}
nums_restants = [str(i) for i in range(len(fiches)) if str(i) not in sent]
sans_constat = [n for n in nums_restants if n not in constats]
print('RESTANTS SANS CONSTAT (preuve manquante):', len(sans_constat), sans_constat[:15])
# corps vierges parmi les restants ?
vierges = [n for n in nums_restants if n in [str(i) for i, f in enumerate(fiches)] and not str(fiches[int(n)].get('corps', '')).strip()]
print('RESTANTS CORPS VIERGE:', len(vierges), vierges[:15])
# objets vides
obj_vide = [n for n in nums_restants if not str(fiches[int(n)].get('objet', '')).strip()]
print('RESTANTS OBJET VIDE:', len(obj_vide), obj_vide[:15])
