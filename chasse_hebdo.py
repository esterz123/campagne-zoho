#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHASSE HEBDOMADAIRE AUTONOME (Levier B) : remplit le stock automatiquement.
Orchestre : Exa (trouve sites PME FR) -> extract_seq (emails HTML) -> Apify JS (emails masques)
-> integre dans campagne_data.json (V3, anti-doublon). 100% gratuit, tourne sur le PC.
Usage: python3 chasse_hebdo.py"""
import os, sys, json, subprocess, datetime, glob

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "chasse_hebdo.log")
PY = sys.executable

def log(msg):
    line = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with open(LOG, "a", encoding="utf-8") as f: f.write(line+"\n")
    except Exception: pass
    print(line)

QUERIES = (
    "serrurerie metalerie France | chaudronnerie entreprise France | usinage mecanique precision France "
    "| tôlerie industrielle France | décolletage France | plomberie chauffage entreprise France "
    "| électricité artisan France | menuiserie agence France | couverture zinguerie France "
    "| maçonnerie entreprise France | emboutissage tôlerie France | injection plastique sous-traitant "
    "| fonderie alu France | traitement surface industrie France | maintenance industrielle France "
    "| plasturgie France | outillage France | metallerie France"
)

def run(script, *args, timeout=560):
    full = [PY, os.path.join(BASE, script)] + list(args)
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, cwd=BASE)
    tail = (r.stdout + "\n" + r.stderr).strip()
    return r.returncode, tail[-1200:]

def main():
    log("=== CHASSE HEBDOMADAIRE ===")

    # 1. Exa : collecte candidats + extraction emails HTML
    log("Phase 1 - exa_bulk (collecte + extraction)")
    code, out = run("exa_bulk.py", QUERIES, "_hebdo_exa.json", "4", timeout=550)
    log(out)

    # 2. extract_seq : extraction robuste sur candidats
    log("Phase 2 - extract_seq (emails profonds)")
    code2, out2 = run("extract_seq.py", "0", "600", timeout=550)
    log(out2)

    # 3. Apify JS : emails masques (optionnel, si APIFY_TOKEN)
    apify_out = ""
    if os.path.exists(os.path.join(BASE, "apify_contact_onerun.py")):
        log("Phase 3 - Apify contact-info-scraper (emails JS)")
        env = dict(os.environ)
        env.setdefault("APIFY_TOKEN","apify_api_2znUUXJQKjxgbdfZTOmw2lsfMCvoM54eENBM")
        try:
            r3 = subprocess.run([PY, os.path.join(BASE, "apify_contact_onerun.py")],
                                capture_output=True, text=True, timeout=550, cwd=BASE, env=env)
            apify_out = (r3.stdout or "") + "\n" + (r3.stderr or "")
            log(apify_out[-800:])
        except Exception as e:
            log("Apify err: "+str(e)[:120])

    # 4. Integrer TOUT (Exa + extract + Apify) en V3 + anti-doublon
    log("Phase 4 - integration")
    added = 0
    for src, f in [("exa_bulk","_exa_bulk_leads.json"),
                   ("apify_contact","_apify_pro_leads.json")]:
        p = os.path.join(BASE, f)
        if os.path.exists(p):
            try:
                leads = json.load(open(p, encoding="utf-8"))
            except Exception:
                continue
            n = integrer(BASE, leads)
            added += n
            log(f"  integre {n} depuis {f}")
    log(f"=== CHASSE TERMINEE : +{added} prospects ===")

def integrer(BASE, leads):
    """Integre une liste de {domaine,email} dans campagne_data.json (V3, anti-doublon)."""
    DATA = os.path.join(BASE, "campagne_data.json")
    data = json.load(open(DATA, encoding="utf-8"))
    file_emails = {(e.get("to") or "").lower() for e in data}
    file_noms = {e.get("nom","").lower() for e in data}
    next_num = max((e.get("num",0) for e in data), default=0) + 1
    GEN = ("gmail.com","live.fr","orange.fr","free.fr","aol.com","yahoo.fr","yahoo.com",
           "hotmail.fr","hotmail.com","wanadoo.fr","outlook.fr","outlook.com","laposte.net",
           "sfr.fr","icloud.com","gmx.fr","protonmail.com")
    added = 0
    for x in leads:
        dom = (x.get("domaine") or "").strip().lower()
        em = (x.get("email") or "").strip().lower()
        if not em or not dom: continue
        if em in file_emails: continue
        if dom.endswith(".cc") or dom.endswith(".tk"): continue
        if any(em.endswith(g) for g in GEN): continue
        if "domaine.com" in em or "utilisateur@" in em: continue
        nom = dom.split(".")[0].replace("-"," ").title()
        if nom.lower() in file_noms: continue
        msg = ("Bonjour,\n\n"
            "Votre site %s n'apparait pas quand un donneur d'ordres cherche du travail de precision sur Google. "
            "Vos concurrents qui ont refait leur site il y a 2 ans sont devant vous sur ces requetes : "
            "c'est eux qui prennent les appels, pas vous.\n\n"
            "Je ne vous vends rien ici. Je regarde votre site 2 minutes et je vous dis exactement ce que "
            "vos prospects fuient (vitesse, mobile, confiance). C'est gratuit, sans engagement.\n\n"
            "Repondez simplement \"oui\" a ce mail et je vous envoie mes constats sous 48h.\n\n"
            "Cordialement,\nMahdi\nPortfolio : mahdi-design.com" % dom)
        data.append({"num":next_num,"nom":nom,"to":em,"prenom":"","siren":"",
            "site":"https://"+dom,"activite":"industrielle","dirigeant":"",
            "subject":"Votre site %s : diagnostic offert" % dom,"body":msg,"source":"moulin"})
        next_num += 1; added += 1; file_emails.add(em)
    json.dump(data, open(DATA,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    return added

if __name__ == "__main__":
    main()
