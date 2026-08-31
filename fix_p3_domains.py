# -*- coding: utf-8 -*-
"""P3 final : recuperer le domaine depuis le CONSTAT du mail (il contient le vrai site)
ou depuis constats_sites.json, puis generer les pages des 89."""
import json
import re

d = json.load(open('campagne_data.json', encoding='utf-8'))
st = json.load(open('campagne_state.json', encoding='utf-8'))
m = json.load(open('diag_pages.json', encoding='utf-8'))
pr = json.load(open('constats_sites.json', encoding='utf-8'))

recup = 0
for r in d:
    num = str(r['num'])
    if num not in st.get('sent', {}) or num in m:
        continue
    # 1) constats_sites.json a le domaine fiable
    p = pr.get(num, {})
    dom = (p.get('domaine') or '').strip()
    # 2) sinon : extraire du corps ("J'ai ouvert X.fr", "tape X.fr")
    if not dom:
        mm = re.search(r"(?:ouvert|tape|sur)\s+([a-z0-9.-]+\.[a-z]{2,})", r.get('body', ''), re.I)
        if mm:
            dom = mm.group(1)
    if dom:
        r['site'] = 'https://' + dom
        recup += 1
json.dump(d, open('campagne_data.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('domains recuperes depuis constats/corps:', recup)

sans = [r for r in d if str(r['num']) in st.get('sent', {}) and str(r['num']) not in m]
avec = [r for r in sans if (r.get('site') or '').strip()]
print('cibles restantes:', len(sans), '| avec site maintenant:', len(avec))
