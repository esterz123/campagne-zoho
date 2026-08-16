#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : verification SMG / UMA / SDEB / GB."""
import json, re, urllib.request, urllib.parse, time
from urllib.parse import urljoin

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

def get(url, mb=400000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(mb).decode("utf-8", "ignore")

def api(q):
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={urllib.parse.quote(q)}&per_page=3"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode("utf-8"))

def emails_of(h):
    ems = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", h)))
    return [e for e in ems if not any(x in e.lower() for x in [".png",".jpg",".jpeg",".gif",".webp",".svg","@2x","sentry","wixpress","example"])]

print("=== SMG : SIREN 178658903 = qui ? ===")
try:
    j = api("178658903")
    for res in j.get("results", [])[:3]:
        print(res.get("nom_complet") or res.get("nom_raison_sociale"), "|", res.get("siren"), "|", res.get("tranche_effectif_salarie"), "|", res.get("siege", {}).get("adresse"))
except Exception as e:
    print("ERR", str(e)[:100])

print("\n=== SMG cible : 484871272 ===")
try:
    j = api("484871272")
    for res in j.get("results", [])[:2]:
        print(res.get("nom_complet") or res.get("nom_raison_sociale"), "|", res.get("siren"), "|", res.get("tranche_effectif_salarie"))
except Exception as e:
    print("ERR", str(e)[:100])

print("\n=== SMG : page l-entreprise + contact, chercher 484871272 ===")
for u in ["https://www.smg-decoupage-tolerie.com/lentreprise-smg-confrere/", "https://www.smg-decoupage-tolerie.com/contact/"]:
    try:
        h = get(u)
        text = re.sub(r"<[^>]+>", " ", h)
        text = re.sub(r"\s+", " ", text)
        print(u)
        print("  siren dans page:", re.findall(r"\d{9}", re.sub(r"\s","",h))[:4])
        print("  emails:", emails_of(h)[:8])
        print("  extrait:", text[:300])
    except Exception as e:
        print(u, "ERR", str(e)[:100])

print("\n=== UMA : page contact / mentions ===")
for u in ["https://uma02.fr/", "https://uma02.fr/contact/", "https://uma02.fr/mentions-legales/"]:
    try:
        h = get(u)
        text = re.sub(r"<[^>]+>", " ", h)
        text = re.sub(r"\s+", " ", text)
        print(u)
        print("  emails:", emails_of(h)[:8])
        print("  siren:", re.findall(r"\d{9}", re.sub(r"\s","",h))[:3])
        print("  extrait:", text[:250])
    except Exception as e:
        print(u, "ERR", str(e)[:100])

print("\n=== SDEB : home HTML brut emails/mailto ===")
try:
    h = get("https://sdeb.fr/")
    print("  emails home:", emails_of(h)[:8])
    print("  mailto:", re.findall(r"mailto:([^\"']+)", h)[:6])
    print("  tel:", re.findall(r"tel:([^\"']+)", h)[:6])
    # chercher un email dans le JS
    print("  js emails:", re.findall(r"[a-zA-Z0-9._%+\-]+@sdeb\.fr", h)[:6])
except Exception as e:
    print("ERR", str(e)[:100])

print("\n=== GB : chercher 397020033 sur groupe-gb.fr ===")
for u in ["https://groupe-gb.fr/gb-metallerie/", "https://groupe-gb.fr/contact/", "https://groupe-gb.fr/"]:
    try:
        h = get(u)
        found = "397020033" in re.sub(r"\s", "", h)
        s_in = re.findall(r"\d{9}", re.sub(r"\s", "", h))[:6]
        print(f"{u}: siren397020033={found} siren_in_page={s_in}")
    except Exception as e:
        print(u, "ERR", str(e)[:100])
