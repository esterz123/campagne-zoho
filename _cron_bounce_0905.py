import json, io, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
s = json.load(io.open('campagne_state.json', encoding='utf-8'))
sent = s['sent']
# echantillon bounce avec on vide
no_date = [(k, v) for k, v in sent.items() if v.get('bounce') and not v.get('on')]
with_date = [(k, v) for k, v in sent.items() if v.get('bounce') and v.get('on')]
print('bounce sans date:', len(no_date), '| avec date:', len(with_date))
for k, v in no_date[:3]:
    print('ND', k, json.dumps(v, ensure_ascii=False)[:160])
for k, v in with_date[:3]:
    print('WD', k, json.dumps(v, ensure_ascii=False)[:160])
try:
    db = json.load(io.open('domaines_bloques.json', encoding='utf-8'))
    print('domaines_bloques:', len(db), db[:10] if isinstance(db, list) else list(db)[:10])
except Exception as e:
    print('domaines_bloques absent:', e)
# fiche des bounce sans date: quel num ?
d = json.load(io.open('campagne_data.json', encoding='utf-8'))
fiches = {str(f['num']): f for f in d}
for k, v in no_date[:5]:
    f = fiches.get(k, {})
    print('fiche', k, f.get('to', '')[:40], '|', str(f.get('site'))[:40])
