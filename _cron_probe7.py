# Probe 7 : journal boucle complet (dates) + priorite d'action actuelle
import json

j = json.load(open('amelioration_journal.json'))
items = j if isinstance(j, list) else list(j.values())
print("nb cycles:", len(items))
for c in items[-8:]:
    if isinstance(c, dict):
        m = c.get('mesure', {})
        print(str(c.get('date', c.get('ts', '?')))[:16], '| diag:', c.get('diagnostic'), '| rep:', m.get('taux_reponse_pct'), '% | cash:', m.get('argent_reel_eur'), '| act:', str(c.get('action'))[:40])
