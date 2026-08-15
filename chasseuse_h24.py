#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHASSEUSE H24 — trouve + VERIFIE + REDIGE + AJOUTE des prospects, en continu.
============================================================================
Le module ① du systeme Mahdi Design. Tourne dans GitHub Actions plusieurs
fois par jour (PC eteint ou pas), en plus de la chasse du workflow campagne.

Pipeline (chaque fiche doit passer TOUTES les barrières) :
  1. API officielle recherche-entreprises.api.gouv.fr (gratuite, sans cle)
     -> candidats PME industrielles (NAF cible, 10-249 salaries, actives)
  2. Site web trouve (DuckDuckGo/Bing, filtre anti-annuaires)
  3. Analyse de vetuste (WordPress/jQuery/SSL/copyright/mobile)
  4. Email de contact trouve sur LE site officiel (jamais devine)
  5. VERROU INFAILLIBLE : domaine de l'email = domaine du site officiel
     + domaine pas dans domaines_bloques.json + pas deja dans la file
  6. REDACTION : l'email personnalise est ecrit par le moteur IA (gratuit)
     + valideur (0 tiret, longueur, virgules/points)
  7. AJOUT a campagne_data.json (num suivant) — l'envoi reste controle
     par campagne_zoho.py (3/jour, verrou anti-erreur)

Regles non negociables :
  - JAMAIS d'email devine (prenom.nom@ a l'aveugle)
  - JAMAIS d'email dont le domaine != site officiel
  - L'IA ne decide RIEN : elle ecrit le texte, le code verifie tout
  - 0 euro : uniquement modeles :free (moteur_ia)

Usage :
  python3 chasseuse_h24.py --dry-run --max 3   # affiche, ne modifie rien
  python3 chasseuse_h24.py --max 3             # ajoute jusqu'a 3 fiches validees
  python3 chasseuse_h24.py --max 5 --force     # ignore le quota journalier
"""
import json, os, re, sys, time, random, urllib.parse, urllib.request
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import moteur_ia as M
from chasseur_prospects import (api_candidats, find_site, analyze,
                                find_email, fetch, SCORE_MIN)

DATA_F = os.path.join(BASE, "campagne_data.json")
BLOQUEES_F = os.path.join(BASE, "domaines_bloques.json")
QUOTA_F = os.path.join(BASE, "chasseuse_quota.json")

MAX_PAR_RUN = 3            # fiches ajoutees max par run (qualite > volume)
MAX_PAR_JOUR = 6           # quota journalier (anti-spam, anti-blocage)
TEMP_EMAILS = ("gmail.com", "orange.fr", "free.fr", "yahoo.fr", "hotmail.fr",
               "laposte.net", "numericable.fr", "wanadoo.fr", "outlook.fr",
               "gmx.fr", "protonmail.com")

def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

def verrou_email(email, site, bloquees, deja_emails):
    """LA REGLE INFAILLIBLE. Retourne (ok, raison)."""
    e = (email or "").strip().lower()
    if not e or "@" not in e:
        return False, "email vide"
    domaine = e.split("@")[1]
    if domaine in TEMP_EMAILS:
        return False, "email gratuit (%s)" % domaine
    if any(b in domaine for b in bloquees):
        return False, "domaine bloque (%s)" % domaine
    if e in deja_emails:
        return False, "deja dans la file"
    # LE domaine de l'email DOIT etre le domaine du site officiel
    site_dom = (site or "").lower().replace("www.", "").split("/")[0]
    if not site_dom:
        return False, "pas de site"
    if domaine != site_dom and not domaine.endswith("." + site_dom):
        return False, "domaine email != site (%s vs %s)" % (domaine, site_dom)
    return True, "ok"

A_REVOIR_F = os.path.join(BASE, "a_revoir.json")

def hold_fiche(cand, site, email, constats, score, raison):
    """Candidat douteux -> a_revoir.json (revue humaine au retour), JAMAIS envoye tel quel."""
    rev = load_json(A_REVOIR_F, [])
    rev.append({"date": date.today().isoformat(), "raison": raison,
                "nom": cand.get("nom"), "siren": cand.get("siren"),
                "ville": cand.get("ville"), "site": site, "email": email,
                "constats": constats, "score": score})
    save_json(A_REVOIR_F, rev)

def dirigeant_fiche(siren):
    """Nom du dirigeant reel via API officielle (gratuite), remontee de chaine holding (max 3).
    Retourne (nom, tranche_effectif, statut). Lecons 15/08 : SAS -> holding -> personne physique.
    Priorite : President > Gerant > DG ; un CAC seul ne compte JAMAIS comme dirigeant."""
    def fetch_siren(s):
        url = 'https://recherche-entreprises.api.gouv.fr/search?q=%s&per_page=1' % urllib.parse.quote(str(s))
        with urllib.request.urlopen(url, timeout=25) as r:
            j = json.loads(r.read().decode('utf-8'))
        return next((x for x in j.get('results', []) if x.get('siren') == str(s)), {})
    def prio(d):
        q = d.get('qualite') or ''
        if 'Président' in q or 'President' in q:
            return 0
        if 'Gérant' in q or 'Gerant' in q:
            return 1
        if 'Directeur Général' in q or 'Directeur General' in q:
            return 2
        return 3
    try:
        res = fetch_siren(siren)
        if not res:
            return None, '', 'INTROUVABLE'
        tranche = res.get('tranche_effectif_salarie') or ''
        courant = str(siren)
        for _ in range(3):
            res2 = fetch_siren(courant)
            dirs = res2.get('dirigeants', [])
            phys = [d for d in dirs if d.get('type_dirigeant') == 'personne physique']
            morales = [d for d in dirs if d.get('type_dirigeant') == 'personne morale']
            phys.sort(key=prio)
            morales.sort(key=lambda d: 0 if ('Président' in (d.get('qualite') or '') or 'President' in (d.get('qualite') or '')) else 1)
            reel = [d for d in phys if prio(d) < 3]
            if reel:
                d = reel[0]
                nom = ((d.get('prenoms') or '') + ' ' + (d.get('nom') or '')).strip()
                return nom, tranche, 'OK'
            # pas de dirigeant physique reel : remonter la holding president
            if morales and morales[0].get('siren'):
                courant = morales[0]['siren']
                continue
            if phys:
                # personne physique non dirigeante (CAC) : statut special, JAMAIS envoye tel quel
                d = phys[0]
                nom = ((d.get('prenoms') or '') + ' ' + (d.get('nom') or '')).strip()
                return nom, tranche, 'CAC_SEUL'
            return None, tranche, 'SANS_DIRIGEANT'
        return None, tranche, 'HOLDING_TROP_PROFONDE'
    except Exception as e:
        return None, '', 'API_ERREUR:%s' % str(e)[:50]

def effectif_cible(tranche):
    """Cible 10-50 salaries. Inconnu -> A_REVOIR. Hors cible -> NON."""
    if not tranche or tranche in ('NN', '?'):
        return 'A_REVOIR'
    if re.search(r'à 9 salariés|50 à|100 à|200 à|250 à|300 à|500 à|1000', tranche):
        return 'NON'
    return 'OK'

# Codes NAF du canal TECH (zone de confort Mahdi : branding startup/SaaS)
NAF_TECH = ("5829C", "6201Z", "6202A", "6312Z", "4791B", "7410Z")

def secteur_fiche(fiche):
    """Retourne 'tech' si l'activite est du numerique/design, sinon 'industrie'."""
    naf = (fiche.get("naf") or "").strip()
    if naf in NAF_TECH:
        return "tech"
    return "industrie"

def rediger_email(fiche, max_secondes=120):
    """Ecris l'email personnalise avec le moteur IA gratuit.
    Le message s'adapte au secteur : branding/logo pour la tech,
    diagnostic site pour l'industrie."""
    secteur = secteur_fiche(fiche)
    constats = ", ".join(fiche.get("constats", [])) or "un site qui merite une mise a jour"
    if secteur == "tech":
        systeme = (
            "Tu es Mahdi, brand designer senior specialise dans les startups et les SaaS "
            "technologiques (identites visuelles, logos, direction artistique, 6 ans "
            "d'experience). Tu ecris un email de prospection B2B court, direct, respectueux, "
            "en francais. IMPORTANT : uniquement des virgules et des points, JAMAIS de tiret "
            "long (— ou –), pas de double espace, pas d'emojis. Tu parles comme un designer "
            "qui comprend la tech. Tu proposes une identite visuelle ou un logo, sans jamais "
            "donner de prix dans l'email."
        )
        prompt = (
            "Entreprise : %(nom)s (%(ville)s, %(region)s)\n"
            "Activite : %(naf)s\n"
            "Site : %(site)s\n"
            "Constats verifies sur le site : %(constats)s\n\n"
            "Ecris un email de prospection personnalise pour le fondateur ou le dirigeant de "
            "cette entreprise tech. Structure : premiere ligne 'SUJET: ' + un sujet accrocheur "
            "(1 phrase, sans tiret), puis une ligne vide, puis le corps. "
            "Le corps doit montrer que tu comprends SON produit et SON marche (tech/SaaS), "
            "mentionner un ou deux constats concrets du site ci-dessus, et proposer une "
            "identite visuelle ou un rafraichissement de marque, avec une simple reponse "
            "pour en discuter. Ne invente aucun autre fait. Reponds UNIQUEMENT avec l'email."
        ) % {**fiche, "constats": constats}
    else:
        systeme = (
            "Tu es Mahdi, brand designer specialise dans les PME industrielles francaises. "
            "Tu ecris un email de prospection B2B court, direct, respectueux, en francais. "
            "IMPORTANT : uniquement des virgules et des points, JAMAIS de tiret long (— ou –), "
            "pas de double espace, pas d'emojis. Tu proposes un diagnostic gratuit de 30 minutes, "
            "sans engagement, sans jamais promettre de prix."
        )
        prompt = (
            "Entreprise : %(nom)s (%(ville)s, %(region)s)\n"
            "Activite : %(naf)s\n"
            "Site : %(site)s\n"
            "Dirigeant : %(dirigeant)s\n"
            "Constats verifies sur le site : %(constats)s\n\n"
            "Ecris un email de prospection personnalise pour %(dirigeant)s. "
            "STRUCTURE OBLIGATOIRE : premiere ligne 'SUJET: ' + un sujet accrocheur (1 phrase, sans tiret), "
            "puis une ligne vide, puis le corps. "
            "Le corps DOIT commencer par 'Bonjour M. NOM,' ou 'Bonjour Mme NOM,' (le nom de famille du "
            "dirigeant en majuscules) et DOIT se terminer par 'Cordialement,' puis 'Mahdi' puis "
            "'Portfolio : mahdi-design.com' sur sa propre ligne. "
            "Le corps doit mentionner concretement un ou deux des constats listes ci-dessus, "
            "proposer un diagnostic gratuit de 30 minutes, et demander une simple reponse. "
            "Ne invente aucun autre fait. Reponds UNIQUEMENT avec l'email."
        ) % {**fiche, "constats": constats}
    try:
        rep = M.repondre(prompt, usage="ecriture", systeme=systeme,
                         max_tokens=700, max_secondes=max_secondes, silencieux=True)
    except Exception as e:
        return None
    # Parser sujet/corps (meme logique que personnalisatrice)
    lignes = rep.strip().split("\n")
    sujet = None
    for i, l in enumerate(lignes):
        if l.lower().startswith("sujet:"):
            sujet = l.split(":", 1)[1].strip()
            corps = "\n".join(x for x in lignes[i + 1:] if x.strip()).strip()
            break
    if not sujet:
        return None
    if any(c in sujet + corps for c in ("—", "–")) or len(corps) < 80:
        return None
    # Revue automatique du corps (lecons 15/08) : salutation + signature obligatoires
    nom_famille = (fiche.get("dirigeant") or "").strip().split()[-1].upper()
    if nom_famille and not re.search(r"^Bonjour (M\.|Mme) %s[,.]" % re.escape(nom_famille), corps, re.M):
        corps = re.sub(r"^Bonjour[^,\n]*,\s*\n?", "", corps, count=1)
        corps = "Bonjour M. %s,\n\n%s" % (nom_famille, corps.lstrip())
    if "Portfolio : mahdi-design.com" not in corps:
        corps = corps.rstrip() + "\n\nCordialement,\nMahdi\nPortfolio : mahdi-design.com"
    return sujet, corps

def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    force = "--force" in args
    max_run = MAX_PAR_RUN
    for a in args:
        if a.startswith("--max"):
            i = args.index(a)
            if i + 1 < len(args):
                max_run = int(args[i + 1])

    data = load_json(DATA_F, [])
    bloquees = load_json(BLOQUEES_F, [])
    deja_emails = {str(e.get("to", "")).strip().lower() for e in data if e.get("to")}
    deja_sirens = {str(e.get("siren", "")).strip() for e in data if e.get("siren")}

    # Quota journalier (sauf --force)
    quota = load_json(QUOTA_F, {})
    today = date.today().isoformat()
    if not force and quota.get("date") == today and quota.get("ajoutes", 0) >= MAX_PAR_JOUR:
        print("Quota journalier atteint (%d). Rien a faire." % quota.get("ajoutes"))
        return 0

    print("=== CHASSEUSE H24 — %s (%s) ===" % (today, "DRY-RUN" if dry else "APPLY"))
    candidats = api_candidats()
    print("Candidats API : %d" % len(candidats))
    random.shuffle(candidats)  # varie d'un run a l'autre

    ajoutes, fiches_ok = 0, []
    for cand in candidats:
        if ajoutes >= max_run:
            break
        if str(cand.get("siren", "")) in deja_sirens:
            continue
        print("\n--- %s (%s) ---" % (cand.get("nom", "?"), cand.get("ville", "?")))
        site = find_site(cand.get("nom", ""), cand.get("ville", ""))
        time.sleep(1)
        if not site:
            print("  pas de site trouve, skip")
            continue
        html = fetch("https://www.%s/" % site) or fetch("http://%s/" % site)
        if not html:
            print("  site injoignable, skip")
            continue
        constats, score = analyze(html)
        if score < SCORE_MIN:
            print("  score %d < seuil, skip (%s)" % (score, constats[:50]))
            continue
        emails = find_email(site)
        if not emails:
            print("  aucun email sur le site officiel, skip (jamais devine)")
            continue
        email = emails[0]
        ok, raison = verrou_email(email, site, bloquees, deja_emails)
        if not ok:
            print("  VERROU: %s, skip" % raison)
            continue
        # REVUE AUTOMATIQUE (lecons 15/08) : dirigeant reel + effectif cible AVANT redaction
        nom_dir, tranche, st = dirigeant_fiche(cand.get("siren", ""))
        eff = effectif_cible(tranche)
        if eff == 'NON':
            print("  effectif hors cible (%s) -> skip" % tranche)
            continue
        if st != 'OK' or eff == 'A_REVOIR':
            print("  dirigeant %s / effectif %s -> A REVOIR (jamais envoye sans nom)" % (st, tranche))
            hold_fiche(cand, site, email, constats, score, 'dirigeant:%s effectif:%s' % (st, tranche))
            continue
        fiche = dict(cand)
        fiche.update({"site": site, "email": email, "constats": constats,
                      "score": score, "date": today, "dirigeant": nom_dir})
        # REDACTION de l'email (IA gratuite)
        res = rediger_email(fiche)
        if not res:
            print("  redaction KO (IA ou valideur), skip")
            continue
        sujet, corps = res
        # Gardes de contenu (lecons 15/08) : zero prix, zero caractere interdit
        if any(x in sujet + corps for x in ('2900', '3900', '79 EUR', '79 €', '1 900')):
            print("  prix dans le 1er contact -> A REVOIR")
            hold_fiche(cand, site, email, constats, score, 'prix dans corps')
            continue
        if '\u2019' in corps or '\u2014' in corps or '\u2013' in corps:
            corps = corps.replace('\u2019', "'").replace('\u2014', ',').replace('\u2013', ',')
        nom_famille = nom_dir.strip().split()[-1].upper()
        if not re.search(r'^Bonjour (M\.|Mme) %s[,.]' % re.escape(nom_famille), corps, re.M):
            print("  greeting invalide -> A REVOIR")
            hold_fiche(cand, site, email, constats, score, 'greeting:%s' % nom_famille)
            continue
        num = str(max([int(e.get("num", 0)) for e in data] + [0]) + 1)
        entry = {
            "num": num,
            "prospect": "%s — %s" % (num, cand.get("nom", "")),
            "to": email,
            "cc": "",
            "subject": sujet,
            "body": corps,
            "to_confirmed": True,
            "dirigeant": nom_dir,
            "siren": cand.get("siren", ""),
            "site": site,
        }
        print("  ✅ VALIDE + REDIGE #%s -> %s" % (num, email))
        print("  SUJET: %s" % sujet[:90])
        if not dry:
            data.append(entry)
            deja_emails.add(email)
            deja_sirens.add(str(cand.get("siren", "")))
            ajoutes += 1
        else:
            ajoutes += 1
        fiches_ok.append(entry)
        time.sleep(1)

    if dry:
        print("\nDRY-RUN : %d fiche(s) pretes a ajouter, rien modifie." % ajoutes)
        return 0

    if ajoutes:
        save_json(DATA_F, data)
        quota = {"date": today, "ajoutes": quota.get("ajoutes", 0) + ajoutes}
        save_json(QUOTA_F, quota)
        print("\n%d fiche(s) AJOUTEE(S) a la file (total: %d). "
              "Quota du jour: %d/%d" % (ajoutes, len(data), quota["ajoutes"], MAX_PAR_JOUR))
    else:
        print("\nAucune fiche ajoutee ce run.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
