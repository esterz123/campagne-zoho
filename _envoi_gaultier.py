# -*- coding: utf-8 -*-
"""Envoi Gaultier - GO nomme par Mahdi le 02/09 ('envoie Gaultier').
Message conforme prepare le 31/08 (commit 478fdae). Adresse perso hors file.
Un seul run. Marque l'etat apres succes."""
import io
import json
import campagne_zoho as cz

REPO = "C:/Users/ulamb/Bureau/prospection/github-campagne"
sujet = io.open(REPO + "/_gaultier_sujet.txt", encoding="utf-8").read().strip()
corps = io.open(REPO + "/_gaultier_corps.txt", encoding="utf-8").read().strip()

boites = cz.load_boites()
b = [x for x in boites if x["nom"] == "hello"][0]
tok = cz.refresh_token(b)
html = cz.build_html(corps, cz.SIG)
r = cz.send_email(tok, sujet, html, "a.gaultier@free.fr", "", b)
print("RESULTAT:", r if not isinstance(r, dict) else {k: r.get(k) for k in ("status", "code", "message") if k in r})

ok = False
if isinstance(r, dict):
    ok = str(r.get("status", "")).lower() in ("success", "ok") or r.get("code") in (200, "200")
elif isinstance(r, str):
    ok = "success" in r.lower()

if ok:
    p = REPO + "/campagne_state.json"
    s = json.load(io.open(p, encoding="utf-8"))
    v = s["sent"]["63"]
    v["gaultier_collab_envoye"] = "2026-09-05"
    v["audit_suivi"]["note_reponse_envoyee"] = "GO 'envoie Gaultier' (02/09) EXECUTE le 05/09 : message collab parti vers a.gaultier@free.fr via hello"
    io.open(p, "w", encoding="utf-8").write(json.dumps(s, ensure_ascii=False, indent=1))
    print("ETAT MARQUE: gaultier_collab_envoye=2026-09-05")
else:
    print("ENVOI NON CONFIRME - etat NON marque, ne pas retenter sans verifier la boite")
