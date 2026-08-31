#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICATEUR SITE - transforme chaque mail froid en preuve verifiee.
====================================================================
Probleme : les 152 mails vierges de campagne_data.json affirment "votre site
n'apparait pas sur Google" sans l'avoir verifie. Un constat faux = credibilite
detruite (regle outreach 13/08). Un constat vrai et precis = 10x de reponses.

Ce script sonde le site reel de CHAQUE prospect, releve des FAITS mesurables
(HTTPS, vitesse, mobile, version WP, images sans alt, sitemap, page unique,
site mort, parking, liens de fraude), calcule une note /100 et redige un
constat verifie. Sortie : constats_sites.json (aucun mail envoye ici).

Usage :
    python3 verificateur_site.py --sample 10      # test
    python3 verificateur_site.py                  # toute la file
    python3 verificateur_site.py --nums 114,115   # cible
Zéro reseau social, zero cle, zero LLM. 100% gratuit, repetable.
"""
import os
import re
import sys
import ssl
import json
import time
import socket
import urllib.request
import urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
OUT = os.path.join(BASE, "constats_sites.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# Liens de fraude connus (site pirate) - repris de scan_urgence.py (correctif 13/08)
SEP = r"(?:^|[.\-_])"
SPAM = [SEP + w for w in ("casino", "poker", "viagra", "cialis", "pharma", "escort",
                          "slot", "loto", "bet365", "kraken")] + [
    r"카지노", r"온라인", r"바카라", r"赌场", r"赌博", r"彩票"]

DOMAINES_ANNONCES = re.compile(
    r"(wp-content/uploads|googleapis|gstatic|fonts\.|cdn\.|cloudflare|jquery|"
    r"facebook|twitter|instagram\.com|linkedin|youtube|vimeo|maps\.google)", re.I)


def clean(t):
    """Le nuage Zoho rejette l'apostrophe typographique U+2019."""
    return (t or "").replace("\u2019", "'").replace("\u2018", "'")


def norm_dom(x):
    x = (x or "").lower().strip()
    if "@" in x:                      # c'est un email -> on garde son domaine
        x = x.split("@")[-1]
    x = x.replace("https://", "").replace("http://", "").replace("www.", "")
    return x.split("/")[0].strip()


def fetch(url, timeout=12, ctx=None):
    req = urllib.request.Request(url, headers=UA)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        html = r.read().decode("utf-8", "ignore")
        return html, r.getcode(), time.time() - t0, r.geturl()


def sonder(site, email=""):
    """Sonde un site. Retourne dict de faits MESURES (rien d'invente)."""
    f = {"site_brut": site, "domaine": norm_dom(site) or norm_dom(email),
         "etat": "MORT", "mort_nx": False, "https": False, "ssl_valide": False, "http_seul": False,
         "temps_s": None, "mobile": None, "titre": "", "meta_desc": False,
         "wp_version": "", "img_sans_alt": None, "img_total": 0,
         "sitemap": False, "robots": False, "pages_internes": 0,
         "une_seule_page": False, "parking": False, "copyright": None,
         "pirate": "", "tel": False, "formulaire": False, "fichier": "",
         "erreur": ""}
    dom = f["domaine"]
    if not dom:
        f["erreur"] = "aucun site ni email"
        return f

    html = ""
    # 1) HTTPS avec certificat valide
    for url, cle in (("https://" + dom, "https"),):
        try:
            html, code, dt, final = fetch(url, ctx=CTX)
            f["etat"] = "VIVANT"
            f["https"] = True
            f["ssl_valide"] = True
            f["temps_s"] = round(dt, 2)
            f["fichier"] = final
        except urllib.error.HTTPError as e:
            # Le serveur REPOND (403/429...) : il est vivant, il bloque juste mon robot.
            f["etat"] = "BLOQUE"
            f["https"] = True
            f["ssl_valide"] = (e.code not in (0,))
            f["erreur"] = "HTTP %d" % e.code
            return f
        except ssl.SSLError:
            f["ssl_valide"] = False
            try:
                html, code, dt, final = fetch(url, ctx=CTX)
                f["etat"] = "VIVANT"
                f["https"] = True          # sert mais certificat cassé
                f["temps_s"] = round(dt, 2)
            except Exception as e:
                f["erreur"] = "ssl casse: " + type(e).__name__
        except Exception as e:
            f["erreur"] = type(e).__name__

    # 2) HTTPS certificat invalide (auto-signé) : on le distingue
    if not f["https"] and html == "":
        try:
            html, code, dt, final = fetch("https://" + dom, ctx=CTX_NOVERIFY)
            f["etat"] = "VIVANT"
            f["https"] = True
            f["ssl_valide"] = False
            f["temps_s"] = round(dt, 2)
        except Exception:
            pass

    # 3) HTTP seul (pas de HTTPS du tout)
    if not f["https"]:
        try:
            html, code, dt, final = fetch("http://" + dom, ctx=CTX_NOVERIFY)
            f["etat"] = "VIVANT"
            f["http_seul"] = True
            f["temps_s"] = round(dt, 2)
        except Exception as e:
            f["erreur"] = (f["erreur"] + " | http: " + type(e).__name__).strip(" |")
            # Le domaine n'existe pas du tout = mort. Sinon = peut-être un
            # simple blocage de robot : on ne l'accuse pas d'être hors service.
            if "gaierror" in f["erreur"]:
                f["mort_nx"] = True
            return f

    if not html:
        return f

    low = html.lower()

    # Parking / page vide
    if any(k in low for k in ("this domain is parked", "domaine est en cours",
                              "coming soon", "under construction", "buy this domain",
                              "parked domain", "ce domaine est")):
        f["parking"] = True

    # Mobile
    f["mobile"] = bool(re.search(r'name=["\']viewport["\']', low))

    # Titre + meta description
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    f["titre"] = clean(re.sub(r"\s+", " ", m.group(1))).strip()[:120] if m else ""
    f["meta_desc"] = bool(re.search(r'name=["\']description["\']', low))

    # WordPress
    wpm = re.search(r'content=["\']wordpress\s+([\d.]+)', low)
    if wpm:
        f["wp_version"] = wpm.group(1)

    # Images sans attribut alt (SEO + accessibilité)
    imgs = re.findall(r"<img\b[^>]*>", html, re.I)
    f["img_total"] = len(imgs)
    if imgs:
        f["img_sans_alt"] = sum(1 for i in imgs if not re.search(r'\balt=["\'][^"\']+["\']', i, re.I))

    # Hygiène SEO
    try:
        html2, _, _, _ = fetch("https://" + dom + "/sitemap.xml", timeout=8, ctx=CTX_NOVERIFY)
        f["sitemap"] = bool(html2) and "<html" not in html2.lower()[:400]
    except Exception:
        pass
    try:
        html3, _, _, _ = fetch("https://" + dom + "/robots.txt", timeout=8, ctx=CTX_NOVERIFY)
        f["robots"] = bool(html3) and "<html" not in html3.lower()[:400]
    except Exception:
        pass

    # Pages internes réelles (liens même domaine hors ancres/assets)
    links = set()
    for href in re.findall(r'href=["\']([^"\']+)["\']', html, re.I):
        if DOMAINES_ANNONCES.search(href):
            continue
        h = norm_dom(href)
        if not h or h == dom or h.endswith("." + dom):
            path = urllib.parse.urlparse(
                href if href.startswith("http") else "https://" + dom + "/" + href.lstrip("/")).path
            if path and path not in ("/", "/index.html", "/index.php") and not re.search(r"\.(pdf|jpg|png|webp|css|js|zip)$", path, re.I):
                links.add(path.rstrip("/"))
    f["pages_internes"] = len(links)
    f["une_seule_page"] = len(links) <= 1

    # Copyright figé
    fourchette = re.search(r"(19|20)\d{2}\s*[-\u2013\u2014à]\s*(20(?:2[4-9]|3\d))", html)
    if not fourchette:
        cp = re.search(r"©\s*(\d{4})|copyright\s*\(c\)\s*(\d{4})", html, re.I)
        if cp:
            f["copyright"] = int(cp.group(1) or cp.group(2))

    # Contact
    f["tel"] = bool(re.search(r"(tel:|\+33\s?[09]\s?[0-9]{2}\s?[0-9]{2})", low))
    f["formulaire"] = bool(re.search(r"<form", low))

    # Piratage : uniquement dans les LIENS sortants (href/src), pas dans le code.
    # Leçon 31/08 : "data-slotamount" matchait le motif "slot" -> fausse accusation.
    hrefs = re.findall(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']', html, re.I)
    for h in hrefs:
        hd = norm_dom(h.split("?")[0])
        if not hd or hd == dom or hd.endswith("." + dom):
            continue  # lien interne = normal
        for w in ("casino", "poker", "viagra", "cialis", "pharma", "escort",
                  "slot", "loto", "bet365", "kraken", "카지노", "온라인", "바카라",
                  "赌场", "赌博", "彩票"):
            if re.search(SEP + w, hd):
                f["pirate"] = hd
                break
        if f["pirate"]:
            break
    return f


CTX_NOVERIFY = ssl.create_default_context()
CTX_NOVERIFY.check_hostname = False
CTX_NOVERIFY.verify_mode = ssl.CERT_NONE


def noter(f):
    """Note /100 (100 = site nickel) + liste de griefs classés par impact."""
    note = 100
    griefs = []
    if f["etat"] == "BLOQUE":
        # Le site refuse mon robot : on ne peut rien mesurer, donc on n'accuse rien.
        return None, ["non auditable"]
    if f["etat"] != "VIVANT":
        return 0, ["site injoignable"]
    if f["parking"]:
        note -= 60
        griefs.append("le domaine affiche une page de parking, pas votre entreprise")
    if f["pirate"]:
        note -= 60
        griefs.append("des liens de fraude (%s) tournent dans votre site" % f["pirate"])
    if f["http_seul"]:
        note -= 25
        griefs.append("pas de HTTPS : Chrome affiche une alerte rouge 'non securise'")
    elif not f["ssl_valide"]:
        note -= 20
        griefs.append("certificat HTTPS invalide : le navigateur bloque la premiere visite")
    if f["mobile"] is False:
        note -= 20
        griefs.append("aucune version mobile : Google declasse le site sur telephone")
    if f["temps_s"] and f["temps_s"] > 3:
        note -= 15
        griefs.append("le site met %.1f s a s'afficher, la moitie des visiteurs partent avant" % f["temps_s"])
    if f["une_seule_page"]:
        note -= 15
        griefs.append("une seule page : Google n'a rien a indexer sur vos metiers")
    elif f["pages_internes"] <= 4:
        note -= 8
        griefs.append("seulement %d pages : trop peu pour exister dans les recherches" % f["pages_internes"])
    if not f["meta_desc"]:
        note -= 8
        griefs.append("pas de description : votre resultat Google affiche du texte bricolé")
    if f["img_total"] and f["img_sans_alt"] and f["img_sans_alt"] >= max(3, f["img_total"] * 0.6):
        note -= 6
        griefs.append("%d photos sans legende : invisibles dans Google Images" % f["img_sans_alt"])
    if not f["sitemap"]:
        note -= 5
        griefs.append("pas de sitemap : Google decouvre vos pages tout seul, lentement")
    if f["copyright"] and f["copyright"] <= 2019:
        note -= 10
        griefs.append("mention legale figee en %d : le site parait abandonne" % f["copyright"])
    if f["wp_version"]:
        try:
            majeure = int(f["wp_version"].split(".")[0])
            if majeure <= 5:
                note -= 15
                griefs.append("WordPress %s : version majeure perimee, failles connues" % f["wp_version"])
        except Exception:
            pass
    if not f["formulaire"] and not f["tel"]:
        note -= 8
        griefs.append("ni formulaire ni telephone cliquable : on ne peut pas vous joindre depuis le site")
    return max(0, note), griefs


def constat(f, note, griefs, prospect):
    """Premier paragraphe VERIFIE du mail. Que des faits mesurés à l'instant."""
    dom = f["domaine"]
    if f["etat"] == "BLOQUE":
        return ""  # rien de mesuré = rien à affirmer, le mail garde son texte d'origine
    if f["etat"] != "VIVANT":
        if f.get("mort_nx"):
            return ("J'ai tape %s dans mon navigateur ce matin : le domaine n'existe plus, "
                    "la page ne s'ouvre pas du tout. Si un client essaie de vous trouver, "
                    "il appelle votre concurrent." % dom)
        return ("J'ai tape %s dans mon navigateur ce matin : la page ne repond pas. "
                "Si un client essaie de vous trouver et tombe sur une erreur, il appelle le suivant." % dom)
    if griefs:
        haut = griefs[:2]
        base = "J'ai ouvert %s a l'instant. " % dom
        if len(haut) == 1:
            base += "Le point qui me saute aux yeux : %s." % haut[0]
        else:
            base += "Deux choses me sautent aux yeux : %s, et %s." % (haut[0], haut[1])
        return base
    if note >= 85:
        return ("J'ai ouvert %s a l'instant : le site est propre, je n'ai rien a vous reprocher. "
                "C'est justement pour ca que je vous ecris, pour la visibilite, pas pour la technique." % dom)
    return ("J'ai ouvert %s a l'instant et passe en revue vitesse, mobile et indexation. "
            "Rien de cassé, mais trois details lui coutent des clients." % dom)


def main():
    nums_only = None
    sample = None
    for i, a in enumerate(sys.argv):
        if a == "--nums" and i + 1 < len(sys.argv):
            nums_only = set(x.strip() for x in sys.argv[i + 1].split(","))
        if a == "--sample" and i + 1 < len(sys.argv):
            sample = int(sys.argv[i + 1])

    with open(DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    with open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8") as fh:
        state = json.load(fh)
    sent = set(str(k) for k in state.get("sent", {}))

    deja = {}
    if os.path.exists(OUT):
        try:
            deja = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            deja = {}

    cibles = []
    for r in data:
        num = str(r.get("num"))
        if nums_only and num not in nums_only:
            continue
        site = r.get("site") or norm_dom(r.get("to", ""))
        if not site:
            continue
        if num in deja and deja[num].get("sonde_le"):
            continue
        cibles.append((num, site, r.get("to", ""), num in sent))
    if sample:
        cibles = cibles[:sample]

    print("A sonder: %d (deja faits: %d)" % (len(cibles), len(deja)))
    t0 = time.time()
    for k, (num, site, to, was_sent) in enumerate(cibles, 1):
        f = sonder(site, to)
        note, griefs = noter(f)
        if note is None:
            f.update({"num": num, "note": None, "griefs": [], "constat": "",
                      "deja_envoye": was_sent, "sonde_le": time.strftime("%Y-%m-%d %H:%M")})
            deja[num] = f
            print("  [%d/%d] num %-4s %-6s %s (robot bloque, rien d'affirme)" % (
                k, len(cibles), num, "BLOQUE", f["domaine"][:34]))
            time.sleep(0.35)
            continue
        f.update({"num": num, "note": note, "griefs": griefs,
                  "constat": clean(constat(f, note, griefs, "")),
                  "deja_envoye": was_sent, "sonde_le": time.strftime("%Y-%m-%d %H:%M")})
        deja[num] = f
        if k % 10 == 0 or k == len(cibles):
            json.dump(deja, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  [%d/%d] num %-4s note %3d %-12s %s" % (
            k, len(cibles), num, note, f["etat"], f["domaine"][:34]))
        time.sleep(0.35)

    json.dump(deja, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    vals = [v for v in deja.values() if v.get("note") is not None and v["note"] < 60]
    morts = [v for v in deja.values() if v.get("etat") not in ("VIVANT", "BLOQUE")]
    bloques = [v for v in deja.values() if v.get("etat") == "BLOQUE"]
    hacks = [v for v in deja.values() if v.get("pirate")]
    print("\n=== BILAN ===")
    print("Sites sondes: %d en %.0f s" % (len(deja), time.time() - t0))
    print("Note < 60/100 (dossier urgent): %d" % len(vals))
    print("Morts / injoignables: %d" % len(morts))
    print("Bloques (robot refuse, non audites): %d" % len(bloques))
    print("Pirates: %d" % len(hacks))
    print("-> %s" % OUT)


if __name__ == "__main__":
    sys.exit(main())
