#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEN DASHBOARD V2 — Tableau de bord Mahdi Design (design de marque, interactif, auto-refresh).
============================================================================================
Genere dashboard.html : stats, boites (compteurs reels API + fallback state), objectifs,
checklist interactive (localStorage), entrees d'argent, relances, file de campagne.
Auto-refresh du navigateur toutes les 5 min ; workflow GitHub toutes les 15 min.
100% gratuit : aucune dependance externe, aucun CDN.
"""
import json, os, re, html, datetime, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import campagne_zoho as CZ

DATA_F = os.path.join(BASE, "campagne_data.json")
STATE_F = os.path.join(BASE, "campagne_state.json")
SUIVI_F = os.path.join(BASE, "suivi_finances.json")
REL_F = os.path.join(BASE, "relances_conges.json")
OUT_F = os.path.join(BASE, "dashboard.html")


def jload(p, default):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


today = datetime.date.today().isoformat()
hier = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
now = datetime.datetime.now().strftime("%H:%M")

data = jload(DATA_F, [])
emails = data if isinstance(data, list) else data.get("emails", [])
state = jload(STATE_F, {})
sent = state.get("sent", {})
suivi = jload(SUIVI_F, {})
prochains = jload(REL_F, {}).get("relances", [])

nb_envoyes = len(sent)
nb_total = len(emails)
nb_restants = nb_total - nb_envoyes
auj = [k for k, v in sent.items()
       if v.get("on") == today or v.get("sent_relance1") == today or v.get("sent_relance2") == today]
encaisse = sum(e.get("montant", 0) for e in suivi.get("entrees", []) if e.get("statut") == "encaisse")
attendu = sum(e.get("montant", 0) for e in suivi.get("entrees", []) if e.get("statut") != "encaisse")
obj_mois = suivi.get("objectifs", {}).get("mois", 2000)
obj_semaine = suivi.get("objectifs", {}).get("semaine", 500)
relances_du_jour = [r for r in prochains if r.get("send_on") == today]


def compte_state(nom, jour):
    n = 0
    for v in sent.values():
        if v.get("via") != nom:
            continue
        if v.get("on") == jour or v.get("sent_relance1") == jour or v.get("sent_relance2") == jour:
            n += 1
    return n


def compte_api(token, account_id):
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


api_ko = 0
rows_boites = ""
try:
    boites = CZ.load_boites()
    for b in boites:
        nom = b["nom"]
        cap = b.get("max_jour", 3)
        try:
            tok = CZ.refresh_token(b)
            c_auj, c_hier = compte_api(tok, b.get("account_id", ""))
        except Exception:
            c_auj, c_hier = None, None
        if c_auj is None:
            c_auj, c_hier = compte_state(nom, today), compte_state(nom, hier)
            api_ko += 1
            badge = '<span class="pill pill-state">SUIVI</span>'
        elif c_auj >= cap:
            badge = '<span class="pill pill-cap">PLAFOND</span>'
        else:
            badge = '<span class="pill pill-ok">ACTIVE</span>'
        pct = min(100, round(c_auj / cap * 100)) if cap else 0
        rows_boites += (
            '<div class="box-row">'
            '<div class="box-head"><span class="box-name">%s</span>%s'
            '<span class="box-count"><b>%d</b>/%d <span class="dim">(hier %d)</span></span></div>'
            '<div class="mini-bar"><div class="mini-fill" style="width:%d%%"></div></div>'
            '</div>') % (html.escape(nom), badge, c_auj, cap, c_hier, pct)
    if not rows_boites:
        rows_boites = '<div class="empty">Aucune boite configuree.</div>'
except Exception as e:
    rows_boites = '<div class="empty">Boites indisponibles : %s</div>' % html.escape(str(e)[:60])


def barre(val, maxi, label, accent):
    pct = min(100, round(val / maxi * 100)) if maxi else 0
    return ('<div class="obj-row"><div class="obj-head"><span>%s</span>'
            '<span class="obj-val">%d / %d EUR (%d%%)</span></div>'
            '<div class="obj-bar"><div class="obj-fill %s" style="width:%d%%"></div></div></div>'
            ) % (label, val, maxi, pct, accent, pct)


rows_entrees = ""
for e in suivi.get("entrees", []):
    st = e.get("statut", "")
    badge = '<span class="pill pill-ok">ENC.</span>' if st == "encaisse" else '<span class="pill pill-wait">ATTENDU</span>'
    rows_entrees += ('<tr><td>%s</td><td>%s</td><td class="num">%d EUR</td><td>%s</td></tr>'
                     % (html.escape(e.get("date", "")), html.escape(e.get("source", "")),
                        e.get("montant", 0), badge))
if not rows_entrees:
    rows_entrees = '<tr><td colspan="4" class="empty">Aucune entree pour l instant. La 1re arrive bientot.</td></tr>'

rows_prochains = ""
for r in prochains:
    rows_prochains += '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        html.escape(r.get("send_on", "")), html.escape(r.get("id", "")), html.escape(r.get("to", "")))
if not rows_prochains:
    rows_prochains = '<tr><td colspan="3" class="empty">Aucune relance programmee.</td></tr>'

pct_file = min(100, round(nb_envoyes / nb_total * 100)) if nb_total else 0
checks = [
    ("emails", "Emails du jour envoyes", len(auj) > 0, "%d envoyes" % len(auj)),
    ("relances", "Relances conges du jour", bool(relances_du_jour), "%d prevues" % len(relances_du_jour)),
    ("mailinblack", "Cliq Mailinblack si notification", False, ""),
    ("closer", "Valider les brouillons du closer si reponse", False, ""),
    ("discord", "Verifier le rapport Discord", False, ""),
]
rows_check = ""
for cid, label, fait, detail in checks:
    rows_check += ('<label class="check" data-cid="%s"><input type="checkbox" %s>'
                   '<span class="box"></span><span class="check-label">%s</span>'
                   '<span class="check-detail">%s</span></label>'
                   % (cid, "checked" if fait else "", html.escape(label), html.escape(detail)))

api_badge = '<span class="pill pill-ok">API REELLE</span>' if api_ko == 0 else \
            '<span class="pill pill-state">SUIVI INTERNE</span>'

T = {}
T["HEADER"] = (
    '<header class="hero">'
    '<div class="brand"><span class="logo">M</span><div><h1>MAHDI DESIGN</h1>'
    '<p class="tagline">Tableau de bord commercial</p></div></div>'
    '<div class="hero-right"><span class="live"><span class="pulse"></span>LIVE</span>'
    '<span class="date">%s</span></div></header>') % today
T["STATS"] = (
    '<section class="stats">'
    '<div class="stat"><div class="ico">📨</div><div class="n">%d</div><div class="l">emails envoyes</div></div>'
    '<div class="stat"><div class="ico">📥</div><div class="n">%d</div><div class="l">restants (%d total)</div></div>'
    '<div class="stat"><div class="ico">⚡</div><div class="n">%d</div><div class="l">envois aujourd hui</div></div>'
    '<div class="stat"><div class="ico">💰</div><div class="n">%d EUR</div><div class="l">encaisse</div></div>'
    '</section>') % (nb_envoyes, nb_restants, nb_total, len(auj), encaisse)
T["BOXES"] = ('<section class="card"><h2>Boites d envoi %s</h2><div class="boxes">%s</div>'
              '<p class="note">Compteurs reels Zoho (verite terrain), repli sur le suivi interne si API indisponible. '
              'Plafonds de warm-up : 5/jour pour contact, 3/jour pour les autres.</p></section>') % (api_badge, rows_boites)
T["OBJECTIFS"] = ('<section class="card"><h2>Objectifs</h2>%s%s</section>'
                  % (barre(encaisse, obj_mois, "Mois", "amber"), barre(encaisse, obj_semaine, "Semaine", "green")))
T["CHECKLIST"] = ('<section class="card"><h2>Checklist du jour</h2><div class="checks" id="checks">%s</div>'
                  '<div class="check-progress"><div class="mini-bar"><div class="mini-fill amber" id="checkFill" '
                  'style="width:0%%"></div></div><span id="checkCount">0/5</span></div></section>') % rows_check
T["ENTREES"] = ('<section class="card"><h2>Entrees d argent</h2>'
                '<table><thead><tr><th>Date</th><th>Source</th><th>Montant</th><th>Statut</th></tr></thead>'
                '<tbody>%s</tbody></table>'
                '<div class="total">Total attendu a venir : <b>%d EUR</b></div></section>') % (rows_entrees, attendu)
# ---- Conversations (reponses traitees par le closer/repondeur) ----
def fraicheur(iso):
    """'il y a X min' depuis un timestamp ISO (UTC)."""
    try:
        from datetime import timezone
        t = datetime.datetime.fromisoformat(iso.replace('Z', '+00:00'))
        d = datetime.datetime.now(timezone.utc) - t
        mins = max(0, int(d.total_seconds() // 60))
        if mins < 1:
            return "a l'instant"
        if mins < 60:
            return "il y a %d min" % mins
        return "il y a %d h" % (mins // 60)
    except Exception:
        return "?"

closer_st = jload(os.path.join(BASE, "closer_state.json"), {})
repond_st = jload(os.path.join(BASE, "repondeur_state.json"), {})
nb_closer = len(closer_st.get("traites", []))
nb_repond = len(repond_st.get("traites", []))
f_closer = fraicheur(str(closer_st.get("dernier_run", "")))
f_repond = fraicheur(str(repond_st.get("dernier_run", "")))
if nb_closer + nb_repond == 0:
    conv_note = '<div class="empty">Aucune reponse client pour l instant. Elles arrivent apres 50-150 envois.</div>'
else:
    conv_note = ('<div class="conv-row"><span>Reponses traitees par le closer</span><b>%d</b></div>'
                 '<div class="conv-row"><span>Messages vus par le repondeur</span><b>%d</b></div>'
                 '<div class="conv-row dim2"><span>Dernier passage closer</span><span>%s</span></div>'
                 '<div class="conv-row dim2"><span>Dernier passage repondeur</span><span>%s</span></div>'
                 ) % (nb_closer, nb_repond, f_closer, f_repond)
T["CONVERSATIONS"] = ('<section class="card"><h2>Conversations</h2>%s'
                      '<p class="note">Une reponse avec signal d interet = le closer repond en ~30 min (diagnostic 79 EUR, '
                      'puis offre Rentree). Tout est automatique.</p></section>') % conv_note

T["RELANCES"] = ('<section class="card"><h2>Prochaines relances</h2>'
                 '<table><thead><tr><th>Date</th><th>Prospect</th><th>Email</th></tr></thead>'
                 '<tbody>%s</tbody></table></section>') % rows_prochains
T["FILE"] = ('<section class="card"><h2>File de campagne</h2>'
             '<div class="file-stats"><span>Envoyes : <b>%d</b></span><span>Restants : <b>%d</b></span>'
             '<span>Total : <b>%d</b></span></div>'
             '<div class="obj-bar big"><div class="obj-fill amber" style="width:%d%%"></div></div>'
             '<p class="note">%d emails/jour max en warm-up. Objectif : 25-30/jour d ici 2 semaines. '
             'Envois 7j/7, espaces de 12 min.</p></section>') % (nb_envoyes, nb_restants, nb_total, pct_file, 17)

page = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="300">
<title>Mahdi Design — Tableau de bord</title>
<style>
:root{--bg:#0b0b10;--card:#15151d;--line:#262633;--txt:#f2efe6;--dim:#8b8a99;
--amber:#e8a33d;--amber2:#b45309;--green:#3fb950;--red:#f85149;--blue:#58a6ff}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:
radial-gradient(1200px 600px at 80% -10%,#1c1626 0%,var(--bg) 55%);color:var(--txt);
padding:28px 20px 60px;min-height:100vh}
.wrap{max-width:1080px;margin:auto}
.hero{display:flex;justify-content:space-between;align-items:center;gap:16px;
padding:22px 26px;background:linear-gradient(135deg,#1a1a24,#131318);
border:1px solid var(--line);border-radius:18px;margin-bottom:18px}
.brand{display:flex;align-items:center;gap:14px}
.logo{width:46px;height:46px;border-radius:12px;display:flex;align-items:center;justify-content:center;
font-size:24px;font-weight:800;color:#14100a;background:linear-gradient(135deg,var(--amber),var(--amber2))}
h1{font-size:20px;letter-spacing:3px}
.tagline{color:var(--dim);font-size:13px;margin-top:2px}
.hero-right{display:flex;align-items:center;gap:12px}
.live{display:flex;align-items:center;gap:7px;font-size:12px;font-weight:700;letter-spacing:2px;
color:var(--green);background:#0f1a12;border:1px solid #1f3a26;padding:6px 12px;border-radius:20px}
.pulse{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pl 1.6s infinite}
@keyframes pl{0%{box-shadow:0 0 0 0 rgba(63,185,80,.6)}70%{box-shadow:0 0 0 7px rgba(63,185,80,0)}100%{box-shadow:0 0 0 0 rgba(63,185,80,0)}}
.date{color:var(--dim);font-size:13px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 14px;text-align:center;
transition:transform .15s, border-color .15s}
.stat:hover{transform:translateY(-2px);border-color:#3a3a4a}
.ico{font-size:22px;margin-bottom:6px}
.n{font-size:30px;font-weight:800;background:linear-gradient(135deg,var(--amber),#f6d9a8);
-webkit-background-clip:text;background-clip:text;color:transparent}
.l{font-size:12px;color:var(--dim);margin-top:4px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px}
.card h2{font-size:13px;text-transform:uppercase;letter-spacing:2px;color:var(--amber);
margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;gap:8px}
.boxes{display:flex;flex-direction:column;gap:10px}
.box-row{background:#101018;border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.box-head{display:flex;align-items:center;gap:8px;margin-bottom:7px}
.box-name{font-weight:600;font-size:14px;flex:1}
.box-count{font-size:13px;color:var(--txt)}
.dim{color:var(--dim);font-size:11px}
.mini-bar{background:#20202c;border-radius:6px;height:7px;overflow:hidden}
.mini-fill{height:7px;border-radius:6px;background:linear-gradient(90deg,var(--amber2),var(--amber));
transition:width .6s}
.mini-fill.amber{background:linear-gradient(90deg,var(--amber2),var(--amber))}
.pill{font-size:10px;font-weight:700;padding:2px 8px;border-radius:12px;letter-spacing:1px}
.pill-ok{background:#12331c;color:var(--green);border:1px solid #1f4a2c}
.pill-cap{background:#33260c;color:var(--amber);border:1px solid #4d3a12}
.pill-state{background:#1c2233;color:var(--blue);border:1px solid #2a3450}
.pill-wait{background:#33260c;color:var(--amber);border:1px solid #4d3a12}
.obj-row{margin-bottom:14px}
.obj-head{display:flex;justify-content:space-between;font-size:13px;margin-bottom:6px;color:var(--dim)}
.obj-val{color:var(--txt);font-weight:600}
.obj-bar{background:#20202c;border-radius:8px;height:12px;overflow:hidden}
.obj-bar.big{height:16px;margin-top:10px}
.obj-fill{height:100%;border-radius:8px;transition:width .7s}
.obj-fill.amber{background:linear-gradient(90deg,var(--amber2),var(--amber))}
.obj-fill.green{background:linear-gradient(90deg,#1d6b2c,var(--green))}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--dim);font-weight:500;padding:6px 8px;border-bottom:1px solid var(--line)}
td{padding:8px;border-bottom:1px solid #1c1c26}
.num{text-align:right;font-weight:600}
.empty{color:var(--dim);text-align:center;padding:14px}
.note{font-size:11px;color:var(--dim);margin-top:12px;line-height:1.5}
.total{margin-top:12px;font-size:13px;color:var(--dim)}
.total b{color:var(--amber)}
.checks{display:flex;flex-direction:column;gap:4px}
.check{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:10px;cursor:pointer;
font-size:14px;transition:background .15s}
.check:hover{background:#1a1a26}
.check input{display:none}
.check .box{width:18px;height:18px;border:2px solid #3a3a4a;border-radius:6px;flex-shrink:0;
display:flex;align-items:center;justify-content:center;font-size:11px;transition:all .15s}
.check input:checked + .box{background:var(--amber);border-color:var(--amber);color:#14100a}
.check input:checked + .box::after{content:"✓"}
.check input:checked ~ .check-label{text-decoration:line-through;color:var(--dim)}
.check-label{flex:1}
.check-detail{font-size:11px;color:var(--dim)}
.check-progress{display:flex;align-items:center;gap:10px;margin-top:12px}
.check-progress .mini-bar{flex:1}
.check-progress span{font-size:12px;color:var(--dim);font-weight:700}
.file-stats{display:flex;gap:20px;font-size:13px;color:var(--dim);margin-bottom:4px}
.file-stats b{color:var(--txt)}
.conv-row{display:flex;justify-content:space-between;align-items:center;font-size:13px;
padding:7px 0;border-bottom:1px solid #1c1c26}
.conv-row b{color:var(--amber);font-size:16px}
.conv-row.dim2{color:var(--dim);font-size:12px;border-bottom:none;padding:4px 0}
footer{text-align:center;color:#5a5a6a;font-size:11px;margin-top:26px;line-height:1.6}
@media(max-width:760px){.stats{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}}
</style></head><body><div class="wrap">
__HEADER__
__STATS__
<div class="grid">__BOXES____OBJECTIFS__</div>
<div class="grid">__CHECKLIST____ENTREES__</div>
<div class="grid">__CONVERSATIONS____RELANCES__</div>
<div class="grid">__FILE__</div>
<footer>Genere le __TODAY__ a __NOW__ · GitHub Actions (100%% gratuit) · Auto-refresh toutes les 5 min<br>
Mahdi Design — La Marque qui Vend · mahdi-design.com</footer>
</div>
<script>
(function(){
var today="__TODAY__";
var key="md_check_"+today;
var done=JSON.parse(localStorage.getItem(key)||"[]");
document.querySelectorAll(".check").forEach(function(l){
var cid=l.getAttribute("data-cid");
if(done.indexOf(cid)>-1){l.querySelector("input").checked=true;}
l.querySelector("input").addEventListener("change",function(){
if(this.checked){if(done.indexOf(cid)<0)done.push(cid);}
else{done=done.filter(function(x){return x!==cid;});}
localStorage.setItem(key,JSON.stringify(done));refresh();});
});
function refresh(){
var n=document.querySelectorAll(".check input:checked").length;
var t=document.querySelectorAll(".check").length;
document.getElementById("checkCount").textContent=n+"/"+t;
document.getElementById("checkFill").style.width=(t?Math.round(n/t*100):0)+"%";}
refresh();
var secs=300;
setInterval(function(){secs--;if(secs<=0)location.reload();},1000);
})();
</script>
</body></html>"""

page = page.replace("__HEADER__", T["HEADER"]).replace("__STATS__", T["STATS"])
page = page.replace("__BOXES__", T["BOXES"]).replace("__OBJECTIFS__", T["OBJECTIFS"])
page = page.replace("__CHECKLIST__", T["CHECKLIST"]).replace("__ENTREES__", T["ENTREES"])
page = page.replace("__RELANCES__", T["RELANCES"]).replace("__FILE__", T["FILE"])
page = page.replace("__CONVERSATIONS__", T["CONVERSATIONS"])
page = page.replace("__NOW__", now).replace("__TODAY__", today)

with open(OUT_F, "w", encoding="utf-8") as f:
    f.write(page)
print("DASHBOARD OK -> %s | envoyes:%d total:%d auj:%d encaisse:%d api_ko:%d"
      % (OUT_F, nb_envoyes, nb_total, len(auj), encaisse, api_ko))
