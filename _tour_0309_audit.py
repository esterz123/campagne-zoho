# -*- coding: utf-8 -*-
"""Audit tour 03/09 03h30 : etat reel de la machine, chiffres verifies."""
import json, io, sys, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'C:\Users\ulamb\Bureau\prospection\github-campagne')

s = json.load(open('campagne_state.json', encoding='utf-8'))
env = s.get('envois') or {}
recs = list(env.values()) if isinstance(env, dict) else env
partis = [r for r in recs if isinstance(r, dict) and r.get('on')]
bounces = [r for r in recs if isinstance(r, dict) and r.get('bounce')]
replied = [r for r in recs if isinstance(r, dict) and r.get('replied')]
auj = [r for r in partis if str(r.get('on','')).startswith('2026-09-03')]
hier = [r for r in partis if str(r.get('on','')).startswith('2026-09-02')]
print('TOTAL envoyes:', len(partis), '| bounces:', len(bounces), '| reponses:', len(replied))
print('envois 02/09:', len(hier), '| envois 03/09:', len(auj))

# fiches totales
data = json.load(open(r'C:\Users\ulamb\Bureau\prospection\campagne_data.json', encoding='utf-8'))
if isinstance(data, dict):
    fiches = data.get('fiches') or data.get('prospects') or {}
    if isinstance(fiches, dict):
        n_fiches = len(fiches)
    else:
        n_fiches = len(fiches)
else:
    n_fiches = '?'
print('fiches data:', n_fiches)
print('file restante:', (n_fiches - len(partis)) if isinstance(n_fiches, int) else '?')

# cash
try:
    rev = json.load(open(r'C:\Users\ulamb\Bureau\prospection\suivi_revenus.json', encoding='utf-8'))
    print('revenus:', json.dumps(rev, ensure_ascii=False)[:400])
except Exception as e:
    print('revenus: ERR', e)

# relances planifiees aujourd'hui (relance1 dues)
import datetime
j1 = [i for i, r in ((k, v) for k, v in env.items() if isinstance(v, dict))
      if r.get('on') and r.get('bounce') is not True and not r.get('replied')]
print('eligibles relance (envoyes non-bounce non-replied):', len(j1))

# relances parties aujourd'hui (via campagne_zoho logs?)
try:
    with open('relances_log.txt', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    print('relances_log tail:', ''.join(lines[-5:]).strip()[:500])
except Exception:
    print('pas de relances_log.txt')

# fichiers GO2 gaultier presents?
for fn in ['go2_gaultier.html', 'go2_gaultier.objet', 'relance_SIMI_closing.html', 'relance3_MILMECA_pour_oui.txt']:
    print(fn, ':', 'OK' if os.path.exists(fn) else 'ABSENT')
