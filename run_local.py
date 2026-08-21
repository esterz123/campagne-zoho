#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lanceur LOCAL de la campagne (plan B sans GitHub Actions).
Tourne sur le PC: envoie la campagne + relances via .boites_zoho.json.
Log dans run_local.log. Kill-switch: PAUSE_ENVOIS.
Usage: python3 run_local.py [--once]"""
import os, sys, json, subprocess, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "run_local.log")

def log(msg):
    line = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)

def main():
    # kill-switch
    if os.path.exists(os.path.join(BASE, "PAUSE_ENVOIS")):
        log("PAUSE_ENVOIS present: aucun envoi.")
        return 0

    # 1. campagne principale (prospects + relances)
    log("=== RUN LOCAL: campagne ===")
    r = subprocess.run([sys.executable, os.path.join(BASE, "campagne_zoho.py")],
                       capture_output=True, text=True, timeout=300, cwd=BASE)
    for line in r.stdout.strip().splitlines():
        log("  C " + line)
    if r.returncode != 0:
        log("  C ERREUR (code %d): %s" % (r.returncode, r.stderr[-500:]))

    # 2. partenaires
    log("=== RUN LOCAL: partenaires ===")
    r2 = subprocess.run([sys.executable, os.path.join(BASE, "partenaire_zoho.py")],
                        capture_output=True, text=True, timeout=300, cwd=BASE)
    for line in r2.stdout.strip().splitlines():
        log("  P " + line)
    if r2.returncode != 0:
        log("  P ERREUR (code %d): %s" % (r2.returncode, r2.stderr[-500:]))

    log("=== RUN LOCAL termine ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
