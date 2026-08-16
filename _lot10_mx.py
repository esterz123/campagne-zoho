#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot10 : verification MX des emails retenus."""
import json, re, socket, sys, urllib.request

EMAILS = [
    "fraisage@fraisageservices.fr",
    "administration@begc.fr",
    "contact@morel-decolletage.fr",
    "contact@usinage-dieppois.fr",
    "stephanemacle@elcam-usinage.fr",
    "info@jcm-decolletage.fr",
    "contact@omedec.com",
    "contact@nordfraisage.fr",
    "tfl.meca@orange.fr",
    "eurl-guillerme-ferrailles@orange.fr",
    "info@decolletage-elbe.fr",
]

def mx_ok(domain):
    try:
        answers = socket.getaddrinfo(domain, 25, socket.AF_INET)
        return bool(answers)
    except Exception:
        pass
    # fallback: resolution DNS MX via dnspython? non, resoud A du domaine
    try:
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False

import subprocess
def nslookup_mx(domain):
    try:
        r = subprocess.run(["nslookup", "-type=mx", domain], capture_output=True, text=True, timeout=15)
        out = r.stdout + r.stderr
        if "mail exchanger" in out.lower():
            return True, [l.strip() for l in out.splitlines() if "mail exchanger" in l.lower()][:2]
        return False, out.strip().splitlines()[-1] if out.strip() else "?"
    except Exception as e:
        return False, str(e)[:60]

for e in EMAILS:
    dom = e.split("@")[1]
    ok, info = nslookup_mx(dom)
    print(("OK  " if ok else "FAIL") + " | " + e + " | " + str(info))
