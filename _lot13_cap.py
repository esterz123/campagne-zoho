#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : captures Chrome headless des 10 sites retenus."""
import subprocess, os, json

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTDIR = r"C:\Users\ulamb\Bureau\prospection\github-campagne\_lot13_shots"
os.makedirs(OUTDIR, exist_ok=True)

SITES = {
 126: "https://lenoirmetallerie.fr/",
 127: "https://oaca.fr/",
 129: "https://sudmetallerie.com/",
 132: "https://torras.fr/",
 135: "https://www.gatsbysoudure.com/",
 137: "https://soudecoup.fr/",
 144: "https://atlantiquetoleriesoudure.fr/",
 145: "https://www.msaron.fr/",
 131: "https://groupe-gb.fr/gb-metallerie/",
 118: "https://www.smg-decoupage-tolerie.com/",
}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"

for idx, url in SITES.items():
    out = os.path.join(OUTDIR, f"lot13_{idx}.png")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
           "--window-size=1280,900",
           f"--user-agent={UA}",
           "--disable-blink-features=AutomationControlled",
           "--virtual-time-budget=9000",
           f"--screenshot={out}", "--timeout=25000", url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        sz = os.path.getsize(out) if os.path.exists(out) else 0
        print(f"[{idx}] {url} -> {sz} octets (rc={r.returncode})")
    except Exception as e:
        print(f"[{idx}] {url} ERR {str(e)[:100]}")
