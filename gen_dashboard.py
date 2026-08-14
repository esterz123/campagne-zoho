# -*- coding: utf-8 -*-
"""GENERATEUR DU TABLEAU DE BORD QUOTIDIEN (dashboard.html) — version CLOUD.
Lit : campagne_state.json + campagne_data.json + relances_conges.json + suivi_revenus.json
      (meme dossier) + compteurs REELS par boite via l'API Zoho (in:sent).
Usage : python3 gen_dashboard.py   (marche en local et dans GitHub Actions)
Le HTML genere est pousse vers le repo public mahdi-design (GitHub Pages).
"""
import json, os, sys, datetime, html

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import campagne_zoho as CZ

def jload(p, default):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

state = jload(os.path.join(BASE, "campagne_state.json"), {"sent": {}})
data = jload(os.path.join(BASE, "campagne_data.json"), [])
relances = jload(os.path.join(BASE, "relances_conges.json"), {"relances": []})
suivi = jload(os.path.join(BASE, "suivi_revenus.json"),
              {"objectifs": {"mois": 2000, "semaine": 500}, "entrees": []})

today = datetime.date.today().isoformat()
hier = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
sent = state.get("sent", {})
nb_total = len(data)
nb_envoyes = len(sent)
nb_restants = nb_total - nb_envoyes
auj = [k for k, v in sent.items()
       if v.get("on") == today or v.get("sent_relance1") == today or v.get("sent_relance2") == today]
relances_du_jour = [r for r in relances.get("relances", []) if r.get("send_on") == today and not r.get("sent")]
prochains = sorted([r for r in relances.get("relances", []) if not r.get("sent")], key=lambda r: r.get("send_on", "9999"))
encaisse = sum(e.get("montant", 0) for e in suivi.get("entrees", []) if e.get("statut") == "encaisse")
attendu = sum(e.get("montant", 0) for e in suivi.get("entrees", []) if e.get("statut") != "encaisse")
obj_mois = suivi.get("objectifs", {}).get("mois", 2000)
obj_semaine = suivi.get("objectifs", {}).get("semaine", 500)

# ---- Compteurs par boite : API in:sent (verite terrain), fallback state ----
def compte_state(nom, jour):
    """Compteur depuis le state (envois post-rotation, champ via)."""
    n = 0
    for v in sent.values():
        if v.get("via") != nom:
            continue
        if v.get("on") == jour or v.get("sent_relance1") == jour or v.get("sent_relance2") == jour:
            n += 1
    return n

def compte_api(token, account_id):
    """(aujourd'hui, hier) depuis les 50 derniers envoyes de la boite."""
    try:
        req = CZ.urllib.request.Request(
            "https://mail.zoho.com/api/accounts/%s/messages/search?searchKey=in%%3Asent&limit=50" % account_id,
            headers={"Authorization": "Zoho-oauthtoken " + token})
        j = json.load(CZ.urllib.request.urlopen(req, timeout=20))
        c_auj = c_hier = 0
        for m in j.get("data", []):
            ts = int(m.get("receivedTime", 0)) / 1000
            d = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            if d == today:
                c_auj += 1
            elif d == hier:
                c_hier += 1
        return c_auj, c_hier
    except Exception:
        return None, None

rows_boites = ""
try:
    boites = CZ.load_boites()
    for b in boites:
        tok = CZ.refresh_token(b)
        c_auj, c_hier = compte_api(tok, b["account_id"])
        if c_auj is None:
            c_auj, c_hier = compte_state(b["nom"], today), compte_state(b["nom"], hier)
            statut = '<span class="badge wait">STATE</span>'
        elif c_auj >= b["max_jour"]:
            statut = '<span class="badge ok">PLAFOND</span>'
        else:
            statut = '<span class="badge ok">ACTIVE</span>'
        rows_boites += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            b["nom"], c_auj, c_hier, b["max_jour"], statut)
except Exception as e:
    rows_boites = '<tr><td colspan="5" class="empty">Boites indisponibles : %s</td></tr>' % str(e)[:60]

def barre(val, maxi, label):
    pct = min(100, round(val / maxi * 100)) if maxi else 0
    return ('<div class="bar"><div class="bar-fill" style="width:%d%%"></div></div>'
            '<div class="bar-label">%s : %d / %d EUR (%d%%)</div>') % (pct, label, val, maxi, pct)

rows_entrees = ""
for e in suivi.get("entrees", []):
    st = e.get("statut", "")
    badge = '<span class="badge ok">ENC.</span>' if st == "encaisse" else '<span class="badge wait">ATTENDU</span>'
    rows_entrees += '<tr><td>%s</td><td>%s</td><td>%s EUR</td><td>%s</td></tr>' % (
        html.escape(e.get("date", "")), html.escape(e.get("source", "")), e.get("montant", 0), badge)
if not rows_entrees:
    rows_entrees = '<tr><td colspan="4" class="empty">Aucune entree pour l instant. La 1re arrive bientot.</td></tr>'

rows_prochains = ""
for r in prochains:
    rows_prochains += '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        r.get("send_on", ""), html.escape(r.get("id", "")), html.escape(r.get("to", "")))
if not rows_prochains:
    rows_prochains = '<tr><td colspan="3" class="empty">Aucune relance programmee.</td></tr>'

page = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>Mahdi Design — Tableau de bord</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#e6edf3;padding:32px;max-width:960px;margin:auto}
h1{font-size:26px;margin-bottom:4px}
.sub{color:#8b949e;margin-bottom:24px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;margin-bottom:16px}
.card h2{font-size:15px;text-transform:uppercase;letter-spacing:1px;color:#58a6ff;margin-bottom:14px}
.bar{background:#21262d;border-radius:8px;height:14px;margin:8px 0 4px}
.bar-fill{background:linear-gradient(90deg,#238636,#3fb950);border-radius:8px;height:14px;transition:width .5s}
.bar-label{font-size:13px;color:#8b949e;margin-bottom:12px}
.badge{font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600}
.badge.ok{background:#238636;color:#fff}
.badge.wait{background:#9e6a03;color:#fff}
table{width:100%%;border-collapse:collapse;font-size:14px}
th{text-align:left;color:#8b949e;font-weight:500;padding:6px 8px;border-bottom:1px solid #30363d}
td{padding:6px 8px;border-bottom:1px solid #21262d}
.empty{color:#8b949e;text-align:center;padding:14px}
.check{display:flex;align-items:center;gap:10px;padding:8px 0;font-size:14px}
.dot{width:12px;height:12px;border-radius:50%%;flex-shrink:0}
.dot.ok{background:#3fb950}.dot.todo{background:#f0883e}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
.stat{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;text-align:center}
.stat .n{font-size:28px;font-weight:700;color:#58a6ff}
.stat .l{font-size:12px;color:#8b949e;margin-top:4px}
@media(max-width:700px){.grid,.stats{grid-template-columns:1fr}}
</style></head><body>
<h1>🎯 Mahdi Design — Tableau de bord</h1>
<div class="sub">%s — Objectif : %d EUR ce mois, %d EUR cette semaine — mis a jour automatiquement</div>
<div class="stats">
<div class="stat"><div class="n">%d</div><div class="l">emails envoyes (file)</div></div>
<div class="stat"><div class="n">%d</div><div class="l">restants (%d total)</div></div>
<div class="stat"><div class="n">%d</div><div class="l">envois aujourd hui</div></div>
<div class="stat"><div class="n">%d EUR</div><div class="l">encaisse</div></div>
</div>
<div class="grid">
<div class="card"><h2>Boites d envoi (compteurs reels)</h2>
<table><tr><th>Boite</th><th>Aujourd hui</th><th>Hier</th><th>Plafond/jour</th><th>Statut</th></tr>%s</table>
<p style="font-size:12px;color:#8b949e;margin-top:8px">Comptes via l API Zoho (verite terrain). Les boites neuves montent progressivement : 3/jour la 1re semaine, puis 5-6.</p></div>
<div class="card"><h2>Objectifs</h2>%s%s</div>
</div>
<div class="grid">
<div class="card"><h2>Checklist du jour</h2>
<div class="check"><span class="dot %s"></span>Emails du jour envoyes (%d)</div>
<div class="check"><span class="dot %s"></span>Relances conges du jour (%d)</div>
<div class="check"><span class="dot todo"></span>Cliq Mailinblack si notification</div>
<div class="check"><span class="dot todo"></span>Valider les brouillons du closer si reponse</div>
<div class="check"><span class="dot todo"></span>Verifier le rapport Discord</div></div>
<div class="card"><h2>Entrees d argent</h2><table><tr><th>Date</th><th>Source</th><th>Montant</th><th>Statut</th></tr>%s</table>
<div class="bar-label" style="margin-top:10px">Total attendu a venir : %d EUR</div></div>
</div>
<div class="grid">
<div class="card"><h2>Prochaines relances</h2><table><tr><th>Date</th><th>Prospect</th><th>Email</th></tr>%s</table></div>
<div class="card"><h2>File de campagne</h2>
<div class="bar-label">Envoyes : %d / %d — Restants : %d</div>
<div class="bar"><div class="bar-fill" style="width:%d%%"></div></div>
<p style="font-size:12px;color:#8b949e;margin-top:8px">17 emails/jour max actuellement (warm-up). Objectif : 25-30/jour d ici 2 semaines.</p></div>
</div>
</body></html>""" % (
    today, obj_mois, obj_semaine,
    nb_envoyes, nb_restants, nb_total, len(auj), encaisse,
    rows_boites,
    barre(encaisse, obj_mois, "Mois"),
    barre(encaisse, obj_semaine, "Semaine"),
    "ok" if len(auj) > 0 else "todo", len(auj),
    "ok" if relances_du_jour else "todo", len(relances_du_jour),
    rows_entrees, attendu, rows_prochains,
    nb_envoyes, nb_total, nb_restants,
    min(100, round(nb_envoyes / nb_total * 100)) if nb_total else 0)

with open(os.path.join(BASE, "dashboard.html"), "w", encoding="utf-8") as f:
    f.write(page)
print("Dashboard genere :", os.path.join(BASE, "dashboard.html"))
print("File:", nb_envoyes, "envoyes |", nb_restants, "restants | Encaisse:", encaisse, "EUR")
