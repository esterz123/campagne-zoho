import json
from collections import Counter
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st['sent']
# replies
rep = {k:v for k,v in sent.items() if v.get('replied')}
print("REPLIED:", len(rep))
for k,v in rep.items():
    print(k, '->', str(v)[:300])
# bounces
b = {k:v for k,v in sent.items() if v.get('bounce')}
print("\nBOUNCES:", len(b))
bc = Counter(str(v.get('bounce'))[:60] for v in b.values())
for k,c in bc.most_common(10): print(c, '|', k)
# relance2
r2 = [k for k,v in sent.items() if v.get('sent_relance2')]
r1 = [k for k,v in sent.items() if v.get('sent_relance1')]
print("\nrelance1:", len(r1), "relance2:", len(r2))
# qui n'a eu QUE le mail 1 (pas relance1) et pas bounce
no_r1 = [k for k,v in sent.items() if not v.get('sent_relance1') and not v.get('bounce') and not v.get('bloque') and not v.get('doublon')]
print("envoyes sans relance1 (candidates relance):", len(no_r1))
print("exemples:", no_r1[:15])
# file restante = 367-210=157
