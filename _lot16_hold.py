#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 16 : remontee holdings + sondes de domaines pour sites reels."""
import json, re, time, urllib.request, urllib.error, ssl, socket

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
socket.setdefaulttimeout(9)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

def api(q):
    url = "https://recherche-entreprises.api.gouv.fr/search?q=" + q + "&per_page=1"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())["results"]

def climb(siren, prof=0):
    if prof >= 3:
        return [("MAXDEPTH", siren)]
    try:
        res = api(siren)
        if not res: return [("VIDE", siren)]
        r0 = res[0]
        dgs = r0.get("dirigeants", [])
        # priorite : personne physique President > Gerant > DG, sinon personne morale
        phys = [d for d in dgs if d.get("type_dirigeant") == "personne physique" and d.get("qualite") in ("Président de SAS", "Président", "Gérant", "Directeur Général", "Président du conseil d'administration", "Président-directeur général")]
        if phys:
            d = phys[0]
            return [(d.get("prenoms", "") + " " + d.get("nom", "")).strip(), d.get("qualite")]
        mor = [d for d in dgs if d.get("type_dirigeant") == "personne morale" and "Commissaire" not in (d.get("qualite") or "")]
        if mor:
            d = mor[0]
            sub = climb(d.get("siren"), prof + 1) if d.get("siren") else [("NOPHYS", d.get("denomination"))]
            return [("MORALE " + d.get("denomination", "?"), d.get("qualite"))] + sub
        # fallback: n'importe quelle personne physique non-CAC
        phys2 = [d for d in dgs if d.get("type_dirigeant") == "personne physique" and "Commissaire" not in (d.get("qualite") or "")]
        if phys2:
            d = phys2[0]
            return [(d.get("prenoms", "") + " " + d.get("nom", "")).strip(), d.get("qualite")]
        return [("AUCUN", siren)]
    except Exception as e:
        return [("ERR " + str(e)[:60], siren)]

HOLDINGS = {
    "525620332_SMG": "822830279",      # C.1947
    "399796861_BAXTER": "824033070",   # HOLDING PG
    "348992488_BERRY": "841648603",    # SARL SDC
    "311666077_OMEDEC": "893077115",   # QUARFLOC
    "338896426_PROGRESS": "434738670", # AMBOISIENNE INVESTISSEMENT
    "303376222_SAVOIE": "389233354",   # H.F.A.
    "419168448_GILLET": "403652167",   # GROUP STSI
    "419808985_NDE": "479852642",      # SOFIRME
    "957502164_VINCENT": "852426469",  # SOKART
    "878798552_ANJOU": "428120331",    # (denomination tronquee)
}
print("== HOLDINGS ==")
hold = {}
for k, s in HOLDINGS.items():
    hold[k] = climb(s)
    print(k, "->", hold[k])
    time.sleep(0.4)

# sondes de domaines
PROBES = {
    "419168448_GILLET": ["https://gillet-decolletage.fr", "https://gillet-decolletage.com", "https://www.gillet-decolletage.fr", "https://decolletage-gillet.fr", "https://gillet-decoupage.fr", "http://gillet-decolletage.fr"],
    "419808985_NDE": ["https://nde-crulai.fr", "https://www.nde-crulai.fr", "https://normandie-decoupage-emboutissage.fr", "https://nde-emboutissage.fr", "https://sites.google.com/view/nde-crulai", "http://nde-crulai.fr"],
    "813390432_GATSBY": ["https://gatsby-soudure.fr", "https://www.gatsby-soudure.fr", "https://gatsbysoudure.fr", "https://gatsby-soudure.com", "http://gatsby-soudure.fr"],
    "348992488_BERRY": ["https://decolletage-berry.fr", "https://www.decolletage-berry.fr", "https://decolletageduberry.fr", "https://decoupage-decolletage-berry.fr", "http://decolletage-berry.fr"],
    "311666077_OMEDEC": ["https://omedec.fr", "https://www.omedec.fr", "https://omedec.com", "https://outillage-omedec.fr", "http://omedec.fr"],
    "338896426_PROGRESS": ["https://outillage-progress.fr", "https://www.outillage-progress.fr", "https://outillageprogress.fr", "http://outillage-progress.fr"],
    "303376222_SAVOIE": ["https://clickoutil.fr", "https://www.clickoutil.fr", "https://savoie-outillage.fr", "https://savoie-outillage-service.fr", "http://clickoutil.fr"],
}
print("== PROBES ==")
probes = {}
for k, urls in PROBES.items():
    res = []
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
            with urllib.request.urlopen(req, timeout=9, context=ctx) as r:
                b = r.read()
                t = re.search(r"<title[^>]*>(.*?)</title>", b.decode("utf-8", "replace"), re.S | re.I)
                title = re.sub(r"\s+", " ", t.group(1)).strip()[:90] if t else ""
                emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", b.decode("utf-8", "replace"))))
                emails = [e for e in emails if "sentry" not in e and "wixpress" not in e][:6]
                res.append((u, r.status, len(b), title, emails))
        except Exception as e:
            res.append((u, "ERR", type(e).__name__, str(e)[:50], []))
    probes[k] = res
    for x in res:
        print(k, "|", x[0], "->", x[1], x[2], "|", (x[3] if x[1] != "ERR" else x[3])[:60], "|", x[4])
json.dump({"holdings": hold, "probes": probes}, open("_lot16_hold_probes_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE")
