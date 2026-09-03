# -*- coding: utf-8 -*-
"""Audit express file campagne v2 - vraie structure."""
import json, io, sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = json.load(open(os.path.join(BASE, 'campagne_data.json'), encoding='utf-8'))
state = json.load(open(os.path.join(BASE, 'campagne_state.json'), encoding='utf-8'))
sent = state.get('sent', {})

prosp = [p for p in data if isinstance(p, dict)]
rest = [p for p in prosp if str(p.get('num')) not in sent]
print("records:", len(prosp), "| envoyes:", len(prosp)-len(rest), "| RESTANTS:", len(rest))

def g(p, *names):
    for n in names:
        v = p.get(n)
        if v: return v
    return ''

no_mail, no_objet, no_corps, no_nom, u2019, plain = [], [], [], [], [], []
for p in rest:
    if not g(p, 'to', 'email', 'mail'): no_mail.append(p.get('num'))
    if not g(p, 'subject', 'objet'): no_objet.append(p.get('num'))
    if not g(p, 'body', 'corps'): no_corps.append(p.get('num'))
    if '\u2019' in (g(p, 'subject') + g(p, 'body')): u2019.append(p.get('num'))

print("sans email:", len(no_mail), no_mail[:12])
print("sans objet:", len(no_objet), no_objet[:12])
print("sans corps:", len(no_corps), no_corps[:12])
print("U+2019 restants:", len(u2019), u2019[:12])

# note distribution
notes = [p.get('note') for p in rest if isinstance(p.get('note'), (int, float))]
if notes:
    notes.sort()
    print("notes: min", notes[0], "max", notes[-1], "n<60:", sum(1 for n in notes if n < 60), "/", len(notes))
else:
    print("notes: aucune note numerique")

# to_confirmed stats
conf = sum(1 for p in rest if p.get('to_confirmed'))
print("to_confirmed:", conf, "/", len(rest))

# sample 2 restants
for p in rest[:2]:
    print("--- SAMPLE num", p.get('num'), "site:", p.get('site'))
    print("objet:", repr(g(p, 'subject')[:130]))
    print("corps:", repr(g(p, 'body')[:400]))
