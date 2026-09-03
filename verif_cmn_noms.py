# -*- coding: utf-8 -*-
"""Verif CMN: mentions-legales + noms sur le site (source dirigeant du mail?)."""
import json, io, sys, urllib.request, re, ssl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(u):
    req = urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0'})
    r = urllib.request.urlopen(req, timeout=25, context=ctx)
    return r.status, r.read(400000).decode('utf-8', errors='replace')

st, html = get('https://cmn-industrie.com/mentions-legales')
txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))
print('mentions HTTP', st, '| len', len(txt))
for pat in ['Chapolard', 'CHAPOLARD', 'Rasper', 'RASPER']:
    idxs = [m.start() for m in re.finditer(pat, txt)]
    print(pat, '->', [txt[max(0,i-100):i+150] for i in idxs[:3]])

# noms sur la home
st, html2 = get('https://cmn-industrie.com')
t2 = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html2))
for pat in ['Chapolard', 'CHAPOLARD', 'Rasper', 'RASPER']:
    idxs = [m.start() for m in re.finditer(pat, t2)]
    print('home', pat, '->', [t2[max(0,i-90):i+130] for i in idxs[:2]])

# JSON-LD / footer
for m in re.finditer(r'<script[^>]*ld\+json[^>]*>(.*?)</script>', html2, re.S|re.I):
    print('JSON-LD:', m.group(1)[:400])
