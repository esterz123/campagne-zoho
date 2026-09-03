import json
st = json.load(open('campagne_state.json', encoding='utf-8'))
v = st['sent'].get('52')
print("MPI #52 state:", json.dumps(v, ensure_ascii=False)[:400])
# MPI relance? ab?
try:
    ab = json.load(open('ab_test.json', encoding='utf-8'))
    print("MPI ab:", ab.get('52'))
except: pass
# check followups.json pour MPI
try:
    fu = json.load(open('followups.json', encoding='utf-8'))
    if isinstance(fu, dict) and '52' in fu: print("fu52:", json.dumps(fu['52'], ensure_ascii=False)[:400])
    elif isinstance(fu, list):
        for f in fu:
            if str(f.get('num'))=='52': print("fu52:", json.dumps(f, ensure_ascii=False)[:400])
except Exception as e: print("followups:", e)
