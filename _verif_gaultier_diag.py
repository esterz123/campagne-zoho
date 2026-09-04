# Gaultier #63 + pages diag des nouvelles fiches
import json, os
d = json.load(open('campagne_data.json', encoding='utf-8'))
s = json.load(open('campagne_state.json', encoding='utf-8'))
print('GAULTIER #63:', json.dumps(s['sent'].get('63', {}), ensure_ascii=False)[:500])
for e in d:
    if e['num'] == 414:
        print('--- fiche 414 ---')
        print('SUBJECT:', e.get('subject'))
        print('BODY 250:', e.get('body', '')[:250].replace(chr(10), ' | '))
        break
pages = 'C:/Users/ulamb/Bureau/prospection/vitrine/diag'
if os.path.isdir(pages):
    man = [e['num'] for e in d
           if int(e['num']) > 413 and str(e['num']) not in s['sent']
           and not os.path.exists(f'{pages}/{e["num"]}.html')]
    print('fiches >413 sans page diag:', man)
    total_pages = len([f for f in os.listdir(pages) if f.endswith('.html')])
    print('total pages diag en ligne:', total_pages)
else:
    print('dossier diag absent:', pages)
