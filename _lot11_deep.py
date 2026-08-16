#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot11 : scan approfondi pages contact + verification identite SIREN sur sites."""
import json, re, time, urllib.request

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

def fetch(url, timeout=9):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(200000).decode("utf-8", "ignore")
    except Exception:
        return None

def emails_in(html):
    out = set()
    for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", (html or "").lower()):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".js",
                                ".css", ".svg", "schema.org", "w3.org", "sentry.io", "alpinejs",
                                "polyfill", "jquery", "email@domain", "@2x", ".webp", ".jpeg")):
            continue
        out.add(e)
    return sorted(out)

DEEP = {
    123: ["https://www.sare-sarl-69.fr/contact.php", "https://www.sare-sarl-69.fr/contact.html", "https://www.sare-sarl-69.fr/contactez-nous", "https://www.sare-sarl-69.fr/nous-contacter", "https://www.sare-sarl-69.fr/mentions-legales.html", "https://www.sare-sarl-69.fr/mentions-legales.php", "https://www.sare-sarl-69.fr/equipe", "https://www.sare-sarl-69.fr/a-propos"],
    124: ["https://uma.fr/contact.html", "https://uma.fr/contact.php", "https://uma.fr/contactez-nous", "https://uma.fr/nous-contacter", "https://uma.fr/mentions-legales", "https://uma.fr/mentions-legales.html", "https://uma.fr/accueil", "https://www.uma.fr/contact", "https://www.uma.fr/mentions-legales"],
    128: ["https://www.batisud.org/contact.html", "https://www.batisud.org/contact.php", "https://www.batisud.org/nous-contacter", "https://www.batisud.org/mentions-legales", "https://www.batisud.org/mentions-legales.html", "https://www.batisud.org/accueil", "https://www.batisud.org/"],
    130: ["https://www.lg-metallerie.fr/contact.html", "https://www.lg-metallerie.fr/contact", "https://www.lg-metallerie.fr/mentions-legales", "https://www.lg-metallerie.fr/mentions-legales.html", "https://www.lg-metallerie.fr/accueil", "https://www.lg-metallerie.fr/"],
    121: ["https://www.groupe-rouger.com/", "https://www.groupe-rouger.com/contact", "https://www.groupe-rouger.com/mentions-legales", "https://groupe-rouger.com/"],
    144: ["https://www.ats.fr/", "https://www.ats.fr/contact", "https://www.ats.fr/mentions-legales", "https://atlantiquetoleriesoudure.fr/mentions-legales", "https://atlantiquetoleriesoudure.fr/contact"],
    148: ["https://www.t-i.fr/", "https://www.t-i.fr/contact", "https://www.t-i.fr/mentions-legales", "https://www.ti-ventilation.fr/mentions-legales", "https://www.ti-ventilation.fr/contact", "https://www.ti-ventilation.fr/nous-contacter"],
    135: ["https://www.gatsbysoudure.com/contact", "https://www.gatsbysoudure.com/contact/", "https://www.gatsbysoudure.com/mentions-legales", "https://www.gatsbysoudure.com/mentions-legales/", "https://www.gatsbysoudure.com/nous-contacter", "https://www.gatsbysoudure.com/"],
    110: ["https://www.nde.fr/", "https://nde.fr/", "https://www.nde-decoupage.fr/", "https://www.nde-emboutissage.fr/", "https://www.normandie-decoupage.fr/", "https://www.normandiedecoupage.fr/"],
    114: ["https://www.jelza.fr/", "https://jelza.fr/", "https://www.jelza-emboutissage.fr/", "https://www.jelzaemboutissage.fr/"],
    116: ["https://www.atec.fr/", "https://atec.fr/", "https://www.groupe-atec.fr/", "https://www.atec-cavignac.fr/"],
    120: ["https://www.talbot-industrie.fr/", "https://talbot-industrie.fr/", "https://www.tde-emboutissage.fr/", "https://www.talbotdecoupage.fr/"],
    122: ["https://www.snde-emboutissage.fr/", "https://snde-emboutissage.fr/", "https://www.snde-decoupage.fr/", "https://www.snde76.fr/"],
    136: ["https://www.es-soudure.fr/", "https://es-soudure.fr/", "https://www.essoudure.fr/"],
    138: ["https://www.sud-soudure.fr/", "https://sud-soudure.fr/", "https://www.sudsoudure.fr/"],
    139: ["https://www.cst-petiville.fr/", "https://cst-petiville.fr/", "https://www.chaudronnerie-soudure-tuyauterie.fr/"],
    141: ["https://www.stm-redon.fr/", "https://stm-redon.fr/", "https://www.stm-soudure.fr/"],
    142: ["https://www.brivet.fr/", "https://brivet.fr/", "https://www.brivet-mecano-soudure.fr/"],
    143: ["https://www.tsc-chauffage.fr/", "https://tsc-chauffage.fr/", "https://www.tsc-tuyauterie.fr/"],
    145: ["https://www.msa-aron.fr/", "https://msa-aron.fr/", "https://www.msa-mecano-soudure.fr/", "https://www.mecano-soudure-aron.fr/"],
    125: ["https://www.samd-decoupage.fr/", "https://samd-decoupage.fr/", "https://www.samd-emboutissage.fr/", "https://www.samd77.fr/"],
    127: ["https://www.oaca-metallerie.fr/", "https://oaca-metallerie.fr/"],
}

# mots-cles identite par index (SIREN / ville / activite)
IDENT = {
    121: ["rouger", "emboutissage", "ussac"],
    144: ["ats", "atlantique", "tolerie", "soudure", "saint-nazaire"],
    148: ["tolerie industrielle", "mazieres", "320800139", "ventilation"],
    135: ["gatsby", "soudure", "bobigny"],
    110: ["nde", "crulai", "decoupage", "emboutissage", "419808985"],
    114: ["jelza", "saint-florent", "892541889"],
    116: ["atec", "cavignac", "447891862"],
    120: ["talbot", "mer", "345088371"],
    122: ["londinieres", "400567160", "normande"],
    136: ["es soudure", "metz", "841196504"],
    138: ["sud soudure", "saint-joseph", "428663686"],
    139: ["petiville", "304217292", "chaudronnerie"],
    141: ["redon", "788636215", "tuyauterie"],
    142: ["brivet", "pontchateau", "392675237"],
    143: ["villecresnes", "385147681", "tuyauterie"],
    145: ["aron", "332265263", "mecano"],
    125: ["collegien", "401884382", "decoupage"],
    127: ["agnos", "443830898", "metallerie"],
}

out = {}
try:
    out = json.load(open(BASE + r"\_lot11_deep_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

for idx, urls in DEEP.items():
    if str(idx) in out:
        continue
    found = {}
    for u in urls:
        h = fetch(u)
        if not h:
            continue
        es = emails_in(h)
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).lower()
        hits = [k for k in IDENT.get(idx, []) if k in t]
        found[u] = {"emails": es, "title": (re.search(r"<title[^>]*>(.*?)</title>", h, re.S | re.I) or [None, ""])[1][:70] if re.search(r"<title[^>]*>(.*?)</title>", h, re.S | re.I) else "", "kw": hits, "len": len(h)}
        print(idx, u, "| len:", len(h), "| kw:", hits, "|", found[u]["title"][:45], "|", es[:3], flush=True)
    out[str(idx)] = found
    json.dump(out, open(BASE + r"\_lot11_deep_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(0.3)
print("TERMINE", flush=True)
