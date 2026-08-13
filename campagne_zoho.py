#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Campagne emails Zoho — envoi automatise depuis contact@mahdi-design.com
Fonctionne EN LOCAL (PC de Mahdi) ET DANS LE CLOUD (GitHub Actions, PC eteint).

Usage:
    python campagne_zoho.py            # envoi selon le quota (3/jour)
    python campagne_zoho.py 5          # quota a 5/jour
    python campagne_zoho.py --dry-run  # montre ce qui serait envoye, sans envoyer
"""
import os
import json
import sys
import datetime
import urllib.request
import urllib.parse

# Chemins relatifs au script -> marche partout (local comme cloud)
BASE = os.path.dirname(os.path.abspath(__file__))
TOKENS = os.path.join(BASE, ".zoho_tokens.json")
DATA = os.path.join(BASE, "campagne_data.json")
STATE = os.path.join(BASE, "campagne_state.json")

ACCOUNT_ID = "7349712000000008002"
FROM = "contact@mahdi-design.com"
DAILY_MAX = 3

# ---- VERROU ANTI-ERREUR (garde-fou permanent) ----
# Un email dont le domaine est ici est un PIEGE (annuaire/scraper/mail gratuit/
# relais technique/mismatch). Le script REFUSE de l'envoyer : ca protegerait le
# domaine mahdi-design.com d'un bounce = blacklist. Liste dans domaines_bloques.json
BLOQUES = os.path.join(BASE, "domaines_bloques.json")

def load_bloquees():
    """Domaines a ne JAMAIS contacter (annuaires, scrapers, mails gratuits)."""
    try:
        with open(BLOQUES, encoding="utf-8") as f:
            j = json.load(f)
        return [d.lower() for d in j.get("bloques", [])]
    except Exception:
        return []

def domaine_bloque(to, bloquees):
    """True si l'email cible est sur un domaine piege."""
    if not to or "@" not in to:
        return True  # pas d'adresse = on ne sait pas envoyer = on bloque
    dom = to.split("@")[1].lower()
    for b in bloquees:
        if dom == b or dom.endswith("." + b):
            return True
    return False

SIG = ("Mahdi<br>"
       "Brand Designer &mdash; Identit&eacute; visuelle &amp; sites web pour PME<br>"
       "Portfolio : <a href=\"https://mahdi-design.com\">mahdi-design.com</a><br>"
       "contact@mahdi-design.com")


def body_to_html(text):
    """Convertit le corps (texte avec \\n et **bold**) en HTML lisible pour Zoho."""
    import re
    # markdown **gras** -> <strong>
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # lignes
    lines = text.split("\n")
    html = []
    para = []
    for ln in lines:
        if ln.strip() == "":
            if para:
                html.append("<p>" + "<br>".join(para) + "</p>")
                para = []
        else:
            para.append(ln)
    if para:
        html.append("<p>" + "<br>".join(para) + "</p>")
    return "\n".join(html)


def build_html(body, signature):
    """Assemble corps HTML + signature en un email bien structure."""
    return body_to_html(body) + "\n<br>\n" + signature


def load_creds():
    """Priorite aux variables d'environnement (GitHub Actions), sinon fichier local."""
    env = {k: os.environ.get(k)
           for k in ("ZOHO_CLIENT_ID", "ZOHO_CLIENT_SECRET", "ZOHO_REFRESH_TOKEN")}
    if all(env.values()):
        return {"client_id": env["ZOHO_CLIENT_ID"],
                "client_secret": env["ZOHO_CLIENT_SECRET"],
                "refresh_token": env["ZOHO_REFRESH_TOKEN"]}
    with open(TOKENS, encoding="utf-8") as f:
        return json.load(f)


def refresh_token(creds):
    data = urllib.parse.urlencode({
        "refresh_token": creds["refresh_token"],
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://accounts.zoho.com/oauth/v2/token", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.loads(r.read().decode())
    if "access_token" not in j:
        raise RuntimeError("OAuth refresh a echoue: " + json.dumps(j))
    return j["access_token"]


def send_email(token, subject, body, to, cc=""):
    # IMPORTANT (corrige 13/08) : Zoho REFUSE le champ "htmlContent" dans le
    # payload (erreur 404 EXTRA_KEY_FOUND_IN_JSON). Le HTML se passe
    # directement dans "content" (verifie en test reel : HTTP 200 + messageId).
    payload = {"fromAddress": FROM, "toAddress": to, "subject": subject,
               "content": body}
    if cc:
        payload["ccAddress"] = cc
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://mail.zoho.com/api/accounts/%s/messages" % ACCOUNT_ID,
        data=data, method="POST",
        headers={"Authorization": "Zoho-oauthtoken " + token,
                 "Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {"sent": {}, "done_notified": False}


def save_state(state):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def load_followups():
    p = os.path.join(BASE, "followups.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    daily_max = int(args[0]) if args and args[0].isdigit() else DAILY_MAX
    dry = "--dry-run" in sys.argv
    # Limite d'emails par run (pour espacer les envois a differents horaires).
    # Ex: --max 1 avec 3 crons 8h30/12h30/17h30 = 3 emails/jour espaces.
    max_per_run = 1
    for i, a in enumerate(sys.argv):
        if a == "--max" and i + 1 < len(sys.argv):
            try:
                max_per_run = int(sys.argv[i + 1])
            except ValueError:
                pass

    with open(DATA, encoding="utf-8") as f:
        emails = {str(e["num"]): e for e in json.load(f)}

    state = load_state()
    sent = state["sent"]
    today = datetime.date.today().isoformat()

    sent_today = [k for k, v in sent.items()
                  if v.get("on") == today or v.get("sent_relance1") == today
                  or v.get("sent_relance2") == today]
    remaining = [(num, e) for num, e in sorted(emails.items(), key=lambda kv: int(kv[0]))
                 if num not in sent and e.get("to")]

    # Relances J+5 / J+12, prioritaires sur les nouveaux emails
    fu = load_followups()
    due_fu = []
    for num, v in sorted(sent.items()):
        if not v.get("on"):
            continue
        days = (datetime.date.today() - datetime.date.fromisoformat(v["on"])).days
        if "sent_relance1" not in v and days >= fu.get("relance1", {}).get("wait_days", 99):
            due_fu.append(("relance1", num))
        elif "sent_relance2" not in v and days >= fu.get("relance2", {}).get("wait_days", 99):
            due_fu.append(("relance2", num))
    due_fu.sort(key=lambda x: (fu[x[0]].get("wait_days", 99), int(x[1])))

    quota = max(0, daily_max - len(sent_today))
    # Espace les envois : au max `max_per_run` par run (1 = un seul email par horaire)
    quota = min(quota, max_per_run)
    todo_fu = due_fu[:quota]
    todo = remaining[:max(0, quota - len(todo_fu))]

    if dry:
        print("[DRY-RUN] %s | deja envoyes aujourd'hui: %d | quota(ce run): %d | max_per_run: %d" % (today, len(sent_today), quota, max_per_run))
        if todo_fu:
            for stage, num in todo_fu:
                print("  relance %-8s #%s %s -> %s" % (stage, num, emails[num]["prospect"][:40], emails[num]["to"]))
        if todo:
            for num, e in todo:
                print("  enverrait  #%s %s -> %s" % (num, e["prospect"][:40], e["to"]))
        if not todo_fu and not todo:
            print("  rien a envoyer (tout envoye ou quota atteint)")
        return

    if not todo_fu and not todo:
        if not remaining and not state.get("done_notified"):
            state["done_notified"] = True
            save_state(state)
            print("Campagne terminee : les %d emails ont tous ete envoyes. Bravo !" % len(emails))
        return  # sinon silence total (watchdog)

    creds = load_creds()
    token = refresh_token(creds)
    bloquees = load_bloquees()
    lines = []
    bloquees_skips = []
    for stage, num in todo_fu:
        e = emails[num]
        if domaine_bloque(e["to"], bloquees):
            # On ne relance JAMAIS un email piege (ca protege le domaine).
            sent[num]["sent_" + stage] = today
            bloquees_skips.append("relance %s #%s %s (%s bloque)" % (stage, num, e["prospect"][:30], e["to"]))
            continue
        tpl = fu[stage]
        subject = tpl["subject"].replace("{sujet}", e["subject"])
        content = build_html(tpl["body"], SIG)
        r = send_email(token, subject, content, e["to"], e.get("cc", ""))
        sent[num]["sent_" + stage] = today
        lines.append("Relance %-8s #%s %s -> %s" % (stage, num, e["prospect"][:40], e["to"]))
    for num, e in todo:
        if domaine_bloque(e["to"], bloquees):
            # Filtre anti-erreur : on ne peut plus jamais envoyer vers un piege.
            # On marque quand meme le quota consomme pour ne pas renvoyer sans fin.
            sent[num] = {"on": today, "bloque": True}
            bloquees_skips.append("#%s %s -> %s (domaine bloque)" % (num, e["prospect"][:30], e["to"]))
            continue
        content = build_html(e["body"], SIG)
        r = send_email(token, e["subject"], content, e["to"], e.get("cc", ""))
        sent[num] = {"on": today, "messageId": str(r["data"].get("messageId", ""))}
        lines.append("Envoye  #%s %s -> %s" % (num, e["prospect"][:40], e["to"]))

    save_state(state)
    rest = len(emails) - len(sent)
    lines.append("Restants : %d" % rest)
    if bloquees_skips:
        lines.append("BLOQUES (domaines a risque, non envoyes) : %d" % len(bloquees_skips))
        for b in bloquees_skips:
            lines.append("   [BLOQUE] " + b)
    missing = [num for num, e in emails.items() if not e.get("to")]
    if missing:
        lines.append("Adresses manquantes a confirmer : #%s (ATP, JSM Perrin, Usimeca)"
                     % ", ".join(missing))
    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — le cron doit remonter l'erreur
        sys.stderr.write("ERREUR campagne_zoho: %s\n" % exc)
        sys.exit(1)