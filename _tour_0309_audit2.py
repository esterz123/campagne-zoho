# -*- coding: utf-8 -*-
"""Audit tour 03/09 03h30 v2 : cles reelles du state."""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'C:\Users\ulamb\Bureau\prospection\github-campagne')

s = json.load(open('campagne_state.json', encoding='utf-8'))
print('TOP KEYS:', list(s.keys()))
sent = s.get('sent', {})
print('len sent:', len(sent))
if sent:
    k0 = next(iter(sent))
    print('sample sent entry:', k0, '->', json.dumps(sent[k0], ensure_ascii=False)[:400])

partis = [v for v in sent.values() if isinstance(v, dict) and v.get('on')]
bounces = [v for v in sent.values() if isinstance(v, dict) and v.get('bounce')]
replied = [v for v in sent.values() if isinstance(v, dict) and v.get('replied')]
auj = [v for v in partis if str(v.get('on', '')).startswith('2026-09-03')]
hier = [v for v in partis if str(v.get('on', '')).startswith('2026-09-02')]
r1 = [v for v in sent.values() if isinstance(v, dict) and v.get('sent_relance1')]
r2 = [v for v in sent.values() if isinstance(v, dict) and v.get('sent_relance2')]
print('PARTIS:', len(partis), '| bounce:', len(bounces), '| replied:', len(replied))
print('envois 02/09:', len(hier), '| envois 03/09:', len(auj))
print('relance1:', len(r1), '| relance2:', len(r2))

bloques = [v for v in sent.values() if isinstance(v, dict) and (v.get('bloque') or v.get('doublon'))]
print('bloques/doublons:', len(bloques))

# data fiches
data = json.load(open(r'C:\Users\ulamb\Bureau\prospection\campagne_data.json', encoding='utf-8'))
print('data type:', type(data).__name__, '| keys:' , list(data.keys())[:15] if isinstance(data, dict) else 'LIST len ' + str(len(data)))
if isinstance(data, dict):
    for kk in ('fiches', 'prospects', 'sites', 'contacts'):
        if kk in data:
            v = data[kk]
            print(kk, '->', (len(v) if hasattr(v, '__len__') else type(v).__name__))

# GO2 / relance files n'importe ou
for root in [r'C:\Users\ulamb\Bureau\prospection', r'C:\Users\ulamb\Bureau\prospection\github-campagne']:
    hits = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules')]
        for f in files:
            fl = f.lower()
            if 'gaultier' in fl or 'simi' in fl:
                hits.append(os.path.join(dirpath, f))
    print(root, '->', len(hits), 'fichiers gaultier/simi:')
    for h in hits[:20]:
        print('   ', h, os.path.getmtime(h))
