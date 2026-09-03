# Probe 5 : SIMI etat exact + corps mail type + bounces + objets
import json, re, glob

st = json.load(open('campagne_state.json'))
sent = st.get('sent', {})
data = json.load(open('campagne_data.json'))
by_num = {str(d.get('num')): d for d in data}

# 1. SIMI
for d in data:
    blob = json.dumps(d, ensure_ascii=False)
    if 'simi' in blob.lower():
        num = str(d.get('num'))
        print("=== SIMI num", num, "===")
        print({k: str(v)[:120] for k, v in d.items() if k in ('num','email','entreprise','site','dirigeant','objet')})
        print("STATE:", json.dumps(sent.get(num, {}), ensure_ascii=False)[:500])
        break

# 2. Un mail envoye recent : corps complet
for d in sorted(data, key=lambda x: int(x.get('num', 0)), reverse=True):
    num = str(d.get('num'))
    v = sent.get(num)
    if isinstance(v, dict) and (v.get('on') or '').startswith('2026-08-3') or (isinstance(v, dict) and str(v.get('on',''))[:10] == '2026-09-01'):
        print("\n=== MAIL TYPE num", num, "objet:", str(d.get('objet'))[:80])
        print(str(d.get('corps', d.get('body', '')))[:1100])
        break

# 3. Bounces detectes ? chercher dans les json d'etat
for f in glob.glob('*bounce*') + glob.glob('*bounce*.*'):
    print("bounce file:", f)

# 4. Distribution des objets (apres reecriture)
from collections import Counter
objs = Counter()
for d in data:
    o = str(d.get('objet', ''))
    objs[o[:45]] += 1
print("\n=== TOP 12 OBJETS ===")
for o, n in objs.most_common(12):
    print(n, '|', o)

# 5. messages_livraison / dernier contact SIMI
try:
    ml = json.load(open('messages_livraison.json'))
    s = json.dumps(ml, ensure_ascii=False)
    i = s.lower().find('simi')
    print("\n=== MESSAGES LIVRAISON (extrait simi) ===")
    print(s[max(0, i-200):i+500] if i >= 0 else 'simi absent')
except Exception as e:
    print("ml ERR", e)
