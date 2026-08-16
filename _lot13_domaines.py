#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : sonde domaines probables pour la plage 110-149 + validation par mots-cles."""
import json, re, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

# index -> (mots-cles attendus dans la page, domaines probables)
PROBES = {
 110: (["decoupage", "emboutissage", "crulai", "27110", "crulay"], ["ndemboutissage.fr", "normandie-decoupage-emboutissage.fr", "normandiedecoupage.fr", "nde-france.fr", "decoupage-emboutissage-normandie.fr", "societe-normande-decoupage.fr"]),
 111: (["sdeb", "cusset", "03300", "emboutissage", "bourbonnais"], ["sdeb.fr", "sdeb.com", "decoupage-emboutissage-bourbonnais.fr", "sdeb-emboutissage.fr"]),
 112: (["mail", "moirans", "38430", "emboutissage"], ["emboutissage-du-mail.fr", "edm-emboutissage.fr", "emboutissagedumail.fr", "groupe-edm.fr", "edm.fr"]),
 113: (["ouest", "emboutissage", "cerizay", "79140"], ["ouest-emboutissage.fr", "ouestemboutissage.fr", "emboutissage-ouest.fr"]),
 114: (["jelza", "saint-florent", "18400", "emboutissage"], ["jelza-emboutissage.fr", "jelzaemboutissage.fr", "jelza.fr", "jelza.com"]),
 116: (["atec", "cavignac", "33620", "emboutissage", "analyse"], ["groupe-atec.fr", "groupeatec.fr", "atec-emboutissage.fr", "atec-analyse.fr", "atec.fr"]),
 117: (["ernst", "niederbronn", "67110", "emboutissage", "decoupage"], ["ernst-decoupage.fr", "ernst-emboutissage.fr", "ernstdecoupage.fr", "ernstdecoupageemboutissage.fr", "ernst-emboutissage.com"]),
 118: (["smg", "decoupage", "emboutissage"], ["smg-decoupage-emboutissage.fr", "smgdecoupage.fr", "smg-emboutissage.fr", "smg-decoupage.fr"]),
 119: (["sep", "emboutissage", "barby", "73230", "precis"], ["societe-emboutissage-precis.fr", "sep-emboutissage.fr", "sepemboutissage.fr", "emboutissage-precis.fr"]),
 120: (["talbot", "decoupage", "emboutissage", "mer"], ["talbot-decoupage.fr", "talbotdecoupageemboutissage.fr", "talbot-emboutissage.fr", "tdemboutissage.fr"]),
 121: (["sud", "ouest", "emboutissage", "ussac", "19270"], ["sud-ouest-emboutissage.fr", "sudouestemboutissage.fr", "soe-emboutissage.fr"]),
 122: (["normande", "decoupage", "emboutissage", "londinieres", "27310"], ["snde.fr", "societe-normande-decoupage.fr", "societenormandededecoupage.fr", "snde-emboutissage.fr"]),
 123: (["azerguoise", "repoussage", "emboutissage", "grandris", "69690"], ["sare-emboutissage.fr", "sare69.fr", "sare-sarl-69.fr", "societe-azerguoise.fr"]),
 124: (["uma", "decoupage", "emboutissage", "tolerie", "neuilly"], ["uma-decoupage.fr", "uma-emboutissage.fr", "umatolerie.fr", "uma-tolerie.fr"]),
 125: (["samd", "decoupage", "emboutissage", "collegien", "77090"], ["samd.fr", "samd-decoupage.fr", "samdemboutissage.fr", "samd-precision.fr"]),
 126: (["lenoir", "metallerie", "villeurbanne", "69100"], ["lenoir-metallerie.fr", "metallerie-lenoir.fr", "lenoirmetallerie.fr", "lenoir-metallerie.com"]),
 127: (["oaca", "metallerie", "agnos", "64230"], ["oaca.fr", "oaca-metallerie.fr", "oacametallerie.fr"]),
 128: (["batisud", "metallerie", "septemes", "13240"], ["batisud.org", "batisud.fr", "batisud-metallerie.fr", "batisudmetallerie.fr"]),
 129: (["sud", "metallerie", "dordives", "45680"], ["sud-metallerie.fr", "sudmetallerie.fr", "sud-metallerie.com"]),
 130: (["lg", "metallerie", "lorient", "56100", "gasse"], ["lg-metallerie.fr", "lgmetallerie.fr", "lg-metallerie.com"]),
 131: (["gb", "metallerie", "gimont", "32200"], ["gb-metallerie.fr", "gbmetallerie.fr", "gb-metallerie.com"]),
 132: (["torras", "metallerie", "paris"], ["torras-metallerie.fr", "torrasmetallerie.fr", "torras-metallerie.com", "torras.fr"]),
 133: (["metallerie", "francilienne", "rosny", "93110"], ["metallerie-francilienne.fr", "metallieriefrancilienne.fr", "metallerie.com"]),
 134: (["institut", "soudure", "villepinte"], ["institut-de-soudure.com", "institutsoudure.com", "isgroupe.com", "groupe-is.com"]),
 135: (["gatsby", "soudure", "bobigny"], ["gatsby-soudure.fr", "gatsbysoudure.fr", "gatsby-soudure.com"]),
 136: (["es", "soudure", "metz"], ["es-soudure.fr", "essoudure.fr", "es-soudure.com"]),
 137: (["soudecoup", "gardanne", "13120", "soudure"], ["soudecoup.fr", "soudecoup.com", "soc-prov-materiel-soudure.fr"]),
 138: (["sud", "soudure", "saint-joseph"], ["sud-soudure.fr", "sudsoudure.fr"]),
 139: (["cst", "chaudronnerie", "petiville", "14390"], ["cst-chaudronnerie.fr", "chaudronnerie-soudure-tuyauterie.fr", "cst-soudure.fr"]),
 140: (["brestoise", "soudure", "tuyauterie", "brest"], ["soudure-tuyauterie-brestoise.fr", "stb-soudure.fr", "stbsoudure.fr"]),
 141: (["stm", "soudure", "tuyauterie", "redon", "35600"], ["stm-soudure.fr", "soudure-tuyauterie-maintenance.fr", "stm-tuyauterie.fr"]),
 142: (["brivet", "mecano", "soudure", "pontchateau"], ["brivet-mecano-soudure.fr", "brivetmecanosoudure.fr", "bms-soudure.fr"]),
 143: (["tsc", "tuyauterie", "soudure", "chauffage", "villecresnes"], ["tsc-tuyauterie.fr", "tuyauterie-soudure-chauffage.fr", "tsc-soudure.fr"]),
 144: (["atlantique", "tolerie", "soudure", "nantes"], ["atlantique-tolerie-soudure.fr", "atlantiquetoleriesoudure.fr", "ats-soudure.fr"]),
 145: (["mecano", "soudure", "aron", "saint-igny"], ["msa-mecano-soudure.fr", "mecanosoudurearon.fr", "mecano-soudure-aron.fr", "msa-soudure.fr"]),
 146: (["msi", "maintenance", "soudure", "thaon", "88110"], ["msi-maintenance-soudure.fr", "maintenance-soudure-industrielle.fr", "msi-soudure.fr"]),
 147: (["tolerie", "loire", "nantes"], ["tolerie-de-la-loire.fr", "toleriesdelaloire.fr", "toleriedelaloire.fr"]),
 148: (["tolerie", "industrielle", "mazieres", "79310"], ["tolerie-industrielle.fr", "tolerieindustrielle.fr"]),
 149: (["remond", "tolerie", "crepand", "54210"], ["tolerie-remond.com", "tolerie-remond.fr", "remond-tolerie.fr"]),
}

def probe(domain):
    for scheme in ("https", "http"):
        for host in (domain, "www." + domain):
            url = "%s://%s/" % (scheme, host)
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=6) as r:
                    body = r.read(300000).decode("utf-8", "ignore")
                    return {"url": url, "status": r.status, "final": r.geturl(), "html": body}
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303, 307, 308):
                    loc = e.headers.get("Location", "")
                    if loc and loc.startswith("http"):
                        try:
                            req2 = urllib.request.Request(loc, headers=UA)
                            with urllib.request.urlopen(req2, timeout=6) as r2:
                                body = r2.read(300000).decode("utf-8", "ignore")
                                return {"url": url, "status": r2.status, "final": loc, "html": body}
                        except Exception:
                            pass
                continue
            except Exception:
                continue
    return None

def norm(s):
    s = s.lower()
    s = s.replace("'", "")
    for a, b in [("é","e"),("è","e"),("ê","e"),("ë","e"),("à","a"),("â","a"),("î","i"),("ï","i"),("ô","o"),("û","u"),("ù","u"),("ç","c"),("-"," "),("_"," "),("."," "),(","," ")]:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()

results = {}
tasks = []
for idx, (kws, doms) in PROBES.items():
    for d in doms:
        tasks.append((idx, kws, d))

def work(t):
    idx, kws, d = t
    r = probe(d)
    if r is None:
        return (idx, d, None)
    html = r["html"].lower()
    nhtml = norm(html)
    hits = [k for k in kws if norm(k) in nhtml or k.lower() in html]
    emails = sorted(set(re.findall(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", html)))
    cp = re.findall(r"©\s*(\d{4})(?:\s*[-–—]\s*(\d{4}))?", html)
    cms = []
    if "wp-content" in html or "wordpress" in html: cms.append("WordPress")
    if "joomla" in html: cms.append("Joomla")
    if "prestashop" in html: cms.append("PrestaShop")
    if "spip" in html: cms.append("SPIP")
    if "wix.com" in html or "wixstatic" in html: cms.append("Wix")
    if "squarespace" in html: cms.append("Squarespace")
    gen = re.findall(r'<meta[^>]*generator[^>]*content=["\']([^"\']+)', html, re.I)
    tables = html.count("<table")
    viewport = '<meta name="viewport"' in html
    return (idx, d, {"status": r["status"], "final": r["final"], "keywords_hits": hits, "emails": emails,
                     "copyright": cp[:5], "cms": cms, "generator": gen[:3], "tables": tables, "viewport": viewport,
                     "title": re.findall(r"<title[^>]*>(.*?)</title>", r["html"], re.I|re.S)[:1]})

with ThreadPoolExecutor(max_workers=10) as ex:
    futs = {ex.submit(work, t): t for t in tasks}
    for f in as_completed(futs):
        idx, d, res = f.result()
        results.setdefault(idx, {})[d] = res

with open(f"{BASE}/_lot13_domaines_tmp.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

for idx in sorted(results):
    found = []
    for d, r in results[idx].items():
        if r:
            tag = "HIT" if r["keywords_hits"] else "REP"
            found.append(f"{d} [{tag} kw={r['keywords_hits'][:3]} title={r['title'][:1]}]")
    print(f"[{idx}] " + " | ".join(found) if found else f"[{idx}] aucun")
