#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : MX robustes (dig/python), SIREN SAMD, emails JS SARE/LG, mentions metallerie.com."""
import subprocess, json, re, urllib.request, socket

def mx_dig(dom):
    """dig si dispo, sinon python socket-based MX via dnspython, sinon nslookup retry."""
    try:
        r = subprocess.run(["dig", "+short", "MX", dom], capture_output=True, text=True, timeout=15)
        if r.stdout.strip():
            return r.stdout.strip().split("\n")
    except Exception:
        pass
    try:
        import dns.resolver
        ans = dns.resolver.resolve(dom, "MX")
        return [str(x.exchange) for x in ans]
    except Exception:
        pass
    return None

print("=== MX re-check ===")
for d in ["soudecoup.fr", "ats.fr", "atlantiquetoleriesoudure.fr", "metallerie.com", "smgconfrere.com",
          "torras.fr", "gatsbysoudure.com", "samd-aero.com", "samd-aero.fr", "lenoirmetallerie.fr",
          "oaca.fr", "sudmetallerie.com", "lg-metallerie.fr", "sare-sarl-69.fr", "gb-metallerie.fr"]:
    print(f"{d}: {mx_dig(d)}")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

def get(url, mb=300000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(mb).decode("utf-8", "ignore")

print("\n=== SAMD : page mentions/contact ===")
for url in ["https://samd-aero.fr/mentions-legales", "https://www.samd-aero.fr/mentions-legales/", "https://www.samd-aero.fr/contact/", "https://samd-aero.fr/contact"]:
    try:
        h = get(url)
        siren = re.findall(r"\d{9}", re.sub(r"\s", "", h))
        ems = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", h)))
        ems = [e for e in ems if not any(x in e.lower() for x in [".png",".jpg",".svg",".webp","sentry"])]
        t = re.findall(r"<title[^>]*>(.*?)</title>", h, re.I|re.S)[:1]
        print(f"{url} -> siren={siren[:3]} emails={ems[:6]} title={t}")
    except Exception as e:
        print(f"{url} ERR {str(e)[:80]}")

print("\n=== SARE : full HTML emails (JS inclus) ===")
try:
    h = get("https://sare-sarl-69.fr/")
    ems = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", h)))
    ems = [e for e in ems if not any(x in e.lower() for x in [".png",".jpg",".svg",".webp","sentry","wix"])]
    print("home emails:", ems[:8])
    # chercher mailto obfusque
    print("mailto:", re.findall(r"mailto:([^\"']+)", h)[:5])
    print("tel:", re.findall(r"tel:([^\"']+)", h)[:5])
    # liens pages
    links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', h)))
    links = [l for l in links if l.startswith("http") or l.startswith("/")]
    print("links:", links[:15])
except Exception as e:
    print("ERR", str(e)[:120])

print("\n=== LG Metallerie : page contact Wix ===")
for url in ["https://www.lg-metallerie.fr/", "https://www.lg-metallerie.fr/contact", "https://www.lg-metallerie.fr/contact-1"]:
    try:
        h = get(url)
        ems = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", h)))
        ems = [e for e in ems if not any(x in e.lower() for x in [".png",".jpg",".svg",".webp","sentry","wixpress"])]
        mt = re.findall(r"mailto:([^\"']+)", h)[:4]
        print(f"{url} -> emails={ems[:8]} mailto={mt}")
    except Exception as e:
        print(f"{url} ERR {str(e)[:80]}")

print("\n=== metallerie.com : tenter https direct + variantes ===")
for url in ["https://metallerie.com/mentions-legales", "https://www.metallerie.com/", "https://www.metallerie.com/mentions-legales/"]:
    try:
        h = get(url)
        siren = re.findall(r"\d{9}", re.sub(r"\s", "", h))
        t = re.findall(r"<title[^>]*>(.*?)</title>", h, re.I|re.S)[:1]
        print(f"{url} -> status ok siren={siren[:3]} title={t}")
    except Exception as e:
        print(f"{url} ERR {str(e)[:80]}")
