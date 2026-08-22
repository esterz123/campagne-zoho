#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GRAND CYCLE ENVOIS (autorise) : pousse les envois jusqu'au quota journalier sur
les 5 boites (respecte max_jour), avec pauses. Log dans grand_cycle.log."""
import os, sys, subprocess, datetime, time

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "grand_cycle.log")
PY = sys.executable

def log(m):
    line = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {m}"
    try:
        open(LOG,"a",encoding="utf-8").write(line+"\n")
    except Exception: pass
    print(line)

def boites(duj):
    """Compte les envois par boite aujourd'hui."""
    counts={}
    try:
        sent=json_load(BASE,"campagne_state.json")["sent"]
    except Exception:
        sent={}
    for v in sent.values():
        if v.get("on")==datetime.date.today().isoformat():
            counts[v.get("via","?")]=counts.get(v.get("via","?"),0)+1
    return counts

def json_load(base,f):
    import json
    return json.load(open(os.path.join(base,f),encoding="utf-8"))

def main():
    # max journalier par boite (miroir de load_boites)
    MAX = {"commercial":3,"hello":3,"info":3,"direction":3,"contact":5}
    total_auj = 0
    for cycle in range(20):  # jusqu'a 20 cycles
        counts = boites(BASE)
        used = sum(min(counts.get(k,0),v) for k,v in MAX.items())
        # quota restant approx = sum(MAX)-used (cap 15/semaine a cote par script)
        if used >= sum(MAX.values()):
            log(f"cycle {cycle}: quota journalier atteint ({used}/{sum(MAX.values())}). STOP.")
            break
        # 1 run = 1-2 envois (quota interne du script)
        log(f"cycle {cycle}: lancement run_local ({used}/{sum(MAX.values())} boite-jours utilises)")
        r = subprocess.run([PY, os.path.join(BASE,"run_local.py")],
                           capture_output=True, text=True, timeout=280, cwd=BASE)
        out=(r.stdout or "")+(r.stderr or "")
        log(out.strip()[-500:])
        total_auj += 1
        time.sleep(8)  # petite pause entre cycles
        # si rien a envoyer (toutes boites au max ou file vide) -> arreter tot
        if "Restants : 124" not in out and "envoye" not in out.lower() and "RELANCE" not in out:
            log(f"cycle {cycle}: plus rien a envoyer ce jour")
            break
    log(f"=== GRAND CYCLE TERMINE : {total_auj} cycles ===")

if __name__=="__main__":
    main()