import json, datetime, os, re
st=json.load(open('campagne_state.json'))
data=json.load(open('campagne_data.json'))
today=datetime.date.today().isoformat()
sent=st.get('sent',{})
n_sent=len(sent)
today_sent=[k for k,v in sent.items() if v.get('on')==today]
replied=[k for k,v in sent.items() if v.get('replied')]
print('total sent:',n_sent)
print('sent today:',len(today_sent), sorted(today_sent, key=lambda x:int(x))[:12])
print('replied total:',len(replied), sorted(replied, key=lambda x:int(x))[:20])
rem=[d['num'] for d in data if str(d['num']) not in sent]
print('remaining:',len(rem))
# dernier 7 jours envoyes
d7=datetime.date.today()-datetime.timedelta(days=7)
last7=[k for k,v in sent.items() if v.get('on','')>=d7.isoformat()]
print('sent last 7d:',len(last7))
# revenus reels
try:
    rev=json.load(open('suivi_revenus.json'))
    ent=rev if isinstance(rev,list) else rev.get('entrees',rev)
    tot=0; nreal=0
    for e in ent:
        note=(e.get('note') or '').upper()
        payeur=(e.get('payeur') or e.get('de') or '').lower()
        if 'TEST' in note or 'mahdi-design' in payeur: continue
        tot+=float(e.get('montant',0)); nreal+=1
    print('CA reel:',tot,'EUR sur',nreal,'entrees')
    for e in ent[-8:]:
        print('  ', e.get('date'), e.get('montant'), (e.get('note') or '')[:50])
except Exception as ex: print('rev err',ex)
print('PAUSE_ENVOIS exists:',os.path.exists('PAUSE_ENVOIS'))
print('SEND_LOCK exists:',os.path.exists('SEND_LOCK'))
# ab test
try:
    ab=json.load(open('ab_test.json'))
    print('ab_test keys:',list(ab)[:5], 'n=',len(ab) if isinstance(ab,(dict,list)) else '?')
except Exception as ex: print('ab err',ex)
