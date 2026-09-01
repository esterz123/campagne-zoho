# -*- coding: utf-8 -*-
"""
FORMULAIRE DIRECT - remplit le formulaire de contact du site du prospect.
=========================================================================
Au lieu d'un email qui finit en spam, le constat arrive dans la boite
interne du patron via SON formulaire. Taux de lecture : 90% vs 15%.

Respecte : zero U+2019, zero tiret long, message branding-first.
Resumable : _form_direct_etat.json. Anti-doublon : une seule fois par domaine.
Usage : python3 form_direct.py [--limit N] [--start N]
"""
import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
import ssl

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
STATE = os.path.join(BASE, "campagne_state.json")
ETAT = os.path.join(BASE, "_form_direct_etat.json")
PR = os.path.join(BASE, "constats_sites.json")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml",
      "Accept-Language": "fr-FR,fr;q=0.9"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def clean(t):
    return (t or "").replace("\u2019", "'").replace("\u2018", "'")


def norm_dom(x):
    x = (x or "").lower().strip()
    if "@" in x:
        x = x.split("@")[-1]
    x = x.replace("https://", "").replace("http://", "").replace("www.", "")
    return x.split("/")[0].strip()


def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "ignore"), r.getcode()


def post_form(url, fields, timeout=15):
    data = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": UA["User-Agent"],
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": url,
    })
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.getcode(), r.read(2000).decode("utf-8", "ignore")


def trouver_formulaire(html, base_url):
    """Trouve le form de contact et son action + les champs."""
    forms = re.findall(r'<form[^>]*>.*?</form>', html, re.S | re.I)
    for form in forms:
        low = form.lower()
        # formulaire de contact (pas newsletter, pas search)
        if re.search(r'newsletter|subscribe|search', low):
            continue
        # doit avoir un champ email et un champ message
        if 'email' not in low or ('message' not in low and 'comment' not in low and 'text' not in low):
            continue
        action_m = re.search(r'action=["\']([^"\']*)["\']', form)
        action = action_m.group(1) if action_m else ""
        if not action:
            action = base_url
        elif action.startswith("/"):
            action = base_url.rstrip("/") + action
        elif not action.startswith("http"):
            action = base_url.rstrip("/") + "/" + action
        # champs
        names = re.findall(r'name=["\']([^"\']+)["\']', form)
        return action, names
    # fallback : chercher page /contact
    return None, []


def message_branding(domaine, note, nom_entreprise):
    """Le message branding-first (pas tech)."""
    if note is not None and note <= 40:
        return ("Bonjour,\n\nJe suis brand designer pour les PME industrielles francaises.\n"
                "En visitant votre site (%s), j'ai remarque plusieurs points qui "
                "donnent une image moins professionnelle que votre vrai savoir-faire.\n\n"
                "Plutot que de vous faire un discours, je vous ai prepare un rapport "
                "gratuit chiffre (vitesse, mobile, image, comparaison avec vos concurrents). "
                "Il est pret, vous le recevez en repondant simplement \"oui\" a ce message.\n\n"
                "Cordialement,\nMahdi\nPortfolio : mahdi-design.com" % domaine)
    return ("Bonjour,\n\nJe suis brand designer specialise dans les PME industrielles.\n"
            "Votre site %s fonctionne, mais je crois qu'il ne reflete pas encore "
            "le vrai niveau de votre entreprise. Vos concurrents directs ont des "
            "images plus modernes, et un client qui compare choisit l'autre.\n\n"
            "Je vous ai prepare un rapport gratuit : ce qui manque a votre image, "
            "compare a vos concurrents. Vous le recevez en repondant \"oui\".\n\n"
            "Cordialement,\nMahdi\nPortfolio : mahdi-design.com" % domaine)


def main():
    start = 0
    limit = 20
    for i, a in enumerate(sys.argv):
        if a == "--start" and i + 1 < len(sys.argv):
            start = int(sys.argv[i + 1])
        if a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    d = json.load(open(DATA, encoding="utf-8"))
    st = json.load(open(STATE, encoding="utf-8"))
    s = st.get("sent", {})
    pr = json.load(open(PR, encoding="utf-8"))
    etat = json.load(open(ETAT, encoding="utf-8")) if os.path.exists(ETAT) else {}

    # cibles : vierges avec site, tries par note (les plus casses d'abord)
    cibles = []
    for r in d:
        num = str(r.get("num"))
        if num in s:
            continue
        if num in etat:
            continue
        site = (r.get("site") or "").strip()
        if not site:
            continue
        note = pr.get(num, {}).get("note")
        cibles.append((num, site, note, r.get("to", "")))
    cibles.sort(key=lambda x: (x[2] if x[2] is not None else 50, int(x[0])))
    cibles = cibles[start:start + limit]

    tally = {"envoye": 0, "pas_de_form": 0, "echec": 0, "doublon": 0}
    for k, (num, site, note, email) in enumerate(cibles, 1):
        dom = norm_dom(site)
        base = "https://" + dom
        if dom in etat:
            continue
        # chercher la page de contact
        for page in (base + "/contact", base + "/contactez-nous", base + "/nous-contacter", base):
            try:
                html, code = fetch(page, timeout=10)
                if code != 200 or len(html) < 500:
                    continue
                action, names = trouver_formulaire(html, page)
                if not action:
                    continue
                # construire les champs
                fields = {}
                for n in names:
                    ln = n.lower()
                    if 'email' in ln or 'mail' in ln:
                        fields[n] = "contact@mahdi-design.com"
                    elif 'name' in ln or 'nom' in ln:
                        fields[n] = "Mahdi - Brand Designer"
                    elif 'message' in ln or 'comment' in ln or 'text' in ln:
                        fields[n] = message_branding(dom, note, "")
                    elif 'subject' in ln or 'objet' in ln:
                        fields[n] = "Votre image de marque - rapport gratuit prepare"
                    elif 'phone' in ln or 'tel' in ln:
                        fields[n] = ""
                    elif n in ('bot-field', 'captcha', 'recaptcha'):
                        fields[n] = ""
                if 'message' not in str(fields).lower():
                    continue  # pas de champ message = pas un form de contact
                code_r, resp = post_form(action, fields)
                if code_r in (200, 301, 302):
                    verdict = "envoye"
                    tally["envoye"] += 1
                else:
                    verdict = "echec"
                    tally["echec"] += 1
                etat[dom] = {"verdict": verdict, "via": page, "code": code_r, "num": num,
                             "date": time.strftime("%Y-%m-%d %H:%M")}
                print("[%d/%d] #%s %-40s -> %s (%d)" % (k, len(cibles), num, dom[:40], verdict, code_r), flush=True)
                break
            except Exception as e:
                continue
        else:
            verdict = "pas_de_form"
            tally["pas_de_form"] += 1
            etat[dom] = {"verdict": verdict, "num": num, "date": time.strftime("%Y-%m-%d %H:%M")}
            print("[%d/%d] #%s %-40s -> %s" % (k, len(cibles), num, dom[:40], verdict), flush=True)
        json.dump(etat, open(ETAT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(1.5)

    json.dump(etat, open(ETAT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== FORM DIRECT done:", tally)


if __name__ == "__main__":
    sys.exit(main())
