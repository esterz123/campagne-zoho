# -*- coding: utf-8 -*-
"""RASSEMBLEUR DE DIAGNOSTIC (idée A) : pour un prospect donne (num de la file),
rassemble en 1 clic TOUTES les donnees necessaires a la redaction du diagnostic :
constats (deja rediges dans l email), business (API entreprise : CA, effectif,
NAF, dirigeant), etat du site en direct (curl : WP, SSL, copyright).
Usage : python rassembleur_diagnostic.py <num>
Sortie : bloc structure pret a etre transforme en diagnostic.
"""
import json, os, re, sys, datetime, urllib.request, urllib.parse, unicodedata, ssl

BASE = os.path.dirname(os.path.abspath(__file__))

def jload(p, default):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s

def curl_site(url):
    """Etat technique du site (version WP, SSL, copyright)."""
    info = []
    for base in (url, url.replace("http://", "https://")):
        try:
            req = urllib.request.Request(base, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"})
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
                html = r.read().decode("utf-8", "ignore").lower()
                final = r.geturl()
                if final.startswith("https://"):
                    info.append("SSL: OK (https)")
                else:
                    info.append("SSL: ABSENT (http)")
                m = re.search(r'generator" content="wordpress ([0-9.]+)', html)
                if m:
                    info.append("WordPress: %s" % m.group(1))
                elif "wp-content" in html:
                    info.append("WordPress: present (version cachee)")
                m = re.search(r"copyright[^<]{0,40}|©\s*[0-9]{4}", html)
                if m:
                    info.append("Copyright: %s" % re.sub(r"\s+", " ", m.group(0))[:50])
                return info
        except Exception:
            continue
    return ["Site injoignable (anti-bot ou down)"]

def api_entreprise(entreprise):
    try:
        req = urllib.request.Request(
            "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=2" % urllib.parse.quote(entreprise),
            headers={"User-Agent": "rassembleur-mahdi/1.0"})
        j = json.load(urllib.request.urlopen(req, timeout=20))
        for r in j.get("results", []):
            return {
                "raison_sociale": r.get("nom_complet"),
                "ville": (r.get("siege") or {}).get("ville"),
                "naf": r.get("activite_principale"),
                "effectif": r.get("tranche_effectif_salarie"),
                "finances": r.get("finances"),
                "dirigeants": [{"prenoms": d.get("prenoms"), "nom": d.get("nom"), "qualite": d.get("qualite")}
                               for d in r.get("dirigeants", []) if d.get("type_dirigeant") == "personne physique"],
            }
    except Exception:
        return {}
    return {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python rassembleur_diagnostic.py <num>")
        sys.exit(1)
    num = sys.argv[1]
    data = jload(os.path.join(BASE, "campagne_data.json"), [])
    e = next((x for x in data if str(x.get("num")) == num), None)
    if not e:
        print("Prospect #%s introuvable dans campagne_data.json" % num)
        sys.exit(1)

    ent = re.sub(r"^\d+\s*[—-]\s*", "", e.get("prospect", ""))
    ent = re.sub(r"\s*\(.*?\)\s*$", "", ent).strip()
    biz = api_entreprise(ent)
    site = e.get("site") or e.get("url") or ""
    if not site:
        # extraire le domaine cite dans le body (ex: jsmperrin.com)
        m = re.search(r"([a-z0-9-]+\.(?:fr|com|eu|net|org|io))", (e.get("body") or "").lower())
        if m:
            site = "https://" + m.group(1)
    # constats deja rediges dans le body (entre la 1re ligne et le CTA)
    body = e.get("body", "")
    constats = body[:1200]

    print("=" * 70)
    print("RASSEMBLEUR — Prospect #%s : %s" % (num, ent))
    print("=" * 70)
    print("\n[1] CONTACT")
    print("  Email cible : %s" % e.get("to"))
    print("  Objet email : %s" % e.get("subject"))
    print("  Site : %s" % (site or "(non renseigne, chercher via web_search)"))
    print("\n[2] BUSINESS (API officielle)")
    if biz:
        print("  Raison sociale : %s" % biz.get("raison_sociale"))
        print("  Ville : %s | NAF : %s" % (biz.get("ville"), biz.get("naf")))
        print("  Effectif : %s" % biz.get("effectif"))
        fin = biz.get("finances") or {}
        if fin:
            annee = max(fin.keys()) if fin else ""
            if annee:
                print("  CA %s : %s | Resultat : %s" % (annee, fin[annee].get("ca"), fin[annee].get("resultat_net")))
        for d in (biz.get("dirigeants") or [])[:2]:
            print("  Dirigeant : %s %s (%s)" % (d.get("prenoms"), d.get("nom"), d.get("qualite")))
    else:
        print("  (API indisponible, chercher via Pappers au moment de la redaction)")
    print("\n[3] ETAT DU SITE (verifie en direct)")
    if site:
        for ligne in curl_site(site):
            print("  - %s" % ligne)
    else:
        print("  (site non renseigne)")
    print("\n[4] CONSTATS DEJA REDIGES (dans l email envoye)")
    print("  " + norm(constats).replace("\n", "\n  ")[:900])
    print("\n[5] A COMPLETER AU MOMENT DE LA REDACTION")
    print("  - 1 concurrent a analyser (web_search : <secteur> <ville> concurrent)")
    print("  - 3 actions immediates concretes")
    print("  - Le ton et la mise en page (template livrable_diagnostic/)")
    print("\n=> Base prete. Redaction du diagnostic : ~20-30 min.")

if __name__ == "__main__":
    main()
