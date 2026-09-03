# -*- coding: utf-8 -*-
"""Verif Anjou Decolletage: images en CSS/background (justifie 17 photos sans legende?) + date mentions."""
import json, io, sys, urllib.request, re, ssl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(u):
    req = urllib.request.Request(u, headers={'User-Agent':'Mozilla/5.0'})
    r = urllib.request.urlopen(req, timeout=25, context=ctx)
    return r.status, r.read(500000).decode('utf-8', errors='replace')

st, html = get('https://anjoudecolletage.com')
print('HTTP', st, '| len', len(html))
# images en background-image / srcset / figures
bgs = re.findall(r'background-image\s*:\s*url\(([^)]+)\)', html, re.I)
srcs = re.findall(r'<img[^>]*src=["\']([^"\']+)["\']', html, re.I)
lazys = re.findall(r'data-src=["\']([^"\']+)["\']', html, re.I)
srcset = re.findall(r'srcset=["\']([^"\']+)["\']', html, re.I)
print('background-image:', len(bgs), '| img src:', len(srcs), '| data-src (lazy):', len(lazys), '| srcset:', len(srcset))
print('echantillon bg:', bgs[:3])
print('echantillon lazy:', lazys[:3])
# figures / legendes
figs = len(re.findall(r'<figure', html, re.I))
caps = len(re.findall(r'<figcaption', html, re.I))
print('figure:', figs, '| figcaption:', caps)
# titre duplique?
m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S|re.I)
print('TITLE brut:', repr(m.group(1)) if m else 'ABSENT')
# h2 interet
h2s = [re.sub(r'<[^>]+>','',h).strip()[:70] for h in re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.S|re.I)]
print('H2:', h2s[:6])
