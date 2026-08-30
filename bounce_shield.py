#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOUNCE SHIELD 28/08 (Pareto: proteger la delivrabilite = capital n1).
Apres chaque run campagne: cherche les bounces (mailer-daemon / failure) dans la
boite contact, marque le prospect mort dans campagne_state (bounce: true) et
blackliste son domaine dans domaines_bloques.json -> jamais re-envoye.
Toujours exit 0 (un crash du bouclier ne doit jamais casser le run).
Regles Mahdi: zero tiret long, zero U+2019."""
import json, os, re, sys, urllib.request, urllib.parse, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "campagne_state.json")
BL = os.path.join(BASE, "domaines_bloques.json")

def zoho_token(boite):
    d = urllib.parse.urlencode({"refresh_token": boite["refresh_token"],
        "client_id": boite["client_id"], "client_secret": boite["client_secret"],
        "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://accounts.zoho.com/oauth/v2/token", data=d)
    return json.load(urllib.request.urlopen(req, timeout=30))["access_token"]

def inbox_msgs(token, account_id, limit=50):
    url = ("https://mail.zoho.com/api/accounts/%s/messages/search?searchKey=%s&limit=%d"
           % (account_id, urllib.parse.quote("in:inbox"), limit))
    req = urllib.request.Request(url, headers={"Authorization": "Zoho-oauthtoken " + token})
    j = json.load(urllib.request.urlopen(req, timeout=25))
    return j.get("data", [])

def is_bounce(m):
    frm = (m.get("fromAddress") or "").lower()
    sub = (m.get("subject") or "").lower()
    if any(k in frm for k in ("mailer-daemon", "postmaster@", "MAILER-DAEMON".lower())):
        return True
    return any(k in sub for k in ("failure", "undeliver", "delivery status notification", "echec de livraison"))

def extract_dead_to(body):
    # le destinataire mort apparait dans le corps du bounce (to / original recipient / ultimate recipient)
    m = re.search(r"(?:to|recipient|destination)[^\n<]{0,40}<([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})>", body, re.I)
    if m: return m.group(1).lower()
    m = re.search(r"\b([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})\b", body, re.I)
    return m.group(1).lower() if m else None

def main():
    try:
        bx = json.load(open(os.path.join(os.path.dirname(BASE), ".boites_zoho.json"), encoding="utf-8"))
    except Exception:
        print("BOUNCE SHIELD: pas de boites locales (cloud: skip, bounces geres par blacklist manuelle)")
        return 0
    # 01/09 : scanner TOUTES les boites (un bounce peut arriver sur n importe laquelle)
    boites_scan = [v for k, v in (bx.items() if isinstance(bx, dict) else enumerate(bx))
                   if isinstance(v, dict) and v.get("account_id")]
    st = json.load(open(STATE, encoding="utf-8"))
    sent = st["sent"]
    try:
        bl = json.load(open(BL, encoding="utf-8"))
    except Exception:
        bl = {}
    blocs = [b for b in bl if not b.startswith("_")]
    data = json.load(open(os.path.join(BASE, "campagne_data.json"), encoding="utf-8"))
    num_par_to = {}
    for e in data:
        t = (e.get("to") or "").strip().lower()
        if t: num_par_to.setdefault(t, e["num"])
    n_dom = 0
    all_msgs = []
    for bx_item in boites_scan:
        try:
            tok = zoho_token(bx_item)
            all_msgs.extend(inbox_msgs(tok, bx_item["account_id"]))
        except Exception as e:
            print("BOUNCE SHIELD: boite ignoree: %s" % str(e)[:80])
    if not all_msgs:
        print("BOUNCE SHIELD: aucune boite lisible, skip")
        return 0
    for m in all_msgs:
        if not is_bounce(m): continue
        try:
            req = urllib.request.Request(
                "https://mail.zoho.com/api/accounts/%s/messages/%s/content" % (x["account_id"], m.get("messageId")),
                headers={"Authorization": "Zoho-oauthtoken " + token})
            body = urllib.request.urlopen(req, timeout=20).read(120000).decode("utf-8", "ignore")
        except Exception:
            body = m.get("summary", "")
        dead = extract_dead_to(body)
        if not dead: continue
        num = num_par_to.get(dead)
        if num:
            sent[str(num)] = dict(sent.get(str(num), {}), on=sent.get(str(num), {}).get("on", datetime.date.today().isoformat()),
                                  bounce=True, note="bounce detecte %s" % datetime.date.today())
        # 01/09 REGLE PARETO : blacklist l EMAIL specifique (pas le domaine entier).
        # Un bounce 550 "user unknown" = CETTE adresse est morte, le reste du domaine peut etre vivant.
        # Blacklister le domaine entier tuait des leads chauds (simi.fr, usimeca.fr...).
        morts = bl.setdefault("_emails_morts", [])
        if dead not in morts:
            morts.append(dead)
            n_dom += 1
        # blacklist domaine UNIQUEMENT si le domaine n existe plus (NXDOMAIN visible dans le bounce)
        body_low = body.lower()
        if "nxdomain" in body_low or "no such domain" in body_low or "domain not found" in body_low:
            dom = dead.split("@")[1]
            if dom not in blocs:
                blocs.append(dom)
                bl[dom] = "domaine inexistant (NXDOMAIN)"
    if n_dom:
        bl["_maj"] = "bounce shield %s" % datetime.date.today()
        for b in blocs: bl.setdefault(b, "bounce")
        json.dump(bl, open(BL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("BOUNCE SHIELD: %d nouveaux domaines blacklists, bounces marques" % n_dom)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("BOUNCE SHIELD err (non bloquant): %s" % str(e)[:120])
        sys.exit(0)
