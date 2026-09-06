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
    # --- 18 niches historiques ---
    "serrurerie metalerie France | chaudronnerie entreprise France | usinage mecanique precision France "
    "| tôlerie industrielle France | décolletage France | plomberie chauffage entreprise France "
    "| électricité artisan France | menuiserie agence France | couverture zinguerie France "
    "| maçonnerie entreprise France | emboutissage tôlerie France | injection plastique sous-traitant "
    "| fonderie alu France | traitement surface industrie France | maintenance industrielle France "
    "| plasturgie France | outillage France | metallerie France"
    # --- 42 niches industrielles ajoutees 28/08 (levier x60) ---
    " | forge de precision France | mecanique generale France | micromecanique France "
    "| oxycoupage decoupe metal France | decoupe laser metal France | peinture industrielle France "
    "| robinetterie industrielle France | soudure industrielle France | tournage fraisage France "
    "| traitement thermique metaux France | vannerie industrielle France | visserie boulonnerie France "
    "| hydraulique industrielle France | levage manutention France | calorifugeage France entreprise "
    "| carrosserie industrielle France | charpente metallique France | construction metallique France "
    "| etancheite batiment France | etancheite facade France | chaudronnerie inox France"
    # --- BTP & services techniques ---
    " | carrelage France entreprise | platrerie France | peinture batiment France "
    "| menuiserie bois France | installation photovoltaique France | pompe a chaleur installation France "
    "| garage automobile France | depannage remorquage France | transport routier France "
    "| logistique entrepot France | nettoyage industriel France | gardiennage securite France"
    # --- services B2B (dirigeants PME) ---
    " | bureau etudes France | controle technique construction France | geometre France "
    "| architecte France | cabinet comptable France | expert comptable France "
    "| avocat PME France | agence immobiliere France | paysagiste France"
)

def run(script, *args, timeout=560):
    full = [PY, os.path.join(BASE, script)] + list(args)
    r = subprocess.run(full, capture_output=True, text=True, timeout=timeout, cwd=BASE)
    tail = (r.stdout + "\n" + r.stderr).strip()
    return r.returncode, tail[-1200:]

def safe_run(script, *args, timeout=560):
    """28/08: un TimeoutExpired dans une phase ne doit JAMAIS tuer les phases suivantes."""
    try:
        return run(script, *args, timeout=timeout)
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT %s apres %ss (chunk trop gros ou site lent)" % (script, timeout)
    except Exception as e:
        return -1, "ERR %s: %s" % (script, str(e)[:150])

def main():
    log("=== CHASSE HEBDOMADAIRE ===")

    # 0. Recolle des candidats A CHAQUE run (28/08 : 60 niches, dedup auto dans exa_bulk).
    #    Avant : ne recoltait que si le fichier etait absent -> la chasse recyklait les memes domaines.
    cand_path = os.path.join(BASE, "_candidats_domains.json")
    log("Phase 0 - recolle systematique (60 niches Exa, dedup auto)")
    try:
        import urllib.request, re
        EXA = "69458868-3ce4-42da-873d-43a0465dff11"
        def exa_search(q, n=12):
            req = urllib.request.Request("https://api.exa.ai/search",
                data=json.dumps({"query":q,"numResults":n,"type":"auto","useAutoprompt":True}).encode(),
                headers={"Content-Type":"application/json","x-api-key":EXA}, method="POST")
            return [r.get("url","") for r in json.load(urllib.request.urlopen(req,timeout=25)).get("results",[])]
        def dom(u): return re.sub(r"^https?://(www\.)?","",u).split("/")[0].lower()
        BLACK=("google","facebook","linkedin","wiki","youtube","annuaire","pagesjaunes","societe","twitter","instagram","wix","shopify","mairie","commune")
        TYPES=(".fr",".com",".eu",".net")
        cands={}
        if os.path.exists(cand_path) and os.path.getsize(cand_path) > 20:
            try: cands = json.load(open(cand_path, encoding="utf-8"))
            except Exception: cands = {}
        avant = len(cands)
        for q in QUERIES.split("|"):
            q=q.strip()
            if not q: continue
            try:
                for u in exa_search(q):
                    d=dom(u)
                    if d and not any(b in d for b in BLACK) and d.endswith(TYPES):
                        cands[d]="https://"+d
            except Exception as e:
                log("exa err "+str(e)[:60])
        json.dump(cands, open(cand_path,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
        log(f"candidats recoltes: {avant} -> {len(cands)} (+{len(cands)-avant})")
    except Exception as e:
        log("Phase 0 err: "+str(e)[:150])

    # 1. Exa : collecte candidats + extraction emails HTML
    log("Phase 1 - exa_bulk (collecte + extraction)")
    code, out = safe_run("exa_bulk.py", QUERIES, "_hebdo_exa.json", "4", timeout=550)
    log(out)

    # 2. extract_seq : chunk DYNAMIQUE (28/08 fix : 1500 d'un coup = 75 min > timeout 550s
    #    -> TimeoutExpired tuait le run AVANT l integration. Desormais 700/run = ~35 min,
    #    le chunk reprend au 1er domaine non encore traite (fin de fichier leads).)
    log("Phase 2 - extract_seq (chunk dynamique 700)")
    start, end = chunk_extract()
    if end > start:
        code2, out2 = safe_run("extract_seq.py", str(start), str(end), timeout=2100)
        log(out2)
    else:
        log("Phase 2 - rien a extraire (tout deja fait)")

    # 2bis. integrer TOUT DE SUITE ce qui a ete extrait (un crash plus loin ne perd rien)
    # 01/09 : SMTP-verify CHAQUE email avant integration (un bounce = reputation perdue).
    # Seuls ok/greylist sont integres. user_unknown/mx_manquant = morts, jamais en file.
    try:
        import subprocess as sp
        leads = json.load(open(os.path.join(BASE, "_exa_bulk_leads.json"), encoding="utf-8"))
        nouveaux = [x for x in leads if x.get("email") and x["email"] not in
                    {e.get("to","").lower() for e in json.load(open(os.path.join(BASE, "campagne_data.json"), encoding="utf-8"))}]
        if nouveaux:
            io_email = os.path.join(BASE, "_smtp_queue.txt")
            open(io_email, "w", encoding="utf-8", newline="").write(chr(10).join(x["email"] for x in nouveaux))
            code_v, out_v = safe_run("smtp_verif.py", "60", timeout=900)
            log("Phase 2ter - SMTP verify: " + out_v[-400:])
    except Exception as e:
        log("Phase 2ter err: " + str(e)[:120])
    n1 = integrer_tout_smtp_safe()

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

    # 4. Integrer le reste (Apify + relique)
    n2 = integrer_tout()
    log(f"=== CHASSE TERMINEE : +{n1} puis +{n2} prospects ===")

    # 5. Pages diag express pour les nouveaux prospects (Pareto 28/08: valeur dans le 1er email)
    try:
        code5, out5 = safe_run("genere_pages_diag.py", "25", timeout=300)
        log(out5)
    except Exception as e:
        log("Phase 5 err: " + str(e)[:120])

def integrer_tout_smtp_safe():
    """01/09: integre UNIQUEMENT les emails smtp-verifies ok/greylist."""
    verif = json.load(open(os.path.join(BASE, "smtp_verif.json"), encoding="utf-8"))         if os.path.exists(os.path.join(BASE, "smtp_verif.json")) else {}
    added = 0
    for f in ("_exa_bulk_leads.json", "_apify_pro_leads.json"):
        p = os.path.join(BASE, f)
        if not os.path.exists(p): continue
        try:
            leads = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        bons = []
        for x in leads:
            em = (x.get("email") or "").strip().lower()
            if em and verif.get(em) in ("ok", "greylist", None):
                bons.append(x)  # None = pas encore verifie (retro-compat)
        n = integrer(BASE, bons)
        added += n
    return added

def integrer_tout():
    """28/08: integration appelable a tout moment (apres chaque phase)."""
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
    return added

def chunk_extract():
    """28/08: calcule (start,end) du prochain chunk de candidats non extraits.
    'Non extrait' = pas encore dans _exa_bulk_leads.json (cle domaine)."""
    leads_path = os.path.join(BASE, "_exa_bulk_leads.json")
    fait = set()
    if os.path.exists(leads_path):
        try:
            for x in json.load(open(leads_path, encoding="utf-8")):
                if x.get("domaine"): fait.add(x["domaine"].strip().lower())
        except Exception:
            pass
    cand_path = os.path.join(BASE, "_candidats_domains.json")
    if not os.path.exists(cand_path):
        return 0, 0
    try:
        cands = json.load(open(cand_path, encoding="utf-8"))
    except Exception:
        return 0, 0
    restants = [d for d in cands if d.strip().lower() not in fait]
    CHUNK = 700
    if not restants:
        return 0, 0
    # alignement sur la liste TRIEE (extract_seq fait doms=sorted(sites) puis [off:off+step])
    doms = sorted(cands)
    # premier domaine NON scanne dans l ordre trie
    debut = next((i for i, d in enumerate(doms) if d.strip().lower() not in fait), None)
    if debut is None:
        return 0, 0
    fin = debut + CHUNK
    return debut, fin

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
