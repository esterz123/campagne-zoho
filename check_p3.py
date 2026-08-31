# -*- coding: utf-8 -*-
"""Pourquoi le run P3 n'a genere aucune page sur 120 ?"""
import json

d = json.load(open('campagne_data.json', encoding='utf-8'))
st = json.load(open('campagne_state.json', encoding='utf-8'))
m = json.load(open('diag_pages.json', encoding='utf-8'))
sans = [r for r in d if str(r['num']) in st.get('sent', {}) and str(r['num']) not in m]
print('cibles restantes:', len(sans))
avec_site = [r for r in sans if (r.get('site') or '').strip()]
print('avec site:', len(avec_site))
for r in avec_site[:6]:
    print('  #%s site=%s' % (r['num'], r.get('site')))
