#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LECTEUR DE BIOS INSTAGRAM via sessionid (connexion au compte utilisateur).
========================================================================
- Lit le sessionid depuis .sessionid.txt (JAMAIS commite, jamais loggue)
- Interroge l'API interne web_profile_info (meme endpoint que l'app mobile)
- Extrait pour chaque compte : bio, site externe, full_name, followers, posts
- Espace les requetes (4s) pour eviter le declenchement de l'anti-bot
- Ecrit bios_insta.json (mise a jour des cibles dans kit_dm_masse.json ensuite)
"""
import json, os, sys, time, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
SID_FILE = os.path.join(BASE, ".sessionid.txt")
OUT_FILE = os.path.join(BASE, "bios_insta.json")
KIT_FILE = os.path.join(BASE, "kit_dm_masse.json")

UA_MOBILE = ("Instagram 219.0.0.12.117 Android (30/11; 420dpi; 1080x2400; "
             "samsung; SM-G991B; o1s; exynos2100; en_US; 335808396)")
APP_ID = "936619743392459"  # x-ig-app-id public de l'app Android

def charger_sessionid():
    if not os.path.exists(SID_FILE):
        print("ERREUR: fichier .sessionid.txt absent. Suis les instructions d'extraction.")
        sys.exit(1)
    with open(SID_FILE, encoding="utf-8") as f:
        sid = f.read().strip()
    if not sid or len(sid) < 10:
        print("ERREUR: sessionid invalide (trop court).")
        sys.exit(1)
    return sid

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

def extraire_handle(u):
    """Extrait le username depuis l'URL complete ou le handle nu."""
    u = (u or "").strip()
    if not u:
        return None
    # https://www.instagram.com/xxx/ ou @xxx ou xxx
    u = u.strip().strip("/")
    if "instagram.com/" in u:
        u = u.split("instagram.com/", 1)[1]
    u = u.split("/")[0].split("?")[0].strip().lstrip("@").strip()
    return u or None

def main():
    sid = charger_sessionid()
    # cibles : usernames depuis le kit + verifications manuelles possibles
    kit = json.load(open(KIT_FILE, encoding="utf-8"))
    usernames = []
    for x in kit:
        u = extraire_handle(x.get("instagram"))
        if u and u not in usernames:
            usernames.append(u)
    extra = sys.argv[1:]
    for u in extra:
        u = extraire_handle(u)
        if u and u not in usernames:
            usernames.append(u)

    print(f"{len(usernames)} comptes a lire (sessionid charge, jamais affiche)")
    resultats = {}
    for i, u in enumerate(usernames, 1):
        r = lire_profil(sid, u)
        # Retry sur 429 (rate-limit) avec backoff
        if r.get("_erreur") == "HTTP 429":
            time.sleep(45)
            r = lire_profil(sid, u)
        if r is None:
            r = {"_erreur": "compte introuvable"}
        resultats[u] = r
        etat = "OK" if "_erreur" not in r else f"ERR {r['_erreur']}"
        print(f"[{i}/{len(usernames)}] {u}: {etat}")
        time.sleep(6)  # espacement anti-bot

    json.dump(resultats, open(OUT_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    ok = sum(1 for r in resultats.values() if "_erreur" not in r)
    print(f"\nTERMINE: {ok}/{len(usernames)} lus avec succes -> {OUT_FILE}")
    print(f"Le fichier .sessionid.txt n'est jamais affiche ni commite.")

if __name__ == "__main__":
    main()
