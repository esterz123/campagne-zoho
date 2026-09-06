#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MESURE A/B 28/08 (Pareto: decider par les chiffres, pas l intuition).
Compare taux de reponse des 2 variantes de sujet (ab_test.json) via repondeur_state.
Usage: python mesure_ab.py          -> affiche le tableau de bord
       python mesure_ab.py --write  -> sauvegarde le rapport dans ab_resultats.json
"""
import json, os, sys, datetime

BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    write = "--write" in sys.argv
    ab = json.load(open(os.path.join(BASE, "ab_test.json"), encoding="utf-8"))
    # reponses: le repondeur marque replied dans campagne_state
    st = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))["sent"]
    resp = {k for k, v in st.items() if v.get("replied")}
    n = {"A": {"env": 0, "rep": 0}, "B": {"env": 0, "rep": 0}, "C": {"env": 0, "rep": 0}}
    for num, v in ab.items():
        var = v.get("variant", "A")
        n.setdefault(var, {"env": 0, "rep": 0})
        n[var]["env"] += 1
        if num in resp:
            n[var]["rep"] += 1
    lignes = []
    lignes.append("=== TABLEAU DE BORD A/B (sujets) %s ===" % datetime.date.today())
    labels = {"A": "A: 3 points qui coutent des clients", "B": "B: Question rapide sur votre site", "C": "C: Score dans le sujet"}
    for var in sorted(n):
        label = labels.get(var, var + ": (sans libelle)")
        e, r = n[var]["env"], n[var]["rep"]
        tx = (100.0 * r / e) if e else 0.0
        lignes.append("%s | envois: %3d | reponses: %d | taux: %.1f%%" % (label.ljust(36), e, r, tx))
    a, b = n["A"], n["B"]
    ta = (100.0 * a["rep"] / a["env"]) if a["env"] else 0
    tb = (100.0 * b["rep"] / b["env"]) if b["env"] else 0
    if a["env"] and b["env"]:
        if ta == tb:
            lignes.append("EGALITE parfaite : relancer avec de nouveaux sujets.")
        else:
            g = "A" if ta > tb else "B"
            ec = abs(ta - tb)
            lignes.append("GAGNANT PROVISOIRE: %s (+%.1f pts)" % (g, ec))
            if a["env"] + b["env"] >= 100 and ec < 2.0:
                lignes.append("ECART < 2 pts sur 100+ envois: pas encore significatif, attendre J+5.")
    print("\n".join(lignes))
    if write:
        json.dump({"date": datetime.date.today().isoformat(), "A": n["A"], "B": n["B"],
                   "gagnant": "A" if ta > tb else ("B" if tb > ta else "egalite")},
                  open(os.path.join(BASE, "ab_resultats.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
