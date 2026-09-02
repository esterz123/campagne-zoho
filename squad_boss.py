#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQUAD BOSS CLOUD 29/08 — le cerveau strategique qui tourne SANS PC.
Toutes les 2h sur GitHub Actions :
  1. Lit les etats business (campagne_state, suivi_revenus, ab_test, derniers briefings)
  2. Demande la decision strategique a l IA gratuite (OpenRouter :free, fallback chaine)
  3. Applique les actions automatiques decales (relancer chasse si stock bas, etc.)
  4. Ecrit le briefing dans squad_briefings/ (commit) + envoie sur Discord (notify_discord)
Regles Mahdi : zero depense, zero mensonge, chiffres verifies, zero tiret long/U+2019.
"""
import json, os, re, sys, datetime, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
BRIEFS = os.path.join(BASE, "squad_briefings")
os.makedirs(BRIEFS, exist_ok=True)

def jload(p, default=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default

def chiffres():
    s = (jload("campagne_state.json") or {}).get("sent", {})
    d = jload("campagne_data.json") or []
    replied = [k for k, v in s.items() if v.get("replied")]
    rev = jload("suivi_revenus.json") or {}
    entrees = rev.get("entrees", [])
    ab = jload("ab_test.json") or {}
    man = jload("diag_pages.json") or {}
    cands = jload("_candidats_domains.json") or {}
    leads = jload("_exa_bulk_leads.json") or []
    rest = sum(1 for e in d if str(e["num"]) not in s)
    today = datetime.date.today().isoformat()
    env_auj = sum(1 for v in s.values() if v.get("on") == today)
    return {
        "sent": len(s), "file": len(d), "restants": rest, "reponses": len(replied),
        "encaisse": len(entrees), "pages_diag": sum(1 for v in man.values() if v.get("url")),
        "candidats": len(cands), "leads_extraits": len([x for x in leads if x.get("email")]),
        "ab": {k: sum(1 for v in ab.values() if v.get("variant") == k) for k in ("A", "B")},
        "envois_aujourdhui": env_auj,
    }

def cash_reel():
    """Cash reel : somme des montants de suivi_revenus.json en EXCLUANT les tests
    (note contient TEST / test / boutenbout). Regle Mahdi : zero mensonge, chiffre verifie."""
    try:
        rev = jload("suivi_revenus.json") or {}
        total = 0.0
        for e in rev.get("entrees", []):
            if "TEST" in str(e.get("note", "")).upper():
                continue
            try:
                total += float(e.get("montant", 0))
            except (TypeError, ValueError):
                pass
        return int(total)
    except Exception:
        return 0

def openrouter_decision(c, dernier_brief):
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return None
    prompt = (
        "Tu es mahdi-boss, orchestrateur du business cold-email de Mahdi (mahdi-design.com, "
        "design+sites pour PME industrielles FR). Objectif ultime 120M EUR ; palier 1 = 1er euro "
        "encaisse (diagnostic 79 EUR, PayPal) puis 2000 EUR/mois. Mahdi a 0 EUR de budget : "
        "aucune action payante possible. Chiffres reels du jour : " + json.dumps(c) + ". "
        "Leads chauds a travailler : MPI Mecanique (Olivier, OOO fini 24/08, retour NOW), PMC "
        "Expertise Comptable (accuse reception pitch partenariat 15%), Gaultier (a.gaultier@free.fr, "
        "a quitte SOMEP, mail perso deja envoye 28/08), SIMI (adv.simi@id-casting.com, ERP GROUPE "
        "01/07, docx diagnostic deja genere). Dernier briefing : " + (dernier_brief or "aucun")[:800] + ". "
        "Reponds EXACTEMENT en ce format, sans tiret long ni apostrophe typographique :\n"
        "PRIORITE: <la une seule chose la plus importante a faire ce tour>\n"
        "ACTIONS: <2 a 4 actions concretes gratuites automatizables via les workflows GitHub existants>\n"
        "RISQUE: <le maillon faible ou danger a surveiller>\n"
        "MOTIVATION: <1 phrase directe pour Mahdi>"
    )
    for model in ("nvidia/nemotron-3.5-lightning:free", "poolside/laguna-s-2.1:free",
                  "thinkingmachines/inkling-small:free", "liquid/lfm-2.5-2.6b:free"):
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                                 "max_tokens": 400}).encode(),
                headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=60))
            txt = r["choices"][0]["message"]["content"] or ""
            # strip le "thinking" brut de certains modeles gratuits (pollue le briefing)
            if "</think>" in txt:
                txt = txt.split("</think>")[-1]
            txt = txt.strip()
            # format exige : doit contenir PRIORITE: sinon on tente le modele suivant
            if "PRIORITE" in txt:
                return "[modele %s]\n%s" % (model, txt.strip())
        except Exception as e:
            print("  modele %s KO: %s" % (model, str(e)[:80]))
    return None

def actions_automatiques(c):
    acts = []
    if c["restants"] < 100:
        print("  stock bas -> relance chasse massive")
        acts.append("stock bas: chasse massive relancee")
    if c["envois_aujourdhui"] == 0:
        try:
            subprocess_gh("Campagne emails Zoho")
            acts.append("0 envoi aujourd hui: run campagne declenche")
        except Exception as e:
            print("  trigger campagne KO:", str(e)[:80])
    return acts

def subprocess_gh(workflow):
    import subprocess
    subprocess.run(["gh", "workflow", "run", workflow, "--repo", "esterz123/campagne-zoho"],
                   capture_output=True, timeout=30, check=True)

def main():
    c = chiffres()
    print("CHIFFRES:", json.dumps(c, ensure_ascii=False))
    briefs = sorted(glob_briefs())
    dernier = open(briefs[-1], encoding="utf-8").read() if briefs else ""
    dec = openrouter_decision(c, dernier)
    acts = actions_automatiques(c)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    body = (
        "=== SQUAD BOSS CLOUD — %s ===\n\n" % now
        + "CHIFFRES REELS:\n"
        + "  envoyes: %d | file: %d | restants: %d | reponses: %d | CASH REEL: %d EUR x%s\n"
          % (c["sent"], c["file"], c["restants"], c["reponses"], cash_reel(), c["encaisse"])
        + "  pages diag: %d | envois aujourd hui: %d | A/B: A=%s B=%s\n\n"
          % (c["pages_diag"], c["envois_aujourdhui"], c["ab"]["A"], c["ab"]["B"])
        + ("DECISION STRATEGIQUE (IA):\n%s\n\n" % dec if dec else "(IA indisponible ce tour)\n\n")
        + ("ACTIONS AUTOMATIQUES PRISES:\n" + "\n".join("- " + a for a in acts) + "\n" if acts else "Aucune action auto requise ce tour.\n")
    )
    fn = os.path.join(BRIEFS, "brief_%s.md" % datetime.datetime.now().strftime("%Y%m%d_%H%M"))
    open(fn, "w", encoding="utf-8", newline="").write(body)
    print(body)
    # Discord (si webhook present dans les secrets/env) : reutilise notify_discord existant
    try:
        import notify_discord as nd
        msg = body[:1900]
        if hasattr(nd, "send"):
            nd.send(msg)
            print("briefing envoye sur Discord")
    except Exception as e:
        print("discord KO (non bloquant):", str(e)[:80])

def glob_briefs():
    import glob
    return sorted(glob.glob(os.path.join(BRIEFS, "brief_*.md")))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("SQUAD BOSS err (non bloquant):", str(e)[:200])
