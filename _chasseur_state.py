import json, os
os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
d = json.load(open('nouveau_prospects.json', encoding='utf-8'))
emails, sites, sirens = set(), set(), set()
for p in d:
    e = p.get('email')
    if isinstance(e, list):
        for x in e:
            emails.add(x.lower())
    elif e:
        emails.add(e.lower())
    if p.get('site'):
        sites.add(p['site'].lower().replace('https://', '').replace('http://', '').rstrip('/'))
    if p.get('siren'):
        sirens.add(str(p['siren']))
print(len(d), 'entries |', len(emails), 'emails |', len(sites), 'sites')
print('SITES:', sorted(sites))
print('EMAILS:', sorted(emails))
print('SIRENS:', sorted(sirens))
