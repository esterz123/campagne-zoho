# -*- coding: utf-8 -*-
"""
QUALIF CABINETS V2 (17/08) : recharge la qualification en masse des 959 cabinets.
Pappers/DDG/Bing/Firecrawl sont bloques (anti-bot / credits epuises).
SOURCE V2 : Brave Search (fonctionne, teste en direct) -> site du cabinet -> extraction email publie.
100% gratuit (aucun LLM, aucune cle).
"""
import json, os, re, sys, time, urllib.request, urllib.parse, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
RESERVE = os.path.join(BASE, "candidats_cabinets.json")
CACHE_DIR = os.path.join(BASE, "_cab_qualifies")
OUT = os.path.join(BASE, "partenaires_qualifies_cabinets.json")
os.makedirs(CACHE_DIR, exist_ok=True)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36"


def brave_site(nom, ville):
    """Trouve le site du cabinet via Brave Search (curl, pas urllib).
    Le nom est nettoYE des mots generiques pour garder le nom distinctif."""
    mots_generiques = ["EXPERTISE", "COMPTABLE", "SOCIETE", "SARL", "SELARL", "SAS",
                       "AUDIT", "CONSEIL", "CONSEILS", "GROUPE", "HOLDING", "SCP",
                       "CABINET", "ET", "DU", "DE", "LA", "LE", "LES", "AUX"]
    tokens = [t for t in nom.upper().replace(",", " ").split()
              if t not in mots_generiques and len(t) > 2]
    nom_net = " ".join(tokens) if tokens else nom
    q = '"%s" %s' % (nom_net, ville)
    try:
        out = subprocess.run(
            ["curl", "-s", "--max-time", "20", "-A", UA,
             "https://search.brave.com/search?q=" + urllib.parse.quote(q)],
            capture_output=True, text=True, timeout=30).stdout
        links = re.findall(r'(https?://[^"<> ]+)', out)
        # domaines d'annuaires / aggregeurs / sites morts : JAMAIS le site reel du cabinet
        NOYAUX_ANNUAIRES = ["pagesjaunes", "societe.com", "annuaire-entreprises", "data.gouv",
                            "pappers", "manageo", "verif.com", "kompass", "infogreffe",
                            "torproject", "w3.org", "wikipedia", "facebook", "linkedin",
                            "google", "bing", "brave", "pinterest", "yellowpages", "cylex",
                            "buzzfile", "opendata", "lesechos", "lefigaro", "dnb.com",
                            "entreprise.data", "hotfrog", "123entreprises", "lannuaire",
                            "turbopages", "sirene.fr", "annuaire.pro", "infonet",
                            "lafabrique", "sas-formation", "cadres", "job", "emploi",
                            "placement", "banque", "assurance", "axa", "credit"]
        ok = []
        for l in links:
            l = l.rstrip(".,);]")
            dom = l.lower()
            if any(x in dom for x in NOYAUX_ANNUAIRES):
                continue
            m = re.match(r'(https?://(?:www\.)?([^/]+))', l)
            if m:
                root = m.group(1)
                bare = m.group(2)
                # un vrai site pro : pas juste la racine navigateur, pas un sous-chemin d'annuaire
                if bare in ("", "www", "web", "home", "index"):
                    continue
                if root not in ok:
                    ok.append(root)
        return ok[:3]
    except Exception:
        return []


def extract_emails(url):
    """Scrape la page d'accueil + /contact pour trouver un email pro.
    NE GARDE QUE les emails dont le domaine = domaine du site (preuve d'officialite)."""
    emails = set()
    m = re.match(r'https?://(?:www\.)?([^/]+)', url)
    site_dom = m.group(1).lower() if m else ""
    for u in [url, url.rstrip("/") + "/contact", url.rstrip("/") + "/contactez-nous",
              url.rstrip("/") + "/mentions-legales", url.rstrip("/") + "/a-propos"]:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=12) as r:
                html = r.read().decode("utf-8", "ignore")
            for e in re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', html):
                e = e.lower()
                dom = e.split("@")[1]
                # STRICT : l'email doit etre sur le domaine du site trouve
                if dom != site_dom and not dom.endswith("." + site_dom):
                    continue
                if e.count("@") == 1 and len(e) < 60:
                    emails.add(e)
        except Exception:
            continue
    return sorted(emails)


def api_gouv_dirigeant(siren):
    try:
        url = "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=1" % siren
        d = json.load(urllib.request.urlopen(url, timeout=20))
        ents = d.get("results", [])
        if not ents:
            return None
        dirs = ents[0].get("dirigeants", []) or []
        for dd in dirs:
            prenoms = (dd.get("prenoms") or "").strip()
            nom = (dd.get("nom") or "").strip()
            if prenoms and nom:
                return "%s %s" % (prenoms.split()[0].capitalize(), nom.upper())
        return None
    except Exception:
        return None


def main():
    reserve = json.load(open(RESERVE, encoding="utf-8"))
    deja = set(f.replace(".json", "") for f in os.listdir(CACHE_DIR))
    MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    qualifies = []
    traites = 0
    for cab in reserve:
        siren = str(cab.get("siren", ""))
        if not siren or siren in deja:
            continue
        if traites >= MAX:
            break
        traites += 1
        nom = cab.get("nom", "")
        ville = cab.get("ville", "")
        print("-- %s | %s %s" % (siren, nom[:35], ville))
        # 1. site via Brave
        sites = brave_site(nom, ville)
        if not sites:
            print("   pas de site trouve")
            continue
        site = sites[0]
        print("   site: %s" % site)
        # 2. emails du site
        emails = extract_emails(site)
        if not emails:
            print("   aucun email sur le site")
            continue
        email = emails[0]
        print("   email: %s" % email)
        # 3. dirigeant via API gouv
        dirg = api_gouv_dirigeant(siren)
        if not dirg:
            print("   pas de dirigeant")
            continue
        print("   dirigeant: %s" % dirg)
        civil = "Mme" if any(x in dirg.upper() for x in ["MME", "MADAME", "MLLE"]) else "M."
        fiche = {
            "nom": nom.title() if nom.isupper() else nom,
            "ville": ville, "siren": siren, "dirigeant": dirg, "civil": civil,
            "prenom": dirg.split()[0], "site": site, "email": email,
            "type": "cabinet", "source": "brave-v2",
            "constat": "Cabinet d'expertise comptable - vos clients industriels ont besoin d'une presence web credible pour rassurer leurs donneurs d'ordre",
        }
        with open(os.path.join(CACHE_DIR, siren + ".json"), "w", encoding="utf-8") as f:
            json.dump(fiche, f, ensure_ascii=False, indent=1)
        qualifies.append(fiche)
        time.sleep(0.4)
    print("=== QUALIFIES CE RUN (v2 brave): %d ===" % len(qualifies))
    if qualifies:
        existing = []
        if os.path.exists(OUT):
            existing = json.load(open(OUT, encoding="utf-8"))
        json.dump(existing + qualifies, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("   ecrits dans %s (total %d)" % (OUT, len(existing) + len(qualifies)))


if __name__ == "__main__":
    main()