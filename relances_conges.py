#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relances programmees au retour de conges.

Les prospects qui ont repondu par un out-of-office (Slicom, Adduxi) recoivent
une relance personnalisee le jour de leur retour. Chaque relance a une date
fixe (send_on) et le constat est REVERIFIE en direct avant envoi (regle
outreach-messages-obligatoires : zero hallucination).

Usage : python3 relances_conges.py [--dry-run]
Cloud : GitHub Actions (secrets ZOHO_*, DISCORD_WEBHOOK), cron quotidien 7h UTC.
Local : lit .zoho_tokens.json dans le dossier parent (Bureau/prospection/).
"""
import json, os, sys, datetime, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import campagne_zoho as CZ

REL_F = os.path.join(BASE, "relances_conges.json")
DRY = "--dry-run" in sys.argv


def notify_discord(text):
    wh = os.environ.get("DISCORD_WEBHOOK", "")
    if not wh:
        return
    req = urllib.request.Request(wh, data=json.dumps({"content": text}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print("  [notif Discord KO]", e)


def check_constat(url):
    """Re-verifie que le site est bien un WordPress (constat encore vrai)."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0"})
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore").lower()
        return ("wp-content" in html) or ("wordpress" in html)
    except Exception:
        return False


def main():
    data = json.load(open(REL_F, encoding="utf-8"))
    today = datetime.date.today().isoformat()
    rapports = []
    for r in data["relances"]:
        if r.get("sent") or r.get("send_on") != today:
            continue
        ok = check_constat(r["check_url"])
        if not ok:
            rapports.append("- %s : constat NON confirme (%s) -> envoi manuel recommande" % (r["id"], r["check_url"]))
            continue
        corps = CZ.build_html(r["body"], CZ.SIG)
        if DRY:
            rapports.append("- %s : [dry-run] serait envoye a %s" % (r["id"], r["to"]))
            continue
        creds = CZ.load_creds()
        token = CZ.refresh_token(creds)
        CZ.send_email(token, r["subject"], corps, r["to"])
        r["sent"] = True
        rapports.append("- %s : ENVOYE a %s" % (r["id"], r["to"]))
    if rapports:
        json.dump(data, open(REL_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        msg = "**Relances retour de conges**\n" + "\n".join(rapports)
        print(msg)
        if not DRY:
            notify_discord(msg)
    else:
        print("Relances conges : rien a envoyer aujourd'hui.")


if __name__ == "__main__":
    main()
