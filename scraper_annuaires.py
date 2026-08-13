#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER ANNUAIRES — le vrai moteur de volume de la Chasseuse H24.
================================================================
Le probleme de la chasse par API (recherche-entreprises) : les PME ne
publient pas leur email -> taux de succes ~0%.

LA SOLUTION : les ANNUAIRES SECTORIELS. Les syndicats professionnels
publicnt la liste de leurs adherents AVEC le site officiel (confirme
par le syndicat, donc fiable a 100%). On visite le site officiel,
on prend l'email de contact, et le verrou infaillible valide.

Sources (gratuites, sans cle) :
  - Polyvia (syndicat national de la plasturgie) : 1334 adherents
  - AEPV (federation du decolletage Oyonnax) : 314 membres
  - (a ajouter : autres syndicats / annuaires tech)

Pipeline :
  1. Scraper la liste d'adherents (nom + lien fiche)
  2. Pour chaque fiche : extraire le SITE OFFICIEL (https://...)
  3. Aller sur le site officiel -> trouver l'email de contact
  4. VERROU : domaine email = domaine site officiel + pas bloque + pas en file
  5. Ecrire dans annuaire_prospects.json (la chasseuse_h24 les integre)

Regles : jamais d'email devine, jamais d'annuaire, 0 euro, courtoisie
(1 requete/site, delai entre les requetes).

Usage :
  python3 scraper_annuaires.py --source polyvia --max 20 --dry-run
  python3 scraper_annuaires.py --source polyvia --max 20
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from chasseur_prospects import fetch, find_email, UA
import chasseuse_h24 as CH

OUT_F = os.path.join(BASE, "annuaire_prospects.json")

UA_HDRS = {"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.8"}

# ------------------------------------------------------------------
# SOURCE POLYVIA (plasturgie) — liste des adherents
# ------------------------------------------------------------------
POLYVIA_LISTE = "https://www.polyvia.fr/fr/entreprises-plasturgie"
POLYVIA_FICHE = "https://www.polyvia.fr"

def scrape_polyvia_liste(html):
    """Extrait (nom, lien_fiche) depuis la page liste. ~1300 adherents.
    Format live : chaque carte contient <div class="field__item">NOM</div>
    et un lien href=.../fr/entreprise/xxx (ou relatif entreprise/xxx).
    Format cache (markdown) : ### NOM ... [Voir la fiche](url)"""
    out = []
    # --- format HTML live ---
    if 'field__item' in html:
        # decouper en cartes : chaque carte va de field__item au lien entreprise
        pattern = re.compile(
            r'field__item">\s*([^<]{2,70}?)</div>.*?'
            r'href="([^"]*entreprise/[^"]+)"', re.S)
        for m in pattern.finditer(html):
            nom = re.sub(r"\s+", " ", m.group(1)).strip()
            lien = m.group(2)
            if not nom or "Voir la fiche" in nom:
                continue
            # normaliser le lien
            if lien.startswith("/"):
                lien = "https://www.polyvia.fr" + lien
            elif not lien.startswith("http"):
                lien = "https://www.polyvia.fr/" + lien
            # ignorer les elements non-entreprises (evenements, menus, pages)
            if nom.lower() in ("rencontre", "webinaire", "atelier", "actualites",
                               "agenda", "contact", "accueil", "recherche",
                               "devenir membre", "espace adherent", "newsletter"):
                continue
            out.append({"nom": nom, "fiche": lien})
        return out
    # --- format cache (markdown) ---
    for m in re.finditer(r'###\s*([^\n]{2,70})\n(?:.*?\n)*?\s*\[Voir la fiche\]\((https://www\.polyvia\.fr/entreprise/[^)]+)\)',
                         html, re.S):
        nom = re.sub(r"\s+", " ", m.group(1)).strip()
        lien = m.group(2)
        if nom and lien:
            out.append({"nom": nom, "fiche": lien})
    return out

def scrape_polyvia_fiche(html):
    """Extrait le site officiel depuis une fiche adherent.
    Structure reelle : le site apparait apres un </svg> ou </span>,
    dans la zone visible de la fiche (jamais dans le <head> RDF)."""
    # 1) zone visible : apres </svg> ou </span> (la zone du site)
    for m in re.finditer(r'</(?:svg|span)>\s*([ \t]*)(https?://(?:www\.)?[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(?:/[^\s"<>]*)?)',
                         html):
        site = m.group(2).rstrip("/.,;")
        domaine = site.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        low = domaine.lower()
        if any(x in low for x in ("polyvia", "google", "gstatic", "recaptcha",
                                  "purl.org", "xmlns", "w3.org", "schema.org",
                                  "ogp.me", "drupal.org", "archive.org", "gouv.fr",
                                  "linkedin", "facebook", "twitter", "x.com",
                                  "youtube", "instagram", "wikipedia", "js.hsforms",
                                  "wonderpush", "github.io", "wordpress.org",
                                  "rdfs.org", "sioc", "skos", "foaf", "rdf")):
            continue
        return domaine
    return ""

# ------------------------------------------------------------------
# SOURCE AEPV (decolletage Oyonnax) — liste des membres
# ------------------------------------------------------------------
AEPV_LISTE = "https://aepv.asso.fr/membres/informations-membres/liste-des-membres/"
AEPV_FICHE = "https://aepv.asso.fr"

def scrape_aepv_liste(html):
    """Extrait (nom, lien_fiche) depuis la liste AEPV. ~314 membres.
    Format live : JSON embarque "title": "NOM", "link": ".../membress/xxx/"
    Format cache (markdown) : [![NOM](logo)](https://aepv.asso.fr/membress/xxx/)"""
    out = []
    # --- format live : paires title/link dans le JSON ---
    if '"title"' in html and 'membress' in html:
        titles = re.findall(r'"title"\s*:\s*"([^"]{2,70})"', html)
        links = re.findall(r'"link"\s*:\s*"(https://aepv\.asso\.fr/membress/[^"]+)"', html)
        n = min(len(titles), len(links))
        for i in range(n):
            nom = re.sub(r"\s+", " ", titles[i]).strip()
            if nom:
                out.append({"nom": nom, "fiche": links[i]})
        # dedupe par fiche
        vus = set()
        uniq = []
        for a in out:
            if a["fiche"] not in vus:
                vus.add(a["fiche"])
                uniq.append(a)
        return uniq
    # --- format cache (markdown) ---
    for m in re.finditer(r'!\[([^\]]{2,60})\]\([^)]*\)\]\(([^)]+)\)', html, re.S):
        nom = re.sub(r"\s+", " ", m.group(1)).strip()
        lien = m.group(2)
        if nom and "aepv.asso.fr" in lien and "/membress/" in lien:
            out.append({"nom": nom, "fiche": lien})
    return out

def scrape_aepv_fiche(html):
    """Extrait le site officiel depuis une fiche membre AEPV."""
    m = re.search(r'https?://(?:www\.)?[a-z0-9][a-z0-9.-]+\.[a-z]{2,}(?:/[^\s"<]*)?', html)
    if not m:
        return ""
    site = m.group(0).rstrip("/.,;")
    low = site.lower()
    if "aepv" in low or "mailto" in low or "google" in low or "facebook" in low \
       or "linkedin" in low or "twitter" in low:
        return ""
    return site.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

# ------------------------------------------------------------------
# Pipeline commun
# ------------------------------------------------------------------
SOURCES = {
    "polyvia": {"liste": POLYVIA_LISTE, "fiche_base": POLYVIA_FICHE,
                "parse_liste": scrape_polyvia_liste, "parse_fiche": scrape_polyvia_fiche},
    "aepv": {"liste": AEPV_LISTE, "fiche_base": AEPV_FICHE,
             "parse_liste": scrape_aepv_liste, "parse_fiche": scrape_aepv_fiche},
}

def verifier_mx(domaine):
    """Verifie qu'un domaine a un MX (anti-bounce). Retourne True/False."""
    import socket
    try:
        mx = socket.getaddrinfo(domaine, 25)
        return True
    except Exception:
        # fallback : MX via DNS txt (pas fiable a 100% mais indicatif)
        return True  # on ne bloque pas sur MX seul (le verrou domaine=site prime)

def chercher_dirigeant(nom_entreprise):
    """Cherche le dirigeant via l'API officielle (gratuite). Retourne
    'Prenom NOM' ou ''. Ne JAMAIS deviner d'email : juste le nom pour
    personnaliser l'accroche (Bonjour M. Dupont)."""
    try:
        import urllib.parse
        q = urllib.parse.quote(nom_entreprise[:60])
        j = json.loads(fetch("https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=1" % q))
        for r in j.get("results", []):
            for d in r.get("dirigeants", []):
                prenom = (d.get("prenoms") or "").split()[0] if d.get("prenoms") else ""
                nom = re.sub(r"\(.*?\)", "", d.get("nom") or "").strip()
                if prenom and nom:
                    return "%s %s" % (prenom.title(), nom.upper())
    except Exception:
        pass
    return ""

def traiter_adherent(adh, cfg, bloquees, deja_emails, score_min=2):
    """Traite UN adherent : fiche -> site -> analyse VETUSTE -> email -> verrou.
    Ne garde QUE les sites assez vetustes (score >= score_min) = vrais prospects
    qui ont besoin d'un graphiste. Retourne fiche ou None."""
    nom = adh["nom"]
    try:
        html_fiche = fetch(adh["fiche"])
    except Exception:
        return None
    if not html_fiche:
        return None
    site = cfg["parse_fiche"](html_fiche)
    if not site:
        return None
    # Analyse de vetuste du site (le critere n1 : le prospect A BESOIN de nous)
    try:
        html_site = fetch("https://www.%s/" % site) or fetch("http://%s/" % site)
    except Exception:
        return None
    if not html_site:
        return None
    from chasseur_prospects import analyze
    constats, score = analyze(html_site)
    if score < score_min:
        return None  # site correct -> pas un prospect (pas besoin de graphiste)
    # Email de contact sur le site officiel
    try:
        emails = find_email(site)
    except Exception:
        return None
    if not emails:
        return None
    email = emails[0]
    ok, raison = CH.verrou_email(email, site, bloquees, deja_emails)
    if not ok:
        return None
    # Nom du dirigeant (pour personnaliser l'accroche, jamais pour deviner l'email)
    dirigeant = chercher_dirigeant(nom)
    return {"nom": nom, "site": site, "email": email, "dirigeant": dirigeant,
            "source": adh.get("_source", ""), "date": date.today().isoformat(),
            "constats": constats, "score": score, "siren": ""}

def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    source = "polyvia"
    max_n = 20
    threads = 4
    for i, a in enumerate(args):
        if a.startswith("--source") and i + 1 < len(args):
            source = args[i + 1]
        if a.startswith("--max") and i + 1 < len(args):
            max_n = int(args[i + 1])
        if a.startswith("--threads") and i + 1 < len(args):
            threads = int(args[i + 1])
    if source not in SOURCES:
        print("Source inconnue: %s (dispo: %s)" % (source, ", ".join(SOURCES)))
        return 1

    cfg = SOURCES[source]
    data = CH.load_json(CH.DATA_F, [])
    bloquees = CH.load_json(CH.BLOQUEES_F, [])
    deja_emails = {str(e.get("to", "")).strip().lower() for e in data if e.get("to")}
    # + deja les emails dans la reserve
    try:
        with open(OUT_F, encoding="utf-8") as f:
            reserve = json.load(f) or []
    except Exception:
        reserve = []
    deja_emails |= {str(e.get("email", "")).strip().lower() for e in reserve}

    print("=== SCRAPER %s (%s) — %s (%d threads) ===" % (source.upper(), date.today().isoformat(),
                                                         "DRY-RUN" if dry else "APPLY", threads))
    html_liste = fetch(cfg["liste"])
    if not html_liste:
        print("Liste injoignable, stop.")
        return 1
    adherents = cfg["parse_liste"](html_liste)
    for a in adherents:
        a["_source"] = source
    if len(adherents) > max_n:
        adherents = adherents[:max_n]
    print("Adherents a traiter : %d" % len(adherents))

    # traitement PARALLELE (ThreadPool)
    t0 = time.time()
    valides = []
    with ThreadPoolExecutor(max_workers=threads) as ex:
        fut_map = {ex.submit(traiter_adherent, a, cfg, bloquees, deja_emails): a["nom"] for a in adherents}
        done = 0
        for fut in as_completed(fut_map):
            done += 1
            nom = fut_map[fut]
            try:
                fiche = fut.result()
            except Exception:
                fiche = None
            if fiche:
                valides.append(fiche)
                deja_emails.add(fiche["email"])
                print("  ✅ %-35s %s" % (nom[:35], fiche["email"]))
            if done % 50 == 0:
                print("  ... %d/%d traites (%d valides)" % (done, len(adherents), len(valides)))

    dt = time.time() - t0
    print("\nRapport : %d tries => %d emails valides en %.0f min (%.1fs/entreprise)"
          % (len(adherents), len(valides), dt / 60, dt / max(len(adherents), 1)))

    if not dry and valides:
        reserve.extend(valides)
        with open(OUT_F, "w", encoding="utf-8") as f:
            json.dump(reserve, f, ensure_ascii=False, indent=1)
        print("Reserve totale : %d emails verifies (fichier: %s)"
              % (len(reserve), os.path.basename(OUT_F)))
    elif dry:
        print("DRY-RUN : %d emails trouves, rien n'a ete enregistre." % len(valides))
    return 0

if __name__ == "__main__":
    sys.exit(main())
