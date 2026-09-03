import json, os, datetime
man = json.load(open('diag_pages.json', encoding='utf-8'))
print('diag_pages entries:', len(man))
k0 = list(man)[0]
print('sample:', k0, man[k0])
sent = json.load(open('campagne_state.json', encoding='utf-8'))['sent']
missing = [n for n in sent if n not in man]
print('leads envoyes sans page diag:', len(missing), missing[:8])
print('diag_pages.json mtime:', datetime.date.fromtimestamp(os.path.getmtime('diag_pages.json')))
# does the URL actually exist locally?
u = (man.get(k0) or {}).get('url', '')
print('url sample:', u)
