# -*- coding: utf-8 -*-
import json, re
data = json.load(open('campagne_data.json', encoding='utf-8'))
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st['sent']
nums_sent = {k for k,v in sent.items() if v.get('on')}
restants = [d for d in data if str(d.get('num')) not in nums_sent]
out = []
for d in restants:
    body = (d.get('corps') or d.get('body') or d.get('message') or '')
    if 'Portfolio' not in body:
        out.append({
            'num': d.get('num'),
            'to': d.get('to'),
            'objet': (d.get('objet') or '')[:80],
            'fin_corps': body[-180:],
        })
json.dump(out, open('_audit_sans_portfolio.json','w',encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(out), 'fiches restantes sans mention Portfolio')
