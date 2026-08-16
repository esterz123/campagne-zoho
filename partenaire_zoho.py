# -*- coding: utf-8 -*-
"""
PARTENAIRE ZOHO : envoi des emails de partenariat (agences web, commission 15%).
File separee : campagne_partenaires.json. Quota : 1-2/jour max (cible petite et qualitative).
Repond au meme protocole anti-spam : espaces, rotation, kill-switch PAUSE_ENVOIS.
"""
import json, os, sys, time, datetime, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_partenaires.json")
STATE = os.path.join(BASE, "partenaires_state.json")
ACCOUNT_ID = "7349712000000008002"
MAX_PAR_RUN = 1
DELAY_S = 12 * 60

sys.path.insert(0, BASE)
import campagne_zoho as cz  # reutilise load_boites / refresh / send


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding="utf-8"))
    return {"sent": {}}


def save_state(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    if os.path.exists(os.path.join(BASE, "PAUSE_ENVOIS")):
        print("ENVOIS PAUSES (PAUSE_ENVOIS present).")
        return 0
    if not os.path.exists(DATA):
        print("Pas de file partenaires : rien a envoyer.")
        return 0
    dry = "--dry-run" in sys.argv
    emails = {str(e["num"]): e for e in json.load(open(DATA, encoding="utf-8"))}
    st = load_state()
    sent = st["sent"]
    today = datetime.date.today().isoformat()
    boites = cz.load_boites()

    restants = [(n, e) for n, e in sorted(emails.items(), key=lambda kv: int(kv[0]))
                if n not in sent]
    if not restants:
        print("File partenaires vide : toutes envoyees.")
        return 0

    num, e = restants[0]
    if dry:
        print("[DRY-RUN] partenaire #%s %s -> %s" % (num, e["prospect"][:40], e["to"]))
        return 0

    # boite avec le moins d'envois aujourd'hui (partage avec la campagne principale)
    def compte(b):
        return sum(1 for v in sent.values() if v.get("boite") == b["nom"])
    boite = min(boites, key=compte)
    token = cz.refresh_token(boite)
    # anti-doublon : verifier que ce destinataire n'a pas deja recu la campagne principale
    try:
        cz.verifier_doublon(token, boite, e["to"])
    except Exception as exc:
        print("DOUBLON ou erreur : %s" % str(exc)[:100])
        sent[num] = {"on": today, "boite": boite["nom"], "note": "doublon/erreur"}
        save_state(st)
        return 1
    cz.send_email(token, e["subject"], e["body"], e["to"], boite=boite)
    sent[num] = {"on": today, "boite": boite["nom"]}
    save_state(st)
    print("PARTENAIRE envoye #%s %s -> %s (via %s)" % (num, e["prospect"][:40], e["to"], boite["nom"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
