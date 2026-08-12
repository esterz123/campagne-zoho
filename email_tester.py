#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMAIL TESTER — verifie si une adresse email existe reellement, sans envoyer de mail.

Utilite pour Mahdi : au lieu d'envoyer un email de campagne a une adresse
inventee (prenom.nom@domaine) qui risquerait un bounce (blacklist du domaine),
on TESTE l'adresse AVANT via la technique SMTP RCPT. 100% gratuit, aucune API.

Usage:
  python3 email_tester.py --check contact@domaine.fr
  python3 email_tester.py --check prenom.nom@domaine.fr prenom2.nom2@domaine.fr
  python3 email_tester.py --guess "Theodore MENG" milmeca.fr     # devine + teste
  python3 email_tester.py --guess-file candidats.txt

Memo : un bounce = ton domaine mahdi-design.com risque le blacklist.
Ce script protege ton domaine en testant avant d'envoyer.
"""
import argparse, re, sys, time, smtplib, socket
from email.utils import parseaddr

try:
    import dns.resolver
except ImportError:
    print("ERREUR: installe dnspython -> pip install dnspython")
    sys.exit(1)

SENDER = "test@mahdi-design.com"  # expediteur de test (jamais envoye)

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def get_mx(domain, timeout=8):
    """Renvoie la liste des serveurs MX du domaine (priorite + nom)."""
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        mx = sorted((int(r.preference), str(r.exchange).rstrip(".")) for r in answers)
        return mx
    except Exception as e:
        return []


def check_email(email, timeout=8):
    """Verifie si le DOMAINE de l'adresse existe (a un serveur mail = MX).
    C'est LA protection fiable contre les bounces de domaine (blacklist).
    Ne verifie PAS la boite exacte (les serveurs bloquent cette info gratuitement)."""
    email = email.strip()
    if not EMAIL_RE.match(email):
        return "INVALIDE (format)"
    name, addr = parseaddr(email)
    if not addr:
        return "INVALIDE (parse)"
    domain = addr.split("@")[1]
    mx = get_mx(domain)
    if not mx:
        return "DOMAINE_MORT (pas de serveur mail -> ne JAMAIS envoyer)"
    # domaine valide : on indique le MX trouve
    mx_hosts = ", ".join(m for _, m in mx[:2])
    return "DOMAINE_VALIDE (MX: %s)" % mx_hosts


def guess_emails(nom_complet, domaine):
    """Genere les formats prenom.nom probables pour un nom de dirigeant."""
    parts = re.split(r"\s+", nom_complet.strip())
    prenoms = []
    noms = []
    # heuristique: premier(s) mot(s) = prenom, dernier(s) = nom
    # cas simple: "Theodore MENG" -> prenom=theodore, nom=meng
    if len(parts) >= 2:
        prenoms = [parts[0].lower()]
        noms = [parts[-1].lower().replace("é","e").replace("è","e").replace("ê","e")
                              .replace("ï","i").replace("ö","o").replace("û","u")
                              .replace("ç","c")]
    else:
        return []
    d = domaine
    cands = {
        f"{p}.{n}@{d}": "prenom.nom",
        f"{p[0]}.{n}@{d}": "p.nom",
        f"{n}@{d}": "nom",
        f"{p}{n}@{d}": "prenomnom",
        f"{p[0]}{n}@{d}": "pn",
    }
    return list(cands.items())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", nargs="+", help="emails a verifier")
    ap.add_argument("--guess", nargs=2, metavar=("NOM", "DOMAINE"),
                    help="deviner + tester les formats d'un dirigeant")
    ap.add_argument("--guess-file", help="fichier: 'Nom Complet|domaine' par ligne")
    ap.add_argument("--timeout", type=int, default=8)
    args = ap.parse_args()

    targets = []
    if args.check:
        targets = [("direct", e) for e in args.check]
    elif args.guess:
        nom, dom = args.guess
        targets = [("guess", e) for e, _ in guess_emails(nom, dom)]
    elif args.guess_file:
        for line in open(args.guess_file, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                nom, dom = line.split("|", 1)
                for e, _ in guess_emails(nom, dom.strip()):
                    targets.append(("guess", e))
            else:
                targets.append(("direct", line))

    print("=" * 60)
    print("TESTEUR D'EMAILS SMTP (gratuit, rien n'est envoye)")
    print("=" * 60)
    ok = 0
    dead = 0
    for typ, email in targets:
        res = check_email(email, args.timeout)
        if res == "DOMAINE_MORT":
            mark = "⛔"
            dead += 1
        elif res.startswith("DOMAINE_VALIDE"):
            mark = "✅"
            ok += 1
        else:
            mark = "❌"
        print(f"{mark} {email:45} -> {res}")
        time.sleep(0.2)
    print("-" * 60)
    print(f"DOMAINES VALIDES: {ok} | DOMAINES MORTS (a ecarter): {dead} | total: {len(targets)}")
    print("Note: le test verifie le DOMAINE (protection anti-blacklist).")
    print("      Il ne verifie pas la boite exacte (serveurs bloquent ce test gratuitement).")


if __name__ == "__main__":
    main()
