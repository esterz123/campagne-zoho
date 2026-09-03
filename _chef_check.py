import json, datetime, os
os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
today = datetime.date.today().isoformat()

notes = json.load(open('constats_sites.json'))
data = json.load(open('campagne_data.json'))
st = json.load(open('campagne_state.json'))
sent = st.get('sent', {})
nonenv = [d for d in data if str(d.get('num')) not in sent]
sans_preuve = [d for d in nonenv if str(d.get('num')) not in notes]
print('non envoyes:', len(nonenv), '| sans preuve constat:', len(sans_preuve))
if nonenv:
    nnums = sorted(int(str(d.get('num'))) for d in nonenv)
    print('num range non-envoyes:', nnums[0], '-', nnums[-1])

try:
    fu = json.load(open('followups.json'))
    items = fu if isinstance(fu, list) else fu.get('relances', fu.get('items', []))
    print('relances followups:', len(items))
except Exception as e:
    print('ERR fu', e)

try:
    db = json.load(open('domaines_bloques.json'))
    n = len(db) if isinstance(db, (list, dict)) else 0
    print('domaines bloques:', n)
except Exception as e:
    print('pas de domaines_bloques:', e)

# relances dues aujourd'hui ?
try:
    rel = json.load(open('relances_conges.json'))
    print('relances conges:', len(rel) if isinstance(rel, list) else rel)
except Exception as e:
    print('pas de relances_conges:', e)
