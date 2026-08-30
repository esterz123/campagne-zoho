#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIVRAISON AUTO v1 — ferme la chaine d'argent : paiement -> diagnostic genere -> livre au client.
============================================================================================
Quand le detecteur de paiement (repondeur) a cree une entree dans suivi_revenus.json
(statut "encaisse", source "paypal"), ce script :
  1. Cherche le prospect correspondant dans campagne_data.json (matching email payeur)
  2. Genere le diagnostic docx (generateur_diagnostic.py <num>)
  3. Envoie l'email de livraison avec le docx en piece jointe (Zoho multipart)
  4. Marque l'entree "livre" dans suivi_revenus.json (anti-double-envoi)

Usage :
  python livraison_auto.py --dry-run    # affiche ce qui serait livre, ne touche a rien
  python livraison_auto.py              # livre les diagnostics payes non livres

Regles :
  - JAMAIS d'envoi sans paiement detecte (statut != encaisse -> ignore)
  - JAMAIS de double livraison (entree deja "livre" -> ignore)
  - ZERO U+2019 et ZERO tiret long dans le corps
  - Piece jointe via API Zoho multipart (endpoint /messages)
"""
import json, os, sys, re, uuid, datetime, subprocess, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

REVENUS = os.path.join(BASE, "suivi_revenus.json")
CAMPAGNE = os.path.join(BASE, "campagne_data.json")
LIV = os.path.join(BASE, "livrable")  # aligne sur generateur_diagnostic.py (dans le repo, dispo cloud)
MESSAGES = os.path.join(BASE, "messages_livraison.json")

DRY = "--dry-run" in sys.argv

# Mecanisme de connexion identique au repondeur : env vars (GitHub Actions)
# ou .boites_zoho.json local. Reutilise les fonctions deja testees.
import repondeur as R


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def multipart_encode(fields, files):
    """Encode multipart/form-data (champs + fichiers) sans dependance externe."""
    boundary = "----hermes" + uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, k, v)).encode("utf-8")
    for k, (fname, content) in files.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\nContent-Type: application/octet-stream\r\n\r\n" % (boundary, k, fname)).encode("utf-8")
        body += content
        body += b"\r\n"
    body += ("--%s--\r\n" % boundary).encode("utf-8")
    return body, boundary


def send_email_pj(token, account_id, fro, to, subject, content, docx_path):
    """Envoie un email avec piece jointe via Zoho Mail API (multipart)."""
    with open(docx_path, "rb") as f:
        docx_bytes = f.read()
    fields = {
        "fromAddress": fro,
        "toAddress": to,
        "subject": subject,
        "content": content,
    }
    body, boundary = multipart_encode(fields, {"attachments": (os.path.basename(docx_path), docx_bytes)})
    req = urllib.request.Request(
        "https://mail.zoho.com/api/accounts/%s/messages" % account_id,
        data=body, method="POST",
        headers={"Authorization": "Zoho-oauthtoken " + token,
                 "Content-Type": "multipart/form-data; boundary=%s" % boundary})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    revenus = load_json(REVENUS, {"entrees": []})
    entrees = revenus.get("entrees", [])
    camp = load_json(CAMPAGNE, [])
    if isinstance(camp, dict):
        camp = camp.get("emails", [])
    messages = load_json(MESSAGES, {})
    boites = R.load_boites()

    livraisons = [e for e in entrees if e.get("statut") == "encaisse" and e.get("livre") != True]
    if not livraisons:
        print("Aucun paiement a livrer")
        return

    print("Paiements a livrer : %d" % len(livraisons))
    for e in livraisons:
        payer = (e.get("email_payeur") or e.get("email") or e.get("payeur") or "").strip().lower()
        # 1. trouver le prospect dans la file
        prospect = None
        for x in camp:
            if str(x.get("to", "")).strip().lower() == payer:
                prospect = x
                break
        num = prospect.get("num") if prospect else None
        if not prospect or num is None:
            print("  ! %s : prospect introuvable dans la file (livraison manuelle requise)" % payer)
            e["livre"] = "introuvable"
            continue
        # 2. generer le diagnostic
        gen = os.path.join(BASE, "generateur_diagnostic.py")
        if DRY:
            print("  [DRY] #%s %s -> diagnostic genere + envoye a %s" % (num, prospect.get("prospect", "")[:30], payer))
            e["livre"] = True
            continue
        try:
            r = subprocess.run([sys.executable, gen, str(num)],
                               capture_output=True, text=True, timeout=180, cwd=BASE)
            print("  generateur: %s" % (r.stdout.strip() or r.stderr.strip())[:160])
        except Exception as ex:
            print("  ! generation KO : %s" % ex)
            e["livre"] = "generation_ko"
            continue
        # fichier genere : livrable_diagnostic/diagnostic_<num>_<entreprise>.docx
        entreprise = re.sub(r'^\d+\s*[—-]\s*', '', prospect.get("prospect", "")).split(" (")[0]
        docx_path = None
        for f in os.listdir(LIV):
            if f.startswith("diagnostic_%d_" % num) and f.endswith(".docx"):
                docx_path = os.path.join(LIV, f)
                break
        if not docx_path:
            print("  ! docx introuvable apres generation (num %d)" % num)
            e["livre"] = "docx_introuvable"
            continue
        # 3. corps du message de livraison
        msg = messages.get("livraison_diagnostic", {})
        dirigeant = (prospect.get("dirigeant") or "").strip() or "Madame, Monsieur"
        civil = "M." if not any(x in dirigeant.upper() for x in ["MME", "MADAME", "MLLE"]) else "Mme"
        nom = dirigeant.split("(")[0].strip()
        sujet = msg.get("subject", "Votre diagnostic est prêt").replace("{dirigeant}", nom)
        corps = msg.get("body", "").replace("{dirigeant}", nom).replace("{civil}", civil)
        corps = corps.replace("\u2019", "'").replace("\u2014", "-").replace("\u2013", "-")
        # 4. boite d'envoi : celle qui a envoye au prospect (ou contact par defaut)
        boite = None
        via = prospect.get("via") if isinstance(prospect, dict) else None
        for b in boites:
            if b.get("nom") == via:
                boite = b
                break
        if not boite:
            boite = boites[0] if boites else None
        if not boite:
            print("  ! aucune boite disponible")
            continue
        try:
            access = R.refresh_access(boite)
            resp = send_email_pj(access, boite["account_id"], boite["from"], payer,
                                 sujet, corps, docx_path)
            ok = resp.get("status", {}).get("code") == 200 or "messageId" in str(resp.get("data", {}))
            e["livre"] = True
            e["livre_le"] = datetime.date.today().isoformat()
            e["message_id"] = resp.get("data", {}).get("messageId", "")
            print("  LIVRE #%s -> %s (%s)" % (num, payer, "OK" if ok else "reponse: %s" % str(resp)[:80]))
        except Exception as ex:
            print("  ! envoi KO : %s" % ex)
            e["livre"] = "envoi_ko"
    if not DRY:
        save_json(REVENUS, revenus)
    print("Termine")


if __name__ == "__main__":
    main()