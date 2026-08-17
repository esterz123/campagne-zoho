#!/usr/bin/env python3
"""plan_action_jour.py — Génère le plan d'action du jour : quels prospects relancer
aujourd'hui (J+3/J+7/J+14), avec leur email prêt à envoyer depuis relances_constats/."""
import json, os, sys
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(BASE, "campagne_data.json"), encoding="utf-8"))
state = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))
sent = state.get("sent", {})

TODAY = date.today().isoformat()

print("=" * 75)
print(f"PLAN D'ACTION DU JOUR — {TODAY}")
print("=" * 75)

# 1. Relances dues
print("\n=== 1. RELANCES DUES (à envoyer aujourd'hui) ===")
relances = []
for p in data:
    num = str(p.get("num"))
    s = sent.get(num, {})
    if not s or not s.get("on"):
        continue
    try:
        d0 = date.fromisoformat(s["on"])
    except Exception:
        continue
    for label, days, key in [("R1", 3, "sent_relance1"), ("R2", 7, "sent_relance2"), ("R3", 14, "sent_relance3")]:
        due_date = (d0 + timedelta(days=days)).isoformat()
        if TODAY >= due_date and key not in s:
            relances.append((num, p, label, due_date))

if not relances:
    print("  Aucune relance due aujourd'hui. Vérifier demain.")
else:
    for num, p, label, due in relances:
        to = p.get("to", "")
        # Vérifier si un fichier de relance personnalisé existe
        fn = os.path.join(BASE, "relances_constats", f"relance1_prospect_{num}.txt") if label == "R1" else None
        fichier = "PERSO" if fn and os.path.exists(fn) else "générique"
        print(f"  #{num:>3} {p.get('prospect','')[:42]:42s} -> {to[:32]:32s} {label} (due {due}) [{fichier}]")

# 2. Réponses à traiter (inbox)
print("\n=== 2. RÉPONSES EN ATTENTE (inbox Zoho) ===")
print("  - Vérifier manuellement : commercial@, contact@ (Mailinblack souvent)")
print("  - AMDI (commercial@) : réponse bloquée Mailinblack -> cliquer 'délivrer'")

# 3. Aujourd'hui priorité
print("\n=== 3. ACTION PRIORITAIRE AUJOURD'HUI ===")
print("  1. Cliquer 'délivrer' sur les emails Mailinblack (AMDI si présent)")
print("  2. Envoyer les relances dues ci-dessus (voir fichiers relances_constats/)")
print("  3. Répondre aux réponses chaudes sous 24h (taux de conversion x3)")

# 4. Générer les emails prêts pour les relances dues
print("\n=== 4. EMAILS PRÊTS À COPIER (relances dues avec fichier PERSO) ===")
for num, p, label, due in relances:
    if label != "R1":
        continue
    fn = os.path.join(BASE, "relances_constats", f"relance1_prospect_{num}.txt")
    if os.path.exists(fn):
        content = open(fn, encoding="utf-8").read()
        print(f"\n{'─'*75}")
        print(f"#{num} {p.get('prospect','')[:50]}")
        print(f"{'─'*75}")
        print(content[:1200])
        print()

print("=" * 75)
