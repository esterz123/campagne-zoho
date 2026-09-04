# -*- coding: utf-8 -*-
"""Audit business 03/09 - verite terrain join data<->state."""
import json, os, re, subprocess, sys
from datetime import datetime

REPO = os.path.expanduser(r"~\Bureau\prospection\github-campagne")
os.chdir(REPO)

def load(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"__error__": str(e)}

data = load("campagne_data.json")
state = load("campagne_state.json")
revenus = load("suivi_revenus.json")

# --- File reelle : join data <-> state ---
if isinstance(data, list):
    fiches = {str(f.get("num")): f for f in data}
elif isinstance(data, dict):
    fiches = {str(k): v for k, v in data.items() if isinstance(v, dict)}
else:
    fiches = {}
print("FICHES data:", len(fiches))

sent = state.get("sent", {}) if isinstance(state, dict) else {}
print("CLES sent:", len(sent))
replied = {k for k, v in sent.items() if isinstance(v, dict) and v.get("replied")}

nums_all = set(fiches.keys())
nums_sent = set(sent.keys())
restants = nums_all - nums_sent
print("ENVOYES:", len(nums_sent), "| FILE RESTANTE REELLE:", len(restants))
print("REPLIES:", len(replied), sorted(replied)[:20])

# --- Cash reel (filtrer TEST et mahdi-design) ---
if isinstance(revenus, dict):
    entries = revenus.get("paiements", revenus.get("entries", []))
    if isinstance(entries, dict):
        entries = list(entries.values())
else:
    entries = []
total, reel = 0, []
for e in entries:
    if not isinstance(e, dict):
        continue
    note = str(e.get("note", ""))
    payeur = str(e.get("payeur", e.get("payer", "")))
    if "TEST" in note.upper() or "mahdi-design" in payeur:
        continue
    try:
        m = float(e.get("montant", e.get("amount", 0)))
    except (TypeError, ValueError):
        continue
    total += m
    reel.append((e.get("date", "?"), m, note[:40]))
print("CASH REEL:", total, "EUR |", len(reel), "paiements")
for r in reel[-8:]:
    print("  ", r)

# --- Kill-switch ---
print("PAUSE_ENVOIS existe:", os.path.exists("PAUSE_ENVOIS"))
print("SEND_LOCK existe:", os.path.exists("SEND_LOCK"))

# --- Relance closing SIMI ---
for f in ["livrable/relance_closing_SIMI.txt", "relance_closing_SIMI.txt"]:
    if os.path.exists(f):
        print("RELANCE SIMI TROUVEE:", f, os.path.getsize(f), "octets")

# --- reply_aliases / Gaultier ---
al = load("reply_aliases.json")
print("ALIASES:", al if not isinstance(al, dict) or "__error__" not in al else "ERREUR")

# --- MAILINBLACK : dernieres notifs repondeur ---
rep_state = load("repondeur_state.json")
if isinstance(rep_state, dict):
    traites = rep_state.get("traites", [])
    print("REPONDEUR traites:", len(traites))

# --- Derniers commits date ---
try:
    d = subprocess.run(["git", "log", "-1", "--format=%ci %s"], capture_output=True, text=True).stdout.strip()
    print("DERNIER COMMIT:", d)
except Exception as e:
    print("git log err", e)

# --- Nouveaux nums sans constat (chaine preuve) ---
try:
    constats = load("constats_sites.json")
    if isinstance(constats, dict):
        nc = set(constats.keys())
        sans = sorted(restants - nc, key=lambda x: int(x) if x.isdigit() else 99999)
        print("RESTANTS SANS PREUVE:", len(sans), sans[:15])
except Exception as e:
    print("constats err", e)
