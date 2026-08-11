#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notifier Discord — rapport quotidien de la campagne sur un webhook Discord.

Usage:
    python notify_discord.py            # envoie le rapport du jour
    python notify_discord.py --test     # message de test (verification cablage)
    python notify_discord.py --dry-run  # affiche le rapport sans l'envoyer
    python notify_discord.py --error    # message d'erreur (utilise par le workflow)

L'URL du webhook vient de la variable d'environnement DISCORD_WEBHOOK
(secret GitHub). Absente -> rien n'est envoye, aucune erreur.
"""
import os
import json
import sys
import datetime
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "campagne_state.json")
DATA = os.path.join(BASE, "campagne_data.json")
PROSPECTS = os.path.join(BASE, "nouveau_prospects.json")


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def build_message():
    today = datetime.date.today().isoformat()
    state = load(STATE, {"sent": {}})
    data = load(DATA, [])
    prospects = load(PROSPECTS, [])

    sent = state.get("sent", {})
    sent_today = [k for k, v in sent.items() if v.get("on") == today]
    total_sent = len(sent)
    total_emails = len(data) if isinstance(data, list) else 0
    remaining = max(0, total_emails - total_sent)

    names = {str(e.get("num")): e.get("prospect", "")
             for e in data if isinstance(e, dict)}

    def clean_name(k):
        name = names.get(k) or sent[k].get("note", "")
        # le champ prospect contient deja le numero ("1 — SIMI...") -> on l'enleve
        if name and name[0].isdigit() and " — " in name:
            name = name.split(" — ", 1)[1]
        return name

    n_prospects = len(prospects) if isinstance(prospects, list) else 0

    lines = ["**Rapport campagne — %s**" % today]
    if sent_today:
        lines.append("✅ Envoyes aujourd'hui : **%d**" % len(sent_today))
        for k in sorted(sent_today, key=int):
            name = clean_name(k)
            lines.append("   - #%s %s" % (k, name))
    else:
        lines.append("Aucun envoi aujourd'hui (quota atteint ou file vide).")
    lines.append("📬 Total envoye : **%d** / %d — reste **%d**"
                 % (total_sent, total_emails, remaining))
    if n_prospects:
        lines.append("🔍 Nouveaux prospects trouves : **%d**" % n_prospects)
    lines.append("👀 Pense a verifier les reponses sur webmail : mail.zoho.com")
    return "\n".join(lines)


def post(webhook, content):
    payload = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(webhook, data=payload, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def main():
    webhook = os.environ.get("DISCORD_WEBHOOK", "")
    dry = "--dry-run" in sys.argv
    test = "--test" in sys.argv
    error = "--error" in sys.argv

    if error:
        content = ("⚠️ **La campagne a rencontre une erreur aujourd'hui.**\n"
                   "Voir les logs : https://github.com/esterz123/campagne-zoho/actions")
    elif test:
        content = ("🔔 **Test Discord — cablage OK !**\n"
                   "Les rapports de campagne arriveront ici chaque matin.")
    else:
        content = build_message()

    if dry or not webhook:
        print("[NOTIFY-DISCORD] webhook present: %s" % bool(webhook))
        print(content)
        return

    status = post(webhook, content)
    print("[NOTIFY-DISCORD] envoye (HTTP %d)" % status)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write("ERREUR notify_discord: %s\n" % exc)
        sys.exit(1)