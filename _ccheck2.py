import json
from collections import Counter
cd = json.load(open('campagne_data.json', encoding='utf-8'))
print("list len:", len(cd))
keys = Counter()
for p in cd:
    keys.update(p.keys())
print("keys:", keys.most_common(25))
st = Counter(p.get('statut','?') for p in cd)
print("statuts:", st.most_common(20))
# champs reponse / statut similaires
for f in ['statut','status','repondu','reply','etape','phase']:
    vals = Counter(str(p.get(f)) for p in cd)
    if len(vals)>1: print(f, dict(vals.most_common(12)))
# combien ont un email
em = [p for p in cd if p.get('email')]
print("avec email:", len(em))
# chauds: repondus
rep = [p for p in cd if any(str(p.get(k,'')).lower() in ('1','true','oui','yes') for k in ('repondu','reply','reponse'))]
print("repondus:", len(rep))
