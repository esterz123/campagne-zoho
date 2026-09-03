import json, os
os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
st = json.load(open('campagne_state.json'))
go2 = {k: v for k, v in st.items() if k.startswith('go2') or k in ('go2_livraison_simi', 'go2_relance3_itplast')}
print('MARQUEURS GO2:', json.dumps(go2, ensure_ascii=False, indent=1))
# cles non-standard du state
std = {'sent', 'traites', 'exclusions', 'bounce'}
others = [k for k in st.keys() if k not in std and not str(k).isdigit()]
print('AUTRES CLES STATE:', others[:30])
