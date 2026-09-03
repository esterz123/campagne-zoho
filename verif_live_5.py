# -*- coding: utf-8 -*-
"""Verif live des 5 fiches sans perso v2 + leurs corps actuels."""
import json, io, sys, urllib.request, urllib.error, re, ssl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = json.load(open('campagne_data.json', encoding='utf-8'))
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cibles = [p for p in d if 'prospect' in p and 'ligne1-v2' not in (p.get('note') or '')]
for p in cibles:
    print('='*70)
    print(p['num'], p['prospect'])
    print('TO:', p.get('to'), '| CC:', p.get('cc'))
    site = p.get('site') or ''
    if site:
        try:
            req = urllib.request.Request(site, headers={'User-Agent': 'Mozilla/5.0'})
            r = urllib.request.urlopen(req, timeout=15, context=ctx)
            html = r.read(200000).decode('utf-8', errors='replace')
            title = re.search(r'<title[^>]*>(.*?)</title>', html, re.S|re.I)
            viewport = bool(re.search(r'name=["\']viewport', html, re.I))
            imgs = re.findall(r'<img\b[^>]*>', html, re.I)
            noalt = [i for i in imgs if not re.search(r'alt\s*=\s*["\'][^"\']+["\']', i)]
            h1s = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.S|re.I)
            desc = re.search(r'name=["\']description["\'][^>]*content=["\'](.*?)["\']', html, re.I|re.S)
            print('HTTP', r.status, '| bytes', len(html))
            print('TITLE:', (title.group(1).strip()[:100] if title else 'ABSENT'))
            print('viewport:', viewport, '| img:', len(imgs), '| img sans alt:', len(noalt))
            print('H1:', [re.sub(r'<[^>]+>','',h).strip()[:80] for h in h1s][:2])
            print('DESC:', (desc.group(1)[:120] if desc else 'ABSENT'))
        except Exception as e:
            print('ERREUR SITE:', type(e).__name__, str(e)[:120])
    else:
        print('PAS DE SITE')
    print('SUJET:', (p.get('subject') or '')[:110])
    print('CORPS:', (p.get('body') or '')[:400].replace('\n',' / '))
