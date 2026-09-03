import json, re, datetime, collections, os
st=json.load(open('campagne_state.json'))
data=json.load(open('campagne_data.json'))
ab=json.load(open('ab_test.json'))
sent=st.get('sent',{})

# A/B: reponses par variante
by_var={'A':[0,0],'B':[0,0]}  # envoyes, replied
for k,v in sent.items():
    var=ab.get(k)
    if var in by_var:
        by_var[var][0]+=1
        if v.get('replied'): by_var[var][1]+=1
print('A/B sent/replied:', by_var)

# par categorie d'objet
def cat(s):
    s=s.lower()
    if re.search(r'pirat|casino|fraude|hack',s): return 'pirate'
    if re.search(r'ouvert|j\'ai (ouvert|regarde|tape)',s): return 'ouverture-site'
    if re.search(r'\?$',s.strip()) or s.startswith('question'): return 'question'
    return 'autre'
cats=collections.defaultdict(lambda:[0,0])
for d in data:
    num=str(d['num'])
    if num not in sent: continue
    c=cat(d.get('subject',''))
    cats[c][0]+=1
    if sent[num].get('replied'): cats[c][1]+=1
for c,(s,r) in sorted(cats.items()):
    print(f'{c}: {s} envoyes, {r} reponses ({100*r/s if s else 0:.1f}%)')

# relances en attente (due_fu)
fu=st.get('followups',st.get('relances',{}))
print('followups keys:', list(fu)[:3] if isinstance(fu,dict) else type(fu))
# dates de dernier envoi pour les replied
for num in [k for k,v in sent.items() if v.get('replied')]:
    print('replied', num, sent[num])
    d=[x for x in data if str(x['num'])==num]
    if d: print('   to:', d[0].get('to'), '| subj:', d[0].get('subject','')[:60])
