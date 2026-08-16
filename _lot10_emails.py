#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot10 : emails sur pages contact + remontee holdings."""
import json, re, time, urllib.request

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"}

def fetch(url, timeout=9):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(150000).decode("utf-8", "ignore")
    except Exception:
        return None

def emails_in(html):
    out = set()
    for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", (html or "").lower()):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".js",
                                ".css", ".svg", "schema.org", "w3.org", "sentry.io", "alpinejs",
                                "polyfill", "jquery", "email@domain")):
            continue
        out.add(e)
    return sorted(out)

# domaines retenus -> pages a scanner
SITES = {
    61: ["https://usinage.com", "https://www.usinage.com/contact", "https://www.usinage.com/nous-contacter", "https://www.usinage.com/mentions-legales"],
    68: ["https://usinage-dieppois.fr", "https://usinage-dieppois.fr/contact", "https://usinage-dieppois.fr/contact.php", "https://usinage-dieppois.fr/mentions-legales"],
    80: ["https://guillerme-decolletage.fr", "https://guillerme-decolletage.fr/contact", "https://guillerme-decolletage.fr/contact.html", "https://guillerme-decolletage.fr/mentions-legales"],
    86: ["https://www.gay-decolletage.fr", "https://www.gay-decolletage.fr/contact", "https://www.gay-decolletage.fr/mentions-legales"],
    96: ["https://www.provence-outillage.fr", "https://www.provence-outillage.fr/contact", "https://www.provence-outillage.fr/nous-contacter", "https://www.provence-outillage.fr/mentions-legales"],
    98: ["http://fixouti.fr", "http://fixouti.fr/contact", "http://fixouti.fr/nous-contacter"],
    108: ["http://remo-outillage.fr", "http://remo-outillage.fr/contact", "http://remo-outillage.fr/contact.html", "http://remo-outillage.fr/coordonnees.html"],
    66: ["https://www.elcam-usinage.fr/contact", "https://www.elcam-usinage.fr/mentions-legales"],
    71: ["https://fraisageservices.fr/contact", "https://fraisageservices.fr/mentions-legales"],
    73: ["https://nordfraisage.fr/contact", "https://nordfraisage.fr/mentions-legales"],
    77: ["https://www.jcm-decolletage.fr/contact", "https://www.jcm-decolletage.fr/mentions-legales"],
    83: ["https://www.decolletage-elbe.fr/contact", "https://www.decolletage-elbe.fr/mentions-legales"],
    85: ["https://www.decolletage-de-reu.com/contact", "https://www.decolletage-de-reu.com/mentions-legales"],
    92: ["https://drault-decolletage.com/fr/contact", "https://drault-decolletage.com/fr/mentions-legales"],
    103: ["https://www.omedec.com/contact", "https://www.omedec.com/nous-contacter", "https://www.omedec.com/mentions-legales"],
    104: ["https://www.begc.fr/contact", "https://www.begc.fr/mentions-legales"],
    62: ["https://eberhard-usinage.fr/contact", "https://eberhard-usinage.fr/mentions-legales"],
    81: ["https://www.decolletage-jurassien.fr/contact", "https://www.decolletage-jurassien.fr/mentions-legales"],
    84: ["https://www.edelweiss-decolletage.com/contact", "https://www.edelweiss-decolletage.com/mentions-legales"],
    78: ["https://www.ouestdecolletage.com/contact", "https://www.ouestdecolletage.com/mentions-legales"],
    88: ["https://www.amd-decolletage.com/contact", "https://www.amd-decolletage.com/mentions-legales"],
}

emails_found = {}
for idx, urls in SITES.items():
    for u in urls:
        h = fetch(u)
        if h:
            es = emails_in(h)
            if es:
                emails_found.setdefault(str(idx), set()).update(es)
    if str(idx) in emails_found:
        print(idx, "->", sorted(emails_found[str(idx)]), flush=True)
    else:
        print(idx, "-> AUCUN EMAIL", flush=True)
    time.sleep(0.3)

json.dump({k: sorted(v) for k, v in emails_found.items()},
          open(BASE + r"\_lot10_emails_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# --- remontee holdings ---
HOLDINGS = ["PG INDUSTRIES DEVELOPPEMENT", "GROUPE ARBM", "ARDEC INDUSTRIES NEWCO", "EMACA",
            "TRAITEMENT DE SURFACE DE BITCHE", "FINANCIERE ALSACE INDUSTRIE", "MECA-JURA",
            "LJ INDUSTRIES", "QUARFLOC", "B.H.B.", "H.F.A.", "GROUP STSI", "REA", "SAFIR",
            "FIFAURE", "AMBOISIENNE INVESTISSEMENT", "SARL SDC", "OPALE GROUP", "KG FINANCE",
            "V GESTION", "HIOLLE INDUSTRIES", "ARDEC", "RAVINET CONSEILS", "AMBIQUAR"]
print("\n--- REMONTEE HOLDINGS ---")
for name in HOLDINGS:
    try:
        url = "https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=3" % urllib.parse.quote(name)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=15) as r:
            j = json.loads(r.read().decode("utf-8"))
        for res in j.get("results", []):
            n = res.get("nom_complet") or res.get("nom_raison_sociale") or ""
            if name.lower() in (res.get("nom_complet","").lower() or ""):
                pers = [d for d in res.get("dirigeants", []) if d.get("type_dirigeant") == "personne physique"]
                print(name, "|", res.get("siren"), "|", n[:50], "|", "; ".join((d.get("prenoms","")+" "+re.sub(r"\(.*?\)","",d.get("nom",""))).strip()+" ("+d.get("qualite","")+")" for d in pers[:3]))
                break
        time.sleep(0.4)
    except Exception as e:
        print(name, "| ERREUR", str(e)[:80])
