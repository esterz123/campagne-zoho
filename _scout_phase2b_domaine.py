#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCOUT PHASE 2b - devinette de domaine + preuve SIREN (sans moteur de recherche).
=================================================================================
Brave/DDG rate-limits cette IP. On n'en a pas besoin : pour une PME FR, le
domaine est presque toujours une variante de son nom/sigle. Pipeline :
  1. generer des candidats domaine (sigle, nom sans espaces/accents, avec tirets)
  2. MX present ? (DNS) -> site repond ? (HTTP)
  3. PREUVE : le SIREN (ou sa version spacee) apparait dans le HTML (mentions legales)
  4. email publie via find_email() (mailto strictement sur le domaine)
  5. SMTP RCPT TO via verify_smtp
Resumable : _scout_phase2b_etat.json. Zero suppression.
Usage : python3 _scout_phase2b_domaine.py [--start N] [--limit N]
"""
import os
import re
import sys
import json
import time
import socket
import unicodedata
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.join(BASE, "_scout_top100.json")
ETAT = os.path.join(BASE, "_scout_phase2b_etat.json")

from chasseur_prospects import fetch, find_email
import verify_smtp

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36"}
MOTS_VIDES = {"sas", "sarl", "sa", "eurl", "sci", "sasu", "et", "de", "du", "la", "le", "les",
              "societe", "ste", "entreprise", "atelier", "ateliers", "etablissements", "ets",
              "france", "fr", "groupe", "group"}


def slug(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def candidats_domaine(c):
    nom = c.get("nom") or ""
    sigle = re.search(r"\(([^)]+)\)", nom)
    mots = re.split(r"[^A-Za-z0-9]+", unicodedata.normalize("NFD", nom.lower()))
    mots = [unicodedata.normalize("NFC", m) for m in mots if m and m not in MOTS_VIDES]
    mots = [slug(m) for m in mots][:4]
    out = []
    if sigle:
        sg = slug(sigle.group(1))
        if 2 <= len(sg) <= 20:
            out.append(sg)
    out.append("".join(mots))                      # tout colle
    out.append("-".join(mots))                     # avec tirets
    if len(mots) >= 2:
        out.append("".join(mots[:2]))              # 2 premiers mots
        out.append("-".join(mots[:2]))
    slugs = [d for d in dict.fromkeys(out) if 3 <= len(d) <= 30]
    # TLD : .fr d'abord (PME FR), .com en secours. Jamais de domaine sans TLD.
    return [d + tld for d in slugs for tld in (".fr", ".com")]


def has_mx(dom):
    try:
        return bool(verify_smtp.get_mx(dom))
    except Exception:
        return False


def site_vivant(dom):
    """Retourne (url, html_cumule) : home + mentions-legales + contact.
    Le SIREN d'une PME apparait dans les mentions legales, jamais sur la home."""
    for base in ("https://" + dom, "https://www." + dom, "http://" + dom):
        try:
            req = urllib.request.Request(base, headers=UA)
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode("utf-8", "ignore")
        except Exception:
            continue
        cumul = [html]
        for p in ("/mentions-legales", "/mentions-legales/", "/contact", "/contact/",
                  "/nous-contacter", "/a-propos"):
            try:
                req2 = urllib.request.Request(base.rstrip("/") + p, headers=UA)
                with urllib.request.urlopen(req2, timeout=8) as r2:
                    cumul.append(r2.read().decode("utf-8", "ignore"))
            except Exception:
                pass
        return base, "\n".join(cumul)
    return None, None


def siren_present(html, siren):
    if not html:
        return False
    spaced = "%s %s %s" % (siren[:3], siren[3:6], siren[6:])
    return siren in html.replace(" ", "") or siren in html or spaced in html


def main():
    start = 0
    limit = 100
    for i, a in enumerate(sys.argv):
        if a == "--start" and i + 1 < len(sys.argv):
            start = int(sys.argv[i + 1])
        if a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    top = json.load(open(TOP, encoding="utf-8"))
    etat = json.load(open(ETAT, encoding="utf-8")) if os.path.exists(ETAT) else {}
    file_doms = set()
    d = json.load(open(os.path.join(BASE, "campagne_data.json"), encoding="utf-8"))
    for r in d:
        dom = (r.get("site") or "").lower().replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        if not dom and r.get("to"):
            dom = r["to"].split("@")[-1].lower()
        if dom:
            file_doms.add(dom)

    tally = {"ok": 0, "pas_de_site": 0, "homonyme": 0, "pas_email": 0, "smtp_mort": 0, "smtp_bloque": 0, "doublon": 0}
    for idx in range(start, min(len(top), start + limit)):
        c = top[idx]
        siren = str(c["siren"])
        if siren in etat:
            tally[etat[siren].get("verdict", "ok")] = tally.get(etat[siren].get("verdict", "ok"), 0) + 1
            continue
        verdict = {"verdict": "pas_de_site", "site": "", "email": "", "nom": c.get("nom", "")[:60]}
        homonyme_vue = None
        for dom in candidats_domaine(c)[:5]:
            if dom in file_doms:
                verdict = {"verdict": "doublon", "site": dom, "email": "", "nom": c.get("nom", "")[:60]}
                break
            if not has_mx(dom):
                continue
            url, html = site_vivant(dom)
            if not html:
                continue
            if not siren_present(html, siren):
                # domaine vivant mais pas le bon SIREN : noter, tenter les autres variantes
                if homonyme_vue is None:
                    homonyme_vue = dom
                continue
            # site prouve : email publie
            try:
                mails = find_email(dom) or []
            except Exception:
                mails = []
            mails = [m for m in mails if m.split("@")[-1].lower() == dom]
            if not mails:
                verdict = {"verdict": "pas_email", "site": dom, "email": "", "nom": c.get("nom", "")[:60]}
                break
            mail = mails[0]
            ok_v, _detail = verify_smtp.smtp_verify(mail)
            if ok_v is False:
                verdict = {"verdict": "smtp_mort", "site": dom, "email": mail, "nom": c.get("nom", "")[:60]}
            elif ok_v is None:
                verdict = {"verdict": "smtp_bloque", "site": dom, "email": mail, "nom": c.get("nom", "")[:60]}
            else:
                verdict = {"verdict": "ok", "site": dom, "email": mail, "nom": c.get("nom", "")[:60],
                           "ville": c.get("ville", "")}
            break
        if verdict["verdict"] == "pas_de_site" and homonyme_vue:
            verdict = {"verdict": "homonyme", "site": homonyme_vue, "email": "", "nom": c.get("nom", "")[:60]}
        etat[siren] = verdict
        tally[verdict["verdict"]] = tally.get(verdict["verdict"], 0) + 1
        print("[%d/%d] %-45s -> %s %s" % (idx + 1, len(top), c.get("nom", "")[:45],
                                          verdict["verdict"], verdict.get("site", "")), flush=True)
        if idx % 5 == 4:
            json.dump(etat, open(ETAT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.5)
    json.dump(etat, open(ETAT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== PHASE 2b done:", tally)


if __name__ == "__main__":
    sys.exit(main())
