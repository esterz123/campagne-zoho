#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHASSEUR DE DIRIGEANTS V2 (parallele) — trouve les emails directs des proprietaires.
- Parallelise le scan (ThreadPoolExecutor) => ~10x plus rapide
- Feedback en temps reel (flush)
- Priorise l'email qui matche le nom du dirigeant
- Verifie le domaine MX (anti-bounce)
Usage : python3 chasseur_dirigeants.py [--max N] [--start K]
"""
import json, re, time, sys
import urllib.parse, urllib.request
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

ANNUAIRES = ("cylex","kompass","pagesjaunes","societe.com","verif.com","infogreffe",
             "pappers","annuaire-entreprises","europages","yellowpages","sous-traiter",
             "telesurveillance","lefigaro","linternaute","franceinfo","123sejours",
             "hotfrog","buzzfile","opendi","agoravox","net1901","association","apel","cdn")

FETCH_TIMEOUT = 8
MAX_WORKERS = 1
SEARCH_DELAY = 4.0   # delai entre requetes SearXNG (evite le rate-limit Google)

def log(s):
    print(s, flush=True)

def fetch(url, tries=2):
    req = urllib.request.Request(url, headers={"User-Agent":UA,"Accept-Language":"fr-FR,fr;q=0.8","Accept":"text/html"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
                return r.read().decode("utf-8","ignore")
        except Exception:
            if i == tries-1:
                return ""
            time.sleep(1)
    return ""

SEARX = "http://127.0.0.1:10577/search"

def search_sites(q):
    """Recherche de site via SearXNG local. Moteur google d'abord (le plus precis),
    fallback bing si google est rate-limite."""
    time.sleep(SEARCH_DELAY)
    for engines in ("google", "bing"):
        url = SEARX + "?" + urllib.parse.urlencode({
            "q": q, "format": "json", "language": "fr-FR", "safesearch": 0, "pageno": 1,
            "engines": engines})
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode("utf-8", "ignore"))
            res = [x.get("url", "") for x in j.get("results", [])]
            if res:
                return res
        except Exception:
            pass
        time.sleep(SEARCH_DELAY)
    return []

SOCIAL = ("linkedin", "facebook", "instagram", "twitter", "x.com", "youtube",
          "pinterest", "tiktok", "whatsapp", "google.com", "flickr", "vimeo")

def name_keywords(nom):
    """Mots significatifs du nom d'entreprise pour valider le domaine."""
    stop = ("societe","sa","sarl","sas","eurl","et","les","la","le","des","du","de",
            "l'","st","ste","ets","groupe","holding","fr","com","ltd","inc","srl","snc")
    mots = set()
    for part in re.split(r"[^a-z0-9']+", nom.lower()):
        part = part.strip("'").replace("'","")
        if len(part) >= 4 and part not in stop and part.isalpha():
            mots.add(part)
    return mots

def find_site(nom, ville):
    q = '"%s" %s' % (nom, ville)
    kws = name_keywords(nom)
    sites = search_sites(q)   # UNE seule requete
    # 1er passage : domaine qui ressemble au nom ou acronyme
    for u in sites:
        try:
            netloc = (urllib.parse.urlsplit(u).netloc or "").lower().replace("www.", "")
        except Exception:
            continue
        if not netloc or "." not in netloc:
            continue
        if any(a in netloc for a in ANNUAIRES) or any(s in netloc for s in SOCIAL):
            continue
        if kws and any(kw in netloc for kw in kws):
            return netloc
        initials = "".join(w[0] for w in re.split(r"[^a-zA-Z]+", nom) if w and w[0].isalpha()).lower()
        if len(initials) >= 3 and initials[:3] in netloc.replace("-","").replace("_",""):
            return netloc
    # fallback : deviner le domaine depuis le nom (nom.fr, nom-com.fr...)
    # efficace pour les PME dont le site suit leur raison sociale
    base = re.sub(r"^(sarl|sa|sas|eurl|eu|ets|ets\.?|les|la|le|group|groupe)\s+", "",
                  nom.lower(), flags=re.I)
    base = re.sub(r"\(.*?\)", "", base)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    if len(base) >= 5:
        for tld in (".fr", ".com", ".eu"):
            cand = base + tld
            # verifie que le domaine existe (a un site qui repond)
            if fetch("https://www." + cand) or fetch("https://" + cand):
                return cand
    return ""

def get_dirigeants(siren):
    try:
        j = json.loads(fetch("https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=1" % siren))
    except Exception:
        return []
    for r in j.get("results", []):
        if r.get("siren") == siren:
            out = []
            for d in r.get("dirigeants", [])[:4]:
                nom = (d.get("prenoms","") + " " + re.sub(r"\(.*?\)","",d.get("nom","")).strip()).strip()
                if nom.strip():
                    out.append({"nom": nom, "qualite": d.get("qualite","")})
            return out
    return []

def emails_in_html(html):
    emails = set()
    for m in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html.lower()):
        e = m.strip(".")
        if any(x in e for x in ("example","wixpress","sentry","godaddy",".png",".jpg",".jpeg",
                                ".gif",".webp",".svg","schema.org","w3.org","noreply","no-reply",
                                "donotreply","privacy","legal","abuse","sentry.io",
                                "googleusercontent",".js",".css")):
            continue
        if "@" in e and "." in e.split("@")[1]:
            emails.add(e)
    return emails

def find_emails_parallel(netloc):
    """Scanne les pages cles en parallele."""
    paths = ["", "/contact","/contacts","/contactez-nous","/nous-contacter","/mentions-legales",
             "/equipe","/qui-sommes-nous","/a-propos","/direction"]
    base_urls = []
    for p in paths:
        base_urls.append("https://www." + netloc + p)
        base_urls.append("https://" + netloc + p)
    all_emails = set()
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch, u): u for u in base_urls}
        for f in as_completed(futs):
            try:
                h = f.result()
            except Exception:
                continue
            if h:
                all_emails |= emails_in_html(h)
    return all_emails

def score_email_for_director(email, dirigeants):
    if not dirigeants:
        return 0
    local = email.split("@")[0].replace("."," ").replace("-"," ").replace("_"," ").lower()
    best = 0
    for d in dirigeants:
        full = d.get("nom","").lower()
        parts = [p for p in full.split() if len(p) > 3]
        for part in parts:
            if part in local:
                best = max(best, 4)
        if full:
            prenom = full.split()[0]
            if len(prenom) > 2 and prenom in local:
                best = max(best, 3)
    return best

def guess_director_emails(netloc, dirigeants):
    """Genere les emails directs probables des dirigeants (prenom.nom@domaine).
    Retourne liste de (email, confiance). A verifier par MX avant envoi."""
    domain = netloc
    if not domain.endswith((".fr",".com",".eu",".net",".org")):
        # garde le domaine nu et ajoute .fr/.com
        cands = set()
    out = []
    for d in dirigeants:
        full = (d.get("nom") or "").strip()
        if not full:
            continue
        parts = full.split()
        if len(parts) < 2:
            continue
        prenom = re.sub(r"[^a-zA-Z]", "", parts[0]).lower()
        # nom de famille = toutes les parties apres le prenom (gere les noms composes)
        nom = "".join(re.sub(r"[^a-zA-Z]", "", p).lower() for p in parts[1:])
        if not prenom or not nom:
            continue
        for dom in [domain]:
            for fmt in (prenom + "." + nom, prenom + nom, nom + "." + prenom,
                        prenom[0] + "." + nom, prenom[0] + nom):
                out.append("%s@%s" % (fmt, dom))
    # dedoublonne en gardant l'ordre
    seen, uniq = set(), []
    for e in out:
        if e not in seen:
            seen.add(e); uniq.append(e)
    return uniq

def mx_valid(email):
    domain = email.split("@")[1]
    try:
        import subprocess
        p = subprocess.run(["python3","email_tester.py","--check",domain],
                           cwd=BASE, capture_output=True, text=True, timeout=60)
        return "DOMAINE_VALIDE" in p.stdout
    except Exception:
        return True

def process_candidate(c):
    nom = c.get("nom",""); ville = c.get("ville",""); siren = c.get("siren","")
    if not nom or not siren:
        return None
    site = find_site(nom, ville)
    if not site:
        return {"nom":nom,"ville":ville,"siren":siren,"site":"","email":"","dirigeants":[],"match":"AUCUN_SITE","date":date.today().isoformat()}
    dirs = get_dirigeants(siren)
    emails = find_emails_parallel(site)
    # emails directs devines pour les dirigeants (a verifier MX)
    guessed = guess_director_emails(site, dirs)
    # email reel trouve sur le site qui matche un dirigeant, sinon generique
    if dirs and emails:
        best = sorted(emails, key=lambda e: score_email_for_director(e, dirs), reverse=True)[0]
        sc = score_email_for_director(best, dirs)
        match = "DIRIGEANT" if sc >= 3 else "GENERIQUE"
    elif emails:
        best = sorted(emails)[0]
        sc = 0
        match = "GENERIQUE"
    else:
        best = ""
        sc = 0
        match = "AUCUN"
    return {"nom":nom,"ville":ville,"siren":siren,"site":site,"email":best,
            "dirigeants":dirs,"match":match,
            "email_dirigeant_devine": guessed if dirs else [],
            "date":date.today().isoformat()}

def main():
    args = sys.argv
    max_proc = 999; start = 0
    if "--max" in args: max_proc = int(args[args.index("--max")+1])
    if "--start" in args: start = int(args[args.index("--start")+1])

    cands = json.load(open(BASE+r"\candidats_bruts.json", encoding="utf-8"))
    file_data = json.load(open(BASE+r"\campagne_data.json", encoding="utf-8"))
    already = set()
    for e in file_data:
        already.add(e.get("prospect","").lower())
        # garde aussi le domaine
        to = e.get("to","")
        if "@" in to:
            already.add(to.split("@")[1].lower())

    # exclusions pour ne pas retraiter
    todo = []
    for c in cands:
        nom = c.get("nom","")
        if not nom or nom.lower() in already:
            continue
        todo.append(c)
    todo = todo[start:start+max_proc]
    log("Total a traiter (lot %d-%d) : %d" % (start, start+len(todo), len(todo)))

    results = {}
    try:
        results = json.load(open(BASE+r"\dirigeants_email.json", encoding="utf-8"))
    except Exception:
        pass

    done = 0; found = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(process_candidate, c): c for c in todo}
        for f in as_completed(futs):
            c = futs[f]
            try:
                r = f.result()
            except Exception as ex2:
                log("  ERR %s: %s" % (c.get("nom","")[:30], str(ex2)[:60]))
                continue
            if r is None:
                continue
            done += 1
            if r.get("site"):
                found += 1
                results[r["siren"]] = r
            mark = r.get("match") or ""
            log("  [%s] %-32s %-22s %s" % (mark, r["nom"][:32], r.get("site",""), r.get("email","")))
            json.dump(results, open(BASE+r"\dirigeants_email.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

    log("Termine : %d traites, %d emails trouves (fichier dirigeants_email.json)" % (done, found))

if __name__ == "__main__":
    main()
