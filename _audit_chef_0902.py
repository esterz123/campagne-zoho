# -*- coding: utf-8 -*-
"""Audit 02/09 soir : verite terrain de la machine campagne."""
import json, io, sys, os, re

os.chdir(r"C:/Users/ulamb/Bureau/prospection/github-campagne")
out = io.StringIO()
def p(*a):
    print(*a)

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

data = load("campagne_data.json")
state = load("campagne_state.json")
if isinstance(data, dict):
    fiches = [v for v in data.values() if isinstance(v, dict)]
else:
    fiches = data

p("== FILE ==")
p("type data:", type(data).__name__, "| total fiches:", len(fiches))
sent = state.get("sent", {})
p("sent:", len(sent))

# join par num
nums_sent = set(sent.keys())
restants = []
for i, f in enumerate(fiches):
    num = str(f.get("num", i))
    if num not in nums_sent:
        restants.append(f)
p("restants (data - sent):", len(restants))

# replied
replied = [k for k, v in sent.items() if isinstance(v, dict) and v.get("replied")]
p("replied:", len(replied), replied[:10])

# go2 markers
go2 = [k for k in state.keys() if str(k).startswith("go2")]
p("go2 markers:", go2)

# today envois
import datetime
today = datetime.date.today().isoformat()
today_sent = []
for k, v in sent.items():
    if isinstance(v, dict) and v.get("on") == today and not v.get("manual"):
        today_sent.append(k)
p("envois du jour (auto):", len(today_sent), today_sent[:8])

# relances du jour
today_rel = [k for k, v in sent.items() if isinstance(v, dict) and (v.get("sent_relance1") == today or v.get("sent_relance2") == today)]
p("relances du jour:", len(today_rel))

# constats couverture
cst = load("constats_sites.json") if os.path.exists("constats_sites.json") else {}
p("constats_sites:", len(cst))

# notes des restants
notes = {}
for r in restants:
    num = str(r.get("num"))
    c = cst.get(num) or {}
    notes[num] = c.get("note")
notes_v = [n for n in notes.values() if isinstance(n, (int, float))]
p("restants avec note:", len(notes_v), "| sans note (None):", len(restants) - len(notes_v))
casses = sorted([n for n in notes_v if n <= 40])
p("restants note <= 40 (preuves fortes):", len(casses))

# file priorite top5
try:
    fp = load("file_priorite_v2.json")
    if isinstance(fp, list):
        p("file_priorite_v2:", len(fp), "entrees, top3:", [x.get("num") for x in fp[:3]])
    else:
        p("file_priorite_v2:", type(fp).__name__)
except Exception as e:
    p("file_priorite_v2 absent/err:", e)

# revenus
try:
    rev = load("suivi_revenus.json")
    if isinstance(rev, dict):
        entries = rev.get("revenus", rev if isinstance(rev, list) else [])
    else:
        entries = rev
    reel = [e for e in entries if isinstance(e, dict) and "TEST" not in str(e.get("note", "")).upper() and "mahdi-design" not in str(e.get("payeur", e.get("from", "")))]
    p("revenus reels:", len(reel))
    tot = 0
    for e in reel:
        m = re.search(r"(\d+)", str(e.get("montant", e.get("amount", "0"))))
        if m:
            tot += int(m.group(1))
    p("total EUR reel:", tot)
except Exception as e:
    p("revenus err:", e)

# A/B
try:
    ab = load("ab_test.json")
    p("ab_test:", ab)
except Exception as e:
    p("ab_test err:", e)
