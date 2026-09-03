# Probe 6 : objets reels (champ ?) + relances_constats echantillon + boucle auto dernier diagnostic
import json
from collections import Counter

data = json.load(open('campagne_data.json'))
d = data[0]
print("=== CHAMPS d'une fiche ===")
print(list(d.keys()))
print({k: str(v)[:80] for k, v in list(d.items())[:12]})

# champ objet sous un autre nom ?
for field in ('sujet', 'subject', 'sujets', 'objet_a', 'objetB', 'ab'):
    if field in d:
        print("TROUVE champ:", field, "=", str(d[field])[:100])

# sujets par variantes
suj = Counter()
for dd in data:
    s = dd.get('sujet') or dd.get('subject') or ''
    suj[str(s)[:60]] += 1
print("\nTOP objets:", suj.most_common(8))

# echantillon relance1 (celles dues J+7 : nums 1-89 du 11-18/08)
import os
f = 'relances_constats/relance1_prospect_12.txt'
if os.path.exists(f):
    print("\n=== RELANCE1 num 12 ===")
    print(open(f, encoding='utf-8', errors='replace').read()[:700])

# boucle auto : dernier diagnostic complet
j = json.load(open('amelioration_journal.json'))
items = j if isinstance(j, list) else list(j.values())
print("\n=== JOURNAL 8 derniers (date+mesure) ===")
for c in items[-8:]:
    if isinstance(c, dict):
        m = c.get('mesure', {})
        print(c.get('date', '?')[:16], '| diag:', c.get('diagnostic'), '| rep:', m.get('taux_reponse_pct'), '% | cash:', m.get('argent_reel_eur'))
