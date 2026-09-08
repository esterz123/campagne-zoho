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
MAX_PAR_RUN = 3
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
    # RELANCE PARTENAIRE : envoyees il y a >= 5 jours sans reponse -> Re: en priorite.
    # Cycle BORNE (fix 08/09 : avant, aucune limite -> relance tous les 5 jours a l'infini) :
    # relance2 (J+5) puis relance3 de cloture (J+10), puis silence definitif.
    relance_fu = []
    if not dry:
        for n, v in sorted(sent.items()):
            if v.get("replied") or not v.get("on") or v.get("relance3"):
                continue
            days = (datetime.date.today() - datetime.date.fromisoformat(v["on"])).days
            if days >= 5:
                stage = "relance3" if v.get("relance2") else "relance2"
                relance_fu.append((stage, n))
    if relance_fu:
        if dry:
            stage, n = relance_fu[0]
            e = emails[n]
            print("[DRY-RUN] %s partenaire #%s %s -> %s" % (stage, n, e["prospect"][:40], e["to"]))
            return 0
        # corps de relance dedie (nom extrait du body initial)
        import re as _re
        # fix 08/09 : un 500 Zoho sur la relance tuait TOUT le run (vecu 07/09 18:39, 21:50, 08/09 00:02)
        # -> try/except par candidat, on passe au suivant, retry au prochain run
        for stage, n in relance_fu:
            e = emails[n]
            m = _re.match(r"Bonjour M\. ([A-ZÀ-Ü]+(?: [A-ZÀ-Ü]+)*),", e["body"])
            nom = m.group(1) if m else ""
            civil = ("M. " + nom) if nom else "Madame, Monsieur"
            if stage == "relance3":
                corps = ("Bonjour %s,\n\n"
                         "Je cloture de mon cote : visiblement le timing n'est pas bon, et je ne veux pas insister.\n\n"
                         "Je laisse juste la porte ouverte : si un de vos clients industriels a besoin un jour d'une refonte "
                         "(identite + site), je m'en occupe entierement, vous gardez la relation client et touchez 15%% de commission. "
                         "Le diagnostic gratuit reste valable pour tester sans risque.\n\n"
                         "Un mot suffit, meme dans 6 mois.\n\n"
                         "Cordialement,\nMahdi\nPortfolio : mahdi-design.com" % civil)
            else:
                corps = ("Bonjour %s,\n\n"
                         "Je me permets de revenir vers vous au sujet de ma proposition de partenariat envoyee il y a quelques jours.\n\n"
                         "En resume : vos clients industriels ont des sites qui datent, je m'occupe de leur refonte complete "
                         "(identite + site), vous gardez la relation client et touchez 15%% de commission. Le client recoit "
                         "d'abord un diagnostic gratuit, zero risque pour votre reputation.\n\n"
                         "Tous les details : mahdi-design.com/partenaires.html\n\n"
                         "Si le sujet vous interesse, une simple reponse suffit.\n\n"
                         "Cordialement,\nMahdi\nPortfolio : mahdi-design.com" % civil)
            boite = min(boites, key=lambda b: sum(1 for v in sent.values() if v.get("boite") == b["nom"]))
            token = cz.refresh_token(boite)
            try:
                cz.send_email(token, "Re: " + e["subject"], corps, e["to"], boite=boite)
            except Exception as exc:
                print("ECHEC relance partenaire #%s -> %s : %s (skip, retry au prochain run)" % (n, e["to"], str(exc)[:120]))
                continue
            flags = {"on": datetime.date.today().isoformat(), "boite": boite["nom"], "relance2": True}
            if stage == "relance3":
                flags["relance3"] = True
            sent[n] = flags
            save_state(st)
            print("RELANCE %s partenaire #%s %s -> %s (via %s)" % (stage, n, e["prospect"][:40], e["to"], boite["nom"]))
            return 0
        print("Relances dues : toutes en echec Zoho, retry au prochain run.")
        return 0
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
    # fix 07/09 : un 500 Zoho ici tuait tout le run partenaires (vecu 18:39) -> skip + reessaie au prochain run
    try:
        cz.send_email(token, e["subject"], e["body"], e["to"], boite=boite)
    except Exception as exc:
        print("ECHEC partenaire #%s -> %s : %s (skip, reessaie au prochain run)" % (num, e["to"], str(exc)[:120]))
        return 1
    sent[num] = {"on": today, "boite": boite["nom"]}
    save_state(st)
    print("PARTENAIRE envoye #%s %s -> %s (via %s)" % (num, e["prospect"][:40], e["to"], boite["nom"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
