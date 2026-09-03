import json, datetime, os, glob
from collections import Counter

s = json.load(open('campagne_state.json', encoding='utf-8'))
sent = s['sent']

print('=== 1. COMPRESION RELANCES (plusieurs etapes le meme jour) ===')
comp = 0
for num, v in sorted(sent.items(), key=lambda x: int(x[0])):
    dates = {}
    for st in ('sent_relance1', 'sent_relance2', 'sent_relance3'):
        if v.get(st):
            dates.setdefault(v[st], []).append(st.replace('sent_', ''))
    for d, stages in dates.items():
        if len(stages) > 1:
            comp += 1
            print('  #%s le %s -> %s (on=%s)' % (num, d, stages, v.get('on')))
print('total leads compresses:', comp)

print('=== 2. sent_relance3 compte dans le quota ? ===')
today = datetime.date.today().isoformat()
r3_today = [k for k, v in sent.items() if v.get('sent_relance3') == today]
in_today = [k for k, v in sent.items() if v.get('on') == today or v.get('sent_relance1') == today or v.get('sent_relance2') == today]
print('relance3 envoyes aujourd\'hui:', len(r3_today), r3_today[:10])
print('comptes dans sent_today (quota):', len(in_today))
overlap = set(r3_today) & set(in_today)
print('relance3 deja comptes:', len(overlap), '| relance3 INVISIBLES au quota:', len(set(r3_today) - overlap))

print('=== 3. PLAFOND PAR BOITE aujourd\'hui ===')
bx = Counter()
for k, v in sent.items():
    if v.get('on') == today or v.get('sent_relance1') == today or v.get('sent_relance2') == today:
        bx[v.get('via', '?')] += 1
bx3 = Counter()
for k, v in sent.items():
    if v.get('sent_relance3') == today:
        bx3[v.get('via', '?')] += 1
print('compte officiel (quota):', dict(bx))
print('relance3 par boite (non comptees):', dict(bx3))

print('=== 4. PROMESSES DATEES dans les mails ===')
d = json.load(open('campagne_data.json', encoding='utf-8'))
import re
pat = re.compile(r'31[ /]0?8|31 ao[uû]t|avant le 31|jusqu[\'`]?au 31|offre v2|gratuit.*48h|48h.*gratuit', re.I)
hits = 0
for e in d:
    txt = (e.get('subject', '') + ' ' + e.get('body', ''))
    m = pat.findall(txt)
    if m:
        hits += 1
        if hits <= 8:
            print('  #%s %s: %s' % (e.get('num'), e.get('prospect', '?')[:25], set(x.lower() for x in m)))
print('mails avec promesse datee suspecte:', hits, '/', len(d))

print('=== 5. RELANCES CONSTATS: fichiers relance3 existent ? ===')
for st in ('relance1', 'relance2', 'relance3'):
    n = len(glob.glob('relances_constats/%s_*.txt' % st))
    print('  %s: %d fichiers' % (st, n))

print('=== 6. U+2019 dans les fichiers de la chaine ===')
bad = []
for f in glob.glob('*.py') + glob.glob('*.json') + glob.glob('relances_constats/*.txt') + glob.glob('followups.json'):
    try:
        t = open(f, encoding='utf-8').read()
        if '\u2019' in t:
            bad.append((f, t.count('\u2019')))
    except Exception:
        pass
print('fichiers avec U+2019:', bad[:10] if bad else 'aucun')

print('=== 7. DOMAINES BLOQUES / BOUNCE SHIELD ===')
for f in ('bloquees.json', 'bounce_log.json', 'domaines_bloques.json'):
    if os.path.exists(f):
        try:
            j = json.load(open(f, encoding='utf-8'))
            print(' ', f, '->', len(j) if hasattr(j, '__len__') else j, list(j)[:6] if isinstance(j, dict) else j[:4])
        except Exception as e:
            print(' ', f, 'ERR', e)
print('SEND_LOCK present:', os.path.exists('SEND_LOCK'), '| PAUSE_ENVOIS present:', os.path.exists('PAUSE_ENVOIS'))
