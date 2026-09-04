# Audit 03/09 : GO2 Gaultier, SIMI, coherence file, revenus
import json, os
os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
st = json.load(open('campagne_state.json'))
go2 = {k: v for k, v in st.items() if k.startswith('go2')}
print('MARQUEURS GO2:', json.dumps(go2, ensure_ascii=False, indent=1)[:1500])
for k, v in st.get('sent', {}).items():
    t = (str(v.get('to', '')) + str(v.get('note', ''))).lower()
    if 'simi' in t:
        print('SIMI', k, json.dumps({a: b for a, b in v.items() if a != 'body'}, ensure_ascii=False)[:500])
