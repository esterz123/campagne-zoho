import json
r = json.load(open('repondeur_state.json', encoding='utf-8'))
t = r.get('traites', [])
print('total traites:', len(t))
print('5 derniers:', t[-5:])
# messages non traites ?
for k in r:
    if k != 'traites':
        print(k, '->', str(r[k])[:300])
