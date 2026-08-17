#!/usr/bin/env python3
"""
gen_premier_message_v2.py — Genere la V2 du premier email pour les prospects
non encore envoyes (31 restants). Au lieu de promettre un diagnostic si on repond
(v1, 0% de conversion), on LIVRE directement le constat concret du site.

Usage:
    python gen_premier_message_v2.py --dry-run   # apercu
    python gen_premier_message_v2.py --apply     # ecrit dans premiers_messages_v2/
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
STATE = os.path.join(BASE, "campagne_state.json")
OUT_DIR = os.path.join(BASE, "premiers_messages_v2")

# Template V2 : livre le constat, pose une question ouverte, propose une suite simple
TPL_V2 = """Bonjour {prenom},

Je suis Mahdi, designer de marque pour PME industrielles. En passant sur {site}, j'ai noté {n_label} qui {verbe} faire hésiter un donneur d'ordre :

{constats_list}

Ces points sont vérifiables par votre équipe en 2 minutes. Pour un client qui compare 3 sous-traitants, c'est souvent ce genre de détail qui fait la différence entre « partenaire crédible » et « fournisseur daté ».

Je vous envoie, gratuitement et sans engagement, un diagnostic de 10 pages qui détaille ces points et les compare à 2 de vos concurrents directs. Vous le gardez, que nous travaillions ensemble ou non.

Répondez simplement « oui » et je vous l'envoie sous 48h.

Cordialement,
Mahdi
Portfolio : mahdi-design.com
"""


def extract_constats(body, subject=""):
    """Extrait les constats du corps de l'email v1 (lignes numerotees)."""
    lines = []
    # Lignes numerotees "1. ..." / "1) ..."
    for line in body.split("\n"):
        m = re.match(r"^\s*\**\s*([1-4])[.)]\s*\**\s*(.+)", line)
        if m:
            txt = re.sub(r"^\*\*|\*\*$", "", m.group(2).strip())
            if len(txt) > 15:
                lines.append(txt[:250])
        if len(lines) >= 3:
            break
    # Fallback : phrases commencant par Votre/Vos
    if len(lines) < 2:
        for line in body.split("\n"):
            m = re.match(r"^\s*(Votre site|Vos|Votre|Le site|La page|Le logo)\s+(.+?)[.!?]", line, re.I)
            if m:
                txt = f"{m.group(1)} {m.group(2)}".strip()
                if len(txt) > 25:
                    lines.append(txt[:250])
            if len(lines) >= 3:
                break
    return lines[:3] or ["Un point vérifiable sur votre site en 2 minutes"]


def main():
    dry = "--dry-run" in sys.argv
    apply = "--apply" in sys.argv

    data = json.load(open(DATA, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8"))
    sent = state.get("sent", {})

    # Prospects confirmés non envoyés
    cibles = [p for p in data if p.get("to_confirmed") and str(p.get("num")) not in sent]
    cibles.sort(key=lambda p: int(p["num"]))

    print(f"=== PREMIER MESSAGE V2 : {len(cibles)} prospects prêts ===\n")

    if dry:
        for p in cibles[:5]:
            constats = extract_constats(p.get("body", ""), p.get("subject", ""))
            print(f"#{p['num']} {p.get('prospect','')[:45]}")
            print(f"   Constats: {len(constats)}")
            for c in constats:
                print(f"   • {c[:80]}")
            print()
        print(f"(apercu de {min(5,len(cibles))}/{len(cibles)})")
        print("Lancer avec --apply pour ecrire tous les fichiers.")
        return 0

    if not apply:
        print("Mode apercu. --apply pour generer.")
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    written = 0
    for p in cibles:
        constats = extract_constats(p.get("body", ""), p.get("subject", ""))
        # Deduplication des constats identiques
        uniques = []
        seen = set()
        for c in constats:
            key = c[:60].lower()
            if key not in seen:
                uniques.append(c)
                seen.add(key)
        constats = uniques
        if len(constats) < 2 and constats:
            constats = [constats[0]]  # garde au moins 1

        # Prenom du dirigeant si present
        prenom = ""
        d = p.get("dirigeant", "")
        if d:
            mots = d.split()
            if len(mots) >= 2:
                prenom = f"{mots[0]} {mots[1]}"
            elif mots:
                prenom = mots[0]
        if not prenom:
            prenom = "Madame, Monsieur"

        site = p.get("site", p.get("to", "").split("@")[-1])

        # Grammaire : 1 point / 2 points
        n = len(constats)
        n_label = "un point" if n == 1 else f"{n} points"
        verbe = "peut" if n == 1 else "peuvent"
        constats_list = "\n".join(f"{i+1}. {c}" for i, c in enumerate(constats[:3]))

        corps = TPL_V2.format(
            prenom=prenom,
            site=site,
            n_label=n_label,
            verbe=verbe,
            constats_list=constats_list,
        )

        # Objet : tire le constat principal du sujet v1 (percutant)
        objet = f"Votre site {site} : {n_label} qui peut faire hésiter un client"
        if n > 1:
            objet = f"Votre site {site} : {n} points qui peuvent faire hésiter un client"

        fn = os.path.join(OUT_DIR, f"premier_msg_v2_prospect_{p['num']}.txt")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(f"OBJET: {objet}\n\n")
            f.write(corps)
        written += 1

    print(f"✅ {written} premiers messages V2 generes dans {OUT_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
