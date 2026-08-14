#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASSE BIOS PRUDENTE — limite le nombre de comptes par run, espace davantage,
retry long sur 429, s'arrete proprement si la session est limitee.
Usage : python3 lecteur_bios_prudent.py [--max N] [--delay S]
"""
import json, os, sys, time, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
SID_FILE = os.path.join(BASE, ".sessionid.txt")
OUT_FILE = os.path.join(BASE, "bios_insta.json")
KIT_FILE = os.path.join(BASE, "kit_dm_masse.json")

UA_MOBILE = ("Instagram 219.0.0.12.117 Android (30/11; 420dpi; 1080x2400; "
             "samsung; SM-G991B; o1s; exynos2100; en_US; 335808396)")
APP_ID = "936619743392459"

def charger_sessionid():
    with open(SID_FILE, encoding="utf-8") as f:
        sid = f.read().strip()
    if not sid or len(sid) < 10:
        print("ERREUR: sessionid invalide.")
        sys.exit(1)
    return sid

def extraire_handle(u):
    u = (u or "").strip()
    if not u:
        return None
    u = u.strip().strip("/")
    if "instagram.com/" in u:
        u = u.split("instagram.com/", 1)[1]
    u = u.split("/")[0].split("?")[0].strip().lstrip("@").strip()
    return u or None

def lire_profil(sid, username):
    url = ("https://i.instagram.com/api/v1/users/web_profile_info/"
           f"?username={urllib.parse.quote(username)}")
    headers = {
        "User-Agent": UA_MOBILE,
        "x-ig-app-id": APP_ID,
        "Cookie": f"sessionid={sid}",
        "Accept": "*/*",
        "Accept-Language": "fr-FR,fr;q=0.9",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            j = json.loads(r.read().decode("utf-8", errors="ignore"))
        u = j.get("data", {}).get("user", {})
        if not u:
            return None
        return {
            "full_name": u.get("full_name"),
            "bio": u.get("biography"),
            "site": u.get("external_url"),
            "followers": (u.get("edge_followed_by") or {}).get("count"),
            "posts": (u.get("edge_owner_to_timeline_media") or {}).get("count"),
            "is_private": u.get("is_private", False),
            "is_business": u.get("is_business_account", False),
            "category": u.get("category_name"),
        }
    except urllib.error.HTTPError as e:
        return {"_erreur": f"HTTP {e.code}"}
    except Exception as e:
        return {"_erreur": str(e)[:80]}

def main():
    args = sys.argv[1:]
    max_n = 30
    delay = 20
    if "--max" in args:
        max_n = int(args[args.index("--max") + 1])
    if "--delay" in args:
        delay = int(args[args.index("--delay") + 1])

    sid = charger_sessionid()
    kit = json.load(open(KIT_FILE, encoding="utf-8"))

    # Ordre de priorite : ceux SANS site connu d'abord (ceux-la ont le plus a gagner),
    # puis les 13 deja confirmes (pour la bio/site supplementaire).
    def priorite(x):
        return 0 if not x.get("website") else 1
    kit_trie = sorted(kit, key=priorite)

    usernames = []
    for x in kit_trie:
        u = extraire_handle(x.get("instagram"))
        if u and u not in usernames:
            usernames.append(u)
    usernames = usernames[:max_n]

    # Fusionner avec les resultats existants (ne pas perdre les anciens)
    resultats = {}
    if os.path.exists(OUT_FILE):
        try:
            resultats = json.load(open(OUT_FILE, encoding="utf-8"))
        except Exception:
            resultats = {}

    print(f"{len(usernames)} comptes (max {max_n}, delai {delay}s). Session jamais affichee.")
    echecs_429_consecutifs = 0
    for i, u in enumerate(usernames, 1):
        r = lire_profil(sid, u)
        if r and r.get("_erreur") == "HTTP 429":
            echecs_429_consecutifs += 1
            if echecs_429_consecutifs >= 3:
                print("3 echecs 429 consecutifs -> quota epuise, on arrete proprement.")
                break
            print(f"[{i}/{len(usernames)}] {u}: 429 -> pause 120s")
            time.sleep(120)
            r = lire_profil(sid, u)
        else:
            echecs_429_consecutifs = 0
        if r is None:
            r = {"_erreur": "compte introuvable"}
        resultats[u] = r
        etat = "OK" if "_erreur" not in r else f"ERR {r['_erreur']}"
        print(f"[{i}/{len(usernames)}] {u}: {etat}")
        time.sleep(delay)

    json.dump(resultats, open(OUT_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for r in resultats.values() if "_erreur" not in r)
    print(f"\nTERMINE: {ok} profils OK dans {OUT_FILE} (cumulatif)")

if __name__ == "__main__":
    main()
