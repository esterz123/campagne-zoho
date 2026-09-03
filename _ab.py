import json
from collections import Counter
ab = json.load(open('ab_test.json', encoding='utf-8'))
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st['sent']
cnt = Counter()
for num, info in ab.items():
    if num in sent and sent[num].get('replied'):
        cnt[info.get('variant')] += 1
# aussi compter les replies hors ab
print("replies par variante A/B:", dict(cnt))
print("total replied:", sum(1 for v in sent.values() if v.get('replied')))
# bounces par variante
bc = Counter()
for num, info in ab.items():
    v = sent.get(num, {})
    if v.get('bounce'): bc[info.get('variant')] += 1
print("bounces par variante:", dict(bc))
