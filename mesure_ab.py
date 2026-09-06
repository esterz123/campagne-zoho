#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MESURE A/B (Pareto: decider par les chiffres, pas l intuition).
Compare taux de reponse de TOUTES les variantes de sujet (ab_test.json).
Usage: python mesure_ab.py          -> affiche le tableau de bord
       python mesure_ab.py --write  -> sauvegarde le rapport dans ab_resultats.json
"""
import json, os, sys, datetime

BASE = os.path.dirname(os.path.abspath(__file__))

LABELS = {"A": "A: 3 points qui coutent des clients",
          "B": "B: Question rapide sur votre site",
          "C": "C: curiosite diagnostic pret (06/09)"}

def main():
    write = "--write" in sys.argv
    ab = json.load(open(os.path.join(BASE, "ab_test.json"), encoding="utf-8"))
    # reponses: le repondeur marque replied dans campagne_state
    st = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))["sent"]
    resp = {k for k, v in st.items() if isinstance(v, dict) and v.get("replied")}
    n = {}
    for num, v in ab.items():
        var = v.get("variant", "A")
        n.setdefault(var, {"env": 0, "rep": 0})
        n[var]["env"] += 1
        if num in resp:
            n[var]["rep"] += 1
    lignes = []
    lignes.append("=== TABLEAU DE BORD SUJETS %s ===" % datetime.date.today())
    taux = {}
    for var in sorted(n):
        label = LABELS.get(var, var + ": (sans libelle)")
        e, r = n[var]["env"], n[var]["rep"]
        tx = (100.0 * r / e) if e else 0.0
        taux[var] = tx
        lignes.append("%s | envois: %3d | reponses: %d | taux: %.1f%%" % (label.ljust(38), e, r, tx))
    actives = [(v, taux[v], n[v]["env"]) for v in n if n[v]["env"] > 0]
    total = sum(e for _, _, e in actives)
    gagnant = "egalite"
    if len(actives) >= 2:
        top = sorted(actives, key=lambda x: -x[1])
        if top[0][1] == top[1][1]:
            lignes.append("EGALITE parfaite : relancer avec de nouveaux sujets.")
        else:
            ec = top[0][1] - top[1][1]
            gagnant = top[0][0]
            lignes.append("GAGNANT PROVISOIRE: %s (+%.1f pts)" % (gagnant, ec))
            if total >= 100 and ec < 2.0:
                lignes.append("ECART < 2 pts sur 100+ envois: pas encore significatif, attendre J+5.")
    print("\n".join(lignes))
    if write:
        out = {"date": datetime.date.today().isoformat(), "gagnant": gagnant}
        for var in sorted(n):
            out[var] = n[var]
        json.dump(out, open(os.path.join(BASE, "ab_resultats.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
