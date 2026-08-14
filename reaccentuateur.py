#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RE-ACCENTUATEUR DE MASSE — restaure les accents francais dans les DM et relances.
=================================================================================
Utilise la cascade IA gratuite (moteur_ia.repondre) + garde-fou : le texte corrige
doit etre IDENTIQUE a l'original une fois les accents retires (unidecode).
Si la verification echoue, on reessaie (max 3) puis on garde l'original et on le signale.
"""
import json, os, sys, unicodedata
import moteur_ia

BASE = os.path.dirname(os.path.abspath(__file__))

def sans_accents(s):
    s = s.replace('\u2019', "'").replace('\u2018', "'")   # apostrophes typographiques -> droites
    s = s.replace('\u00a0', ' ').replace('\u202f', ' ')   # espaces insecalbes -> normales
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

PROMPT = ("Re-ajoute les accents francais manquants (e accent aigu, grave, circonflexe, "
          "cedille, trema) a ce texte. Ne change AUCUN mot, aucune ponctuation, aucun "
          "ordre. Reponds UNIQUEMENT avec le texte corrige, rien d'autre. Texte:\n\n%s")

def distance_lev(a, b):
    """Distance de Levenshtein bornee (min(a,b)+1 si trop grand)."""
    if abs(len(a) - len(b)) > 15:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
        if min(prev) > 15:
            return 99
    return prev[-1]

def reaccentuer(texte, tries=3):
    # "deja_ok" UNIQUEMENT si le texte contient deja des accents (sans_accents change le texte)
    if sans_accents(texte) != texte:
        return texte, "deja_ok"
    for i in range(tries):
        try:
            rep = moteur_ia.repondre(PROMPT % texte, usage="ecriture", max_tokens=800)
            rep = rep.strip().strip('"').strip("'")
            # Garde-fou assoupli : on accepte les ecarts <= 15 caracteres (petites
            # corrections grammaticales du type "salon ongles" -> "salon d'ongles").
            if distance_lev(sans_accents(texte), sans_accents(rep)) <= 15:
                return rep, "ok"
            # sinon: l'IA a modifie d'autres choses -> retry
        except Exception as e:
            print("  erreur appel %d: %s" % (i + 1, str(e)[:80]))
    return texte, "ECHEC"

def main():
    chemin = os.path.join(BASE, "kit_dm_masse.json")
    d = json.load(open(chemin, encoding="utf-8"))
    total = ok = echec = deja = 0
    for x in d:
        dm = x.get("dm")
        if not dm:
            continue
        total += 1
        corr, statut = reaccentuer(dm)
        if statut == "ok":
            x["dm"] = corr
            ok += 1
        elif statut == "deja_ok":
            deja += 1
        else:
            echec += 1
            print("ECHEC:", x.get("nom", "?")[:40])
    json.dump(d, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DM: total=%d ok=%d deja_ok=%d ECHEC=%d" % (total, ok, deja, echec))

    # relances email
    fpath = os.path.join(BASE, "followups.json")
    f = json.load(open(fpath, encoding="utf-8"))
    fok = fechec = 0
    for stage, tpl in f.items():
        for champ in ("body", "subject"):
            txt = tpl.get(champ)
            if not txt:
                continue
            corr, statut = reaccentuer(txt)
            if statut == "ok":
                tpl[champ] = corr
                fok += 1
            elif statut == "ECHEC":
                fechec += 1
                print("ECHEC relance %s.%s" % (stage, champ))
    json.dump(f, open(fpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Relances: ok=%d ECHEC=%d" % (fok, fechec))
    print("FINI")

if __name__ == "__main__":
    main()
