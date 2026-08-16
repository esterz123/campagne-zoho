# -*- coding: utf-8 -*-
"""
REPONDEUR IA : lit les 5 boites de reception Zoho, repond aux clients de la campagne
avec un message personnalise genere par OpenRouter (modele gratuit), ou propose un brouillon sur Discord.
Marque sent[num]["replied"] dans campagne_state.json : la campagne ne relance alors JAMAIS ce prospect.

Cloud : GitHub Actions (env vars ZOHO_*, ZOHO_B2..B5, OPENROUTER_API_KEY, DISCORD_WEBHOOK)
Local : peut lire les tokens depuis .boites_zoho.json (dossier parent de BASE).
Etat partage avec le closer (repondeur_state.json) : pas de double reponse possible.
"""
import json, os, sys, re, urllib.request, urllib.parse, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ACCOUNT_ID = "7349712000000008002"
MODEL = "deepseek/deepseek-v4-flash:free"  # :free obligatoire (0 euro garanti, regle Mahdi 16/08)
DATA_F = os.path.join(BASE, "campagne_data.json")
PARTENAIRES_F = os.path.join(BASE, "campagne_partenaires.json")
STATE_F = os.path.join(BASE, "repondeur_state.json")
CAMPAGNE_STATE_F = os.path.join(BASE, "campagne_state.json")
PARTENAIRES_STATE_F = os.path.join(BASE, "partenaires_state.json")

AUTO_PATTERNS = [
    "reponse automatique", "automatic reply", "out of office",
    "cong", "vacances", "je serai", "de retour", "absent",
    "prendrai connaissance", "a mon retour", "disponible a partir",
]


def load_boites():
    """Les 5 boites d'envoi. Priorite env (GitHub Actions), sinon .boites_zoho.json local."""
    env = os.environ.get
    boites = []
    b1 = {"nom": "contact", "from": "contact@mahdi-design.com",
          "client_id": env("ZOHO_CLIENT_ID"), "client_secret": env("ZOHO_CLIENT_SECRET"),
          "refresh_token": env("ZOHO_REFRESH_TOKEN"), "account_id": env("ZOHO_ACCOUNT_ID", ACCOUNT_ID)}
    if all(b1[k] for k in ("client_id", "client_secret", "refresh_token", "account_id")):
        boites.append(b1)
    for i in range(2, 6):
        nom = {2: "commercial", 3: "hello", 4: "info", 5: "direction"}[i]
        b = {"nom": nom, "from": nom + "@mahdi-design.com",
             "client_id": env("ZOHO_B%d_CLIENT_ID" % i), "client_secret": env("ZOHO_B%d_CLIENT_SECRET" % i),
             "refresh_token": env("ZOHO_B%d_REFRESH_TOKEN" % i), "account_id": env("ZOHO_B%d_ACCOUNT_ID" % i)}
        if all(b[k] for k in ("client_id", "client_secret", "refresh_token", "account_id")):
            boites.append(b)
    # 2e domaine (mahdi-design.fr) : B6-B10, actives des que les secrets existent
    noms2 = {6: "contact", 7: "commercial", 8: "hello", 9: "info", 10: "direction"}
    for i, nom in noms2.items():
        b = {"nom": nom + "2", "from": nom + "@mahdi-design.fr",
             "client_id": env("ZOHO_B%d_CLIENT_ID" % i), "client_secret": env("ZOHO_B%d_CLIENT_SECRET" % i),
             "refresh_token": env("ZOHO_B%d_REFRESH_TOKEN" % i), "account_id": env("ZOHO_B%d_ACCOUNT_ID" % i)}
        if all(b[k] for k in ("client_id", "client_secret", "refresh_token", "account_id")):
            boites.append(b)
    if boites:
        return boites
    local = os.path.join(os.path.dirname(BASE), ".boites_zoho.json")
    if os.path.exists(local):
        d = json.load(open(local, encoding="utf-8"))
        return [{"nom": nom, "from": b.get("from") or nom + "@mahdi-design.com",
                 "client_id": b["client_id"], "client_secret": b["client_secret"],
                 "refresh_token": b["refresh_token"], "account_id": b["account_id"]}
                for nom, b in d.items()]
    return []


def refresh_access(boite):
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "client_id": boite["client_id"],
                                   "client_secret": boite["client_secret"],
                                   "refresh_token": boite["refresh_token"]}).encode()
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
    """Les 2 files : prospects industriels (campagne_data) + agences partenaires (campagne_partenaires)."""
    out = {}
    for f, typ in ((DATA_F, "prospect"), (PARTENAIRES_F, "partenaire")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for e in d:
            to = (e.get("to") or "").strip().lower()
            if to:
                out[to] = {"num": e.get("num"), "entreprise": e.get("prospect", e.get("entreprise", "")),
                           "subject": e.get("subject", ""), "type": typ}
    return out


def load_state():
    if os.path.exists(STATE_F):
        return json.load(open(STATE_F, encoding="utf-8"))
    return {"traites": []}


def save_state(st):
    json.dump(st, open(STATE_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def load_campagne_state():
    if os.path.exists(CAMPAGNE_STATE_F):
        return json.load(open(CAMPAGNE_STATE_F, encoding="utf-8"))
    return {"sent": {}}


def save_campagne_state(st):
    json.dump(st, open(CAMPAGNE_STATE_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def marquer_repondu(num, typ="prospect"):
    """Marque replied : la campagne/les partenaires ne relanceront plus ce contact."""
    try:
        if typ == "partenaire":
            st = json.load(open(PARTENAIRES_STATE_F, encoding="utf-8")) if os.path.exists(PARTENAIRES_STATE_F) else {"sent": {}}
            if num and str(num) in st.get("sent", {}):
                st["sent"][str(num)]["replied"] = datetime.date.today().isoformat()
                json.dump(st, open(PARTENAIRES_STATE_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                return True
        else:
            st = load_campagne_state()
            if num and str(num) in st.get("sent", {}):
                st["sent"][str(num)]["replied"] = datetime.date.today().isoformat()
                save_campagne_state(st)
                return True
    except Exception:
        pass
    return False


def is_auto(summary, subject):
    t = (summary + " " + subject).lower()
    return any(p in t for p in AUTO_PATTERNS)


def is_ours(frm):
    f = frm.lower()
    return f.endswith("@mahdi-design.com") or f in ("welcome@zoho.com", "no-reply@zoho.com", "zoho@zoho.com")


def fetch_inbox(boite, access, limit=30):
    j = zoho_get("https://mail.zoho.com/api/accounts/%s/messages/search?searchKey=in%%3Ainbox&limit=%d"
                 % (boite["account_id"], limit), access)
    out = []
    for m in j.get("data", []):
        frm = (m.get("fromAddress") or "")
        out.append({"id": "%s:%s" % (boite["nom"], m.get("messageId")), "from": frm,
                    "subject": m.get("subject", ""), "summary": m.get("summary", ""),
                    "when": m.get("receivedTime", ""), "boite": boite})
    return out


def openrouter(prompt, key):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.6}).encode()
    url = "https://openrouter.ai/api/v1/chat/completions"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json",
                                                          "Authorization": "Bearer " + key})
    j = json.load(urllib.request.urlopen(req, timeout=60))
    return j["choices"][0]["message"]["content"].strip()


def build_prompt(prosp, msginfo):
    p = prosp or {}
    return """Tu rediges la reponse email de Mahdi, designer de marque independant (studio MAHDI.), qui travaille avec des PME et industriels francais.
Prospect (entreprise connue de la campagne) : %s
Notre email initial envoye a ce prospect etait : "%s"
Le client vient de repondre : "%s" (sujet : %s)
Nos offres exactes : Diagnostic express 79 EUR (offre de lancement, rapport de 5 pages sous 48h, rembourse si pas de valeur, c'est l'entree de gamme la plus facile a accepter). Diagnostic complet 290 a 490 EUR selon complexite. Refonte de marque 3500 a 15000 EUR. Pack securite WordPress 79 EUR/mois, premier mois offert, sans engagement.
Regles strictes :
- Francais naturel, ton chaleureux et pro, jamais de pub ni de survente.
- PERSONNALISE avec le contexte ci-dessus. Ne colle aucun texte generique.
- JAMAIS de tiret (ni em-dash ni autre) dans la phrase finale : virgules, points, deux-points, parentheses uniquement.
- JAMAIS d'apostrophe typographique (') : apostrophe droite (') uniquement.
- 3 a 8 phrases max. Termine par "Mahdi" seul (pas de signature longue, pas de site, pas de telephone).
- PRIORITE : propose le diagnostic express a 79 EUR en premier si le client hesite sur le prix ou demande un cout. C'est la porte d'entree la plus facile a accepter.
- IMPORTANT : si le client repond OUI a l'offre gratuite (montrer ce que j'ai trouve), livre d'abord gratuitement les constats principaux (les points qui datent, en 2-3 phrases), puis propose en option le diagnostic complet a 79 EUR (rapport de 5 pages). Ne presente JAMAIS le 79 EUR comme la seule option : le gratuit a ete promis dans l'email initial.
- Si on demande les prix, donne ceux ci-dessus.
- Si le client demande un devis precis, une date engagee, ou negocie : type = "draft". Sinon type = "reply".
Reponds UNIQUEMENT en JSON valide : {"type": "reply" ou "draft", "message": "le texte complet"}""" % (
        p.get("entreprise", "inconnu"), p.get("subject", ""), msginfo["summary"], msginfo["subject"])


def build_prompt_partenaire(prosp, msginfo):
    p = prosp or {}
    return """Tu rediges la reponse email de Mahdi, designer de marque independant (studio MAHDI.), qui a envoye une offre de PARTENARIAT a une agence web / studio de communication.
Agence partenaire : %s
Notre email initial a cette agence etait : "%s"
L'agence vient de repondre : "%s" (sujet : %s)
L'accord propose : Mahdi refait l'identite et le site des clients industriels de l'agence, l'agence garde la relation client et touche 15%% de commission sur chaque projet signe. Le client reçoit d'abord un diagnostic gratuit.
Regles strictes :
- Francais naturel, ton chaleureux et pro.
- Si l'agence accepte ou est interesse : remercie, confirme la commission de 15%%, propose d'envoyer un exemple de projet reel (diagnostic), et demande quels clients industriels pourraient en profiter en premier.
- Si l'agence hesite ou a des questions : reponds clairement, sans pression.
- JAMAIS de tiret (ni em-dash ni autre) : virgules, points, deux-points, parentheses uniquement.
- JAMAIS d'apostrophe typographique (') : apostrophe droite (') uniquement.
- 3 a 8 phrases max. Termine par "Mahdi" seul (pas de signature longue, pas de site, pas de telephone).
- Si l'agence demande un contrat ou des conditions precises : type = "draft". Sinon type = "reply".
Reponds UNIQUEMENT en JSON valide : {"type": "reply" ou "draft", "message": "le texte complet"}""" % (
        p.get("entreprise", "inconnu"), p.get("subject", ""), msginfo["summary"], msginfo["subject"])


def parse_gemini_out(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return "draft", text
    try:
        d = json.loads(m.group(0))
        return (d.get("type") or "draft"), (d.get("message") or "").strip()
    except Exception:
        return "draft", text


def send(boite, to, subject, content, access):
    clean = re.sub(r"^(re|r) *: *", "", subject, flags=re.I)
    if not re.match(r"^(re|r) *: *", subject, flags=re.I):
        clean = "Re: " + subject
    payload = {"fromAddress": boite["from"], "toAddress": to, "subject": clean, "content": content}
    j = zoho_post("https://mail.zoho.com/api/accounts/%s/messages" % boite["account_id"], payload, access)
    return j.get("data", {}).get("messageId")


def notify_discord(text):
    hook = os.environ.get("DISCORD_WEBHOOK")
    if not hook:
        return False
    body = json.dumps({"content": text}).encode()
    req = urllib.request.Request(hook, data=body, headers={"Content-Type": "application/json",
                                                           "User-Agent": "campagne-bot/1.0"})
    urllib.request.urlopen(req, timeout=20)
    return True


def main():
    dry = "--dry-run" in sys.argv
    boites = load_boites()
    if not boites:
        print("PAS DE CREDENTIALS : impossible de lire les boites. Abandon.")
        return 1
    key = os.environ.get("OPENROUTER_API_KEY", "")

    st = load_state()
    traites = set(st.get("traites", []))
    # Lecture croisee : le closer (boite contact) peut avoir deja traite un message
    try:
        cl = json.load(open(os.path.join(BASE, "closer_state.json"), encoding="utf-8"))
        traites |= set(cl.get("traites", []))
    except Exception:
        pass
    prospects = load_prospects()
    rapports = []

    for boite in boites:
        if dry:
            rapports.append("[DRY-RUN] boite %s : non lue (mode sec)" % boite["nom"])
            continue
        try:
            access = refresh_access(boite)
            msgs = fetch_inbox(boite, access, limit=30)
        except Exception as e:
            rapports.append("[ERREUR] boite %s : %s" % (boite["nom"], str(e)[:90]))
            continue
        for m in msgs:
            if m["id"] in traites:
                continue
            frm = m["from"].lower()
            if is_ours(m["from"]):
                traites.add(m["id"])
                continue
            if is_auto(m["summary"], m["subject"]):
                traites.add(m["id"])
                rapports.append("[AUTO] %s : %s (reponse automatique, rien envoye)" % (m["from"], m["subject"][:50]))
                continue
            prosp = prospects.get(frm)
            if not prosp:
                traites.add(m["id"])
                rapports.append("[IGNORE] %s : expéditeur inconnu de la campagne" % m["from"])
                continue
            typ = prosp.get("type", "prospect")
            # Contact connu : il a repondu -> plus jamais relance par la machine
            if marquer_repondu(prosp.get("num"), typ):
                rapports.append("[REPLY-MARQUE] %s (#%s, %s) : replied" % (m["from"], prosp.get("num"), typ))
            if not key:
                rapports.append("[SANS CLE IA] %s : message vu, pas de cle IA (repris au prochain run)" % m["from"])
                continue
            prompt = build_prompt_partenaire(prosp, m) if typ == "partenaire" else build_prompt(prosp, m)
            try:
                out = openrouter(prompt, key)
                typ, msg = parse_gemini_out(out)
            except Exception as e:
                typ, msg = "draft", "Erreur de generation : %s" % str(e)[:120]
            if dry:
                rapports.append("[DRY-RUN] %s : %s genererait (%s)" % (m["from"], typ, m["subject"][:40]))
                continue
            if typ == "reply":
                mid = send(boite, m["from"], m["subject"], msg, access)
                rapports.append("[REPONDU] %s : %s (messageId %s)" % (m["from"], m["subject"][:40], mid))
            else:
                rapports.append("[DRAFT] %s : brouillon propose, pas envoye.\n%s" % (m["from"], msg[:400]))
            traites.add(m["id"])

    st["traites"] = sorted(traites)
    st["dernier_run"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if not dry:
        save_state(st)   # le dry-run ne doit JAMAIS ecrire l'etat (fix 16/08)

    titre = "REPONDEUR IA" + (" (dry run)" if dry else "")
    if rapports:
        rapport = "**%s** : %d boite(s) surveillee(s).\n%s" % (titre, len(boites), "\n".join(rapports))
    else:
        rapport = "**%s** : rien de nouveau (boites : %s)." % (titre, ", ".join(b["nom"] for b in boites))
    print(rapport)
    if not dry:
        notify_discord(rapport)
    return 0


if __name__ == "__main__":
    sys.exit(main())
