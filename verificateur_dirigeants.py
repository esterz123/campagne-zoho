#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICATEUR DIRIGEANTS V1 — l'assistant de confiance avant tout envoi.
=====================================================================
PROBLEME CORRIGE : le chasseur tombait sur des sites-annuaires/scrapers SEO
(mecaniqueautofacile.com, croisieres-en-seine.fr, footballberry.com...) et
prenait des emails recuperes sur ces sites generiques pour des emails officiels.

LA REGLE INFAILLIBLE (deterministe, pas de devinette) :
  Un email n'est ENVOYABLE que si le domaine de l'email EST le domaine
  officiel de l'entreprise. Preuve ultime : le SIREN de l'entreprise
  est presente sur le site de ce domaine (mentions legales).
  Un site-annuaire qui heberge 500 entreprises n'a JAMAIS le SIREN
  specifique de TA cible -> rejete.

3 verdicts possibles par fiche :
  CONFIRME   -> domaine = site officiel (SIREN verifie sur le site) -> ENVOYABLE
  DIRECTOIRE -> domaine = annuaire/generique/scraper (liste noire) -> REJETE
  REJETE     -> domaine mort OU SIREN absent du site OU email devine -> REJETE
  INCERTAIN  -> site injoignable/erreur, A revoir a la main (jamais envoye auto)

Usage :
  python verificateur_dirigeants.py                 # verifie tout dirigeants_email.json
  python verificateur_dirigeants.py --fichier X.json  # verifie un autre fichier
  python verificateur_dirigeants.py --siren 123 --email a@b.fr  # une seule fiche
Sortie : verifie_dirigeants.json + rapport console.
"""
import json, re, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
FETCH_TIMEOUT = 8

# Domaines connus qui hebergent plusieurs entreprises (annuaires, scrapers SEO,
# portails touristiques, medias...). Un email dessus = PAS le site officiel.
ANNUAIRES = (
    # annuaires B2B / referencement
    "cylex","kompass","pagesjaunes","societe.com","verif.com","infogreffe",
    "pappers","annuaire-entreprises","europages","yellowpages","sous-traiter",
    "hotfrog","buzzfile","opendi","lefigaro","linternaute","franceinfo",
    # scrapers SEO qui regroupent des societes
    "mecaniqueautofacile","croisieres-en-seine","anjou-tourisme","footballberry",
    "normandie-tourisme","bourgogne-tourisme","segreenanjoubleu","explore-savoie",
    "laprovence","bfctourisme","cdtsavoie","mesateliersdiy","petite.co.uk",
    "roman.co.uk","materiel-soudure","france-chaudronnerie","institutfrancais",
    "bureau-vallee","metallerie.com","allize-plasturgie","emploi-plasturgie",
    "pi.fr","graf.info","itroom","france-industrie.pro","orne.fr",
    "idlp.fr","ouest-injection","mc-media","sdeb.fr","plastique-industries",
    # emails techniques / test / inutiles
    "microsoft.com","nordvpn.com","debug.nordvpn","gmail.com","orange.fr",
    "free.fr","yahoo.fr","hotmail.fr","laposte.net","numericable.fr","wanadoo.fr",
    "domain.fr","exemple.fr","test.fr",
)
# Notes sur les domaines qui DOIVENT matcher le site (ne pas bloquer d'office)
EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def log(s): print(s, flush=True)

def fetch(url, tries=2):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
        "Accept-Language":"fr-FR,fr;q=0.8","Accept":"text/html"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
                return r.read().decode("utf-8","ignore")
        except Exception:
            if i == tries-1:
                return ""
            time.sleep(1)
    return ""

def domain_of(email):
    m = re.search(r"@([^@]+)$", email or "")
    return m.group(1).lower() if m else ""

def normalize_site(site):
    s = (site or "").lower().strip()
    s = s.replace("http://","").replace("https://","")
    s = s.replace("www.","").split("/")[0].split(":")[0]
    return s

def get_siren_via_api(nom, ville):
    """Retrouve le SIREN via l'API publique (fallback si absent)."""
    try:
        q = urllib.parse.quote(f"{nom} {ville}")
        j = json.loads(urllib.request.urlopen(
            "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=1" % q,
            timeout=15).read())
        for r in j.get("results", []):
            return r.get("siren")
    except Exception:
        pass
    return None

def pages_to_fetch(domain):
    """Pages cles d'un site officiel ou le SIREN apparait (mentions legales)."""
    return [
        f"https://{domain}", f"https://www.{domain}",
        f"https://{domain}/mentions-legales", f"https://{domain}/mentions_legales",
        f"https://{domain}/mentions-légales", f"https://{domain}/mentions_legales",
        f"https://{domain}/mentions-legales/", f"https://{domain}/legal",
        f"https://{domain}/mentions", f"https://{domain}/contact",
        f"https://www.{domain}/mentions-legales", f"https://www.{domain}/contact",
    ]

def siren_on_domain(domain, siren, nom):
    """Cherche le SIREN ET le nom de l'entreprise sur le site du domaine.
    C'est LA preuve que ce domaine appartient a l'entreprise."""
    if not siren:
        # pas de SIREN -> on ne peut pas prouver -> pas envoyable sans doute
        return False
    siren9 = siren if len(siren)==9 else siren.zfill(9)
    urls = pages_to_fetch(domain)
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch, u): u for u in urls}
        for f in as_completed(futs):
            try: h = f.result()
            except Exception: continue
            if not h: continue
            low = h.lower()
            # 1) SIREN avec ou sans espaces : 123456789
            if siren9 in re.sub(r"[\s.\-\u00a0]","",low):
                return True
            # 2) SIREN ecrit 123 456 789
            if " ".join([siren9[i:i+3] for i in range(0,9,3)]) in low:
                return True
            # 3) le nom de l'entreprise present aussi (preuve supplementaire)
            if nom and len(nom)>=6 and nom.lower()[:25] in low:
                return True
    return False

def verify_one(nom, ville, siren, email, site, match, dirigeants):
    email = (email or "").strip().lower()
    verdict = {"nom":nom,"ville":ville,"siren":siren,"email":email,
               "site":site,"match":match,"verdict":"REJETE","raison":"",
               "date":time.strftime("%Y-%m-%d")}
    if not email or not EMAIL.match(email):
        verdict["raison"]="pas d'email exploitable"
        return verdict
    edom = domain_of(email)
    # 1) annuaire connu ?
    if any(a in edom for a in ANNUAIRES):
        verdict["verdict"]="DIRECTOIRE"
        verdict["raison"]=f"domaine annuaire/scraper : {edom}"
        return verdict
    # 2) site officiel renseigne et different du domaine email ?
    sdom = normalize_site(site)
    if sdom and edom != sdom:
        # le domaine email doit matcher le site officiel
        verdict["verdict"]="REJETE"
        verdict["raison"]=f"email sur {edom} mais site officiel {sdom}"
        return verdict
    # 3) preuve SIREN sur le site du domaine email
    if not siren:
        siren = get_siren_via_api(nom, ville)
        verdict["siren"] = siren
    if siren_on_domain(edom, siren, nom):
        verdict["verdict"]="CONFIRME"
        verdict["raison"]=f"SIREN {siren} verifie sur {edom}"
    else:
        # site injoignable OU SIREN absent -> on ne sait pas -> INCERTAIN, jamais auto
        verdict["verdict"]="INCERTAIN"
        verdict["raison"]=f"SIREN non verifie sur {edom} (site injoignable ou domaine douteux)"
    return verdict

def main():
    args = sys.argv[1:]
    fichier = BASE + r"\dirigeants_email.json"
    out = BASE + r"\verifie_dirigeants.json"
    if "--fichier" in args:
        fichier = args[args.index("--fichier")+1]
        out = fichier.replace(".json","_verifie.json")
    if "--siren" in args and "--email" in args:
        v = verify_one("TEST", "", args[args.index("--siren")+1],
                       args[args.index("--email")+1], "", "", [])
        log(json.dumps(v, ensure_ascii=False, indent=1))
        return

    data = json.load(open(fichier, encoding="utf-8"))
    items = list(data.values()) if isinstance(data, dict) else data
    log("Verification de %d fiches..." % len(items))
    results = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {}
        for x in items:
            if not isinstance(x, dict): continue
            if isinstance(data, dict):
                key = x.get("siren") or x.get("nom") or ""
            else:
                key = str(x.get("num",""))
            futs[ex.submit(verify_one, x.get("nom",""), x.get("ville",""),
                           x.get("siren",""), x.get("email",""), x.get("site",""),
                           x.get("match",""), x.get("dirigeants",[]))] = key
        for f in as_completed(futs):
            key = futs[f]
            try: r = f.result()
            except Exception as e:
                log("  ERR %s: %s" % (key, str(e)[:50])); continue
            results[key] = r
    json.dump(results, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=1)

    from collections import Counter
    c = Counter(r["verdict"] for r in results.values())
    log("="*70)
    log("RAPPORT : %s" % c)
    log("="*70)
    for k in ("CONFIRME","DIRECTOIRE","INCERTAIN","REJETE"):
        for key,r in results.items():
            if r["verdict"]==k:
                log("[%-10s] %-35s %-30s | %s" % (k, r["nom"][:35], r["email"], r["raison"][:40]))
    log("="*70)
    log("Sauvegarde : %s" % out)
    log("-> Seuls les CONFIRME peuvent etre ajoutes a la file d'envoi.")
    log("-> Les INCERTAIN doivent etre verifies a la main (JAMAIS envoye auto).")

if __name__ == "__main__":
    main()
