#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLOSER IA — transforme une reponse "interesse" en vente (diagnostic 79 EUR).
===========================================================================
Canal email (Zoho) : comme repondeur.py mais SPECIFIQUE CLOSING.
Quand un prospect repond a notre email initial avec un signal d'interet
("interesse", "ok", "prix", "devis", "combien", "pourquoi pas", "ca marche"...),
le CLOSER redige une reponse de vente qui :
  1. Accuse reception chaleureusement (personnalise).
  2. Propose le diagnostic express 79 EUR remboursable (porte d'entree).
  3. Pose une QUESTION fermee (facilite la prise de decision) + propose un
     creneau (rendez-vous 15 min) pour debloquer.
  4. Si objection prix/hesitation -> reformule la valeur, garde le 79 EUR.
  5. ZERO tiret, signe "Mahdi", sans survente.

Cloud : GitHub Actions (secrets ZOHO_*, cles IA via moteur_ia).
Local : lit .zoho_tokens.json + .ia_tokens.json.
Usage : python3 closer_ia.py [--dry-run] [--max N]
"""
import json, os, re, sys, urllib.request, urllib.parse, datetime, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import moteur_ia as IA

BASE = os.path.dirname(os.path.abspath(__file__))
ACC = "7349712000000008002"
ME = "contact@mahdi-design.com"
DATA_F = os.path.join(BASE, "campagne_data.json")
STATE_F = os.path.join(BASE, "closer_state.json")

# Signaux : un prospect qui utilise l'un de ces mots est un LEADS CHAUD.
INTERET = [
    "intéress", "interesse", "interess", " ok ", " d'accord ", "d'accord",
    "prix", "devis", "combien", "cout", "coût", "pourquoi pas", "ca marche",
    "ça marche", "je veux", "j'aimerais", "allez", "go ", "c'est parti",
    "vas-y", "vas y", "oui", "ca m'interesse", "souhaite", "pas cher",
    "rembourse", "expliquez", "explique", "plus de details", "en savoir plus",
]
OBJECTION_PRIX = ["trop cher", "cher", "pas le budget", "budget", "combien ca coute",
                  "c'est combien", "prix", "cout"]
AUTO_PATTERNS = ["reponse automatique", "automatic reply", "out of office",
                 "cong", "vacances", "de retour", "absent", "a mon retour"]

OFFRE = ("Notre diagnostic express, c'est 79 EUR, une seule fois, remboursable "
         "si vous n'y trouvez pas de valeur. Sous 48h vous avez un rapport de "
         "5 pages qui montre concretement ce qui freine votre visibilite et "
         "comment le corriger. Vous gardez le document dans tous les cas.")


def paypal_link():
    """Lien de paiement (fichier local .paypal_link.txt, jamais commite)."""
    try:
        with open(os.path.join(BASE, ".paypal_link.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def load_creds():
    env = os.environ.get
    if env("ZOHO_CLIENT_ID") and env("ZOHO_CLIENT_SECRET") and env("ZOHO_REFRESH_TOKEN"):
        return env("ZOHO_CLIENT_ID"), env("ZOHO_CLIENT_SECRET"), env("ZOHO_REFRESH_TOKEN")
    local = os.path.join(os.path.dirname(BASE), ".zoho_tokens.json")
    if os.path.exists(local):
        d = json.load(open(local, encoding="utf-8"))
        return d["client_id"], d["client_secret"], d["refresh_token"]
    return None


def refresh_access(cid, csec, ref):
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "client_id": cid,
                                   "client_secret": csec, "refresh_token": ref}).encode()
    req = urllib.request.Request("https://accounts.zoho.com/oauth/v2/token", data=body, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=30))["access_token"]


def zoho_get(url, access):
    req = urllib.request.Request(url, headers={"Authorization": "Zoho-oauthtoken " + access})
    return json.load(urllib.request.urlopen(req, timeout=30))


def zoho_post(url, payload, access):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Authorization": "Zoho-oauthtoken " + access,
                                          "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def load_prospects():
    d = json.load(open(DATA_F, encoding="utf-8"))
    out = {}
    for e in d:
        to = (e.get("to") or "").strip().lower()
        if to:
            out[to] = {"num": e.get("num"), "entreprise": e.get("entreprise", ""),
                       "subject": e.get("subject", "")}
    return out


def load_state():
    if os.path.exists(STATE_F):
        return json.load(open(STATE_F, encoding="utf-8"))
    return {"traites": []}


def save_state(st):
    json.dump(st, open(STATE_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def is_auto(summary, subject):
    t = ((summary or "") + " " + (subject or "")).lower()
    return any(p in t for p in AUTO_PATTERNS)


def is_ours(frm):
    return frm.lower() in (ME, "welcome@zoho.com", "no-reply@zoho.com", "zoho@zoho.com")


def a_un_signal_interet(summary, subject):
    t = (" " + (summary or "") + " " + (subject or "")).lower()
    return any(p in t for p in INTERET)


def a_objection_prix(summary):
    t = (" " + (summary or "") + " ").lower()
    return any(p in t for p in OBJECTION_PRIX)


def fetch_inbox(access, limit=30):
    j = zoho_get("https://mail.zoho.com/api/accounts/%s/messages/search?searchKey=in%%3Ainbox&limit=%d" % (ACC, limit), access)
    out = []
    for m in j.get("data", []):
        out.append({"id": str(m.get("messageId")), "from": (m.get("fromAddress") or ""),
                    "subject": m.get("subject", ""), "summary": m.get("summary", ""),
                    "when": m.get("receivedTime", "")})
    return out


def build_prompt(prosp, msginfo, objection_prix):
    entreprise = (prosp or {}).get("entreprise", "votre entreprise")
    sujet = (prosp or {}).get("subject", "")
    pp = paypal_link()
    paiement = (f"\nLien de paiement du client (a envoyer UNIQUEMENT quand il a dit oui ou demande comment payer) : {pp}"
                if pp else
                "\nPas de lien de paiement configure : propose le creneau 15 min, le paiement se fera par la suite.")
    focus = ("Le client hesite sur le prix. Reformule la VALEUR du diagnostic 79 EUR "
             "remboursable sans baisser le prix, et pose une question fermee."
             if objection_prix else
             "Le client est interesse. Tu le fais passer a l'action.")
    return """Tu es le Closer IA de Mahdi, designer de marque independant. Un prospect de la campagne vient de repondre positivement a notre email.
Entreprise : %s
Notre email initial : "%s"
Sa reponse : "%s" (sujet : %s)
Contexte : %s
Paiement : %s

Offres exactes : Constats et recommandations immediates GRATUITS (deja envoyes dans notre email, le client les a). Diagnostic de credibilite 79 EUR (rapport 10 pages sous 48h, rembourse si pas de valeur, deduit du projet). Projet complet MARQUE + SITE : identite visuelle (logo, couleurs, typographie, charte) + site vitrine 6-8 pages coherent : 3900 a 5900 EUR. Offre rentree septembre : 3 projets complets au tarif 2025, 2900 EUR au lieu de 3900, devis sous 48h, places dans l'ordre des reponses. Pack securite WordPress : 69 EUR/mois ou 690 EUR/an (2 mois offerts), premier mois offert, sans engagement.

Regles strictes :
- Francais naturel, chaleureux, pro. JAMAIS de survente ni de pub.
- PERSONNALISE avec le contexte (nom du dirigeant si present dans l'email initial).
- JAMAIS de tiret (ni em-dash ni autre) : virgules, points, parentheses uniquement.
- 4 a 7 phrases max. Termine par "Mahdi" seul.
- PRIORITE ABSOLUE : proposer le diagnostic complet 79 EUR remboursable (deduit de la refonte). C'est la porte d'entree facile a accepter.
- Si le client repond "envoyez le diagnostic gratuit" : preciser que les constats et recommandations immediates sont deja gratuits (dans notre email), et que l'analyse complete (10 pages, 3 concurrents) est a 79 EUR remboursable, montant deduit en cas de refonte. Ne jamais laisser croire qu'on retire une promesse.
- Mentionner l'offre rentree (2900 EUR au lieu de 3900, 3 places, places dans l'ordre des reponses) uniquement si le client parle de projet de marque ou de site.
- AUCUN appel ni visio : tout se regle par email. Proposer un echange par email.
- Poser UNE question fermee pour debloquer la decision.
Reponds UNIQUEMENT en JSON valide : {"type": "reply", "message": "le texte complet"}""" % (
        entreprise, sujet, msginfo["summary"], msginfo["subject"], focus, paiement)


def parse_out(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return "reply", text
    try:
        d = json.loads(m.group(0))
        return (d.get("type") or "reply"), (d.get("message") or "").strip()
    except Exception:
        return "reply", text


def send(to, subject, content, access):
    clean = re.sub(r"^(re|r) *: *", "", subject, flags=re.I)
    if not re.match(r"^(re|r) *: *", subject, flags=re.I):
        clean = "Re: " + subject
    payload = {"fromAddress": ME, "toAddress": to, "subject": clean, "content": content}
    j = zoho_post("https://mail.zoho.com/api/accounts/%s/messages" % ACC, payload, access)
    return j.get("data", {}).get("messageId")


def notify_discord(text):
    hook = os.environ.get("DISCORD_WEBHOOK")
    if not hook:
        return False
    body = json.dumps({"content": text}).encode()
    req = urllib.request.Request(hook, data=body, headers={"Content-Type": "application/json", "User-Agent": "closer-ia/1.0"})
    try:
        urllib.request.urlopen(req, timeout=20)
        return True
    except Exception:
        return False


def main():
    dry = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    max_n = 30
    if "--max" in args:
        max_n = int(args[args.index("--max") + 1])

    creds = load_creds()
    if not dry and not creds:
        print("PAS DE CREDENTIALS ZOHO. Abandon.")
        return 1

    access = None
    if not dry and creds:
        access = refresh_access(*creds)

    st = load_state()
    traites = set(st.get("traites", []))
    prospects = load_prospects()
    rapports = []

    msgs = fetch_inbox(access, limit=max_n) if (not dry and access) else []

    for m in msgs:
        if m["id"] in traites:
            continue
        frm = m["from"].lower()
        if is_ours(m["from"]) or is_auto(m["summary"], m["subject"]):
            traites.add(m["id"])
            continue
        prosp = prospects.get(frm)
        if not prosp:
            traites.add(m["id"])
            rapports.append("[IGNORE] %s : inconnu campagne" % m["from"])
            continue
        if not a_un_signal_interet(m["summary"], m["subject"]):
            # pas un signal d'interet -> on laisse repondeur.py standard gerer
            rapports.append("[SANS-INTERET] %s : pas de signal de closing" % m["from"])
            traites.add(m["id"])
            continue

        objection = a_objection_prix(m["summary"])
        prompt = build_prompt(prosp, m, objection)
        try:
            out = IA.repondre(prompt, usage="ecriture", silencieux=True, max_secondes=90)
            typ, msg = parse_out(out)
        except Exception as e:
            typ, msg = "reply", ("Erreur de generation : %s" % str(e)[:100])
        # garde-fou anti-tiret
        msg = msg.replace("—", ",").replace("–", ",")
        if dry:
            rapports.append("[DRY] %s : %s\n%s" % (m["from"], "CLOSE(prix)" if objection else "CLOSE", msg[:300]))
            traites.add(m["id"])
            continue
        if typ == "reply":
            mid = send(m["from"], m["subject"], msg, access)
            rapports.append("[CLOSE-ENVOYE] %s : messageId %s" % (m["from"], mid))
        traites.add(m["id"])

    st["traites"] = sorted(traites)
    st["dernier_run"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save_state(st)

    titre = "CLOSER IA" + (" (dry run)" if dry else "")
    rapport = ("**%s** : %d message(s) vus.\n%s" % (titre, len(msgs), "\n".join(rapports))) if rapports else ("**%s** : rien de nouveau." % titre)
    print(rapport)
    if not dry:
        notify_discord(rapport)
    return 0


if __name__ == "__main__":
    sys.exit(main())
