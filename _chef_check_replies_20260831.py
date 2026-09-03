import json, os

def load(p):
    if os.path.exists(p):
        return json.load(open(p, encoding='utf-8'))
    return None

st = load('repondeur_state.json')
if st is not None:
    if isinstance(st, dict):
        print('repondeur entries:', len(st))
        for k, v in list(st.items())[-6:]:
            print(' ', k, str(v)[:150])

cs = load('campagne_state.json')
if cs is not None and isinstance(cs, dict):
    replied = [k for k, v in cs.items() if isinstance(v, dict) and v.get('status') == 'replied']
    print('campagne_state replied:', len(replied), replied[:10])

sr = load('suivi_revenus.json')
if sr is not None:
    print('suivi_revenus:', str(sr)[:400])
