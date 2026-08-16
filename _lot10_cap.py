#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot10 : captures Chrome headless des sites shortlistes."""
import os, re, subprocess, sys, json

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CAP = os.path.join(BASE, "captures")

def slug(nom):
    return re.sub(r"[^a-z0-9]+", "_", nom.lower()).strip("_")[:40]

SITES = {
    "begc": "https://www.begc.fr/",
    "usinage_dieppois": "https://usinage-dieppois.fr",
    "fraisage_services": "https://fraisageservices.fr",
    "omedec": "https://www.omedec.com",
    "drault": "https://drault-decolletage.com/fr/",
    "elcam": "https://www.elcam-usinage.fr/",
    "jcm": "https://www.jcm-decolletage.fr/",
    "de_reu": "https://www.decolletage-de-reu.com/",
    "elbe": "https://www.decolletage-elbe.fr/",
    "edelweiss": "https://www.edelweiss-decolletage.com/",
    "provence_outillage": "https://www.provence-outillage.fr/",
    "nord_fraisage": "https://nordfraisage.fr",
    "eberhard": "https://eberhard-usinage.fr",
    "guillerme": "https://guillerme-decolletage.fr",
    "ba_usinage": "https://usinage.com",
    "ouest_decolletage": "https://www.ouestdecolletage.com",
    "morel": "https://www.morel-decolletage.fr/",
    "amd": "https://www.amd-decolletage.com",
    "decolletage_jurassien": "https://www.decolletage-jurassien.fr/",
    "fixouti": "http://fixouti.fr",
}

os.makedirs(CAP, exist_ok=True)
ok = []
for name, url in SITES.items():
    out = os.path.join(CAP, "lot10_" + name + ".png")
    try:
        r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                            "--hide-scrollbars", "--window-size=1280,900",
                            "--screenshot=" + out, "--timeout=20000", url],
                           capture_output=True, timeout=60)
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            ok.append({"name": name, "url": url, "png": out, "size": os.path.getsize(out)})
            print("OK ", name, url, flush=True)
        else:
            print("VIDE", name, url, flush=True)
    except Exception as e:
        print("ERR", name, url, str(e)[:80], flush=True)

json.dump(ok, open(BASE + r"\_lot10_captures_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("CAPTURES:", len(ok))
