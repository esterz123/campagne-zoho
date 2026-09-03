import json, os
os.chdir(r'C:\Users\ulamb\Bureau\prospection\github-campagne')
d=json.load(open('campagne_data.json',encoding='utf-8'))
by_num={str(e.get('num')):e for e in d}
for n in ['252','264','284','404']:
    e=by_num[n]
    print('NUM', n)
    print('  to:', e.get('to'))
    print('  url/site:', e.get('url'), '|', e.get('site',''))
    print('  sujet:', e.get('subject',''))
    print('  body 300:', repr(e.get('body','')[:300]))
    print()
