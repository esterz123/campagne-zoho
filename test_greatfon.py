#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test greatfon : extraire bio + site du profil Instagram."""
import urllib.request, re, sys

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'}

def extraire(handle):
    url = f'https://greatfon.com/v/{handle}'
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode('utf-8', errors='ignore')
    bios = re.findall(r'"biography":"([^"]{5,400})"', d)
    urls = re.findall(r'[^a-z]((?:www\.)?[a-z0-9-]+\.[a-z]{2,}(?:/[^"\s]*)?)', d)
    names = re.findall(r'"full_name":"([^"]{2,80})"', d)
    print('==', handle)
    print(' bios:', len(bios), bios[:2])
    print(' names:', list(set(names))[:3])
    # filtrer les urls qui ressemblent a des sites (pas instagram/facebook/greatfon)
    sites = set()
    for u in urls:
        u2 = u.rstrip('.').lower()
        if not any(b in u2 for b in ['instagram.com', 'facebook.com', 'greatfon', 'google.', 'youtube', 'twitter.com', 't.me', 'wa.me']):
            sites.add(u2[:60])
    print(' sites:', list(sites)[:15])
    return bios

for h in sys.argv[1:]:
    try:
        extraire(h)
    except Exception as e:
        print(h, 'ERR', str(e)[:80])
