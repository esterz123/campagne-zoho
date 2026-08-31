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
import time
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
DAILY_MAX = 25  # 5 boites : contact 5/jour + 4 boites neuves 3/jour (warm-up), rotation 15/08

# ---- VERROU ANTI-ERREUR (garde-fou permanent) ----
# Un email dont le domaine est ici est un PIEGE (annuaire/scraper/mail gratuit/
# relais technique/mismatch). Le script REFUSE de l'envoyer : ca protegerait le
# domaine mahdi-design.com d'un bounce = blacklist. Liste dans domaines_bloques.json
BLOQUES = os.path.join(BASE, "domaines_bloques.json")

def load_bloquees():
    """Domaines a ne JAMAIS contacter (annuaires, scrapers, mails gratuits) + emails morts (bounce 550)."""
    try:
        with open(BLOQUES, encoding="utf-8") as f:
            j = json.load(f)
        out = [d.lower() for d in j.get("bloques", [])]
        # 01/09 : les emails specifiques morts (bounce) sont bloques aussi
        out += [e.lower() for e in j.get("_emails_morts", [])]
        return out
    except Exception:
        return []

def domaine_bloque(to, bloquees):
    """True si l'email cible est piege : domaine blackliste OU email deja mort (bounce 550)."""
    if not to or "@" not in to:
        return True  # pas d'adresse = on ne sait pas envoyer = on bloque
    low = to.lower()
    if low in bloquees:  # 01/09 : emails specifiquement morts (bounce) dans la blacklist
        return True
    dom = low.split("@")[1]
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


def load_boites():
    """Les 5 boites d'envoi en rotation. Priorite env (GitHub Actions), sinon
    fichier local .boites_zoho.json (dossier parent de BASE).
    Domaine 2 (mahdi-design.fr, achete au 1er euro) : boites B6-B10, activees
    automatiquement des que les secrets existent. ZERO impact sinon."""
    env = os.environ.get
    boites = []
    if env("ZOHO_CLIENT_ID") and env("ZOHO_CLIENT_SECRET") and env("ZOHO_REFRESH_TOKEN"):
        boites.append({"nom": "contact", "from": "contact@mahdi-design.com",
                       "account_id": env("ZOHO_ACCOUNT_ID", ACCOUNT_ID),
                       "client_id": env("ZOHO_CLIENT_ID"), "client_secret": env("ZOHO_CLIENT_SECRET"),
                       "refresh_token": env("ZOHO_REFRESH_TOKEN"),
                       "max_jour": int(env("ZOHO_MAX_JOUR", "8"))})
    # Boites 2-5 : mahdi-design.com ; boites 6-10 : mahdi-design.fr (2e domaine)
    noms = {2: "commercial", 3: "hello", 4: "info", 5: "direction",
            6: "contact", 7: "commercial", 8: "hello", 9: "info", 10: "direction"}
    for i, nom in noms.items():
        p = "ZOHO_B%d_" % i
        if env(p + "CLIENT_ID") and env(p + "CLIENT_SECRET") and env(p + "REFRESH_TOKEN"):
            domaine = "mahdi-design.fr" if i >= 6 else "mahdi-design.com"
            boites.append({"nom": nom + ("2" if i >= 6 else ""), "from": nom + "@" + domaine,
                           "account_id": env(p + "ACCOUNT_ID", ""),
                           "client_id": env(p + "CLIENT_ID"), "client_secret": env(p + "CLIENT_SECRET"),
                           "refresh_token": env(p + "REFRESH_TOKEN"),
                           "max_jour": int(env(p + "MAX_JOUR", "4"))})
    if boites:
        return boites
    local = os.path.join(os.path.dirname(BASE), ".boites_zoho.json")
    if os.path.exists(local):
        d = json.load(open(local, encoding="utf-8"))
        return [{"nom": k, "from": v.get("from", k + "@mahdi-design.com"),
                 "account_id": v.get("account_id", ""), "client_id": v["client_id"],
                 "client_secret": v["client_secret"], "refresh_token": v["refresh_token"],
                 "max_jour": v.get("max_jour", 3)} for k, v in d.items()]
    with open(TOKENS, encoding="utf-8") as f:
        c = json.load(f)
    return [{"nom": "contact", "from": "contact@mahdi-design.com", "account_id": ACCOUNT_ID,
             "client_id": c["client_id"], "client_secret": c["client_secret"],
             "refresh_token": c["refresh_token"], "max_jour": DAILY_MAX}]


def compte_boite(sent, nom, today):
    """Emails deja envoyes par cette boite aujourd'hui."""
    return sum(1 for v in sent.values()
               if v.get("via") == nom and (v.get("on") == today
                                           or v.get("sent_relance1") == today
                                           or v.get("sent_relance2") == today))


def choisir_boite(boites, sent, today):
    """Boite avec le moins d'envois du jour, sous son plafond max_jour."""
    dispo = [b for b in boites if compte_boite(sent, b["nom"], today) < b["max_jour"]]
    if not dispo:
        return None
    return min(dispo, key=lambda b: compte_boite(sent, b["nom"], today))


def verifier_doublon_global(token_pour, boites, to):
    """Anti-doublon TOUTES boites (fix 16/08) : le redemarrage a prouve qu'un envoi
    non enregistre dans le state peut etre renvoye depuis UNE AUTRE boite.
    Verifie les 5 boites d'envoi avant chaque email."""
    for b in boites:
        try:
            tok = token_pour(b)
        except Exception:
            continue
        if verifier_doublon(tok, b, to):
            return True
    return False


def _norm_addr(a):
    """Normalise une adresse email. L'API Zoho renvoie <email> OU &lt;email&gt; (HTML encode).
    Fix 16/08 : sans le decodage &lt;/&gt;, le verrou anti-doublon ne matchait JAMAIS."""
    return (a or "").replace("<", "").replace(">", "").replace("&lt;", "").replace("&gt;", "").strip().lower()


def verifier_doublon(token, boite, to):
    """Anti-doublon (verite terrain API) : si ce destinataire a deja recu un
    email AUJOURD'HUI depuis cette boite, on ne renvoie pas. Protege contre les
    regressions du state (doublon reel 14/08 : 4,5,6 renvoyes)."""
    try:
        req = urllib.request.Request(
            "https://mail.zoho.com/api/accounts/%s/messages/search?searchKey=in%%3Asent&limit=30" % boite["account_id"],
            headers={"Authorization": "Zoho-oauthtoken " + token})
        j = json.load(urllib.request.urlopen(req, timeout=20))
        today = datetime.date.today().isoformat()
        cible = _norm_addr(to)
        for m in j.get("data", []):
            if _norm_addr(m.get("toAddress")) == cible:
                ts = int(m.get("receivedTime", 0)) / 1000
                d = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                if d == today:
                    return True
    except Exception:
        pass
    return False


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


def send_email(token, subject, body, to, cc="", boite=None):
    # IMPORTANT (corrige 13/08) : Zoho REFUSE le champ "htmlContent" dans le
    # payload (erreur 404 EXTRA_KEY_FOUND_IN_JSON). Le HTML se passe
    # directement dans "content" (verifie en test reel : HTTP 200 + messageId).
    boite = boite or {"from": FROM, "account_id": ACCOUNT_ID}
    payload = {"fromAddress": boite["from"], "toAddress": to, "subject": subject,
               "content": body}
    if cc:
        payload["ccAddress"] = cc
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://mail.zoho.com/api/accounts/%s/messages" % boite["account_id"],
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


def envoi_go2(dry=False):
    """Envois GO nominatifs (Mahdi a dit OUI le 30/08): SIMI livraison diagnostic
    + ITPLAST relance 3 breakup. Idempotent via marqueurs dans campagne_state.json.
    Bypass SEND_LOCK (declenchement manuel unique) ; anti-doublon = marqueur state."""
    liv = os.path.join(BASE, "livrable")
    cibles = [
        ("1", "go2_simi", "adv.simi@id-casting.com", "go2_livraison_simi",
         "Diagnostic livre en ligne le 31/08 (OFFRE V2)"),
        ("11", "go2_itplast", "andre.muller@itplast.com", "go2_relance3_itplast",
         "Relance 3 breakup envoyee le 31/08 (site renvoie vers annuaire)"),
        ("44", "go2_fpsa", "fd@fonderies-dechaumont.com", "go2_urgence_fpsa",
         "Urgence pirate: liens xena-casino.gr verifies 31/08 03h30, intervention 150 EUR"),
    ]
    state = load_state()
    sent = state.setdefault("sent", {})
    boites = load_boites()
    if not boites:
        print("GO2: aucune boite config (secrets absents), rien envoye.")
        return
    boite = boites[0]
    tok = None
    if not dry:
        tok = refresh_token(boite)
    for num, slug, to, marqueur, note in cibles:
        ent = sent.setdefault(num, {})
        if ent.get(marqueur):
            print("GO2: %s deja envoye (%s), skip" % (slug, ent[marqueur]))
            continue
        html = open(os.path.join(liv, slug + ".html"), encoding="utf-8").read()
        objet = open(os.path.join(liv, slug + ".objet"), encoding="utf-8").read().strip()
        if dry:
            print("GO2 DRY: %s -> %s objet='%s' (%d octets)" % (slug, to, objet[:55], len(html.encode("utf-8"))))
            continue
        r = send_email(tok, objet, html, to, boite=boite)
        code = (r.get("status") or {}).get("code")
        mid = (r.get("data") or {}).get("messageId", "")
        print("GO2: %s -> %s code=%s messageId=%s" % (slug, to, code, mid))
        if str(code) == "200":
            ent[marqueur] = datetime.datetime.now().isoformat()
            ent["note"] = note
            save_state(state)
        else:
            print("GO2 ECHEC %s: %s" % (slug, json.dumps(r)[:300]))
            return


def main():
    # KILL-SWITCH URGENCE : si le fichier PAUSE_ENVOIS existe, aucun envoi (cloud + local).
    if os.path.exists(os.path.join(BASE, "PAUSE_ENVOIS")):
        print("ENVOIS PAUSES : fichier PAUSE_ENVOIS present, aucun envoi ce run.")
        return
    # GO nominatifs (SIMI + ITPLAST) : mode manuel idempotent, avant le verrou normal.
    if "--go2" in sys.argv:
        envoi_go2(dry="--dry-run" in sys.argv)
        return
    # VERROU LOCAL : un seul processus d'envoi a la fois (fix 16/08, anti-double-run).
    lock = os.path.join(BASE, "SEND_LOCK")
    if "--dry-run" not in sys.argv:
        if os.path.exists(lock):
            try:
                age = time.time() - os.path.getmtime(lock)
            except Exception:
                age = 0
            if age < 3 * 3600:
                print("ENVOI BLOQUE : un autre processus tourne (SEND_LOCK frais, %.0f min)." % (age / 60))
                return
            print("SEND_LOCK stale (%.0f min) : reprise." % (age / 60))
        open(lock, "w").write(datetime.datetime.now().isoformat())
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    # Quota journalier : DAILY_MAX par defaut (warm-up), ou 1er argument numerique positionnel (legacy).
    # IMPORTANT (fix 16/08) : --max ne doit JAMAIS devenir le quota journalier, sinon 3 relances
    # envoyees le matin epuisent le quota et plus rien ne part de la journee.
    daily_max = DAILY_MAX
    # 2e domaine (mahdi-design.fr, boites B6-B10) : plafond global x2 quand il est actif
    if any(os.environ.get("ZOHO_B%d_CLIENT_ID" % i) for i in (6, 7, 8, 9, 10)):
        daily_max = max(daily_max, 50)
    if "--max" not in sys.argv and args and args[0].isdigit():
        daily_max = int(args[0])
    dry = "--dry-run" in sys.argv
    # Limite d'emails par run (pour espacer les envois a differents horaires).
    # Ex: --max 1 avec 3 crons 8h30/12h30/17h30 = 3 emails/jour espaces.
    max_per_run = 5  # 5 boites (contact 5 + 4x3) = 17/jour max ; 5/run vide 154 restants en ~3x plus vite, espacement 3min conserve (anti-ban OK)
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
    boites = load_boites()

    sent_today = [k for k, v in sent.items()
                  if v.get("on") == today or v.get("sent_relance1") == today
                  or v.get("sent_relance2") == today]
    # PREUVE-DRIVEN (31/08) : envoyer d'abord les sites les plus cassés.
    # constats_sites.json (verificateur_site.py) porte la note /100 mesurée.
    # Sans constat = note neutre 50 (après les cassés, avant les nickel).
    try:
        NOTES = {k: (v.get("note") if v.get("note") is not None else 50)
                 for k, v in json.load(open(os.path.join(BASE, "constats_sites.json"),
                                            encoding="utf-8")).items()}
    except Exception:
        NOTES = {}
    remaining = [(num, e) for num, e in sorted(
        emails.items(), key=lambda kv: (NOTES.get(kv[0], 50), int(kv[0])))
        if num not in sent and e.get("to")]

    # Relances J+3 / J+7, prioritaires sur les nouveaux emails
    fu = load_followups()
    # Exclusions : ne JAMAIS relancer quelqu'un qui a repondu (repondeur marque
    # sent[num]["replied"]) ni quelqu'un avec une relance dediee (relances_conges.json).
    conges_to = set()
    try:
        rc = json.load(open(os.path.join(BASE, "relances_conges.json"), encoding="utf-8"))
        conges_to = {r.get("to", "").strip().lower() for r in rc.get("relances", [])}
    except Exception:
        pass
    due_fu = []
    for num, v in sorted(sent.items()):
        if not v.get("on"):
            continue
        if v.get("replied"):
            continue  # le prospect a repondu : conversation en cours, pas de relance
        if emails[num].get("to", "").strip().lower() in conges_to:
            continue  # relance dediee programmee (retour de conges) : pas de relance auto
        days = (datetime.date.today() - datetime.date.fromisoformat(v["on"])).days
        if "sent_relance1" not in v and days >= fu.get("relance1", {}).get("wait_days", 99):
            due_fu.append(("relance1", num))
        elif "sent_relance2" not in v and days >= fu.get("relance2", {}).get("wait_days", 99):
            due_fu.append(("relance2", num))
        elif "sent_relance3" not in v and days >= fu.get("relance3", {}).get("wait_days", 99):
            due_fu.append(("relance3", num))
    due_fu.sort(key=lambda x: (fu[x[0]].get("wait_days", 99), int(x[1])))

    quota = max(0, daily_max - len(sent_today))
    # LEVIER x1000 : jusqu'a 2 relances + 3 nouveaux par run (max_per_run=5, plafond boites intact)
    quota = min(quota, max_per_run)
    todo_fu = due_fu[:min(quota, 2)]
    todo = remaining[:min(max(0, quota - len(todo_fu)), 3)]
    # Si quota=2 : 2 relances. Si quota=5 : 2 relances + 3 nouveaux en meme run. DELAY_S=180s protege la delivrabilite.

    if dry:
        print("[DRY-RUN] %s | deja envoyes aujourd'hui: %d | quota(ce run): %d | max_per_run: %d" % (today, len(sent_today), quota, max_per_run))
        if todo_fu:
            for stage, num in todo_fu:
                b = choisir_boite(boites, sent, today)
                print("  relance %-8s #%s %s -> %s (via %s)" % (stage, num, emails[num].get("prospect", emails[num].get("nom", "?"))[:40], emails[num]["to"], b["nom"] if b else "AUCUNE"))
        if todo:
            for num, e in todo:
                b = choisir_boite(boites, sent, today)
                print("  enverrait  #%s %s -> %s (via %s)" % (num, e.get("prospect", e.get("nom", "?"))[:40], e["to"], b["nom"] if b else "AUCUNE"))
        if not todo_fu and not todo:
            print("  rien a envoyer (tout envoye ou quota atteint)")
        return

    if not todo_fu and not todo:
        if not remaining and not state.get("done_notified"):
            state["done_notified"] = True
            save_state(state)
            print("Campagne terminee : les %d emails ont tous ete envoyes. Bravo !" % len(emails))
        return  # sinon silence total (watchdog)

    tokens = {}

    def token_pour(boite):
        if boite["nom"] not in tokens:
            tokens[boite["nom"]] = refresh_token(boite)
        return tokens[boite["nom"]]
    bloquees = load_bloquees()
    lines = []
    bloquees_skips = []
    # Espacement anti-spam : 3 min entre envois (x1000: 4x plus rapide que 12 min, reste safe pour Zoho)
    import time as _time
    DELAY_S = 180
    envois_reels = 0
    for stage, num in todo_fu:
        e = emails[num]
        if domaine_bloque(e["to"], bloquees):
            # On ne relance JAMAIS un email piege (ca protege le domaine).
            sent[num]["sent_" + stage] = today
            bloquees_skips.append("relance %s #%s %s (%s bloque)" % (stage, num, e.get("prospect", e.get("nom", "?"))[:30], e["to"]))
            continue
        tpl = fu[stage]
        subject = tpl["subject"].replace("{sujet}", e["subject"])
        # 17/08 + 20/08 : branchement sur contraints concrets prêts (relances_constats/).
        # Privilégie le fichier généré par sequencage_constats.py (constats réels sur le site du prospect)
        # au template followups.json (texte générique, demande de permission).
        corps_relance = ""
        if stage in ("relance1", "relance2", "relance3"):
            fn = os.path.join(BASE, "relances_constats", f"{stage}_prospect_{num}.txt")
            if os.path.exists(fn):
                fh = open(fn, encoding="utf-8")
                txt = fh.read()
                fh.close()
                # format : "OBJET: Re : <sujet>\n\n<body>"
                if txt.startswith("OBJET"):
                    idx = txt.index("\n\n")
                    corps_relance = txt[idx + 2:]
                    # subject reste comme dans tpl (Re : <sujet>), ok
        if corps_relance == "":
            corps_relance = tpl["body"].replace("{sujet}", e["subject"])
        for doublon in ("?.", "!."):
            corps_relance = corps_relance.replace(doublon, doublon[0])
        content = build_html(corps_relance, SIG)
        boite = choisir_boite(boites, sent, today)
        if not boite:
            lines.append("Toutes les boites sont a leur plafond du jour")
            break
        if verifier_doublon_global(token_pour, boites, e["to"]):
            sent[num]["sent_" + stage] = today
            lines.append("DOUBLON evite (deja envoye aujourd'hui, toutes boites) : %s" % e["to"])
            continue
        r = send_email(token_pour(boite), subject, content, e["to"], e.get("cc", ""), boite)
        sent[num]["sent_" + stage] = today
        sent[num]["via"] = boite["nom"]
        save_state(state)  # fix 16/08 : sauvegarde APRES CHAQUE envoi (un crash ne perd plus rien)
        lines.append("Relance %-8s #%s %s -> %s (via %s)" % (stage, num, e.get("prospect", e.get("nom", "?"))[:40], e["to"], boite["nom"]))
        envois_reels += 1
        if envois_reels < len(todo_fu) + len(todo):
            _time.sleep(DELAY_S)
    for num, e in todo:
        if domaine_bloque(e["to"], bloquees):
            # Filtre anti-erreur : on ne peut plus jamais envoyer vers un piege.
            # On marque quand meme le quota consomme pour ne pas renvoyer sans fin.
            sent[num] = {"on": today, "bloque": True}
            bloquees_skips.append("#%s %s -> %s (domaine bloque)" % (num, e.get("prospect", e.get("nom", "?"))[:30], e["to"]))
            continue
        # 18/08 : brancher le premier message sur la V2 (constats concrets) si presente.
        corps_premier = e.get("body", "")
        fn_v2 = os.path.join(BASE, "premiers_messages_v2", f"premier_msg_v2_prospect_{num}.txt")
        if os.path.exists(fn_v2):
            with open(fn_v2, encoding="utf-8") as fh2:
                txt2 = fh2.read()
            if txt2.startswith("OBJET"):
                idx = txt2.index("\n\n")
                corps_premier = txt2[idx + 2:]
        # 28/08 PARETO : page diag personnalisee -> le prospect voit la valeur AVANT de repondre
        man_path = os.path.join(BASE, "diag_pages.json")
        if os.path.exists(man_path):
            try:
                man = json.load(open(man_path, encoding="utf-8"))
                url_diag = (man.get(num) or {}).get("url")
                if url_diag:
                    corps_premier += ("\n\nP.S. J'ai deja prepare le diagnostic express de votre site : "
                                      "score, points bloquants, tout est ici : %s" % url_diag)
                else:
                    corps_premier += ("\n\nP.S. Testez vous-meme votre site en 30 secondes (gratuit, sans inscription) : "
                                      "https://mahdi-design.com/audit.html")
            except Exception:
                pass
        content = build_html(corps_premier, SIG)
        boite = choisir_boite(boites, sent, today)
        if not boite:
            lines.append("Toutes les boites sont a leur plafond du jour")
            break
        if verifier_doublon_global(token_pour, boites, e["to"]):
            sent[num] = {"on": today, "doublon": True, "via": boite["nom"]}
            lines.append("DOUBLON evite (deja envoye aujourd'hui, toutes boites) : %s" % e["to"])
            continue
        r = send_email(token_pour(boite), e["subject"], content, e["to"], e.get("cc", ""), boite)
        resp = r  # fix 27/08 : send_email retourne DEJA le JSON parse (double-parse = crash)
        sent[num] = {"on": today, "messageId": str(resp.get("data", {}).get("messageId", "")), "via": boite["nom"],
                     "status_code": resp.get("status", {}).get("code"),
                     "to": e["to"], "body": content}
        save_state(state)  # fix 16/08 : sauvegarde APRES CHAQUE envoi (un crash ne perd plus rien)
        lines.append("Envoye  #%s %s -> %s (via %s)" % (num, e.get("prospect", e.get("nom", "?"))[:40], e["to"], boite["nom"]))
        envois_reels += 1
        if envois_reels < len(todo_fu) + len(todo):
            _time.sleep(DELAY_S)

    save_state(state)
    try:
        os.remove(lock)  # liberation du verrou local (fix 16/08)
    except OSError:
        pass
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