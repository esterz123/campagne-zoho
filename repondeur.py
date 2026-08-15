# -*- coding: utf-8 -*-
"""
REPONDEUR IA : lit la boite de reception Zoho, repond aux clients de la campagne
avec un message personnalise genere par OpenRouter (modele gratuit), ou propose un brouillon sur Discord.

Cloud : GitHub Actions (env vars ZOHO_*, OPENROUTER_API_KEY, DISCORD_WEBHOOK)
Local : peut lire les tokens depuis .zoho_tokens.json (si present a cote).
"""
import json, os, sys, re, urllib.request, urllib.parse, datetime, time

BASE = os.path.dirname(os.path.abspath(__file__))
ACC = "7349712000000008002"
ME = "contact@mahdi-design.com"
MODEL = "deepseek/deepseek-v4-flash:free"  # :free obligatoire (0 euro garanti, regle Mahdi 16/08)
DATA_F = os.path.join(BASE, "campagne_data.json")
STATE_F = os.path.join(BASE, "repondeur_state.json")

AUTO_PATTERNS = [
    "reponse automatique", "automatic reply", "out of office",
    "cong", "vacances", "je serai", "de retour", "absent",
    "prendrai connaissance", "a mon retour", "disponible a partir",
]

def load_creds():
    env = os.environ.get
    cid = env("ZOHO_CLIENT_ID"); csec = env("ZOHO_CLIENT_SECRET"); ref = env("ZOHO_REFRESH_TOKEN")
    if cid and csec and ref:
        return cid, csec, ref
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
    # adresses additionnelles deja connues (ex: reponse auto renvoyee par techno@)
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

def fetch_inbox(access, limit=30):
    j = zoho_get("https://mail.zoho.com/api/accounts/%s/messages/search?searchKey=in%%3Ainbox&limit=%d" % (ACC, limit), access)
    out = []
    for m in j.get("data", []):
        frm = (m.get("fromAddress") or "")
        out.append({"id": str(m.get("messageId")), "from": frm, "subject": m.get("subject", ""),
                    "summary": m.get("summary", ""), "when": m.get("receivedTime", "")})
    return out

def openrouter(prompt, key):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.6}).encode()
    url = "https://openrouter.ai/api/v1/chat/completions"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
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
- 3 a 8 phrases max. Termine par "Mahdi" seul (pas de signature longue, pas de site, pas de telephone).
- PRIORITE : propose le diagnostic express a 79 EUR en premier si le client hesite sur le prix ou demande un cout. C'est la porte d'entree la plus facile a accepter.
- Si on demande les prix, donne ceux ci-dessus.
- Si le client demande un devis precis, une date engagee, ou negocie : type = "draft". Sinon type = "reply".
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
    req = urllib.request.Request(hook, data=body, headers={"Content-Type": "application/json", "User-Agent": "campagne-bot/1.0"})
    urllib.request.urlopen(req, timeout=20)
    return True

def main():
    dry = "--dry-run" in sys.argv
    creds = load_creds()
    if not dry and not creds:
        print("PAS DE CREDENTIALS : impossible de lire la boite. Abandon.")
        return 1
    key = os.environ.get("OPENROUTER_API_KEY", "")

    access = None
    if not dry and creds:
        access = refresh_access(*creds)

    st = load_state()
    traites = set(st.get("traites", []))
    prospects = load_prospects()
    rapports = []

    if not dry:
        msgs = fetch_inbox(access, limit=30)
    else:
        msgs = []

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
        if not key:
            rapports.append("[SANS CLE IA] %s : message vu, pas de cle Gemini (il sera repris au prochain run)" % m["from"])
            continue
        prompt = build_prompt(prosp, m)
        try:
            out = openrouter(prompt, key)
            typ, msg = parse_gemini_out(out)
        except Exception as e:
            typ, msg = "draft", "Erreur de generation : %s" % str(e)[:120]
        if dry:
            rapports.append("[DRY-RUN] %s : %s genererait (%s)" % (m["from"], typ, m["subject"][:40]))
            continue
        if typ == "reply":
            mid = send(m["from"], m["subject"], msg, access)
            rapports.append("[REPONDU] %s : %s (messageId %s)" % (m["from"], m["subject"][:40], mid))
        else:
            rapports.append("[DRAFT] %s : brouillon propose, pas envoye.\n%s" % (m["from"], msg[:400]))
        traites.add(m["id"])

    st["traites"] = sorted(traites)
    st["dernier_run"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save_state(st)

    titre = "REPONDEUR IA" + (" (dry run)" if dry else "")
    total_vus = len(msgs)
    nouveaux_initiaux = len([m for m in msgs if m["id"] not in traites])
    if rapports:
        rapport = "**%s** : %d message(s) vus, %d nouveau(x).\n%s" % (
            titre, total_vus, nouveaux_initiaux, "\n".join(rapports))
    else:
        rapport = "**%s** : rien de nouveau." % titre
    print(rapport)
    if not dry:
        notify_discord(rapport)
    return 0

if __name__ == "__main__":
    sys.exit(main())