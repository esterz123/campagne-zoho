import json, io, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
d = json.load(io.open('campagne_data.json', encoding='utf-8'))
s = json.load(io.open('campagne_state.json', encoding='utf-8'))
sent = s.get('sent', {})
if isinstance(d, list):
    nums_d = {str(x.get('num')) for x in d}
    print('fiches file:', len(d))
else:
    nums_d = set(d.keys())
    print('fiches file:', len(d))
print('sent:', len(sent))
rest = [n for n in nums_d if n not in sent]
print('restants reels:', len(rest))
reps = [(k, sent[k].get('on')) for k in sent if sent[k].get('replied')]
print('replied:', len(reps))
for k, on in sorted(reps, key=lambda t: t[1] or '', reverse=True)[:8]:
    print('  rep', k, on)
# relances du jour ?
today = '2026-09-05'
fu1 = [k for k, v in sent.items() if v.get('sent_relance1', '') == today or str(v.get('sent_relance1', '')).startswith(today)]
fu_any = [k for k, v in sent.items() if 'relance' in str(v) and str(v.get('on', '')) <= '2026-08-30']
print('relances marquees today:', len(fu1))
print('envois today:', [k for k, v in sent.items() if str(v.get('on', '')).startswith('2026-09-05')])
print('envois 0904:', [k for k, v in sent.items() if str(v.get('on', '')).startswith('2026-09-04')])
rev = json.load(io.open('suivi_revenus.json', encoding='utf-8'))
ents = [e for e in rev.get('entrees', [])]
cash = sum(e.get('montant', 0) for e in ents if e.get('statut') == 'encaisse' and 'TEST' not in str(e.get('note', '')).upper() and 'mahdi-design' not in str(e.get('source', '')))
print('cash reel cycle:', cash)
for e in ents[-5:]:
    print('  rev', e.get('date'), e.get('montant'), e.get('statut'), str(e.get('source'))[:40])
