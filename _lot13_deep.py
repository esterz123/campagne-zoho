#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : verifs complementaires (133, 125, 118, 130, 123, 128) : SIREN + emails toutes pages."""
import json, re, urllib.request, time
from urllib.parse import urljoin

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

def get(url, mb=300000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(mb).decode("utf-8", "ignore")

def scan(url, siren, label):
    print(f"=== {label} : {url} (siren {siren}) ===")
    try:
        html = get(url)
    except Exception as e:
        print(f"    ERR {str(e)[:120]}")
        return
    links = set()
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html):
        l = m.group(1)
        if l.startswith("http") or l.startswith("/") or l.startswith("."):
            links.add(urljoin(url, l))
    links = [l for l in links if l.split("#")[0] != url.split("#")[0]][:40]
    emails_all = set()
    siren_ok = False
    pages_checked = 0
    for l in links[:25]:
        try:
            h2 = get(l, 200000)
            pages_checked += 1
            ems = set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", h2))
            ems = {e for e in ems if not any(x in e.lower() for x in [".png",".jpg",".jpeg",".gif",".webp",".svg","@2x","sentry","example","wixpress"])}
            emails_all |= ems
            if siren in re.sub(r"\s", "", h2):
                siren_ok = True
            if len(emails_all) > 10:
                break
        except Exception:
            pass
        time.sleep(0.15)
    print(f"    pages_checked={pages_checked} siren_ok={siren_ok}")
    print(f"    emails={sorted(emails_all)[:12]}")

scan("https://metallerie.com/", "817734593", "133 Metallerie Francilienne")
scan("https://samd-aero.fr/", "401884382", "125 SAMD")
scan("https://www.smg-decoupage-tolerie.com/", "484871272", "118 SMG")
scan("https://lg-metallerie.fr/", "803868660", "130 LG Metallerie")
scan("https://sare-sarl-69.fr/", "351174081", "123 SARE")
scan("https://batisud.org/", "501007652", "128 Batisud")
