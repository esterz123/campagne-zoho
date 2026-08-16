#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : verification finale reserves (SAMD, metallerie.com, SMG, SDEB, GB)."""
import re, urllib.request
from urllib.parse import urljoin

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

def get(url, mb=400000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(mb).decode("utf-8", "ignore")

def emails_of(h):
    ems = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", h)))
    return [e for e in ems if not any(x in e.lower() for x in [".png",".jpg",".jpeg",".gif",".webp",".svg","@2x","sentry","wixpress","example"])]

print("=== 125 SAMD : contenu complet ===")
try:
    h = get("https://samd-aero.fr/")
    text = re.sub(r"<[^>]+>", " ", h)
    text = re.sub(r"\s+", " ", text)
    print("emails:", emails_of(h)[:8])
    print("siren:", re.findall(r"\d{9}", re.sub(r"\s","",h))[:3])
    print("extrait:", text[:600])
    links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', h)))
    print("liens:", [l for l in links if l.startswith("http") or l.startswith("/")][:12])
except Exception as e:
    print("ERR", str(e)[:120])

print("\n=== 133 metallerie.com : HTML complet ===")
try:
    h = get("https://metallerie.com/")
    text = re.sub(r"<[^>]+>", " ", h)
    text = re.sub(r"\s+", " ", text)
    print("emails:", emails_of(h)[:8])
    print("siren:", re.findall(r"\d{9}", re.sub(r"\s","",h))[:3])
    print("extrait:", text[:700])
    links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', h)))
    print("liens:", [l for l in links if l.startswith("http") or l.startswith("/")][:15])
except Exception as e:
    print("ERR", str(e)[:120])

print("\n=== 118 SMG : retry home + pages internes ===")
try:
    h = get("https://www.smg-decoupage-tolerie.com/", 500000)
    text = re.sub(r"<[^>]+>", " ", h)
    text = re.sub(r"\s+", " ", text)
    print("emails:", emails_of(h)[:10])
    print("siren:", re.findall(r"\d{9}", re.sub(r"\s","",h))[:3])
    print("extrait:", text[:500])
    links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', h)))
    plinks = [l for l in links if l.startswith("http") or l.startswith("/")]
    print("liens:", plinks[:15])
    for l in plinks[:10]:
        if "contact" in l.lower() or "mention" in l.lower():
            try:
                h2 = get(urljoin("https://www.smg-decoupage-tolerie.com/", l))
                s2 = re.findall(r"\d{9}", re.sub(r"\s", "", h2))[:2]
                print(f"  {l}: emails={emails_of(h2)[:8]} siren={s2}")
            except Exception as e:
                print(f"  {l}: ERR {str(e)[:80]}")
except Exception as e:
    print("ERR", str(e)[:120])

print("\n=== 111 SDEB : pages internes pour email @sdeb.fr ===")
try:
    h = get("https://sdeb.fr/")
    links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', h)))
    plinks = [l for l in links if l.startswith("http") or l.startswith("/")]
    print("liens:", plinks[:15])
    print("home emails:", emails_of(h)[:8])
    for l in plinks[:12]:
        if any(k in l.lower() for k in ["contact", "mention"]):
            try:
                h2 = get(urljoin("https://sdeb.fr/", l))
                print(f"  {l}: emails={emails_of(h2)[:8]}")
            except Exception as e:
                print(f"  {l}: ERR {str(e)[:80]}")
except Exception as e:
    print("ERR", str(e)[:120])

print("\n=== 131 GB Metallerie : page groupe + mentions ===")
try:
    h = get("https://groupe-gb.fr/gb-metallerie/")
    text = re.sub(r"<[^>]+>", " ", h)
    text = re.sub(r"\s+", " ", text)
    print("emails:", emails_of(h)[:10])
    print("siren:", re.findall(r"\d{9}", re.sub(r"\s","",h))[:3])
    print("extrait:", text[:500])
    for url in ["https://groupe-gb.fr/mentions-legales/", "https://groupe-gb.fr/mentions-legales"]:
        try:
            h2 = get(url)
            s2 = re.findall(r"\d{9}", re.sub(r"\s", "", h2))[:4]
            print(f"  {url}: siren={s2} emails={emails_of(h2)[:6]}")
        except Exception as e:
            print(f"  {url}: ERR {str(e)[:80]}")
except Exception as e:
    print("ERR", str(e)[:120])
