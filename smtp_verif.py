#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VERIF SMTP 01/09 (Pareto : chaque bounce nous coute de la reputation).
Verifie que l adresse existe VRAIMENT avant envoi, en 2 etapes gratuites :
  1. MX du domaine existe ? (domaine mort = bounce garanti)
  2. RCPT TO direct sur le MX ? (le serveur repond "user unknown" = adresse morte)
Resultat : smtp_verif.json {email: "ok"|"mx_manquant"|"user_unknown"|"greylist"|"erreur"}
Seules les adresses "ok" et "greylist" partent. Les autres sont marquees bounce.
Regles Mahdi : zero depense, zero mensonge.
"""
import json, os, re, sys, socket, smtplib, dns.resolver, dns.exception

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "smtp_verif.json")
DATA = os.path.join(BASE, "campagne_data.json")
STATE = os.path.join(BASE, "campagne_state.json")

HELO = "mahdi-design.com"
FROM = "contact@mahdi-design.com"

def mx_domaine(dom):
    try:
        recs = dns.resolver.resolve(dom, "MX", lifetime=8)
        mxs = sorted((r.preference, str(r.exchange).rstrip(".")) for r in recs)
        return [m[1] for m in mxs]
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout, socket.herror):
        return []

def rcpt_verif(email, mxs, timeout=12):
    """RCPT TO direct : le serveur accepte-t-il cette adresse ?"""
    for mx in mxs[:2]:
        try:
            with smtplib.SMTP(mx, 25, timeout=timeout) as srv:
                srv.ehlo_or_helo_if_needed()
                code, _ = srv.docmd("MAIL", "FROM:<%s>" % FROM)
                if code != 250:
                    return "mail_from_refuse"
                code, msg = srv.docmd("RCPT", "TO:<%s>" % email)
                if code == 250:
                    try: srv.docmd("RSET")
                    except Exception: pass
                    return "ok"
                elif code in (450, 451, 452):
                    return "greylist"  # serveur prudent : on tente quand meme, bounce non garanti
                elif code in (550, 551, 553):
                    return "user_unknown"
                else:
                    return "refuse_%d" % code
        except smtplib.SMTPServerDisconnected:
            continue
        except (socket.timeout, ConnectionRefusedError, OSError):
            continue
    return "mx_injoignable"

def main():
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    verif = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    data = json.load(open(DATA, encoding="utf-8"))
    state = json.load(open(STATE, encoding="utf-8"))
    sent = state["sent"]
    restants = [e for e in data if str(e["num"]) not in sent and e.get("to")]
    faits = 0
    for e in restants:
        if faits >= limite:
            break
        email = e["to"].strip().lower()
        num = str(e["num"])
        if email in verif:
            continue
        dom = email.split("@")[1]
        mxs = mx_domaine(dom)
        if not mxs:
            verif[email] = "mx_manquant"
            verdict = "MX MANQUANT (domaine mort)"
        else:
            verif[email] = rcpt_verif(email, mxs)
            verdict = verif[email]
        json.dump(verif, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("  #%s %s -> %s" % (num, email, verdict), flush=True)
        faits += 1
    ok = sum(1 for v in verif.values() if v in ("ok", "greylist"))
    mort = sum(1 for v in verif.values() if v in ("mx_manquant", "user_unknown"))
    print("TOTAL: %d verifiees | ok: %d | mortes: %d | a retester: %d" % (
        len(verif), ok, mort, len(verif) - ok - mort))

if __name__ == "__main__":
    main()
