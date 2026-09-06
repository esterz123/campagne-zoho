#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHASSEUR DE PROSPECTS — alimente la campagne en nouveaux prospects qualifies.
Tourne dans GitHub Actions chaque jour (PC eteint ou pas).

Pipeline :
  1. API recherche-entreprises.api.gouv.fr (officielle, gratuite, sans cle)
     -> candidats PME industrielles (NAF cible, 10-249 salaries)
  2. Recherche du site web (DuckDuckGo HTML, filtre anti-annuaires)
  3. Analyse heuristique du site (WordPress/jQuery/copyright/SSL/mobile)
  4. Extraction de l'email de contact (contact / mentions-legales / mailto)
  5. Ecriture dans nouveau_prospects.json — Hermes redige ensuite l'email perso

Sortie : nouveau_prospects.json (liste de fiches, jamais envoye directement).
"""
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# Domaines d'annuaires a ne JAMAIS considerer comme site officiel
ANNUAIRES = ("cylex", "kompass", "pagesjaunes", "societe.com", "verif.com",
             "infogreffe", "pappers", "annuaire-entreprises", "europages",
             "yellowpages", "sous-traiter", "telesurveillance", "lefigaro",
             "linternaute", "franceinfo", "123sejours", "hotfrog", "buzzfile",
             "opendi", "agoravox", "net1901", "net1901.org", "association", "apel", "cdn")

# (mot-cle recherche, code NAF) — 2 canaux :
#   CANAL INDUSTRIE : mecanique/usinage/plasturgie/moules (existant, deja en prod)
#   CANAL TECH/STARTUP : edition logicielle, programmation, web, e-commerce, design
#     -> la zone de confort de Mahdi (logos startup / branding SaaS)
CIBLES = [
    # --- Canal Industrie ---
    ("usinage", "2562B"), ("mecanique", "2562A"), ("fraisage", "2562B"),
    ("plasturgie", "2229A"), ("injection plastique", "2229B"),
    ("moules injection", "2573A"), ("outillage", "2573B"), ("decoupage", "2550A"),
    # --- Canal Tech / SaaS / Startup (point fort Mahdi) ---
    ("edition logiciels", "5829C"), ("developpement logiciel", "6201Z"),
    ("conseil informatique", "6202A"), ("portails web", "6312Z"),
    ("e-commerce", "4791B"), ("agence web", "7410Z"),
    ("design graphique", "7410Z"), ("creation websites", "6312Z"),
    ("solutions SaaS", "6201Z"), ("applications mobiles", "6201Z"),
]

# Tranches INSEE : 11=10-19, 12=20-49, 21=50-99, 22=100-199, 31=200-249
EFFECTIFS_OK = ("11", "12", "21", "22", "31")

MAX_SITES = 8          # sites analyses par jour (quotas et courtoisie)
FETCH_TIMEOUT = 15
SCORE_MIN = 2          # seuil de vetuste (2 au lieu de 3 : on garde + de cibles)


def fetch(url, tries=2):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.8",
        "Accept": "text/html,application/xhtml+xml"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception:
            if i == tries - 1:
                return ""
            time.sleep(2)
    return ""


def api_candidats():
    """Candidats depuis l'API officielle. Retourne liste de dicts."""
    out, deja = [], set()
    for mot, naf in CIBLES:
        q = urllib.parse.urlencode({"q": mot, "code_naf": naf, "per_page": 5})
        try:
            j = json.loads(fetch("https://recherche-entreprises.api.gouv.fr/search?%s" % q))
        except Exception:
            continue
        for r in j.get("results", []):
            siren = r.get("siren")
            if not siren or siren in deja:
                continue
            if r.get("etat_administratif") != "A":
                continue
            if r.get("categorie_entreprise") not in ("PME", "ETI"):
                continue
            if r.get("tranche_effectif_salarie") not in EFFECTIFS_OK:
                continue
            deja.add(siren)
            siege = r.get("siege", {})
            nom = r.get("nom_complet", "").title()
            dirs = ["%s %s (%s)" % (d.get("prenoms", "").title(), re.sub(r"\(.*?\)", "", d.get("nom", "")).strip().title(), d.get("qualite", ""))
                    for d in r.get("dirigeants", [])[:2]]
            out.append({
                "nom": nom, "siren": siren, "naf": r.get("activite_principale", ""),
                "ville": siege.get("libelle_commune", ""), "region": siege.get("region", ""),
                "effectif": r.get("tranche_effectif_salarie", ""),
                "dirigeants": dirs, "date_creation": r.get("date_creation", "")})
        time.sleep(1)
    return out


def _brave_sites(nom, ville):
    """Sites via Brave Search (marche, teste en direct 18/08) - filtre anti-annuaires."""
    q = '"%s" %s' % (nom, ville)
    NOYAUX = ANNUAIRES + ("usinenouvelle", "rubypayeur", "mappy", "118712", "lagazettefrance",
                          "xerfi", "zoominfo", "crunchbase", "chimiefrance", "koufra",
                          "prenezplace", "everand", "hal.science", "linkedin", "facebook",
                          "wikipedia", "google", "bing", "brave", "youtube", "pinterest")
    try:
        out = fetch("https://search.brave.com/search?q=" + urllib.parse.quote(q))
    except Exception:
        return []
    hits = []
    for l in re.findall(r'(https?://[^"<> ]+)', out):
        l = l.rstrip(".,);]")
        dom = l.lower()
        if any(x in dom for x in NOYAUX):
            continue
        m = re.match(r'(https?://(?:www\.)?([^/]+))', l)
        if m:
            netloc = m.group(2).lower()
            if netloc not in ("", "www", "web", "home", "index") and "." in netloc and m.group(1) not in hits:
                hits.append(m.group(1))
        if len(hits) >= 4:
            break
    return hits


def find_site(nom, ville):
    """Site web via Brave (primaire), secours DuckDuckGo puis Bing. Filtre anti-annuaires."""
    q = '"%s" %s' % (nom, ville)
    # 0. Brave d'abord (retrouve les vrais sites que DDG/Bing ratent - fix 18/08)
    for u in _brave_sites(nom, ville):
        netloc = (urllib.parse.urlsplit(u).netloc or "").lower().replace("www.", "")
        if netloc and not any(a in netloc for a in ANNUAIRES) and "." in netloc:
            return netloc
        time.sleep(0.3)
    for engine in ("ddg", "bing"):
        if engine == "ddg":
            url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q)
            hits = re.findall(r'uddg=([^&"]+)', fetch(url))[:8]
        else:
            url = "https://www.bing.com/search?q=" + urllib.parse.quote(q)
            hits = re.findall(r'<h2><a[^>]+href="([^"]+)"', fetch(url))[:12]
        for m in hits:
            try:
                u = urllib.parse.unquote(m)
            except Exception:
                continue
            netloc = (urllib.parse.urlsplit(u).netloc or "").lower().replace("www.", "")
            if netloc and not any(a in netloc for a in ANNUAIRES) and "." in netloc:
                return netloc
        time.sleep(1)
    # Fallback : domaine devine depuis le nom propre (DELTA USINAGE -> delta-usinage.fr)
    base = re.sub(r"^(sarl|sa|sas|eurl|eu|ets|ets\.?|les|la|le|group|groupe)\s+", "",
                  nom.lower(), flags=re.I)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    if base:
        for tld in (".fr", ".com", ".eu"):
            candidat = base + tld
            if fetch("https://www." + candidat):
                return candidat
    return ""


def analyze(html):
    """Constats de vetuste. Retourne (constats, score)."""
    c, score = [], 0
    low = html.lower()
    m = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', low)
    if m:
        gen = m.group(1)
        if "wordpress" in gen:
            v = re.search(r"wordpress\s*([\d.]+)", gen)
            ver = v.group(1) if v else "?"
            c.append("WordPress %s" % ver)
            try:
                old_wp = v and float(ver.split(".")[0]) < 6
            except ValueError:
                old_wp = False
            score += 2 if old_wp else 1
        elif "joomla" in gen or "drupal" in gen:
            c.append("CMS %s" % gen.strip())
            score += 1
    jq = re.search(r"jquery[-/]([\d.]+)", low)
    if jq:
        ver = jq.group(1)
        try:
            if float(ver[:3]) < 3:
                c.append("jQuery %s (avant 2016)" % ver); score += 2
        except ValueError:
            pass
    if '<meta name="viewport"' not in low:
        c.append("Pas de vue mobile (viewport)"); score += 2
    cop = re.search(r"(?:&copy;|©|copyright)\s*(\d{4})", low, re.I)
    if cop:
        an = int(cop.group(1))
        if an < date.today().year - 1:
            c.append("Copyright %d" % an); score += 1
    if not low.startswith("https"):
        c.append("Pas de certificat SSL"); score += 1
    if len(html) > 700000:
        c.append("Page lourde (%d Ko)" % (len(html) // 1024)); score += 1
    if not c:
        c.append("Aucun constat majeur")
    return c, score


def find_email(netloc):
    """Email de contact depuis home + /contact + /mentions-legales.
    FIX 17/08 : exclut les extensions de fichiers (JS, CSS, JSON, TS...) qui
    étaient capturées comme de faux emails (ex: alpinejs@3.10.4.js)."""
    emails = set()
    pages = ["https://www.%s/" % netloc, "https://%s/" % netloc,
             "https://www.%s/contact" % netloc, "https://www.%s/contactez-nous" % netloc,
             "https://www.%s/nous-contacter" % netloc,
             "https://www.%s/mentions-legales" % netloc, "https://www.%s/a-propos" % netloc]

    # Extensions de fichiers = JAMAIS un email
    EXT_FICHIER = (".js", ".css", ".json", ".ts", ".tsx", ".jsx", ".map", ".min.js",
                   ".min.css", ".html", ".htm", ".txt", ".xml", ".csv", ".pdf",
                   ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".woff",
                   ".woff2", ".ttf", ".eot", ".mp4", ".webm", ".mp3", ".zip", ".gz", ".tar")
    # Domaines techniques / non-email (jamais un vrai destinataire)
    TECH_DOM = ("example", "wixpress", "sentry", "godaddy", "schema.org", "w3.org",
                "noreply", "no-reply", "donotreply", "privacy", "legal", "abuse",
                "sentry.io", "googleusercontent", "gravatar", "facebook", "twitter",
                "linkedin", "instagram", "youtube", "cloudflare", "wix.com",
                "webflow", "squarespace", "wordpress", "github", "unbounce")
    # TLD invalides (fins de fichier sans vraie extension)
    FAUX_TLD = (".js", ".css", ".json", ".ts", ".py", ".php", ".asp", ".yml", ".yaml")

    site_dom = netloc.lower()
    for p in pages:
        html = fetch(p)
        if not html:
            continue
        for m in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z0-9]{2,}", html):
            e = m.lower().strip(".")
            # extensions de fichier -> jamais un email
            if any(e.endswith(ext) for ext in EXT_FICHIER):
                continue
            if any(e.endswith(t) for t in FAUX_TLD):
                continue
            # domaine technique -> jamais
            if any(x in e for x in TECH_DOM):
                continue
            dom = e.split("@")[-1]
            # STRICT : domaine email == domaine du site (preuve d'officialite)
            if dom != site_dom and not dom.endswith("." + site_dom):
                continue
            if e.count("@") != 1 or len(e) > 50:
                continue
            local = e.split("@")[0]
            if local and local[0].isdigit():
                continue
            emails.add(e)
    # uniquement les emails du domaine (plus de fallback hors-domaine dangereux)
    return sorted(emails)


def main():
    candidats = api_candidats()
    print("Candidats API : %d" % len(candidats))
    fiches, traites, sites_trouves = [], 0, 0
    for cand in candidats:
        if traites >= MAX_SITES:
            break
        site = find_site(cand["nom"], cand["ville"])
        time.sleep(1)
        if not site:
            continue
        sites_trouves += 1
        html = fetch("https://www.%s/" % site) or fetch("http://%s/" % site)
        traites += 1
        if not html:
            continue
        constats, score = analyze(html)
        if score < SCORE_MIN:
            continue
        emails = find_email(site)
        fiche = dict(cand)
        fiche.update({"site": site, "email": emails[:2], "constats": constats,
                      "score": score, "date": date.today().isoformat()})
        fiches.append(fiche)
        print("FICHE  %-35s %-20s score=%d email=%s constats=%s"
              % (cand["nom"][:35], site, score, emails[:1], constats))

    print("Rapport : %d candidats => %d sites => %d fiches > seuil %d"
          % (len(candidats), sites_trouves, len(fiches), SCORE_MIN))
    try:
        with open("nouveau_prospects.json", encoding="utf-8") as f:
            existant = json.load(f) or []
    except Exception:
        existant = []
    # Dedup : ne jamais re-ajouter un SIREN deja present dans le fichier (vecu 06/09 :
    # 2 entreprises dupliquees 17x chacune par des runs repetes)
    deja_siren = {str(f0.get("siren")) for f0 in existant if f0.get("siren")}
    nouvelles = [f for f in fiches if str(f.get("siren")) not in deja_siren]
    existant.extend(nouvelles)
    with open("nouveau_prospects.json", "w", encoding="utf-8") as f:
        json.dump(existant, f, ensure_ascii=False, indent=1)
    print("Total nouvelles fiches ce jour : %d (accumulees : %d)"
          % (len(fiches), len(existant)))


if __name__ == "__main__":
    main()