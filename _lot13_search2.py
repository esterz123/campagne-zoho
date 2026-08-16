#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : test gb-metallerie.fr + recherche web candidats restants."""
import json, re, subprocess, time, urllib.request
from hermes_tools import web_search

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"}

def get(url, mb=400000):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(mb).decode("utf-8", "ignore")

def emails_of(h):
    ems = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", h)))
    return [e for e in ems if not any(x in e.lower() for x in [".png",".jpg",".jpeg",".gif",".webp",".svg","@2x","sentry","wixpress","example"])]

print("=== gb-metallerie.fr ===")
for u in ["https://gb-metallerie.fr/", "http://gb-metallerie.fr/", "https://www.gb-metallerie.fr/"]:
    try:
        h = get(u)
        text = re.sub(r"<[^>]+>", " ", h)
        text = re.sub(r"\s+", " ", text)
        print(u, "OK | title:", re.findall(r"<title[^>]*>(.*?)</title>", h, re.I|re.S)[:1])
        print("  emails:", emails_of(h)[:8])
        print("  siren:", re.findall(r"\d{9}", re.sub(r"\s","",h))[:4])
        print("  extrait:", text[:250])
        break
    except Exception as e:
        print(u, "ERR", str(e)[:90])

print("\n=== web_search candidats restants ===")
queries = {
 110: "NDE Normandie decoupage emboutissage Crulai tôlerie site officiel",
 112: "Emboutissage du Mail Moirans site",
 114: "Jelza emboutissage Saint-Florent-sur-Cher site",
 139: "CST Chaudronnerie Soudure Tuyauterie Petiville site",
 140: "Soudure tuyauterie brestoise Brest site",
 142: "Brivet Mecano Soudure Pontchateau site",
 143: "TSC Tuyauterie Soudure Chauffage Villecresnes site",
 147: "Tolerie de la Loire Nantes site",
 145: "Mecano soudure Aron Saint-Igny-de-Roche site",
 136: "ES Soudure Metz site",
 138: "Sud Soudure Saint-Joseph site",
 122: "Societe normande decoupage emboutissage Londinieres site",
 121: "Sud Ouest Emboutissage Ussac site",
 113: "Ouest Emboutissage Cerizay site",
 116: "Groupe ATEC Cavignac emboutissage",
}
for idx, q in queries.items():
    try:
        r = web_search(q, limit=4)
        res = r.get("data", {}).get("web", [])
        urls = [(x.get("url",""), x.get("title","")) for x in res]
        interesting = [u for u,t in urls if not any(a in u for a in ["pagesjaunes","societe.com","pappers","annuaire","kompass","yelp","linfodurable","verif.com","data.gouv","francebleu","facebook"])]
        print(f"[{idx}] {q[:45]}")
        for u,t in interesting[:3]:
            print(f"    {u} | {t[:70]}")
    except Exception as e:
        print(f"[{idx}] ERR {e}")
    time.sleep(1.2)
