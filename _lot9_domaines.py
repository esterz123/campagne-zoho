#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 9 (subagent): test direct de domaines devines pour les candidats index 10-59."""
import json, os, re, sys, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

PARKING = ("sedo", "afternic", "dan.com", "godaddy", "namecheap", "hugedomains",
           "shopify", "wixsite", "webnode", "sitew", "1and1", "ovh", "gandi",
           "buy this domain", "domain is for sale", "parked", "en construction",
           "site en construction")

def slug_net(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())

def get_html(domain, path=""):
    for proto in ("https", "http"):
        try:
            req = urllib.request.Request(proto + "://" + domain + path, headers=UA, method="GET")
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read(150000).decode("utf-8", "ignore")
                return html, r.getcode()
        except Exception:
            continue
    return "", 0

def extrait(html, domain):
    """Extrait les indices factuels utiles: titre, copyright, generator, emails."""
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = re.sub(r"\s+", " ", t.group(1)).strip()[:120] if t else ""
    gen = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I)
    generator = gen.group(1)[:60] if gen else ""
    years = sorted(set(re.findall(r"(19[89]\d|20[0-2]\d)", html)))
    emails = set()
    for m in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html.lower()):
        if any(x in m for x in ("example", "wixpress", "sentry", "schema.org", "w3.org", ".png", ".jpg", ".gif", ".svg", "noreply")):
            continue
        emails.add(m)
    low = html.lower()
    flags = []
    if "<table" in low and low.count("<table") >= 3:
        flags.append("tables_html")
    if re.search(r"copyright[^0-9]{0,30}(19\d\d|200\d|201[0-9]|202[0-3])", low):
        m = re.search(r"copyright[^0-9]{0,30}((?:19\d\d|200\d|201[0-9]|202[0-3]))", low)
        flags.append("copyright_%s" % m.group(1))
    if "wp-content" in low: flags.append("wordpress")
    if "joomla" in low: flags.append("joomla")
    if "spip" in low and "/spip.php" in low: flags.append("spip")
    if "drupal" in low: flags.append("drupal")
    if "typo3" in low: flags.append("typo3")
    if "prestashop" in low: flags.append("prestashop")
    if "magento" in low: flags.append("magento")
    if "shopify" in low: flags.append("shopify")
    if "wix" in low and "wixstatic" in low: flags.append("wix")
    if re.search(r"\.swf|flash", low): flags.append("flash")
    if "google-analytics" not in low and "gtag" not in low: flags.append("pas_de_tracking")
    return {"title": title, "generator": generator, "annees": years[-6:],
            "emails": sorted(emails), "flags": flags, "taille": len(html)}

def domaines_candidats(nom):
    base = re.sub(r"\(.*?\)", "", nom).strip()
    base = re.sub(r"^(societe|sa|sarl|sas|eurl|ets|les|la|le|des)\s+", "", base, flags=re.I)
    slugs = set()
    s = slug_net(base)
    if 4 <= len(s) <= 40:
        slugs.add(s)
    mots = [w for w in re.findall(r"[a-z0-9]+", base.lower()) if len(w) >= 3]
    stop = ("societe", "sarl", "sas", "eurl", "ets", "plastique", "plastiques",
            "mecanique", "precision", "usinage", "distribution", "industries",
            "faconnes", "injectes", "ateliers", "maintenance")
    mots2 = [w for w in mots if w not in stop]
    if mots2:
        slugs.add("".join(mots2[:2]))
        slugs.add("-".join(mots2[:2]))
        if len(mots2) >= 2:
            slugs.add("-".join(mots2[:3]))
            slugs.add(mots2[0] + "-" + mots2[1] + "-" + (mots2[2] if len(mots2) > 2 else ""))
    initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", nom) if w and w[0].isalpha()).lower()
    if 2 <= len(initials) <= 5:
        slugs.add(initials)
    # aussi avec le nom de ville pour les noms tres generiques
    out = []
    for s in slugs:
        if not s: continue
        for ext in (".fr", ".com"):
            out.append(s + ext)
    return out[:14]

def main():
    plage = json.load(open(os.path.join(BASE, "_lot9_plage.json"), encoding="utf-8"))
    excl = {16, 18, 26}
    out = json.load(open(os.path.join(BASE, "_lot9_domaines.json"), encoding="utf-8")) if os.path.exists(os.path.join(BASE, "_lot9_domaines.json")) else {}
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    for c in plage:
        i = c["_index"]
        if i in excl or (only and str(i) not in only):
            continue
        key = str(i)
        if key in out and out[key].get("teste"):
            continue
        cands = domaines_candidats(c["nom"])
        vivants = []
        for d in cands:
            html, code = get_html(d)
            if code != 200 or not html:
                continue
            low = html.lower()
            if any(p in low for p in ("buy this domain", "domain is for sale", "parked free", "page introuvable")) and len(html) < 2000:
                continue
            if "<title" not in low:
                continue
            info = extrait(html, d)
            if not info["title"] or len(info["title"]) < 3:
                continue
            vivants.append({"domaine": d, **info})
        out[key] = {"nom": c["nom"], "ville": c["ville"], "siren": c["siren"],
                    "candidats_testes": cands, "vivants": vivants, "teste": True}
        if vivants:
            print("%s | %s | %d vivants" % (key, c["nom"][:40], len(vivants)))
            for v in vivants:
                print("    -> %s | %s | %s | emails:%s" % (v["domaine"], v["title"][:50], v["flags"], v["emails"][:2]))
        else:
            print("%s | %s | RIEN" % (key, c["nom"][:40]))
        json.dump(out, open(os.path.join(BASE, "_lot9_domaines.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
