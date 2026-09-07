import json, os
os.chdir(r'C:\Users\ulamb\Bureau\prospection\github-campagne')

# Levee de doute J+14 : les 79 relances "dues" ont-elles deja recu J+14 ?
s = json.load(open('campagne_state.json', encoding='utf-8'))
sent = s['sent']

import datetime
now = datetime.date(2026, 9, 6)
suspects = []
for k, v in sent.items():
    if not isinstance(v, dict):
        continue
    r1 = v.get('sent_relance1'); r2 = v.get('sent_relance2'); r3 = v.get('sent_relance3')
    r14 = v.get('sent_relance14') or v.get('sent_j14') or v.get('relance_j14')
    if r2 and not r3 and not r14:
        d2 = str(r2)[:10]
        try:
            dd = datetime.date.fromisoformat(d2)
        except Exception:
            continue
        if (now - dd).days >= 7:
            suspects.append((k, d2, sorted(v.keys())))

print("SUSPECTS J+14 non envoye malgre retard:", len(suspects))
if suspects:
    k, d2, keys = suspects[0]
    print("exemple cle", k, "relance2 le", d2)
    print("cles dispo:", keys)
    # quels suffixes sent_ existent dans tout l'etat ?
    allkeys = set()
    for v in sent.values():
        if isinstance(v, dict):
            allkeys.update(v.keys())
    print("TOUTES cles rencontrees:", sorted(allkeys))
