#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST CAMPAGNE v1 — pre-flight avant CHAQUE run d'envoi (16/08).
========================================================================
Verifie les invariants critiques AVANT d'envoyer. Si un test echoue,
le workflow s'arrete (exit 1) et AUCUN email ne part : mieux vaut zero
envoi qu un envoi casse.

Usage : python3 test_campagne.py   (exit 0 = OK, exit 1 = BLOQUANT)

Verifie :
  1. campagne_zoho.py compile
  2. _norm_addr decode l'encodage HTML de l'API (cause racine doublons)
  3. verifier_doublon_global existe et est branche (2 appels)
  4. save_state est appele apres chaque envoi (2 points)
  5. PAUSE_ENVOIS : si present, signaler PAUSE (exit 0, pas d envoi prevu)
  6. le fichier de file est un JSON valide avec des nums uniques
"""
import json, os, sys, py_compile

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(BASE, "campagne_zoho.py")
PAUSE = os.path.join(BASE, "PAUSE_ENVOIS")

fails = []


def check(name, cond, detail=""):
    if cond:
        print("PASS | %s" % name)
    else:
        print("FAIL | %s %s" % (name, detail))
        fails.append(name)


# 1. compile
check("campagne_zoho compile", py_compile.compile(SCRIPT, doraise=True) is not None)

sys.path.insert(0, BASE)
import campagne_zoho as CZ

# 2. cause racine des doublons (encodage HTML de l API)
check("_norm_addr decode &lt;/&gt;",
      CZ._norm_addr("&lt;x@y.fr&gt;") == "x@y.fr")
check("_norm_addr decode < >",
      CZ._norm_addr("<x@y.fr>") == "x@y.fr")

# 3. verrou multi-boites branche
src = open(SCRIPT, encoding="utf-8").read()
check("verifier_doublon_global defini + 2 appels",
      src.count("verifier_doublon_global(token_pour, boites") == 3)

# 4. sauvegarde apres chaque envoi
check("save_state apres CHAQUE envoi (2 points)",
      src.count("save_state(state)  # fix 16/08") == 2)

# 5. kill-switch
if os.path.exists(PAUSE):
    print("PAUSE | fichier PAUSE_ENVOIS present : aucun envoi ce run (kill-switch)")
    print("RESULTAT GLOBAL: PAUSE")
    sys.exit(0)
check("kill-switch present dans le code", "PAUSE_ENVOIS" in src)

# 6. file valide
try:
    data = json.load(open(CZ.DATA, encoding="utf-8"))
    emails = data if isinstance(data, list) else data.get("emails", [])
    nums = [e.get("num") for e in emails]
    check("file JSON valide + nums uniques", len(nums) == len(set(nums)) and len(emails) > 0,
          "emails=%d" % len(emails))
except Exception as e:
    check("file JSON valide", False, str(e)[:60])

print()
if fails:
    print("RESULTAT GLOBAL: %d FAIL -> AUCUN ENVOI (pre-flight bloque)" % len(fails))
    sys.exit(1)
print("RESULTAT GLOBAL: OK, pre-flight valide")
sys.exit(0)
