# -*- coding: utf-8 -*-
# Fix portfolio 03/09 : 5 fiches restantes sans la ligne "Portfolio : mahdi-design.com" en fin de corps
import json, shutil, re

shutil.copy('campagne_data.json', 'campagne_data.json.bak-portfolio-0903')
data = json.load(open('campagne_data.json', encoding='utf-8'))

LINE = 'Portfolio : mahdi-design.com'
fixed = []
for d in data:
    n = str(d.get('num'))
    if n not in ('102', '176', '180', '199', '206'):
        continue
    body = d.get('corps') or d.get('body') or d.get('message') or ''
    orig = body
    if n == '180':
        # corps casse : "...ce que vos prospects fuient.com" -> ligne portfolio perdue
        body = body.replace('ce que vos prospects fuient.com',
                            'ce que vos prospects fuient.\n\n' + LINE)
    elif n == '206':
        body = re.sub(r'Site : mahdi-design\.com\s*$', LINE, body.rstrip() + '\n').rstrip() + '\n'
    else:
        # finit par "mahdi-design.com" nu -> prefixer Portfolio :
        body = re.sub(r'mahdi-design\.com\s*$', LINE, body.rstrip() + '\n').rstrip() + '\n'
    if body != orig and 'Portfolio : mahdi-design.com' in body:
        if d.get('corps') is not None: d['corps'] = body
        elif d.get('body') is not None: d['body'] = body
        else: d['message'] = body
        fixed.append((n, body[-90:].replace('\n', ' | ')))

json.dump(data, open('campagne_data.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('FIXED:', len(fixed))
for n, tail in fixed:
    print(n, '->', tail)
