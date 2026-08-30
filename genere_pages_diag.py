#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GENERE PAGES DIAG WEB 28/08 (Pareto: valeur dans le 1er email).
Pour chaque prospect non envoye: scan rapide du site + page HTML personnalisee
dans le repo vitrine -> https://mahdi-design.com/diag/<num>.html
Le 1er email de ce prospect recoit un P.S. avec le lien (voir campagne_zoho.py).
Usage: python genere_pages_diag.py <nb_prospects>
Regles Mahdi: zero tiret long (— –), zero apostrophe typographique (U+2019)."""
import json, os, re, sys, time, random, datetime, urllib.request, ssl

BASE = os.path.dirname(os.path.abspath(__file__))
VITRINE = os.path.normpath(os.path.join(BASE, "..", "vitrine"))
DIAG_DIR = os.path.join(VITRINE, "diag")
MANIFEST = os.path.join(BASE, "diag_pages.json")
DATA = os.path.join(BASE, "campagne_data.json")
STATE = os.path.join(BASE, "campagne_state.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def fetch(url, timeout=8):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            body = r.read(400000).decode("utf-8", "ignore")
            return time.time() - t0, r.getcode(), body
    except Exception:
        return time.time() - t0, None, ""

def scan(site):
    """Scan express -> liste de constats (status, texte) + score 0-100."""
    dom = site.replace("https://", "").replace("http://", "").strip("/")
    t_https, code, html = fetch("https://" + dom)
    if not code:
        t_http, code, html = fetch("http://" + dom)
    if not code:
        return None, [], 0
    low = html.lower()
    constats = []
    score = 100
    # 1. mobile viewport
    if "viewport" not in low:
        constats.append(("warn", "Pas de mise en page mobile : sur un telephone, votre site est illisible ou casse. Un acheteur industriel qui vous decouvre depuis son portable passe son chemin."))
        score -= 30
    else:
        constats.append(("ok", "La mise en page mobile est geree : bon point, vos concurrents ne l'ont pas tous."))
    # 2. titre
    m = re.search(r"<title[^>]*>(.{0,120}?)</title>", low, re.S)
    titre = m.group(1).strip() if m else ""
    if not titre:
        constats.append(("warn", "Le titre de la page est vide ou absent : Google ne sait pas quoi afficher, et votre prospect non plus."))
        score -= 20
    elif len(titre) > 65:
        constats.append(("warn", "Le titre de la page depasse 65 caracteres : Google le coupe, votre message principal est perdu."))
        score -= 8
    else:
        constats.append(("ok", "Le titre de la page est propre et lisible."))
    # 3. vitesse
    vitesse = t_https if t_https else t_http
    if vitesse > 4:
        constats.append(("warn", "Le site met %.1f secondes a s'afficher : au dela de 3 secondes, plus d'un visiteur sur deux quitte avant de vous voir." % vitesse))
        score -= 25
    else:
        constats.append(("ok", "Le site s'affiche en moins de 3 secondes : correct."))
    # 4. copyright date
    annees = [int(a) for a in re.findall(r"(?:©|&copy;|copyright)[^0-9]{0,30}(20[0-2][0-9])", low)]
    if annees and max(annees) < datetime.date.today().year - 1:
        constats.append(("warn", "Le pied de page affiche %d : un site qui semble abandonne fait fuir un donneur d'ordres qui compare 3 prestataires." % max(annees)))
        score -= 12
    # 5. plateforme
    plats = {"oxatis": "Oxatis (technologie en fin de vie, tables HTML)", "wix": "Wix", "joomla": "Joomla",
             "wordpress": "WordPress", "prestashop": "PrestaShop", "e-monsite": "e-monsite"}
    plat = next((v for k, v in plats.items() if k in low), None)
    if plat and "oxatis" in plat.lower():
        constats.append(("warn", "Votre site repose sur %s : mise en page en tables HTML, technologie que les sites concurrents recents ont abandonnee." % plat))
        score -= 15
    # 6. email visible
    if not re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", low):
        constats.append(("warn", "Aucune adresse email visible sur la page d'accueil : un acheteur presse repart sans vous contacter."))
        score -= 10
    return dom, constats, max(20, min(100, score))

def page_html(num, nom, dom, constats, score):
    rows = ""
    for st, txt in constats:
        if st == "ok":
            icon, col = "&#10003;", "#0a7d32"
        else:
            icon, col = "&#9888;", "#b45309"
        rows += ('<div style="display:flex;gap:14px;margin:0 0 18px 0;">'
                 '<div style="flex:0 0 34px;height:34px;border-radius:50%%;background:%s;color:#fff;'
                 'text-align:center;line-height:34px;font-weight:bold;">%s</div>'
                 '<div style="flex:1;color:#1f2937;font-size:16px;line-height:1.55;">%s</div></div>' % (col, icon, txt))
    html = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diagnostic express - {dom}</title></head>
<body style="margin:0;background:#f6f7f9;font-family:Arial,Helvetica,sans-serif;">
<div style="max-width:680px;margin:0 auto;padding:28px 20px 40px 20px;">
<div style="background:#111827;color:#fff;border-radius:12px;padding:22px 24px;">
<div style="font-size:13px;letter-spacing:1px;color:#9ca3af;">DIAGNOSTIC EXPRESS · OFFERT</div>
<div style="font-size:22px;font-weight:bold;margin-top:6px;">{nom}</div>
<div style="font-size:14px;color:#9ca3af;margin-top:2px;">{dom}</div>
<div style="margin-top:14px;font-size:15px;">Score express de confiance : <b style="font-size:20px;">{score}/100</b></div>
</div>
<div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:22px 24px;margin-top:16px;">
{rows}
</div>
<div style="background:#eef4ff;border:1px solid #c7d7f5;border-radius:12px;padding:20px 24px;margin-top:16px;">
<div style="font-weight:bold;color:#1e3a8a;font-size:17px;">La suite, si vous la voulez</div>
<div style="color:#1f2937;font-size:15px;line-height:1.6;margin-top:8px;">
Je prepare gratuitement la version complete : votre site compare a 2 concurrents directs
et le plan d'action chiffre en euros. Vous le gardez, que nous travaillions ensemble ou non.
Repondez simplement <b>"oui"</b> a l'email qui vous a conduit ici.</div>
</div>
<div style="color:#6b7280;font-size:13px;margin-top:18px;line-height:1.6;">
<div style="margin-top:22px;background:#f0fdf4;border:2px solid #16a34a;border-radius:12px;padding:18px;">
<div style="font-weight:bold;color:#14532d;font-size:17px;">Version complete du diagnostic : 79 EUR</div>
<div style="color:#1f2937;font-size:15px;line-height:1.6;margin-top:6px;">
Votre site compare a 2 concurrents directs, le plan d'action chiffre en euros, et la liste exacte des corrections a faire.
Livraison immediate apres paiement, sans rendez-vous, sans appel.</div>
<a href="https://www.paypal.com/ncp/payment/FQYKP733699LQ" style="display:inline-block;margin-top:14px;background:#16a34a;color:#ffffff;font-weight:bold;font-size:16px;padding:14px 26px;border-radius:10px;text-decoration:none;">
Payer 79 EUR et recevoir ma version complete</a>
<div style="color:#6b7280;font-size:13px;margin-top:10px;">Paiement securise PayPal. Vous pouvez aussi repondre "oui" a l'email pour la version gratuite.</div>
</div>
Mahdi · Designer de marque pour PME industrielles<br>
<a href="https://mahdi-design.com" style="color:#2563eb;">mahdi-design.com</a> · contact@mahdi-design.com
</div>
</div></body></html>"""
    return html.format(dom=dom, nom=nom, score=score, rows=rows)

def main():
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    data = json.load(open(DATA, encoding="utf-8"))
    sent = json.load(open(STATE, encoding="utf-8"))["sent"]
    man = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
    os.makedirs(DIAG_DIR, exist_ok=True)
    fait = 0
    for e in sorted(data, key=lambda x: int(x["num"])):
        if fait >= nb: break
        num = str(e["num"])
        if num in sent or num in man: continue
        site = (e.get("site") or "").strip()
        if not site: continue
        dom, constats, score = scan(site)
        if not dom:
            man[num] = {"url": None, "note": "site injoignable"}
            json.dump(man, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("  -", num, "injoignable", flush=True)
            time.sleep(0.4 + random.random() * 0.4)
            continue
        nom = e.get("prospect") or dom.split(".")[0].title()
        fn = os.path.join(DIAG_DIR, "%s.html" % num)
        open(fn, "w", encoding="utf-8", newline="").write(page_html(num, nom, dom, constats, score))
        man[num] = {"url": "https://mahdi-design.com/diag/%s.html" % num, "score": score}
        json.dump(man, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  +", num, dom, "score", score, flush=True)
        fait += 1
        time.sleep(0.4 + random.random() * 0.5)
    print("PAGES GENEREES:", fait, "| manifest:", sum(1 for v in man.values() if v.get("url")))

if __name__ == "__main__":
    main()
