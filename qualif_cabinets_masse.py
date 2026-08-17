# qualif_cabinets_masse.py — qualification automatique des cabinets comptables (zéro LLM)
# Pipeline : reserve cabinets -> site web (API + DDG) -> email contact (scrape) -> dirigeant (API gouv, cache) -> fiche partenaire
# Sortie : _cab_qualifies/<siren>.json (un fichier par cabinet qualifie) + resume JSON
import json, os, re, sys, time, urllib.request, urllib.parse, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
RESERVE = os.path.join(BASE, "candidats_cabinets.json")
CACHE_DIR = os.path.join(BASE, "_cab_qualifies")
os.makedirs(CACHE_DIR, exist_ok=True)

sys.path.insert(0, BASE)

def api_gouv_dirigeant(siren):
    """Dirigeant via API officielle (gratuite). Retourne (nom_complet, fonction) ou None."""
    try:
        url = "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=1" % siren
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        for res in data.get("results", []):
            for d in res.get("dirigeants", []):
                prenoms = " ".join(d.get("prenoms", []))
                nom = d.get("nom", "")
                fn = d.get("fonction", "")
                if nom:
                    return (prenoms + " " + nom).strip(), fn
    except Exception:
        pass
    return None

def google_search_site(nom, ville):
    """Cherche le site web du cabinet via DDG (html.duckduckgo.com)."""
    q = '%s %s' % (nom.replace('"', ''), ville)
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", "ignore")
        # extraire les liens
        links = re.findall(r'href="(https?://[^"]+)"', html)
        sites = []
        for l in links:
            if "duckduckgo.com" in l or "yahoo.com" in l or "bing.com" in l:
                continue
            # decoder les redirections DDG
            m = re.search(r'uddg=([^&"]+)', l)
            if m:
                l = urllib.parse.unquote(m.group(1))
            sites.append(l)
        return sites[:5]
    except Exception:
        return []

def extract_emails_from_site(url):
    """Scrape la page (et /contact) pour trouver un email."""
    emails = []
    for u in [url, url.rstrip("/") + "/contact", url.rstrip("/") + "/contactez-nous", url.rstrip("/") + "/contact.html"]:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode("utf-8", "ignore")
            found = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', html)
            for f in found:
                if not any(x in f.lower() for x in ["png", "jpg", "jpeg", "gif", "webp", "example", "wixpress", "sentry"]):
                    # un seul @ et pas de caractere suspect
                    if f.count("@") == 1 and len(f) < 60 and "." in f.split("@")[1]:
                        emails.append(f.lower())
        except Exception:
            continue
    # dedup en gardant l'ordre
    seen = set()
    out = []
    for e in emails:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out[:6]

def est_ok_email(email, site_domaine):
    """L'email doit etre PRO et sur un domaine propre (pas de reseau/DPO/agregateur)."""
    try:
        dom = email.split("@")[1].lower()
        if site_domaine and dom == site_domaine:
            return True
        # domaines generiques = rejetes (gmail, wanadoo... = pas pro)
        if any(x in dom for x in ["gmail", "wanadoo", "orange", "hotmail", "outlook", "yahoo", "live", "free.fr", "sfr", "laposte"]):
            return False
        # domaines agregateurs / DPO / reseaux de cabinets = rejetes (pas leur propre site)
        if any(x in dom for x in ["google.com", "inextenso", "cabinet-comptable", "expert-comptable",
                                   "compteo", "pont9", "annuaire", "pagesjaunes", "societe.com",
                                   "googlemail", "yopmail", "outlook.fr", "hotmail.fr"]):
            return False
        return True
    except Exception:
        return False

def site_domaine(url):
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "").lower()
    except Exception:
        return ""

def pappers_email(siren):
    """Scrape Pappers pour trouver l'email pro du cabinet. Retourne liste d'emails."""
    try:
        req = urllib.request.Request("https://www.pappers.fr/entreprise/%s" % siren,
                                     headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36"})
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
        emails = set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', html))
        pros = []
        for e in emails:
            if "pappers" in e or "png" in e or "jpg" in e or "example" in e or "sentry" in e or e.count("@") != 1:
                continue
            dom = e.split("@")[1].lower()
            if any(x in dom for x in ["gmail", "wanadoo", "orange", "hotmail", "outlook", "yahoo", "live", "free.fr", "sfr", "laposte"]):
                continue
            if len(e) < 60:
                pros.append(e.lower())
        return pros[:4]
    except Exception:
        return []

def main():
    reserve = json.load(open(RESERVE, encoding="utf-8"))
    if isinstance(reserve, dict):
        reserve = list(reserve.values())
    # deja qualifies ?
    deja = set(f.replace(".json", "") for f in os.listdir(CACHE_DIR))
    cache = json.load(open(os.path.join(BASE, "_lot21_cache.json"), encoding="utf-8"))
    MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 15
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
        # 1. dirigeant
        dirg = None
        if siren in cache:
            info = cache[siren]
            if isinstance(info, list) and info and info[0]:
                dirg = info[0]
        if not dirg:
            d = api_gouv_dirigeant(siren)
            if d and d[0]:
                dirg = d[0]
                cache[siren] = [dirg, "01"]
        if not dirg:
            continue  # pas de dirigeant -> pas envoyable
        prenom = dirg.split()[0] if dirg.split() else dirg
        civil = "M." if not any(x in dirg.upper() for x in ["MME", "MADAME", "MLLE"]) else "Mme"
        # 2. email pro via Pappers (le domaine pro = la preuve d'activite)
        emails = pappers_email(siren)
        email = None
        for e in emails:
            if est_ok_email(e, None):
                email = e
                break
        if not email:
            continue
        dom = email.split("@")[1]
        url = "https://" + dom
        # 3. fiche
        fiche = {
            "nom": nom.title() if nom.isupper() else nom,
            "ville": ville,
            "siren": siren,
            "dirigeant": dirg,
            "civil": civil,
            "prenom": prenom,
            "site": url,
            "email": email,
            "type": "cabinet",
            "constat": "Cabinet d'expertise comptable - vos clients industriels ont besoin d'une presence web credible pour rassurer leurs donneurs d'ordre",
        }
        with open(os.path.join(CACHE_DIR, siren + ".json"), "w", encoding="utf-8") as f:
            json.dump(fiche, f, ensure_ascii=False, indent=1)
        qualifies.append(fiche)
        print("OK %s | %s | %s | %s" % (siren, nom[:40], email, dirg))
        time.sleep(0.5)
    # sauver cache dirigeants
    with open(os.path.join(BASE, "_lot21_cache.json"), "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    print("=== QUALIFIES CE RUN: %d ===" % len(qualifies))

if __name__ == "__main__":
    main()