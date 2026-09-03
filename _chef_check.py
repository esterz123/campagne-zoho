import json, datetime
from collections import Counter

st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st.get('sent', {})
d = json.load(open('campagne_data.json', encoding='utf-8'))
nums_sent = set(str(k) for k in sent)
print('fiches:', len(d), '| envoyes:', len(nums_sent), '| restants:', len([r for r in d if str(r.get('num')) not in nums_sent]))

vals = [v for v in sent.values() if isinstance(v, dict)]
dates = Counter(str(v.get('date', ''))[:10] for v in vals)
for dt in sorted(dates)[-5:]:
    print('  envois', dt, '->', dates[dt])

auj = [k for k, v in sent.items() if isinstance(v, dict) and str(v.get('date', '')).startswith('2026-09-03')]
print('envois 03/09:', len(auj), auj[:12])

now = datetime.date(2026, 9, 3)
due = []
for k, v in sent.items():
    if isinstance(v, dict):
        try:
            d0 = datetime.date.fromisoformat(str(v.get('date', ''))[:10])
        except ValueError:
            continue
        j = (now - d0).days
        if j in (3, 7, 14):
            due.append((k, j))
print('relances dues (J+3/7/14):', len(due), sorted(due)[:15])
