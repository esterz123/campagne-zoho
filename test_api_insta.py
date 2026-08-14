#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test acces API interne Instagram (voie app mobile) sans login."""
import urllib.request, urllib.parse, json

UA_MOBILE = 'Instagram 219.0.0.12.117 Android (30/11; 420dpi; 1080x2400; samsung; SM-G991B; o1s; exynos2100; en_US; 335808396)'
UA_WEB = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'

def test(nom, url, headers):
    try:
        req = urllib.request.Request(url, headers=headers)
        d = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', errors='ignore')
        print(f'[{nom}] OK len={len(d)}')
        # extraire bio si JSON
        try:
            j = json.loads(d)
            u = j.get('data', {}).get('user', {})
            print('   full_name:', u.get('full_name'))
            print('   bio:', (u.get('biography') or '')[:120])
            print('   website:', u.get('external_url'))
            print('   followers:', u.get('edge_followed_by', {}).get('count'))
        except Exception as e:
            print('   (pas JSON exploitable)', str(e)[:80])
        return True
    except Exception as e:
        print(f'[{nom}] ERR {getattr(e, "code", "")}: {str(e)[:90]}')
        return False

username = 'salonbernardgassies33'
qs = urllib.parse.quote(username)

# Voie 1 : API web_profile_info (utilisee par l'app mobile) - sans login
test('web_profile_info', f'https://i.instagram.com/api/v1/users/web_profile_info/?username={qs}',
     {'User-Agent': UA_MOBILE, 'x-ig-app-id': '936619743392459'})

# Voie 2 : endpoint __a=1 (ancien endpoint web)
test('a=1', f'https://www.instagram.com/{qs}/?__a=1&__d=dis',
     {'User-Agent': UA_WEB, 'Accept': 'application/json'})

# Voie 3 : endpoint __a=1 avec __d=dis
test('a=1 dis', f'https://www.instagram.com/{qs}/?__a=1&__d=dis',
     {'User-Agent': UA_WEB})

# Voie 4 : i.instagram.com/users/username_info (endpoint public ancien)
test('username_info', f'https://i.instagram.com/api/v1/users/{qs}/username_info/',
     {'User-Agent': UA_MOBILE})
