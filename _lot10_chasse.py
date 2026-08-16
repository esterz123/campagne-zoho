#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot10 : chasse domaines + analyse HTML (parallele). Usage: python _lot10_chasse.py START END"""
import json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

STOP = ("societe", "sa", "sarl", "sas", "eurl", "ets", "les", "la", "le", "des", "du", "de", "d", "l", "st", "ste")

with open(BASE + r"\candidats_bruts.json", encoding="utf-8") as f:
    bruts = json.load(f)

def gen_domains(nom):
    base = re.sub(r"\(.*?\)", "", nom).strip()
    mots = [w for w in re.findall(r"[a-zA-Z0-9]+", base.lower()) if len(w) >= 3 and w not in STOP and not w.isdigit()]
    acro = None
    m = re.search(r"\(([^)]+)\)", nom)
    if m:
        acro = m.group(1).strip().lower()
    slugs = set()
    if acro and 2 <= len(acro) <= 8 and acro.isalpha():
        slugs.add(acro)
    if mots:
        slugs.add("-".join(mots))
        slugs.add("".join(mots))
        slugs.add(mots[0])
        if len(mots) >= 2:
            slugs.add(mots[0] + "-" + mots[1])
    out = set()
    for s in slugs:
        if len(s) < 3:
            continue
        for ext in (".fr", ".com"):
            out.add(s + ext)
    return sorted(out)[:12]

def fetch(url, timeout=6):
    try:
        req = urllib.request.Request(url, headers=UA, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(120000).decode("utf-8", "ignore"), r.geturl()
    except Exception:
        return None, None

def check_one(d):
    for proto in ("https", "http"):
        for host in (d, "www." + d):
            html, final = fetch(proto + "://" + host)
            if html is None:
                continue
            low = html.lower()
            if any(p in low for p in ("buy this domain", "domain is for sale", "parked free")):
                continue
            text = re.sub(r"<[^>]+>", " ", html)
            if "<title" in low and len(text.strip()) > 60:
                return html, final
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
                     (r"drupal", "Drupal"), (r"spip", "SPIP"), (r"prestashop", "PrestaShop"),
                     (r"mobirise", "Mobirise"), (r"jimdo", "Jimdo"), (r"wix\.com", "Wix"),
                     (r"e-monsite", "E-monsite"), (r"1and1", "1and1")]:
        if re.search(pat, low):
            out["cms"].append(tag)
    if "<table" in low:
        out["tech"].append("tables HTML")
    if ".swf" in low:
        out["tech"].append("Flash")
    if "<frameset" in low or "<frame " in low:
        out["tech"].append("frames")
    for e in set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html.lower())):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", "schema.org", "w3.org")):
            continue
        out["emails"].append(e)
    return out

def traiter(i):
    c = bruts[i]
    doms = gen_domains(c["nom"])
    found = None
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(check_one, d): d for d in doms}
        for f in as_completed(futs):
            html, final = f.result()
            if html is not None:
                info = analyser_html(html)
                found = {"domaine_test": futs[f], "url": final, **info}
                for fut in futs:
                    fut.cancel()
                break
    return i, {"nom": c["nom"], "ville": c["ville"], "siren": c["siren"],
               "domaines_testes": doms, "trouve": found}

if __name__ == "__main__":
    start, end = int(sys.argv[1]), int(sys.argv[2])
    out = {}
    try:
        out = json.load(open(BASE + r"\_lot10_domaines_tmp.json", encoding="utf-8"))
    except Exception:
        out = {}
    for i in range(start, min(end, 110)):
        if str(i) in out and out[str(i)].get("trouve"):
            continue
        ii, r = traiter(i)
        out[str(ii)] = r
        f = r.get("trouve")
        if f:
            print(ii, "|", r["nom"][:30], "->", f["url"].replace("https://", "").replace("http://", ""),
                  "|", f["titre"][:45], "| ©", f["copyright"], f["cms"], f["tech"], "|", f["emails"][:2], flush=True)
        else:
            print(ii, "|", r["nom"][:30], "-> RIEN", flush=True)
        json.dump(out, open(BASE + r"\_lot10_domaines_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("TERMINE", start, end, flush=True)
