# -*- coding: utf-8 -*-
"""Verifs ciblees: fiches 351-354 (champs), CMN (nom dirigeant dans site), EST (mentions 2015), Anjou (img via CSS)."""
import json, io, sys, urllib.request, re, ssl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = json.load(open('campagne_data.json', encoding='utf-8'))
for p in d:
    if 'prospect' in p and p['num'] in (351, 352, 353, 354):
        print(p['num'], '|', p['prospect'], '| to:', p.get('to'), '| cc:', p.get('cc'))
        for k in p:
            if k not in ('num','prospect','to','cc','subject','body','site'):
                print('   ', k, '=', str(p[k])[:120])

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(u):
    req = urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0'})
    r = urllib.request.urlopen(req, timeout=20, context=ctx)
    return r.status, r.read(400000).decode('utf-8', errors='replace')

# CMN: chercher des noms de personnes dans le site
try:
    st, html = get('https://cmn-industrie.com')
    txt = re.sub(r'<[^>]+>', ' ', html)
    txt = re.sub(r'\s+', ' ', txt)
    for pat in ['Chapolard', 'CHAPOLARD', 'Rasper', 'RASPER', 'Dirigeant', 'dirigeant', 'Gerant', 'gérant', 'Président', 'M. ']:
        idxs = [m.start() for m in re.finditer(re.escape(pat), txt)]
        if idxs:
            i = idxs[0]
            print('CMN match', repr(pat), '->', txt[max(0,i-80):i+120][:220])
    # mentions legales page?
    m = re.search(r'href=["\']([^"\']*mention[^"\']*)["\']', html, re.I)
    print('CMN lien mentions:', m.group(1) if m else 'non trouve')
except Exception as e:
    print('CMN err:', type(e).__name__, str(e)[:100])

# EST: mentions legales -> date
try:
    st, html = get('https://estusinage.fr')
    m = re.search(r'href=["\']([^"\']*mention[^"\']*)["\']', html, re.I)
    print('EST lien mentions:', m.group(1) if m else 'non trouve')
    if m:
        mu = m.group(1)
        if mu.startswith('/'): mu = 'https://estusinage.fr' + mu
        st2, h2 = get(mu)
        t2 = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h2))
        years = re.findall(r'20[0-2][0-9]', t2)
        print('EST mentions HTTP', st2, 'annees vues:', sorted(set(years))[:12])
except Exception as e:
    print('EST err:', type(e).__name__, str(e)[:100])
