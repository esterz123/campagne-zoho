#!/usr/bin/env python3
"""etat_relances.py — Rapport concret sur l'état des relances + identification des urgences."""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
STATE = os.path.join(BASE, "campagne_state.json")
OUT_DIR = os.path.join(BASE, "relances_constats")

data = json.load(open(DATA, encoding="utf-8"))
state = json.load(open(STATE, encoding="utf-8"))
sent = state.get("sent", {})

print("=" * 70)
print("ÉTAT DES RELANCES (sujet = constats concrets DONT le prospect a besoin)")
print("=" * 70)

# Catégories
r1_envoyes = []          # déjà R1 envoyée (machine actuelle envoie du vide)
r1_attente_deja_envoye = []   # premier envoyé MAIS pas encore R1
r1_a_envoyer = []        # jamais envoyé du tout

for p in data:
    num = str(p.get("num"))
    s = sent.get(num, {})
    fmt = lambda d: d if d != "" else "—"
    if not p.get("to_confirmed"):
        continue
    if num in sent:
        if "sent_relance1" in s:
            r1_envoyes.append((p, s))
        else:
            r1_attente_deja_envoye.append((p, s))
    else:
        r1_a_envoyer.append(p)

print(f"R1 envoyées au total : {len(r1_envoyes)}")
print(f"  dont envoyées avec le système ACTUEL (templates followups.json / vides) : {len(r1_envoyes)}")
print(f"Arriérés : premier envoyé MAIS R1 pas encore sortie : {len(r1_attente_deja_envoye)}")
print(f"Pas encore envoyé du tout : {len(r1_a_envoyer)}")
print()

# Fichiers générés par sequencage_constats.py
fichiers = os.listdir(OUT_DIR) if os.path.exists(OUT_DIR) else []
fichiers_r1 = [f for f in fichiers if "relance1" in f]
print(f"Fichiers relances_constats générés : {len(fichiers)} ({len(fichiers_r1)} relance1)")
print()

# ============================================================
# LISTER LE TOP 10 À RELANCE1 DE FRÉQUENCE (urgences)
# ============================================================
print("=" * 70)
print(f"TOP {min(12, len(r1_attente_deja_envoye))} ARRIÉRS À RELANCE1 CETTE WEEK — CONSTATS À LIVRER")
print("=" * 70)
for i, (p, s) in enumerate(sorted(r1_attente_deja_envoye, key=lambda x: x[1].get("on", "9999-99-99"))[:12]):
    num = str(p["num"])
    jour = s.get("on", "?")
    jo = s.get("sent_relance1", "-")
    subject = p.get("subject", "")
    print(f"\n[{i+1}] #{num:>3} {p['prospect'][:45]:45s} (premier envoyé : {jour})")
    print(f"    Sujet : {subject[:80]}")
    print(f"    À : {p.get('to','?')[:35]}")
    # montrer ce qu'il va recevoir (fichier)
    fn = os.path.join(OUT_DIR, f"relance1_prospect_{num}.txt")
    if os.path.exists(fn):
        content = open(fn, encoding="utf-8").read()
        preview = content[len("OBJET: Re : "):][:250] if content.startswith("OBJET") else content[:250]
        print(f"    → Relance prête : {preview.replace(chr(10),' | ')[:180]}")

# ============================================================
# VÉRIFIER LES R1 DÉJÀ ENVOYÉES (contenu actuel vs attendu)
# ============================================================
print()
print("=" * 70)
print(f"3 DERNIÈRES R1 ENVOYÉES AVEC LE SYSTÈME ACTUEL (pour comparer à l'attendu)")
print("=" * 70)
for i, (p, s) in enumerate(reversed(r1_envoyes[-3:])):
    num = str(p["num"])
    jour = s.get("sent_relance1", "?")
    subject = p.get("subject", "")
    print(f"\n[i+1] #{num:>3} {p['prospect'][:40]:40s} (R1 envoyée : {jour})")
    print(f"    Sujet d'origine : {subject[:70]}")
    print(f"    Prospect attendrait CONSTATS SUR {p.get('to','?')[:30]}")
    print(f"    MAIS le système actuel envoie du template générique followups.json")

print()
print("=" * 70)
print("RÉSUMÉ ACTION")
print("=" * 70)
print(f"R1 à envoyer : {len(r1_attente_deja_envoye)} arriérés + {len(r1_a_envoyer)} frais")
print(f"R1 déjà envoyées : {len(r1_envoyes)} (système actuel = cœur vide, pas de constats)")
print(f"Dernières réponses reçues : MARQUER (voir scan_inbox pour : AMDI, Atelier Physis, MPI, DEMC...)")
print()
print(f"ACTION 1 : brancher laposte sur relances_constats pour les {len(r1_attente_deja_envoye)} arriérés.")
print(f"ACTION 2 : scanner inbox Zoho tous les jours (réponses Chaudes attendent).")