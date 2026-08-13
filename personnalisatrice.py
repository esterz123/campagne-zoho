#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PERSONNALISATRICE — réécrit chaque email de la file pour chaque prospect.
====================================================================
Le principe (décision Mahdi) :
  - Chaque prospect recoit un email qui parle de SON metier, SON site,
    SON probleme reel (pas un email generique).
  - L'IA ne fait QUE ecrire du texte : elle ne decide jamais d'un envoi.
  - Le Controleur final (verrou) valide avant tout envoi (deja en place).
  - REGLE D'OR : jamais de tiret « — » ni « – » (virgules/points).

Utilisation :
  python3 personnalisatrice.py --dry-run        # reecrit, ne modifie RIEN (affiche)
  python3 personnalisatrice.py --num 7          # reecrit uniquement le prospect #7
  python3 personnalisatrice.py --apply          # reecrit et ENREGISTRE dans campagne_data.json
  python3 personnalisatrice.py --all            # idem --apply mais pour tous les restants

Securite :
  - Garde-fou : uniquement modeles :free (cascade infinie Portal->Mistral->Groq->OpenRouter)
  - Si l'IA echoue sur un email, on garde l'email actuel (jamais d'email vide).
  - On ne touche JAMAIS aux emails deja envoyes (nums dans campagne_state.json).
"""
import json, os, sys, re, time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import moteur_ia as M

DATA_F = os.path.join(BASE, "campagne_data.json")
STATE_F = os.path.join(BASE, "campagne_state.json")

# REGLES DE STYLE (non negociables)
INTERDITS = ["—", "–", "–", " - ", "\u2014"]
MAX_LONGUEUR = 1900          # garde le corps raisonnable

SYSTEME = (
    "Tu es Mahdi, brand designer specialise dans les PME industrielles francaises. "
    "Tu ecris des emails de prospection B2B courts, directs, respectueux, en francais. "
    "IMPORTANT : utilise uniquement des virgules et des points, JAMAIS de tiret long (— ou –) "
    "ni de double espace. Pas d'emojis. Ton : professionnel, concret, sans jargon. "
    "Tu parles du prospect a la 2e personne (vous). Tu ne promets JAMAIS de prix. "
    "Tu proposes un diagnostic gratuit de 30 minutes, sans engagement."
)

def charger():
    with open(DATA_F, encoding="utf-8") as f:
        return json.load(f)

def charger_envoyes():
    try:
        with open(STATE_F, encoding="utf-8") as f:
            return set(str(k) for k in json.load(f).get("sent", {}).keys())
    except Exception:
        return set()

def valider_texte(texte):
    """Retourne (ok, raison). Verifie les regles non negociables."""
    if not texte or len(texte.strip()) < 60:
        return False, "trop court"
    if len(texte) > MAX_LONGUEUR:
        return False, "trop long (%d chars)" % len(texte)
    for c in INTERDITS:
        if c in texte:
            return False, "tiret interdit '%s'" % c
    if "  " in texte:
        return False, "double espace"
    return True, "ok"

def construire_prompt(prospect):
    """Construit le prompt de personnalisation a partir des infos du prospect."""
    info = {
        "prospect": prospect.get("prospect", ""),
        "to": prospect.get("to", ""),
        "sujet_actuel": prospect.get("subject", ""),
        "corps_actuel": prospect.get("body", "")[:1200],
    }
    return (
        "Voici le prospect : %(prospect)s\n"
        "Adresse : %(to)s\n"
        "Sujet actuel : %(sujet_actuel)s\n"
        "Email actuel :\n%(corps_actuel)s\n\n"
        "Reecris cet email pour qu'il soit PERSONNALISE pour ce prospect precis : "
        "un sujet accrocheur (1 phrase, sans tiret) et un corps qui parle de SON "
        "activite, de SON site, de SON probleme concret. Reste sur les constats "
        "verifiables de l'email actuel (ne invente pas de nouveaux faits). "
        "Garde la structure : sujet sur la premiere ligne (prefixe 'SUJET: '), "
        "puis une ligne vide, puis le corps. "
        "Reponds UNIQUEMENT avec le nouvel email, rien d'autre. "
        "Virgules et points uniquement, aucun tiret long."
    ) % info

def parser_reponse(rep):
    """Separe sujet et corps depuis la reponse IA. Retourne (sujet, corps) ou None."""
    rep = rep.strip()
    lignes = rep.split("\n")
    sujet = None
    corps_lignes = []
    for i, l in enumerate(lignes):
        if l.lower().startswith("sujet:"):
            sujet = l.split(":", 1)[1].strip()
            corps_lignes = lignes[i + 1:]
            break
    if not sujet:
        # fallback : la 1re ligne courte = sujet
        for l in lignes:
            if l.strip() and len(l.strip()) < 100 and "http" not in l:
                sujet = l.strip()
                corps_lignes = lignes[1:]
                break
    if not sujet:
        return None
    corps = "\n".join(x for x in corps_lignes if x.strip()).strip()
    return sujet, corps

def personnaliser(prospect, max_secondes=120):
    """Reecrit un email. Retourne (sujet, corps) ou None si echec."""
    prompt = construire_prompt(prospect)
    try:
        rep = M.repondre(prompt, usage="ecriture", systeme=SYSTEME,
                         max_tokens=700, max_secondes=max_secondes, silencieux=True)
    except Exception as e:
        sys.stderr.write("ERREUR IA pour %s : %s\n" % (prospect.get("num"), str(e)[:100]))
        return None
    parsed = parser_reponse(rep)
    if not parsed:
        sys.stderr.write("PARSING KO pour #%s (reponse illisible)\n" % prospect.get("num"))
        return None
    sujet, corps = parsed
    ok_s, rs = valider_texte(sujet)
    ok_c, rc = valider_texte(corps)
    if not (ok_s and ok_c):
        sys.stderr.write("VALIDEUR KO #%s : sujet=%s corps=%s\n"
                         % (prospect.get("num"), rs, rc))
        return None
    return sujet, corps

def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    apply = ("--apply" in args or "--all" in args)
    num_only = None
    for a in args:
        if a.startswith("--num"):
            i = args.index(a)
            if i + 1 < len(args):
                num_only = str(args[i + 1])

    data = charger()
    envoyes = charger_envoyes()
    cibles = [e for e in data if str(e.get("num")) not in envoyes]
    if num_only:
        cibles = [e for e in cibles if str(e.get("num")) == num_only]
        if not cibles:
            print("Aucun prospect restant avec num=%s (ou deja envoye)." % num_only)
            return 1

    print("Personnalisation de %d email(s) restant(s)..." % len(cibles))
    modifs = 0
    for i, e in enumerate(cibles, 1):
        num = str(e.get("num"))
        print("[%d/%d] #%s %s" % (i, len(cibles), num, e.get("prospect", "")[:45]))
        res = personnaliser(e)
        if not res:
            print("  -> conserve l'email actuel (echec IA ou validation)")
            continue
        sujet, corps = res
        print("  SUJET: %s" % sujet[:90])
        if dry:
            print("  CORPS: %s..." % corps[:150].replace("\n", " "))
        else:
            e["subject"] = sujet
            e["body"] = corps
            modifs += 1
        time.sleep(1)  # espace les requetes (anti-ban)

    if apply and modifs:
        with open(DATA_F, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("\n%d email(s) mis a jour dans campagne_data.json (non pousse, a committer)." % modifs)
    elif dry:
        print("\nMode dry-run : rien n'a ete modifie.")
    else:
        print("\nAucune modification.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
