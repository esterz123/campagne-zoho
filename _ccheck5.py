import json
from collections import Counter
cd = json.load(open('campagne_data.json', encoding='utf-8'))
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st['sent']
bynum = {str(p['num']): p for p in cd}
# les 29 sans relance1: qui sont-ils, note, to_confirmed?
no_r1 = [k for k,v in sent.items() if not v.get('sent_relance1') and not v.get('bounce') and not v.get('bloque') and not v.get('doublon')]
print("=== 29 candidats relance1 ===")
for k in no_r1:
    p = bynum.get(k, {})
    v = sent[k]
    print(k, '|', v.get('on','?'), '|', v.get('via','?'), '| to_confirmed:', p.get('to_confirmed'), '|', str(p.get('prospect'))[:45], '| note:', str(v.get('note',''))[:80])
