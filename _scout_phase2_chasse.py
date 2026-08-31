# -*- coding: utf-8 -*-
"""
SCOUT PHASE 2 v2 - le SIREN sert de SELECTEUR de site officiel.

Chaine par candidat :
  1. Collecter jusqu'a 6 domaines candidats (Brave + DuckDuckGo + devine-domaine
     depuis le nom). Filtrer annuaires/reservoirs de liens.
  2. Pour chaque domaine candidat : fetch home + pages contact/mentions-legales.
     Le domaine dont le HTML contient le SIREN du candidat = site officiel.
     (c'est LA preuve d'officialite, et ca tue le piege de l'homonyme de sigle)
  3. Sur ce site officiel uniquement : extraire les emails publies (mailto),
     domaine email == domaine du site. JAMAIS inventer.
  4. SMTP RCPT TO : True=OK / False=mort / None=bloque (rejet prudent).
  5. Anti-doublon domaine vs campagne_data.json + vs ce run.
Resumable : _scout_phase2_etat.json (save tous les 5 + a chaque decision).
"""
import json, os, re, sys, time, traceback, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
sys.path.insert(0, BASE)

from chasseur_prospects import fetch, _brave_sites, ANNUAIRES
import verify_smtp

TOP = json.load(open("_scout_top100.json", encoding="utf-8"))
ETAT = os.path.join(BASE, "_scout_phase2_etat.json")
LOG = os.path.join(BASE, "_scout_phase2.log")

# reservoirs de liens / annuaires / sites tiers jamais acceptes comme "officiel"
JUNK = ("w3.org", "schema.org", "wikipedia.org", "linkedin.com", "facebook.com",
        "instagram.com", "youtube.com", "x.com", "twitter.com", "pinterest.",
        "github.com", "gitlab.com", "google.", "bing.com", "brave.com",
        "duckduckgo.com", "apple.com", "microsoft.", "android.", "mozilla.org",
        "jquery.com", "fontawesome", "bootstrapcdn", "cloudflare", "gstatic",
        "googleapis", "doubleclick", "tiendeo", "indeed.com", "glassdoor",
        "viadeo", "welcometothejungle", "lassociation.fr", "journal-officiel",
        "legifrance", "service-public.fr", "impots.gouv", "inpi.fr",
        "economie.gouv", "annuaire", "118712", "118218", "pagesjaunes",
        "societe.com", "verif.com", "pappers", "infogreffe", "kompass",
        "cylex", "europages", "hotfrog", "opendi", "mappy", "viacars",
        "infonet", "e-pro.fr", "usinedefrance", "repreneurs", "businessfrance",
        "made-in", "directindustry", "virtual_expo", "virtualexpo", "allbiz",
        "fnac", "amazon.", "rakuten", "yellowpages", "findglocal", "experteer",
        "francenum", "lentreprise", "bpifrance", "cmi-france", "sudouest",
        "ouest-france", "leparisien", "figaro", "linternaute", "france3",
        "3000fr", "monavis", "avisverifies", "trustpilot", "yelp", "qonto",
        "joineo", "hellopro", "meilleurs-artisans", "cordia", "apec")

EXT_FICHIER = (".js", ".css", ".json", ".ts", ".tsx", ".jsx", ".map", ".html",
               ".htm", ".txt", ".xml", ".csv", ".pdf", ".png", ".jpg", ".jpeg",
               ".gif", ".webp", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".mp4")
TECH_DOM = ("example", "wixpress", "sentry", "godaddy", "schema.org", "w3.org",
            "noreply", "no-reply", "donotreply", "privacy", "legal", "abuse",
            "googleusercontent", "gravatar", "cloudflare", "wix.com", "webflow",
            "squarespace", "wordpress", "github", "unbounce", "sentry.io")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z0-9]{2,}")
PREF = ("direction", "contact", "info", "commercial", "accueil", "standard",
        "communication", "admin", "secretariat", "courrier", "service")


def log(msg):
    line = "%s %s" % (time.strftime("%H:%M:%S"), msg)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    # 31/08 15h : print() crashait "OSError Errno 22" quand la console du
    # process background est fermee (chasse de nuit). Le fichier fait foi.
    try:
        print(line, flush=True)
    except OSError:
        pass


def spaced(siren):
    return re.sub(r"(\d{3})(?=\d)", r"\1 ", siren)


def has_siren(html, siren):
    if not html:
        return False
    import html as _h
    t = _h.unescape(html)
    t = re.sub(r"\s+", " ", t)
    return siren in t or spaced(siren) in t


def clean_netloc(u):
    n = (urllib.parse.urlsplit(u).netloc or "").lower().replace("www.", "")
    return n


def site_plausible(n):
    if not n or "." not in n:
        return False
    if any(j in n for j in JUNK):
        return False
    if any(a in n for a in ANNUAIRES):
        return False
    if len(n) < 5:
        return False
    return True


def guess_domains(nom):
    """4 J CHAUDRONNERIE -> 4j-chaudronnerie.{fr,com}; A.F.U.M.E. (...) -> afume.fr"""
    out = []
    # 1. acronymes entre parentheses ou a points (A.F.U.M.E. -> afume, ABAG -> abag)
    for m in re.findall(r"\(([^)]{2,12})\)", nom):
        a = re.sub(r"[^A-Za-z0-9]", "", m)
        if 2 <= len(a) <= 10 and not a.isdigit():
            out.append(a.lower() + ".fr")
            out.append(a.lower() + ".com")
    pts = re.match(r"^([A-Z]\.){2,6}[A-Z]", nom.strip())
    if pts:
        a = pts.group(0).replace(".", "")
        out.append(a.lower() + ".fr")
        out.append(a.lower() + ".com")
    # 2. nom complet hyphenise
    base = re.sub(r"\(.*?\)", " ", nom)
    base = re.sub(r"^(sarl|sa|sas|eurl|eu|ets|les|la|le|group|groupe)\s+", "",
                  base.strip(), flags=re.I)
    base = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    if base and len(base) > 3:
        for tld in (".fr", ".com", ".eu", ".net"):
            out.append(base + tld)
        if "-" in base:
            out.append(base.replace("-", "") + ".fr")
    # 3. premiers mots seulement (coupe les descriptions longues)
    words = re.sub(r"[^a-z0-9 ]", " ", base.replace("-", " ")).split()
    if len(words) >= 2:
        for n in (2, 3):
            short = "-".join(words[:n])
            if len(short) > 3:
                out.append(short + ".fr")
                out.append(short + ".com")
    seen, res = set(), []
    for d in out:
        if d not in seen:
            seen.add(d)
            res.append(d)
    return res


def candidate_sites(nom, ville):
    cands, seen = [], set()
    def add(u):
        n = clean_netloc(u) if "/" in u or ":" in u else u.lower().replace("www.", "")
        if n and n not in seen and site_plausible(n):
            seen.add(n)
            cands.append(n)
    brave_raw = ""
    try:
        brave_raw = fetch("https://search.brave.com/search?q=" + urllib.parse.quote('"%s" %s' % (nom, ville)), tries=2)
    except Exception as e:
        log("brave EXC %s" % e)
    for l in re.findall(r'(https?://[^"<> ]+)', brave_raw):
        add(l)
    time.sleep(0.4)
    q = '"%s" %s' % (nom, ville)
    ddg_raw = ""
    try:
        ddg_raw = fetch("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q), tries=2)
        for m in re.findall(r'uddg=([^&"]+)', ddg_raw)[:8]:
            try:
                add(urllib.parse.unquote(m))
            except Exception:
                pass
    except Exception:
        pass
    # GARDE-BLACKOUT : les 2 moteurs renvoient vide -> rate-limit, on STOPPE
    # (sinon tout part en faux homonymes sur les domaines devines)
    if not brave_raw and not ddg_raw:
        raise RuntimeError("BLACKOUT MOTEURS (brave+ddg vides) -> stop, relancer plus tard")
    for g in guess_domains(nom):
        add(g)
    return cands[:10]


def dns_vivant(netloc):
    """Le domaine a-t-il au moins un enregistrement A/AAAA ? (evite les
    devinettes qui pendent 15s en connexion)"""
    try:
        import dns.resolver
        try:
            dns.resolver.resolve(netloc, "A", lifetime=4)
            return True
        except Exception:
            dns.resolver.resolve(netloc, "AAAA", lifetime=4)
            return True
    except Exception:
        return False


def pages_of(netloc):
    return ["https://www.%s/" % netloc, "https://%s/" % netloc,
            "https://www.%s/contact" % netloc, "https://%s/contact" % netloc,
            "https://www.%s/contactez-nous" % netloc,
            "https://www.%s/mentions-legales" % netloc,
            "https://%s/mentions-legales" % netloc,
            "https://www.%s/mentions_legales" % netloc,
            "https://www.%s/a-propos" % netloc,
            "http://www.%s/" % netloc, "http://%s/" % netloc]


def extract_emails(htmls, netloc):
    emails = set()
    site_dom = netloc.lower()
    for html in htmls:
        if not html:
            continue
        for m in EMAIL_RE.findall(html):
            e = m.lower().strip(".")
            if any(e.endswith(x) for x in EXT_FICHIER):
                continue
            if any(x in e for x in TECH_DOM):
                continue
            dom = e.split("@")[-1]
            if dom != site_dom and not dom.endswith("." + site_dom):
                continue
            if e.count("@") != 1 or len(e) > 50:
                continue
            local = e.split("@")[0]
            if local and local[0].isdigit():
                continue
            emails.add(e)
    return sorted(emails)


def main():
    data = json.load(open("campagne_data.json", encoding="utf-8"))
    doms = set()
    for r in data:
        for champ in ("to", "cc"):
            for m in re.finditer(r"@([A-Za-z0-9.-]+)", (r.get(champ) or "")):
                doms.add(m.group(1).lower())
    log("=== PHASE 2 v2 start: %d candidats, %d domaines a exclure ===" % (len(TOP), len(doms)))

    etat = {}
    if os.path.exists(ETAT):
        try:
            etat = json.load(open(ETAT, encoding="utf-8"))
            log("reprise: %d deja traites" % len(etat))
            for v in etat.values():
                if v.get("site"):
                    doms.add(v["site"].lower())
        except Exception:
            etat = {}

    def save():
        tmp = ETAT + ".tmp"
        json.dump(etat, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        os.replace(tmp, ETAT)

    n_done = 0
    for i, c in enumerate(TOP):
        siren = str(c["siren"])
        if siren in etat:
            continue
        nom, ville = c["nom"], c.get("ville", "")
        rec = {"nom": nom, "siren": siren, "ville": ville}
        cands = candidate_sites(nom, ville)
        rec["candidats"] = cands
        if not cands:
            rec["status"] = "no_site"
            etat[siren] = rec; save()
            log("[%d/100] NO_SITE %s (%s)" % (i + 1, nom[:38], ville))
            continue

        # 1er domaine dont le HTML porte le SIREN = site officiel prouve
        officiel, htmls = "", []
        for dom in cands:
            if not dns_vivant(dom):
                continue
            ph = [fetch(p) for p in pages_of(dom)[:6]]
            if any(has_siren(h, siren) for h in ph):
                officiel, htmls = dom, ph
                break
            time.sleep(0.3)
        if not officiel:
            rec["status"] = "homonyme"
            etat[siren] = rec; save()
            log("[%d/100] HOMONYME %s (%s) candidats=%s" % (
                i + 1, nom[:35], ville, ",".join(cands[:3])))
            continue
        rec["site"] = officiel

        # anti-doublon domaine
        if officiel in doms or ("www." + officiel) in doms:
            rec["status"] = "doublon"
            etat[siren] = rec; save()
            log("[%d/100] DOUBLON %s %s" % (i + 1, nom[:35], officiel))
            continue

        # emails publies (home+contact deja en main, + pages supplementaires)
        htmls += [fetch(p) for p in pages_of(officiel)[6:]]
        emails = extract_emails(htmls, officiel)
        if not emails:
            rec["status"] = "no_email"
            doms.add(officiel)
            etat[siren] = rec; save()
            log("[%d/100] NO_EMAIL %s %s" % (i + 1, nom[:35], officiel))
            continue
        emails.sort(key=lambda e: (0 if any(e.startswith(p) for p in PREF) else 1, len(e)))
        email = emails[0]
        rec["email"] = email
        rec["emails"] = emails[:3]

        ok, detail = verify_smtp.smtp_verify(email, timeout=8)
        rec["smtp"] = detail
        rec["status"] = {True: "ok", False: "mort"}.get(ok, "bloque")
        doms.add(officiel)
        etat[siren] = rec
        n_done += 1
        if n_done % 5 == 0:
            save()
        log("[%d/100] %-8s %s %s %s (%s)" % (
            i + 1, rec["status"].upper(), nom[:28], email, officiel, detail))

    save()
    from collections import Counter
    tally = Counter(v.get("status", "?") for v in etat.values())
    log("=== PHASE 2 done: %s ===" % dict(tally))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log("FATAL:\n" + traceback.format_exc())
        raise
