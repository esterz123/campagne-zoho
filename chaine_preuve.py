#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHAINE PREUVE - un seul bouton pour garder toute la file en mails à preuve.
===========================================================================
Enchaîne (tout est idempotent et incrémental) :
 1. verificateur_site.py   : sonde les sites jamais audités (saute les acquis)
 2. injecteur_preuves.py   : remplace l'accusation générique par le constat mesuré
                             + réécrit l'objet sur le fait le plus fort
 3. sequencage_constats.py : régénère les relances J+3/J+7 à partir des nouveaux corps
 4. validateur_mail.py     : contrôle R1-R6 (tirets, U+2019, portfolio, personnalisation)
Sortie : rapport court. Exit 1 si violation bloquante -> ne pas push.
Usage : python3 chaine_preuve.py [--skip-scan]
"""
import os
import sys
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(args, label):
    print("\n=== %s ===" % label)
    r = subprocess.run([PY] + args, cwd=BASE, capture_output=True, text=True, timeout=3600)
    out = (r.stdout or "") + (r.stderr or "")
    tail = "\n".join(out.strip().splitlines()[-12:])
    print(tail)
    return r.returncode, out


def main():
    skip_scan = "--skip-scan" in sys.argv
    if not skip_scan:
        rc, _ = run(["verificateur_site.py"], "1/4 SONDE LES SITES NON AUDITES")
        if rc not in (0,):
            print("scan en erreur, on continue avec ce qui existe")
    rc, _ = run(["injecteur_preuves.py"], "2/4 INJECTE LES CONSTATS MESURES")
    if rc != 0:
        return 1
    run(["generateur_rapports.py"], "2bis RAPPORTS DOCX PRE-GENERES (promesse 'deja fait' = vraie)")
    run(["sequencage_constats.py", "--apply"], "3/4 REGENERE LES RELANCES")
    rc, _ = run(["validateur_mail.py"], "4/4 VALIDE LES REGLES D'OR")
    print("\nCHAINE PREUVE TERMINEE" + (" - VIOLATIONS BLOQUANTES, NE PAS PUSH" if rc else " - PRET AU PUSH"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
