#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICATEUR SMTP RCPT — verifie si une boite email existe VRAIMENT,
en se connectant au serveur MX et en testant l'adresse (technique RCPT TO).
Fiable a ~90-95% (certains serveurs anti-spam masquent la reponse).

IMPORTANT pour Mahdi : cela permet d'envoyer UNIQUEMENT aux boites qui
existent reellement => zero bounce => pas de blacklist de mahdi-design.com.

Usage:
  python3 verify_smtp.py --check "prenom.nom@domaine.fr" "contact@domaine.fr"
  python3 verify_smtp.py --guess "Theodore MENG" milmeca.fr
"""
import argparse, re, sys, smtplib, socket, time
import dns.resolver

SENDER = "verif@mahdi-design.com"
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def get_mx(domain, timeout=8):
    try:
        ans = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        return sorted((int(r.preference), str(r.exchange).rstrip(".")) for r in ans)
    except Exception:
        return []

def smtp_verify(email, timeout=8):
    """Verifie via RCPT TO si la boite existe. Renvoie (bool, detail)."""
    domain = email.split("@")[1]
    mx = get_mx(domain)
    if not mx:
        return False, "domaine sans MX (mort)"
    host = mx[0][1]
    try:
        with smtplib.SMTP(host, 25, timeout=timeout) as s:
            s.ehlo(name="mail.mahdi-design.com")
            s.mail(SENDER)
            code, msg = s.rcpt(email)
            s.quit()
            return code in (250, 251, 252), f"RCPT code {code}"
    except (socket.timeout, ConnectionRefusedError, OSError, smtplib.SMTPException) as e:
        return None, f"serveur bloque/injoignable ({type(e).__name__})"

def guess_emails(nom_complet, domaine):
    parts = re.split(r"\s+", nom_complet.strip())
    if len(parts) < 2:
        return []
    prenom = parts[0].lower()
    nom = parts[-1].lower()
    for a, b in [("é","e"),("è","e"),("ê","e"),("à","a"),("ç","c"),("ô","o"),("î","i"),("ï","i"),("û","u"),("ö","o"),(" '",""),("'","")]:
        nom = nom.replace(a, b); prenom = prenom.replace(a, b)
    p = prenom; n = nom
    return {
        f"{p}.{n}@{domaine}": "prenom.nom",
        f"{p[0]}.{n}@{domaine}": "p.nom",
        f"{n}@{domaine}": "nom",
        f"{p}{n}@{domaine}": "prenomnom",
        f"{p[0]}{n}@{domaine}": "pn",
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", nargs="+", help="emails a verifier")
    ap.add_argument("--guess", nargs=2, metavar=("NOM","DOMAINE"))
    ap.add_argument("--guess-file")
    ap.add_argument("--timeout", type=int, default=8)
    args = ap.parse_args()

    targets = []
    if args.check:
        targets = [("direct", e) for e in args.check]
    elif args.guess:
        for e, fmt in guess_emails(*args.guess).items():
            targets.append(("guess", e, fmt))
    elif args.guess_file:
        for line in open(args.guess_file, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                nom, dom = line.split("|", 1)
                for e, fmt in guess_emails(nom, dom.strip()).items():
                    targets.append(("guess", e, fmt))
            else:
                targets.append(("direct", line, ""))

    print("="*62)
    print("VERIFICATEUR SMTP RCPT (teste si la boite existe vraiment)")
    print("="*62)
    ok, dead, blocked = [], [], []
    for t in targets:
        if len(t) == 2:
            typ, email = t; fmt = ""
        else:
            typ, email, fmt = t
        res, detail = smtp_verify(email, args.timeout)
        if res is True:
            mark = "✅ EXISTE"; ok.append(email)
        elif res is None:
            mark = "➖ bloque"; blocked.append(email)
        else:
            mark = "❌ n'existe pas"; dead.append(email)
        print(f"{mark} {email:42} ({fmt or 'direct'}) {detail}")
        time.sleep(0.3)
    print("-"*62)
    print(f"✅ Existants: {len(ok)} | ❌ Mortes: {len(dead)} | ➖ Bloques (reverifier): {len(blocked)}")
    print("\nÀ ENVOYER (existants):")
    for e in ok:
        print("  ", e)

if __name__ == "__main__":
    main()
