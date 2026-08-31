#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REPARATION COHERENCE - l'injection de preuves cree une contradiction :
le mail commence par "J'ai ouvert votre site ce matin" puis dit encore
"Je regarde votre site 2 minutes" (futur). Le prospect le verrait.
Ce script remplace le paragraphe futur par la suite logique : le rapport
est DEJA prepare, il suffit de dire oui.
Idempotent : ne touche que les mails contenant un constat "J'ai ..." ET le
vieux paragraphe futur.
Usage : python3 reparation_coherence.py [--dry]
"""
import os
import re
import sys
import json

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
DRY = "--dry" in sys.argv

ANCIEN = re.compile(
    r"Je ne vous vends rien ici\.? Je regarde votre site (?:2|deux) minutes[^.]*\.\s*"
    r"|Je ne vous vends rien aujourd'hui\.? Je regarde votre site (?:2|deux) minutes[^.]*\.\s*"
    r"|Je ne vous propose rien ici\.? Je regarde votre site (?:en )?(?:deux|2) minutes[^.]*\.",
    re.I)

NOUVEAU = ("Je ne vous vends rien ici. Le rapport complet est deja fait : "
           "les mesures exactes, ce qui casse, et l'ordre des reparations. "
           "Deux pages, gratuit, sans engagement, vous pouvez le donner a votre "
           "webmaster tel quel. Repondez simplement « oui » et je vous l'envoie.")


def clean(t):
    return (t or "").replace("\u2019", "'").replace("\u2018", "'")


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    fixes = 0
    for r in data:
        body = r.get("body", "")
        if not re.search(r"J'ai (ouvert|tape|audite)", body):
            continue  # pas un mail a preuve
        new = ANCIEN.sub(NOUVEAU, body)
        # variantes plus courtes non couvertes par la regex principale
        new = new.replace("Je regarde votre site 2 minutes et je vous dis exactement ce que vos prospects fuient",
                          "Je vous envoie le rapport deja fait et vous verrez exactement ce que vos prospects fuient")
        new = new.replace("Je regarde votre site deux minutes et je vous expose les points qui font fuir vos prospects",
                          "Je vous envoie le rapport deja fait, avec les points qui font fuir vos prospects")
        new = new.replace("Je regarde votre site 2 minutes et je vous indique précisément ce qui fait fuir vos clients potentiels",
                          "Dans le rapport deja fait, je vous indique precisement ce qui fait fuir vos clients potentiels")
        # dedoublonnage CTA : le nouveau paragraphe contient deja "Repondez oui".
        # On retire l'ancien CTA de fin + les queues orphelines devenues redondantes.
        new = re.sub(r"\s*C'est gratuit, sans engagement\.\s*", " ", new)
        new = re.sub(r"R[ée]pond[ée]z simplement [\"\u00ab]oui[\"\u00bb] [àa] ce mail et je vous envoie mes constats sous 48h\.?\s*",
                     "", new)
        new = re.sub(r"R[ée]pond[ée]z [\"\u00ab]oui[\"\u00bb] et je vous l'envoie sous 48h\.?\s*", "", new)
        new = re.sub(r"[ \t]{2,}", " ", new)
        new = re.sub(r"(\.?\s*)Cordialement,", "\n\nCordialement,", new)
        new = re.sub(r"\n{3,}", "\n\n", new)
        if new != body:
            r["body"] = clean(new)
            fixes += 1
    print("mails recousus:", fixes)
    if DRY:
        ex = [r for r in data if "Le rapport complet est deja fait" in r.get("body", "")][:1]
        for r in ex:
            print("--- exemple num", r["num"], "---")
            print(r["body"][:600])
        return 0
    if fixes:
        json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("ECRIT:", DATA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
