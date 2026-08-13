#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VISION SITE — analyse le visuel reel d'un site avant d'ecrire un email.
=====================================================================
Pourquoi : l'audit par le code (WordPress vieux, jQuery...) ne prouve PAS
la laideur visuelle. Un site peut etre vétuste en code et beau au visuel.
La regle (decision Mahdi 2026-08) : verifier le VISUEL de chaque prospect
avec un modele vision AVANT d'ecrire l'email.

Pipeline :
  1. Screenshot du site avec Chrome headless (1280x900)
  2. Envoi de l'image a Qwen3-VL-32B via Nous Portal (coût ~0.0002 $/site
     = negligeable, qualite maximale) OU modele :free si disponible
  3. Retourne des CONSTATS VISUELS concrets (design date, couleurs,
     typo, hierarchie, professionalisme) + un verdict 1-5

Modele vision (decision boss 2026-08) :
  - qwen/qwen3-vl-32b-instruct via Nous Portal : le meilleur juge design
    (valide 2026-08, detaille precisement pourquoi un site est moche)
  - Coût reel : ~0.0002 $/screenshot (500 sites = 10 centimes)
  - Le modele local minicpm-v:8b est TROP INDULGENT -> ne pas utiliser

Usage :
  python3 vision_site.py https://example.com
  python3 vision_site.py https://example.com --json   # sortie JSON
"""
import base64, json, os, subprocess, sys, tempfile, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Modele vision via Nous Portal (endpoint OpenAI-compatible)
VISION_MODEL = "qwen/qwen3-vl-32b-instruct"

PROMPT_VISION = (
    "Tu es un directeur artistique senior. Analyse cette capture d'ecran d'un "
    "site web d'entreprise. Reponds en francais, concret, sans jargon inutile. "
    "Structure ta reponse en 3 parties :\n"
    "1. CONSTATS VISUELS : ce que tu vois reellement (design date ou moderne, "
    "couleurs, typographie, hierarchie, photos, espacement, professionalisme).\n"
    "2. PROBLEMES : les 2-3 defauts visuels les plus visibles qui nuisent a la "
    "credibilite (ex: logo pixelise, texte illisible, couleurs criardes, page "
    "vide, mise en page annee 2000, pas de coherence).\n"
    "3. VERDICT : note de 1 a 5 (1 = tres moche, 3 = moyen, 5 = tres beau) "
    "sur une ligne au format 'VERDICT: X/5'.\n"
    "Sois honnete et precis. Si le site est beau, dis-le (ne pas inventer de "
    "defauts). Ne reponds rien d'autre."
)


def charger_token():
    """Token Portal : env PORTAL_API_KEY (cloud) ou .ia_tokens.json (local)."""
    key = os.environ.get("PORTAL_API_KEY")
    if key:
        return key
    with open(os.path.join(BASE, ".ia_tokens.json"), encoding="utf-8") as f:
        return json.load(f)["portal"]


def screenshot(url, chemin=None):
    """Screenshot Chrome headless. Retourne le chemin du PNG."""
    if not os.path.exists(CHROME):
        raise RuntimeError("Chrome introuvable: " + CHROME)
    if not chemin:
        fd, chemin = tempfile.mkstemp(prefix="site_", suffix=".png")
        os.close(fd)
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
           "--hide-scrollbars", "--window-size=1280,900",
           "--screenshot=" + chemin, "--timeout=20000", url]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    if not os.path.exists(chemin) or os.path.getsize(chemin) < 1000:
        raise RuntimeError("Screenshot vide (site injoignable ou bloque)")
    return chemin


def analyser_image(token, chemin_png):
    """Envoie l'image a Qwen3-VL-32B (Nous Portal). Retourne le texte d'analyse."""
    with open(chemin_png, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = {
        "model": VISION_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT_VISION},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "max_tokens": 600,
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        "https://inference-api.nousresearch.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        j = json.loads(r.read().decode())
    msg = j["choices"][0]["message"]
    return (msg.get("content") or msg.get("reasoning") or "").strip()


def parser_verdict(analyse):
    """Extrait la note X/5 de l'analyse. Retourne (note, texte)."""
    import re
    m = re.search(r"VERDICT\s*:\s*(\d)/5", analyse)
    note = int(m.group(1)) if m else None
    return note, analyse


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 vision_site.py <url> [--json]")
        return 1
    url = args[0]
    as_json = "--json" in args

    token = charger_token()
    try:
        png = screenshot(url)
        analyse = analyser_image(token, png)
        note, texte = parser_verdict(analyse)
        try:
            os.remove(png)
        except Exception:
            pass
        if as_json:
            print(json.dumps({"url": url, "note": note, "analyse": texte},
                             ensure_ascii=False, indent=1))
        else:
            print("URL:", url)
            print("NOTE:", note, "/5" if note else "")
            print(texte)
        return 0
    except Exception as e:
        print("ERREUR vision_site:", str(e)[:200], file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
