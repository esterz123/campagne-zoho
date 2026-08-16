#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot10 : verification domaines specifiques + match mots-cles entreprise."""
import json, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

# domaines specifiques a tester (index -> domaines)
CAND = {
    62: ["eberhard-usinage.fr", "eberhard-usinage.com"],
    63: ["ravon-usinage.fr", "ravon-usinage.com"],
    65: ["usinage-alsace.com"],
    67: ["urma-usinage.fr", "urma.fr"],
    69: ["bc-usinages.fr", "bcu.fr"],
    70: ["sauvaitre-usinage.fr", "sauvaitre-usinage.com"],
    79: ["rm-decolletage.fr", "rm-decolletage.com"],
    81: ["decolletage-jurassien.fr"],
    83: ["decolletage-elbe.fr"],
    84: ["edelweiss-decolletage.fr", "edelweiss-decolletage.com"],
    85: ["decolletage-de-reu.com", "decolletage-de-reu.fr"],
    86: ["gay-decolletage.fr", "gay-decolletage.com"],
    87: ["coulot-decolletage.fr", "coulot-decolletage.com", "exalta-group.com"],
    89: ["orne-decolletage.fr", "decolletage-orne.fr", "orne-decolletage.com"],
    90: ["anjou-decolletage.fr", "anjou-decolletage.com"],
    91: ["decolletage-morel.com", "decolletage-morel.fr"],
    92: ["drault-decolletage.com", "drault-decolletage.fr"],
    93: ["gilletsa.com", "gillet-decolletage.fr"],
    94: ["decolletage-du-berry.fr", "decolletage-berry.fr", "decolletage-du-berry.com"],
    97: ["outillage-saint-etienne.fr", "outillage-st-etienne.fr"],
    98: ["fixouti.fr", "fix-outi.fr", "fixouti.com"],
    99: ["magafor.fr", "magafor.com", "magafor-outillage.fr"],
    101: ["soib.fr", "soib.com", "outillage-industriel-batiment.fr"],
    102: ["savoie-outillage.fr", "clickoutil.fr", "clickoutil.com", "savoie-outillage-service.fr"],
    103: ["omedec.fr", "omedec.com", "outillage-mecanique-decoupage.fr"],
    104: ["begc.fr", "begc.com", "bureau-etude-outillage.fr"],
    105: ["athisienne.fr", "athisienne-mecanique.fr", "a-m-m-o.fr"],
    107: ["philippe-outillage.fr", "outillage-philippe.fr", "philippe-outillage.com"],
    109: ["outillage-progress.fr", "progress-outillage.fr", "outillage-progress.com"],
    72: ["fraisage-tp.fr", "fraisagetp.fr"],
    73: ["nord-fraisage.fr", "nordfraisage.fr"],
    74: ["afm-usinage.fr", "atelier-fraisage-mecanique.fr", "afm61.fr"],
    75: ["tfl.fr", "tournage-fraisage-lorrain.fr", "tfl-hagondange.fr"],
    76: ["sdm-decolletage.fr", "sdm-marignier.fr", "sdm-decolletage.com"],
    95: ["defi-cruejouls.fr", "houillieres-cruejouls.fr"],
}

# domaines deja trouves a verifier (index -> domaine)
VERIF = {
    61: "usinage.com", 66: "elcam-usinage.fr", 68: "usinage-dieppois.fr",
    71: "fraisageservices.fr", 77: "jcm-decolletage.fr", 78: "ouestdecolletage.com",
    80: "guillerme-decolletage.fr", 88: "amd-decolletage.com",
    96: "provence-outillage.fr", 100: "rao.fr", 106: "specialite.fr", 108: "remo-outillage.fr",
}

# mots-cles attendus par entreprise (index -> mots)
KEYS = {
    61: ["ba usinage"], 62: ["eberhard"], 63: ["ravon"], 64: ["europ"], 65: ["usinage alsace", "usinage-alsace"],
    66: ["elcam"], 67: ["urma"], 68: ["usinage dieppois"], 69: ["bc usinage", "bcu"], 70: ["sauvaitre"],
    71: ["fraisage services"], 72: ["fraisage tp", "fraisage travaux"], 73: ["nord fraisage"],
    74: ["fraisage", "afm"], 75: ["tournage fraisage", "t.f.l"], 76: ["decolletage", "sdm"],
    77: ["jcm"], 78: ["ouest decolletage", "ouest decolletage"], 79: ["rm decolletage"],
    80: ["guillerme"], 81: ["decolletage jurassien", "jurassien"], 82: ["ravinet"],
    83: ["decolletage elbe", "elbe"], 84: ["edelweiss"], 85: ["de reu", "decolletage de reu"],
    86: ["gay decolletage", "gay"], 87: ["coulot"], 88: ["amd decolletage", "amd"],
    89: ["orne decolletage", "decolletage orne"], 90: ["anjou decolletage"],
    91: ["decolletage morel", "morel"], 92: ["drault"], 93: ["gillet"],
    94: ["decolletage du berry", "berry"], 95: ["cruejouls", "defi"],
    96: ["provence outillage"], 97: ["outillage saint", "outillage st"],
    98: ["fix outi", "fixouti", "fixations outillages"], 99: ["magafor"],
    100: ["rao"], 101: ["soib"], 102: ["savoie outillage", "clickoutil"],
    103: ["omedec"], 104: ["begc"], 105: ["athisienne"],
    106: ["some", "specialite outillage"], 107: ["philippe outillage"],
    108: ["remo outillage", "remo"], 109: ["outillage progress"],
}

def fetch(url, timeout=7):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(120000).decode("utf-8", "ignore"), r.geturl()
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
    for pat, tag in [(r"wp-content", "WordPress"), (r"joomla", "Joomla"), (r"typo3", "Typo3"),
                     (r"drupal", "Drupal"), (r"prestashop", "PrestaShop"), (r"mobirise", "Mobirise"),
                     (r"jimdo", "Jimdo"), (r"wix\.com", "Wix"), (r"e-monsite", "E-monsite"),
                     (r"sitew\.", "siteW"), (r"1and1", "1and1"), (r"websco", "Websco"),
                     (r"creation-site", "cms fr"), (r"o2switch", "O2switch")]:
        if re.search(pat, low):
            out["cms"].append(tag)
    if "<table" in low:
        out["tech"].append("tables HTML")
    if ".swf" in low:
        out["tech"].append("Flash")
    if "<frameset" in low or "<frame " in low:
        out["tech"].append("frames")
    for e in set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html.lower())):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".js", "schema.org", "w3.org", "alpinejs")):
            continue
        out["emails"].append(e)
    # version wordpress / generator
    mg = re.search(r"<meta[^>]+name=[\"']generator[\"'][^>]+content=[\"']([^\"']+)[\"']", html, re.I)
    if mg:
        out["tech"].append("generator: " + mg.group(1)[:40])
    return out

def check_dom(dom):
    for proto in ("https", "http"):
        for host in (dom, "www." + dom):
            html, final = fetch(proto + "://" + host)
            if html is None:
                continue
            low = html.lower()
            if any(p in low for p in ("buy this domain", "domain is for sale", "parked free", "en vente")):
                continue
            text = re.sub(r"<[^>]+>", " ", html).lower()
            if "<title" in low and len(text.strip()) > 60:
                return html, final
    return None, None

def match_ent(html, keys):
    text = re.sub(r"<[^>]+>", " ", html).lower()
    t = re.sub(r"\s+", " ", text)
    for k in keys:
        if k in t:
            return True, k
    return False, ""

out = {}
try:
    out = json.load(open(BASE + r"\_lot10_verif_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

# 1) verification des domaines deja trouves
for i, dom in VERIF.items():
    if str(i) in out:
        continue
    html, final = check_dom(dom)
    if html is None:
        out[str(i)] = {"verifie": None}
        print(i, "|", dom, "-> DOWN", flush=True)
    else:
        info = analyser_html(html)
        ok, kw = match_ent(html, KEYS[i])
        out[str(i)] = {"verifie": {"url": final, "match": ok, "kw": kw, **info}}
        print(i, "|", dom, "->", final, "| match:", ok, "(", kw, ")", "|", info["titre"][:45], "|", info["copyright"], info["cms"], info["tech"], "|", info["emails"][:2], flush=True)
    json.dump(out, open(BASE + r"\_lot10_verif_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 2) domaines supplementaires
for i, doms in CAND.items():
    if str(i) in out and out[str(i)].get("verifie") is not None and out[str(i)]["verifie"].get("match"):
        continue
    for dom in doms:
        html, final = check_dom(dom)
        if html is None:
            continue
        info = analyser_html(html)
        ok, kw = match_ent(html, KEYS[i])
        out[str(i)] = {"verifie": {"url": final, "match": ok, "kw": kw, **info}}
        print(i, "|", dom, "->", final, "| match:", ok, "(", kw, ")", "|", info["titre"][:45], "|", info["copyright"], info["cms"], info["tech"], "|", info["emails"][:2], flush=True)
        json.dump(out, open(BASE + r"\_lot10_verif_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if ok:
            break
print("TERMINE", flush=True)
