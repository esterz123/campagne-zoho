#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : retests + MX."""
import subprocess, json, re, urllib.request, time

def curl_head(url):
    try:
        r = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code} %{url_effective} %{time_total}s", "-L", "--max-time", "20", "-A", "Mozilla/5.0", url], capture_output=True, text=True, timeout=30)
        return r.stdout
    except Exception as e:
        return f"ERR {e}"

print("=== RETESTS ===")
for label, url in [("118 SMG", "https://www.smg-decoupage-tolerie.com/"),
                   ("128 Batisud", "https://batisud.org/"),
                   ("133 Metallerie.com", "https://metallerie.com/"),
                   ("125 SAMD", "https://samd-aero.fr/"),
                   ("130 LG", "https://lg-metallerie.fr/")]:
    print(f"{label}: {curl_head(url)}")

print("\n=== MENTIONS metallerie.com (suivre redirect) ===")
try:
    req = urllib.request.Request("https://metallerie.com/mentions-legales/", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read(200000).decode("utf-8", "ignore")
        print("final:", r.geturl(), "status:", r.status)
        siren = re.search(r"\d{9}", re.sub(r"\s", "", html))
        emails = sorted(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)))
        emails = [e for e in emails if not any(x in e.lower() for x in [".png",".jpg",".svg","sentry","example"])]
        cp = re.findall(r"©\s*(\d{4})", html)[:4]
        print("siren9:", siren.group(0) if siren else None, "| emails:", emails[:6], "| cp:", cp)
        print("titre:", re.findall(r"<title[^>]*>(.*?)</title>", html, re.I|re.S)[:1])
        print("adresse:", re.findall(r"[0-9]{5}\s+[A-Za-zÀ-ÿ' \-]+", html)[:3])
except Exception as e:
    print("ERR", str(e)[:150])

print("\n=== MX des domaines email retenus ===")
doms = ["lenoirmetallerie.fr", "oaca.fr", "sudmetallerie.com", "gb-metallerie.fr", "groupe-gb.fr",
        "torras.fr", "gatsbysoudure.com", "soudecoup.fr", "ats.fr", "atlantiquetoleriesoudure.fr",
        "metallerie.com", "smgconfrere.com", "smg-decoupage-tolerie.com", "sdeb.fr", "uma02.fr",
        "samd-aero.fr", "samd-aero.com", "batisud.org", "lg-metallerie.fr"]
for d in doms:
    r = subprocess.run(["nslookup", "-type=mx", d], capture_output=True, text=True, timeout=20)
    out = r.stdout.encode("cp850", errors="replace").decode("utf-8", errors="replace")
    mx = re.findall(r"mail exchanger = (\S+)", out)
    if not mx:
        mx = re.findall(r"(\S+\.\S+)\s+MX\s+preference", out)
    print(f"{d}: {mx[:3] if mx else 'PAS DE MX'}")

print("\n=== Test email_tester/verify_smtp si dispo ===")
