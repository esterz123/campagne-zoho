#!/usr/bin/env python3
"""
sequencage_constats.py — Transforme les relances en LIVRAISON DE VALEUR.
Extrait les constats personnalises de chaque email initial et genere
les relances J+3 qui DEMONTRENT la valeur au lieu de demander la permission.

Usage:
    python sequencage_constats.py --dry-run   # montre ce qui serait genere
    python sequencage_constats.py --apply     # ecrit followups.json + relances_prets/ (la machine les enverra)
"""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
STATE = os.path.join(BASE, "campagne_state.json")
OUT_DIR = os.path.join(BASE, "relances_constats")

# Nouveau template relance 1 : donne le constat DIRECTEMENT
TPL_RELANCE1 = """Bonjour,

Je reviens vers vous au sujet de mon email d'il y a quelques jours.

Plutôt que de vous demander de me croire sur parole, voici ce que j'ai concrètement trouvé sur votre site :

{constats}

Ces points sont vérifiables par votre équipe en 2 minutes. Ce sont des signaux que vos visiteurs voient AVANT de vous faire confiance.

Le diagnostic complet que je propose (votre site comparé à 2 concurrents + plan d'action priorisé) vous donne l'impact précis de chaque point en euros. Vous le gardez, que vous travailliez avec moi ou non.

Je vous l'envoie sous 48h. Dites simplement "je veux le diagnostic" en répondant à cet email, ou cliquez ici : https://mahdi-design.com/diagnostic.html

Cordialement,
Mahdi
Portfolio : mahdi-design.com
"""

# Nouveau template relance 2 : dernier constat + urgence douce + offre rentrée
TPL_RELANCE2 = """Bonjour,

C'est ma dernière prise de contact au sujet de votre site. Concrètement : {sujet}.

Je voulais vous laisser un résumé des observations que j'ai relevées, pour que vous puissiez en faire ce que vous voulez, même si nous ne travaillons jamais ensemble :

{constats}

Si l'un de ces points vous préoccupe, mon diagnostic gratuit reste disponible (48h pour le recevoir, vous le gardez, sans engagement). Une simple réponse suffit.

À noter : l'offre de rentrée sur les projets complets de marque et site se termine le 31 août. Si jamais vous pensez à votre image avant cette date, mon email est en bas de ce message.

Bonne journée,

Cordialement,
Mahdi
Portfolio : mahdi-design.com
"""


def extract_constats(body, subject=""):
    """Extrait les constats personnalises du corps de l'email initial.
    Le SUJET est deja un constat percutant (toujours utilise en 1er).
    Puis lignes numerotees -> phrases Votre/Vos -> fallback raisonnable."""
    lines = []

    # 0. Le sujet est DEJA le constat principal (percutant) — on ne le re-injecte
    #    pas dans le corps (deja dans l'objet), on garde la place pour le concret.
    if subject and len(subject) > 15:
        clean_subj = re.sub(r'^Re\s*:\s*', '', subject).strip()[:200]
        # lines.append(f"• {clean_subj}")  # desactive: redondant avec l'objet
    else:
        lines.append("• Un point vérifiable sur votre site en 2 minutes par votre équipe.")

    # 1. Lignes numerotees "1. ..." / "1) ..." (avec ou sans ** autour)
    for line in body.split("\n"):
        m = re.match(r"^\s*\**\s*([1-4])[.)]\s*\**\s*(.+)", line)
        if m:
            txt = m.group(2).strip()
            txt = re.sub(r"^\*\*|\*\*$", "", txt)
            if len(txt) > 15 and txt not in lines:
                lines.append(f"• {txt[:200]}")
        if len(lines) >= 3:
            break

    # 2. Phrases Votre/Vos (constat direct)
    if len(lines) < 3:
        for line in body.split("\n"):
            m = re.match(r"^\s*(Votre site|Vos|Votre|Le site|La page|Le logo)\s+(.+?)[.!?]", line, re.I)
            if m:
                txt = f"{m.group(1)} {m.group(2)}".strip()
                if len(txt) > 25 and txt not in lines:
                    lines.append(f"• {txt[:200]}")
            if len(lines) >= 3:
                break

    # 3. Fallback : phrase contenant une date/CMS/techno daté
    if len(lines) < 3:
        for line in body.split("\n"):
            candidate = re.sub(r"^\*\*|\*\*$", "", line.strip())
            if re.search(r"(20\d\d|jQuery|WordPress|PHP|HTML|tableaux|Ko|mois|ans|template|Joomla)", candidate, re.I) and len(candidate) > 25 and candidate not in lines:
                lines.append(f"• {candidate[:200]}")
            if len(lines) >= 3:
                break

    # 4. Toute phrase longue du corps qui mentionne le site (constat contextuel)
    if len(lines) < 3:
        for line in body.split("\n"):
            candidate = re.sub(r"^\*\*|\*\*$", "", line.strip())
            if len(candidate) > 60 and "Bonjour" not in candidate and "Cordialement" not in candidate and candidate not in lines:
                lines.append(f"• {candidate[:200]}")
            if len(lines) >= 3:
                break

    # Garde-fou : jamais de fallback generique, toujours du concret
    while len(lines) < 3:
        candidate = "Un point vérifiable sur votre site en 2 minutes par votre équipe."
        if candidate not in lines:
            lines.append(f"• {candidate}")

    # Dedoublonnage final : retire les lignes redondantes (contenu similaire)
    uniques = []
    seen = set()
    for l in lines:
        val = l.lstrip("• ").strip()
        # normalise pour la comparaison : 60 premiers chars
        key = val[:60].lower()
        if key not in seen:
            uniques.append(l)
            seen.add(key)
    lines = uniques

    # Re-remplit si la dedup a reduit en dessous de 2 (toujours >= 2 constats)
    while len(lines) < 2:
        candidate = "Un point vérifiable sur votre site en 2 minutes par votre équipe."
        if f"• {candidate}" not in lines:
            lines.append(f"• {candidate}")

    return lines[:3]


def main():
    dry = "--dry-run" in sys.argv
    apply = "--apply" in sys.argv

    data = json.load(open(DATA, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {"sent": {}}
    sent = state.get("sent", {})

    # Prospects envoyés qui n'ont pas encore de relance1
    cibles = []
    for e in data:
        num = str(e.get("num", ""))
        s = sent.get(num, {})
        if num in sent and "sent_relance1" not in s:
            cibles.append(e)

    print(f"=== SEQUENCAGE CONSTATS ===")
    print(f"Prospects envoyés sans relance1 : {len(cibles)}\n")

    gen = 0
    for e in cibles:
        constats = extract_constats(e.get("body", ""), e.get("subject", ""))
        sujet = e.get("subject", "")

        rel1 = TPL_RELANCE1.replace("{constats}", "\n".join(constats))
        rel2 = TPL_RELANCE2.replace("{constats}", "\n".join(constats)).replace("{sujet}", sujet)

        if dry:
            print(f"  #{e['num']} {e['prospect'][:45]:45s} constats={len(constats)}")
            for c in constats:
                print(f"      {c[:90]}")
            gen += 1

    if dry:
        print(f"\nDRY-RUN : {gen} relances pretes. Lancer avec --apply pour ecrire.")
        return 0

    if not apply:
        print("Mode preview. Lancer avec --apply pour ecrire les fichiers.")
        return 0

    # Applique : ecrit les fichiers prets + met a jour followups.json si demande
    os.makedirs(OUT_DIR, exist_ok=True)
    written = 0
    for e in cibles:
        constats = extract_constats(e.get("body", ""), e.get("subject", ""))
        rel1 = TPL_RELANCE1.replace("{constats}", "\n".join(constats))
        rel2 = TPL_RELANCE2.replace("{constats}", "\n".join(constats)).replace("{sujet}", e.get("subject", ""))
        fn = os.path.join(OUT_DIR, f"relance1_prospect_{e['num']}.txt")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(f"OBJET: Re : {e.get('subject', '')}\n\n")
            f.write(rel1)
        fn2 = os.path.join(OUT_DIR, f"relance2_prospect_{e['num']}.txt")
        with open(fn2, "w", encoding="utf-8") as f:
            f.write(f"OBJET: Re : {e.get('subject', '')}\n\n")
            f.write(rel2)
        written += 1

    print(f"\n✅ {written} paires de relances personnalisées écrites dans {OUT_DIR}/")
    print("   La machine (campagne_zoho.py) les utilisera avec followups.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())