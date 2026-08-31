# -*- coding: utf-8 -*-
"""P3 (audit Boss) : etat des pages diag manquantes + plan de generation."""
import json

diag = json.load(open('diag_pages.json', encoding='utf-8'))
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = set(str(k) for k in st.get('sent', {}))
have = set(str(k) for k in diag.keys())
d = json.load(open('campagne_data.json', encoding='utf-8'))
sans = [r.get('num') for r in d if str(r.get('num')) in sent and str(r.get('num')) not in have]
print('envoyes sans page diag:', len(sans))
print('nums:', sans[:60])
print('pages existantes:', len(have))
