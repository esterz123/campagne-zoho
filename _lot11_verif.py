#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot11 : verification domaines cibles (mots-cles entreprise) + scan emails."""
import json, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

# index -> [domaines a tester]
CAND = {
    110: ["nde-decoupage.fr", "nde-emboutissage.fr", "nde.fr", "normandiedecoupage.fr",
          "normandie-decoupage.fr", "nde-decoupage-emboutissage.fr", "nde-emboutissage.fr"],
    111: ["sdeb.fr", "sdeb.com", "decoupage-emboutissage-bourbonnais.fr"],
    114: ["jelza.fr", "jelza-emboutissage.fr", "jelzaemboutissage.fr", "jelza.com"],
    116: ["atec-cavignac.fr", "groupe-atec.fr", "atec.fr", "atec-emboutissage.fr"],
    118: ["smg-decoupage-tolerie.com", "smg-decoupage.fr", "smg-emboutissage.fr", "smgdecoupage.fr"],
    120: ["tde-emboutissage.fr", "talbot-decoupage.fr", "tde41.fr", "talbotdecoupage.fr", "tde-mer.fr"],
    121: ["ouest-emboutissage.fr", "ouestemboutissage.fr", "sud-ouest-emboutissage.fr", "soe-emboutissage.fr"],
    122: ["snde.fr", "snde-decoupage.fr", "snde-emboutissage.fr", "societe-normande-decoupage.fr"],
    123: ["sare-sarl-69.fr", "sare69.fr", "sare-emboutissage.fr", "sare-repoussage.fr"],
    124: ["uma.fr", "uma-decoupage.fr", "uma-tolerie.fr", "uma-emboutissage.fr"],
    125: ["samd.fr", "samd-decoupage.fr", "samd-emboutissage.fr", "samd-decoupe.fr"],
    128: ["batisud.org", "batisud-metallerie.fr", "batisudmetallerie.fr"],
    129: ["sud-metallerie.fr", "sudmetallerie.fr", "sud-metallerie.com"],
    130: ["lg-metallerie.fr", "lgmetallerie.fr", "lg-metallerie.com"],
    131: ["gb-metallerie.fr", "gbmetallerie.fr", "gb-metallerie.com"],
    132: ["torras.fr", "torras-metallerie.fr", "metallerie-torras.fr", "torrasmetallerie.fr"],
    133: ["metallerie-francilienne.fr", "mf-metallerie.fr", "metalleriefrancilienne.fr"],
    135: ["gatsbysoudure.com", "gatsby-soudure.fr", "gatsbysoudure.fr"],
    136: ["es-soudure.fr", "essoudure.fr", "es-soudure.com"],
    137: ["soudecoup.fr", "soudecoup.com", "soudecoup-materiel.fr"],
    138: ["sud-soudure.fr", "sudsoudure.fr", "sud-soudure.com"],
    139: ["cst-petiville.fr", "cst76.fr", "chaudronnerie-soudure-tuyauterie.fr"],
    140: ["stb-brest.fr", "stb-soudure.fr", "soudure-tuyauterie-brestoise.fr"],
    141: ["stm-redon.fr", "stm35.fr", "stm-soudure.fr", "stm-tuyauterie.fr"],
    142: ["brivet.fr", "brivet-mecano-soudure.fr", "brivetmecanosoudure.fr", "brivet-soudure.fr"],
    143: ["tsc-chauffage.fr", "tsc94.fr", "tsc-tuyauterie.fr", "tuyauterie-soudure-chauffage.fr"],
    144: ["atlantiquetoleriesoudure.fr", "atlantique-tolerie-soudure.fr", "ats-saint-nazaire.fr"],
    145: ["msa-aron.fr", "mecano-soudure-aron.fr", "msa58.fr", "msa-mecano-soudure.fr"],
    146: ["msi-thaon.fr", "msi-industrie.fr", "msi-vosges.fr", "maintenance-soudure-industrielle.fr"],
    148: ["tolerie-industrielle.fr", "tolerie-industrielle.com"],
}

KEYS = {
    110: ["nde", "normandie", "decoupage", "emboutissage", "crulai"],
    111: ["sdeb", "bourbonnais"],
    114: ["jelza"],
    116: ["atec", "cavignac", "emboutissage"],
    118: ["smg", "decoupage", "confrere"],
    120: ["talbot", "tde", "mer"],
    121: ["ouest emboutissage", "sud ouest emboutissage", "emboutissage"],
    122: ["normande", "londinieres", "decoupage"],
    123: ["sare", "azerguoise", "repoussage", "grandris"],
    124: ["uma", "neuilly", "decoupage"],
    125: ["samd", "collegien", "decoupage", "applications mecaniques"],
    128: ["batisud", "septemes"],
    129: ["sud metallerie", "dordives", "metallerie"],
    130: ["lg metallerie", "lorient", "metallerie"],
    131: ["gb metallerie", "gimont"],
    132: ["torras", "metallerie"],
    133: ["francilienne", "rosny", "metallerie"],
    135: ["gatsby", "soudure"],
    136: ["es soudure", "soudure"],
    137: ["soudecoup", "soudure", "prov"],
    138: ["sud soudure", "saint-joseph"],
    139: ["cst", "petiville", "chaudronnerie", "tuyauterie"],
    140: ["stb", "brest", "soudure"],
    141: ["stm", "redon", "soudure", "tuyauterie"],
    142: ["brivet", "pontchateau", "soudure"],
    143: ["tsc", "villecresnes", "tuyauterie", "chauffage"],
    144: ["ats", "atlantique", "saint-nazaire", "tolerie"],
    145: ["msa", "aron", "mecano soudure"],
    146: ["msi", "thaon", "soudure industrielle"],
    148: ["tolerie industrielle", "mazieres", "tolerie"],
}

def fetch(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(150000).decode("utf-8", "ignore"), r.geturl()
    except Exception:
        return None, None

def analyser_html(html):
    low = html.lower()
    out = {"titre": "", "copyright": [], "cms": [], "emails": [], "tech": []}
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if m:
        out["titre"] = re.sub(r"\s+", " ", m.group(1)).strip()[:120]
    for cm in re.finditer(r"(?:©|&copy;|copyright)\s*[^\d]{0,20}(\d{4})", html, re.I):
        out["copyright"].append(cm.group(1))
    for pat, tag in [(r"wp-content", "WordPress"), (r"joomla", "Joomla"), (r"spip", "SPIP"),
                     (r"prestashop", "PrestaShop"), (r"mobirise", "Mobirise"), (r"jimdo", "Jimdo"),
                     (r"wix\.com", "Wix"), (r"e-monsite", "E-monsite"), (r"1and1", "1and1"),
                     (r"sitew\.", "siteW"), (r"o2switch", "O2switch"), (r"webself", "Webself")]:
        if re.search(pat, low):
            out["cms"].append(tag)
    if "<table" in low:
        out["tech"].append("tables HTML")
    if ".swf" in low:
        out["tech"].append("Flash")
    if "<frameset" in low or "<frame " in low:
        out["tech"].append("frames")
    if "name=\"viewport\"" not in low and "name='viewport'" not in low:
        out["tech"].append("pas_de_viewport_mobile")
    mg = re.search(r"<meta[^>]+name=[\"']generator[\"'][^>]+content=[\"']([^\"']+)[\"']", html, re.I)
    if mg:
        out["tech"].append("generator: " + mg.group(1)[:40])
    for e in set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html.lower())):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".js",
                                ".css", ".svg", "schema.org", "w3.org", "alpinejs", "polyfill",
                                "jquery", "sentry.io", "email@domain", "@2x")):
            continue
        out["emails"].append(e)
    return out

def check_dom(dom):
    for proto in ("https", "http"):
        for host in (dom, "www." + dom):
            html, final = fetch(proto + "://" + host)
            if html is None:
                continue
            low = html.lower()
            if any(p in low for p in ("buy this domain", "domain is for sale", "parked free", "en vente",
                                      "dovendi")):
                continue
            text = re.sub(r"<[^>]+>", " ", html).lower()
            if "<title" in low and len(text.strip()) > 40:
                return html, final
    return None, None

def match_ent(html, keys):
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).lower()
    hits = [k for k in keys if k in text]
    return len(hits) > 0, hits

out = {}
try:
    out = json.load(open(BASE + r"\_lot11_verif_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

for i, doms in CAND.items():
    if str(i) in out and out[str(i)].get("verifie") and out[str(i)]["verifie"].get("match"):
        continue
    for dom in doms:
        html, final = check_dom(dom)
        if html is None:
            continue
        info = analyser_html(html)
        ok, hits = match_ent(html, KEYS[i])
        out[str(i)] = {"verifie": {"url": final, "match": ok, "kw": hits, **info}}
        print(i, "|", dom, "->", final, "| match:", ok, hits, "|", info["titre"][:40],
              "| ©", info["copyright"], info["cms"], info["tech"], "|", info["emails"][:3], flush=True)
        json.dump(out, open(BASE + r"\_lot11_verif_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if ok:
            break
    if str(i) not in out:
        out[str(i)] = {"verifie": None}
        json.dump(out, open(BASE + r"\_lot11_verif_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TERMINE", flush=True)
