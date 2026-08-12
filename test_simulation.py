#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test : simule un message entrant d'un prospect de la campagne,
genere la reponse via OpenRouter, et envoie le brouillon sur Discord.
Utilise les tokens locaux (.zoho_tokens.json) pour l'acces Zoho/Discord.
"""
import json, os, sys, re, urllib.request, urllib.parse, datetime

# --- Import du code du repondeur (copie des fonctions necessaires) ---
BASE = os.path.dirname(os.path.abspath(__file__))
ACC = "7349712000000008002"
ME = "contact@mahdi-design.com"
MODEL = "deepseek/deepseek-v4-flash"
DATA_F = os.path.join(BASE, "campagne_data.json")

AUTO_PATTERNS = [
    "reponse automatique", "automatic reply", "out of office",
    "cong", "vacances", "je serai", "de retour", "absent",
    "prendrai connaissance", "a mon retour", "disponible a partir",
]

def load_creds_local():
    local = os.path.join(os.path.dirname(BASE), ".zoho_tokens.json")
    if os.path.exists(local):
        d = json.load(open(local, encoding="utf-8"))
        return d["client_id"], d["client_secret"], d["refresh_token"]
    return None

def refresh_access(cid, csec, ref):
    body = urllib.parse.urlencode({"grant_type": "refresh_token", "client_id": cid,
                                   "client_secret": csec, "refresh_token": ref}).encode()
    req = urllib.request.Request("https://accounts.zoho.com/oauth/v2/token", data=body, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=30))["access_token"]

def zoho_get(url, access):
    req = urllib.request.Request(url, headers={"Authorization": "Zoho-oauthtoken " + access})
    return json.load(urllib.request.urlopen(req, timeout=30))

def load_prospects():
    d = json.load(open(DATA_F, encoding="utf-8"))
    out = {}
    for e in d:
        to = (e.get("to") or "").strip().lower()
        if to:
            out[to] = {"num": e.get("num"), "entreprise": e.get("entreprise", ""),
                       "subject": e.get("subject", "")}
    return out

def is_auto(summary, subject):
    t = ((summary or "") + " " + (subject or "")).lower()
    return any(p in t for p in AUTO_PATTERNS)

def openrouter(prompt, key):
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.6}).encode()
    url = "https://openrouter.ai/api/v1/chat/completions"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    j = json.load(urllib.request.urlopen(req, timeout=60))
    return j["choices"][0]["message"]["content"].strip()

def build_prompt(prosp, msginfo):
    p = prosp or {}
    return """Tu rediges la reponse email de Mahdi, designer de marque independant (studio MAHDI.), qui travaille avec des PME et industriels francais.
Prospect (entreprise connue de la campagne) : %s
Notre email initial envoye a ce prospect etait : "%s"
Le client vient de repondre : "%s" (sujet : %s)
Nos offres exactes : Diagnostic express 290 EUR (jusqu'a 490 EUR selon complexite, rapport en 48h, rembourse si pas de valeur). Refonte de marque 3500 a 15000 EUR. Pack securite WordPress 79 EUR/mois, premier mois offert, sans engagement.
Regles strictes :
- Francais naturel, ton chaleureux et pro, jamais de pub ni de survente.
- PERSONNALISE avec le contexte ci-dessus. Ne colle aucun texte generique.
- JAMAIS de tiret (ni em-dash ni autre) dans la phrase finale : virgules, points, deux-points, parentheses uniquement.
- 3 a 8 phrases max. Termine par "Mahdi" seul (pas de signature longue, pas de site, pas de telephone).
- Si on demande les prix, donne ceux ci-dessus.
- Si le client demande un devis precis, une date engagee, ou negocie : type = "draft". Sinon type = "reply".
Reponds UNIQUEMENT en JSON valide : {"type": "reply" ou "draft", "message": "le texte complet"}""" % (
        p.get("entreprise", "inconnu"), p.get("subject", ""), msginfo["summary"], msginfo["subject"])

def parse_gemini_out(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return "draft", text
    try:
        d = json.loads(m.group(0))
        return (d.get("type") or "draft"), (d.get("message") or "").strip()
    except Exception:
        return "draft", text

def notify_discord(text):
    hook = os.environ.get("DISCORD_WEBHOOK")
    if not hook:
        # essayer de lire depuis le .zoho_tokens.json qui contient aussi le webhook
        local = os.path.join(os.path.dirname(BASE), ".zoho_tokens.json")
        if os.path.exists(local):
            d = json.load(open(local, encoding="utf-8"))
            hook = d.get("discord_webhook") or d.get("DISCORD_WEBHOOK")
    if not hook:
        print("⚠️  Pas de webhook Discord configuré")
        return False
    body = json.dumps({"content": text}).encode()
    req = urllib.request.Request(hook, data=body, headers={"Content-Type": "application/json", "User-Agent": "campagne-bot/1.0"})
    urllib.request.urlopen(req, timeout=20)
    return True

# --- SIMULATION ---
if __name__ == "__main__":
    # 1. Charger la clé OpenRouter (depuis env ou .env hermes)
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        # tenter .env Hermes
        hermes_env = r"C:\Users\ulamb\AppData\Local\hermes\.env"
        if os.path.exists(hermes_env):
            for line in open(hermes_env, encoding="utf-8"):
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip().strip('"')
                    break
    if not key:
        print("❌ OPENROUTER_API_KEY manquante (env ou .env Hermes)")
        sys.exit(1)
    print(f"✅ Clé OpenRouter chargée (fin: ...{key[-10:]})")

    # 2. Charger prospects
    prospects = load_prospects()
    print(f"✅ {len(prospects)} prospects chargés")

    # 3. SIMULER un message entrant depuis techno@slicom-group.com (Slicom #2)
    # C'est un prospect CONFIRMÉ de la campagne
    test_from = "techno@slicom-group.com"
    test_subject = "Re: WordPress 2018 sur votre site , un détail qui coûte cher"
    test_summary = "Bonjour Mahdi, merci pour votre email. Nous sommes intéressés par votre diagnostic gratuit. Pouvez-vous nous envoyer plus de détails sur la méthodologie et le délai ? Cordialement, L'équipe technique Slicom"
    
    prosp = prospects.get(test_from.lower())
    if not prosp:
        print(f"❌ Prospect {test_from} non trouvé dans la campagne")
        sys.exit(1)
    
    print(f"📧 Simulation message de: {test_from}")
    print(f"   Entreprise: {prosp['entreprise']}")
    print(f"   Sujet original: {prosp['subject']}")
    print(f"   Réponse simulée: {test_summary[:80]}...")

    # 4. Générer la réponse via OpenRouter
    msginfo = {"summary": test_summary, "subject": test_subject}
    prompt = build_prompt(prosp, msginfo)
    print("\n🤖 Appel OpenRouter (nemotron-3-ultra)...")
    try:
        out = openrouter(prompt, key)
        print(f"✅ Réponse brute reçue ({len(out)} chars)")
        print(f"   ---\n{out}\n---")
    except Exception as e:
        print(f"❌ Erreur OpenRouter: {e}")
        sys.exit(1)

    # 5. Parser la réponse
    typ, msg = parse_gemini_out(out)
    print(f"\n📝 Type: {typ}")
    print(f"📝 Message généré:\n{msg}")

    # 6. Construire le rapport pour Discord
    rapport = f"""**REPONDEUR IA (SIMULATION TEST)** : 1 message simulé traité.

**[DRAFT]** {test_from} : brouillon proposé (type={typ}).
--- DÉBUT BROUILLON ---
{msg}
--- FIN BROUILLON ---

Prospect: {prosp['entreprise']}
Email initial: {prosp['subject']}
Réponse client: {test_summary[:100]}...
"""

    print(f"\n📤 Envoi du brouillon sur Discord...")
    try:
        ok = notify_discord(rapport)
        if ok:
            print("✅ Brouillon envoyé sur Discord avec succès !")
        else:
            print("⚠️  Discord non envoyé (webhook manquant)")
    except Exception as e:
        print(f"❌ Erreur Discord: {e}")

    print("\n✅ SIMULATION TERMINÉE AVEC SUCCÈS")
    print("👀 Regarde ton Discord : le brouillon y est !")