# -*- coding: utf-8 -*-
# Couverture constats + sujet actuel des non-envoyes, pour variante C (score dans l'objet)
import json, os, re
os.chdir(os.path.dirname(os.path.abspath(__file__)))

d = json.load(open('campagne_data.json', encoding='utf-8'))
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st.get('sent', {})
try:
    co = json.load(open('constats_sites.json', encoding='utf-8'))
except Exception:
    co = {}

rest = [e for e in d if str(e.get('num')) not in sent]
with_note = [e for e in rest if str(e.get('num')) in co and co[str(e.get('num'))].get('note') is not None]
print(f"restants={len(rest)} avec_constat_note={len(with_note)}")
sujets = {}
for e in rest[:500]:
    s = e.get('subject', '')
    key = re.sub(r'[\d\s]+', 'N', s)[:40]
    sujets[key] = sujets.get(key, 0) + 1
for k, v in sorted(sujets.items(), key=lambda x: -x[1])[:6]:
    print(v, '|', k)
# echantillon avec note
for e in with_note[:5]:
    n = str(e.get('num'))
    print(n, co[n].get('note'), '| sujet:', e.get('subject', '')[:60])
