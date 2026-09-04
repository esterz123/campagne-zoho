# Les nouveaux corps contiennent-ils le lien /diag/<num>.html ?
import json
d = json.load(open('campagne_data.json', encoding='utf-8'))
s = json.load(open('campagne_state.json', encoding='utf-8'))
new = [e for e in d if int(e['num']) > 413 and str(e['num']) not in s['sent']]
with_link = [e['num'] for e in new if 'diag/' in e.get('body', '')]
with_ps = [e['num'] for e in new if 'P.S' in e.get('body', '') or 'P.S.' in e.get('body', '')]
print(f'nouvelles fiches: {len(new)} | avec lien diag/: {len(with_link)} | avec P.S.: {len(with_ps)}')
print('nums avec lien:', with_link)
# exemple du bloc P.S.
for e in new:
    if 'diag/' in e.get('body', ''):
        b = e['body']
        i = b.find('P.S')
        print('exemple P.S. fiche', e['num'], ':', b[i:i+160].replace(chr(10), ' '))
        break
# verif croisement: les envoyes recents (>413 envoyes) avaient-ils des liens diag vers pages existantes ?
sentnew = [e for e in d if int(e['num']) > 413 and str(e['num']) in s['sent']]
swl = [e['num'] for e in sentnew if 'diag/' in e.get('body', '')]
print('envoyes >413 avec lien diag:', swl)
