#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOTEUR IA MAISON V3 — couche 0 du systeme Mahdi Design.
========================================================
PRINCIPE (decisions Mahdi) :
  - On n'utilise QUE des modeles GRATUITS. Jamais un modele payant.
  - Si tous les gratuits echouent, on retourne une ERREUR (0 credit consomme).
  - Cascade de secours : provider 1 -> 2 -> 3 -> ... pour n'etre jamais a court.

Providers tries par priorite (cles dans .ia_tokens.json en local, secrets GitHub en cloud) :
  1. Nous Portal  (modeles :free uniquement, pricing=0)  -> tencent/hy3:free      [TESTE OK]
  2. Mistral      (1B tokens/mois, quasi illimite)  -> mistral-small/large  [TESTE OK]
  3. Groq         (1000-14400 req/jour)             -> llama-3.3-70b        [TESTE OK via curl]
  4. OpenRouter   (50 req/jour, :free uniquement)   -> nemotron/gpt-oss     [TESTE OK]

NB Cloudflare : certains providers (Groq, Nous Portal) bloquent urllib (code 1010). On appelle
donc via `curl` (vrai client HTTP). Mistral et OpenRouter passent par urllib.

REGLES DE SECURITE (non negociables) :
  - Nous Portal / OpenRouter / OpenCode Zen : modeles DOIVENT finir par :free (garde-fou).
  - Si tous les gratuits echouent -> ERREUR propre, 0 credit consomme.
  - Les cles ne sont JAMAIS poussees sur GitHub (.gitignore + secrets env).
"""
import json, os, sys, time, subprocess, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
CREDS = os.path.join(BASE, ".ia_tokens.json")

# REGLE : uniquement des modeles gratuits. Ajuster ici si besoin.
CONFIG = {
    "ecriture": [
        ("portal",    "tencent/hy3:free"),               # Nous Portal, pricing=0 = GRATUIT
        ("mistral",   "mistral-small-latest"),           # 1B tokens/mois gratuit
        ("groq",      "llama-3.3-70b-versatile"),
        ("openrouter","nvidia/nemotron-nano-12b-v2-vl:free"),
    ],
    "reflexion": [
        ("portal",    "tencent/hy3:free"),
        ("mistral",   "mistral-large-latest"),
        ("groq",      "llama-3.3-70b-versatile"),
        ("openrouter","nvidia/nemotron-3-super-120b-a12b:free"),
    ],
    "code": [
        ("portal",    "stepfun/step-3.7-flash:free"),
        ("mistral",   "codestral-latest"),
        ("groq",      "qwen3-32b"),
        ("openrouter","openai/gpt-oss-20b:free"),
    ],
}

# providers ou le modele DOIT finir par :free (aucun modele payant jamais appele)
FREE_SUFFIX_PROVIDERS = {"portal", "nous", "openrouter", "zen", "opencode"}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

def charger_tokens():
    """Cles IA : variables d'environnement d'abord (GitHub Actions / secrets),
    puis fichier local .ia_tokens.json (dev / PC). Jamais pousse sur GitHub."""
    env_map = {
        "portal":     os.environ.get("PORTAL_API_KEY"),
        "nous":       os.environ.get("PORTAL_API_KEY"),
        "mistral":    os.environ.get("MISTRAL_API_KEY"),
        "groq":       os.environ.get("GROQ_API_KEY"),
        "cerebras":   os.environ.get("CEREBRAS_API_KEY"),
        "openrouter": os.environ.get("OPENROUTER_API_KEY"),
        "zen":        os.environ.get("OPENCODE_ZEN_API_KEY"),
        "opencode":   os.environ.get("OPENCODE_ZEN_API_KEY"),
    }
    from_env = {k: v for k, v in env_map.items() if v}
    if from_env:
        return from_env
    if not os.path.exists(CREDS):
        raise RuntimeError("Fichier .ia_tokens.json manquant et aucune cle en env.")
    with open(CREDS, encoding="utf-8") as f:
        return json.load(f)

def _curl_json(url, data, headers, timeout=90):
    """Appelle via curl (contourne Cloudflare 1010). Retourne le JSON.
    Ecrit le payload dans un fichier temp reel puis -d @fichier (fiable Windows)."""
    import tempfile
    hdrs = " ".join("-H '%s: %s'" % (k, v) for k, v in headers.items())
    fd, payload_path = tempfile.mkstemp(prefix="ia_payload_", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    try:
        cmd = ("curl -s -m %d '%s' %s -H 'Content-Type: application/json' "
               "-d @%s " % (timeout, url, hdrs, payload_path))
        p = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout + 15)
        if p.returncode != 0:
            raise RuntimeError("curl exit %d: %s" % (p.returncode, p.stderr[:120]))
        out = p.stdout.strip()
        if not out:
            raise RuntimeError("curl reponse vide (Cloudflare?)")
        return json.loads(out)
    finally:
        try: os.remove(payload_path)
        except Exception: pass

def _urllib_json(url, data, headers, timeout=60):
    req = urllib.request.Request(url, data=json.dumps(data).encode(),
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def _call_provider(provider, modele, messages, max_tokens, temperature):
    # GARDE-FOU D'ABORD (regle absolue) : jamais un modele payant,
    # meme si la cle existe. Passe avant tout le reste.
    if provider in FREE_SUFFIX_PROVIDERS and not modele.endswith(":free"):
        raise ValueError("Modele refuse pour %s (doit finir par :free) : %s"
                         % (provider, modele))
    tok = charger_tokens()
    key = tok.get(provider)
    if not key:
        raise RuntimeError("Pas de cle pour %s" % provider)
    body = {"model": modele, "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature}
    hdr = {"Authorization": "Bearer " + key, "User-Agent": UA}

    if provider == "mistral":
        return _urllib_json("https://api.mistral.ai/v1/chat/completions",
                            body, {**hdr, "Content-Type": "application/json"})
    if provider == "groq":
        # Cloudflare bloque urllib -> curl
        return _curl_json("https://api.groq.com/openai/v1/chat/completions",
                          body, {**hdr, "Content-Type": "application/json"})
    if provider == "cerebras":
        return _curl_json("https://api.cerebras.ai/v1/chat/completions",
                          body, {**hdr, "Content-Type": "application/json"})
    if provider == "openrouter":
        return _urllib_json("https://openrouter.ai/api/v1/chat/completions",
                            body, {**hdr, "Content-Type": "application/json",
                                   "HTTP-Referer": "https://mahdi-design.com"})
    if provider in ("portal", "nous"):
        base = tok.get("portal_base", "https://inference-api.nousresearch.com/v1")
        return _curl_json(base + "/chat/completions",
                          body, {**hdr, "Content-Type": "application/json"})
    raise ValueError("Provider inconnu: %s" % provider)

def _extract(j):
    if "choices" in j and j["choices"]:
        m = j["choices"][0].get("message", {})
        # Les modeles "reasoning" (ex: tencent/hy3:free) mettent la reponse dans
        # message.reasoning quand content est null.
        content = m.get("content")
        if not content:
            content = m.get("reasoning")
        if content:
            return content.strip()
    raise RuntimeError("Reponse illisible: " + str(j)[:150])

# ============================================================
# BOUCLE INFINIE + COOLDOWNS ANTI-BAN + AUTO-TEST
# ============================================================

_COOLDOWNS = {}   # provider -> timestamp (epoch) jusqu'auquel il est en pause
_ECHECS = {}      # provider -> nombre d'echecs consecutifs

def _en_cooldown(provider):
    return time.time() < _COOLDOWNS.get(provider, 0)

def _marquer_echec(provider, erreur):
    _ECHECS[provider] = _ECHECS.get(provider, 0) + 1
    n = _ECHECS[provider]
    e = str(erreur)
    # 429 = rate limit -> pause longue (anti-ban)
    if "429" in e or "Too Many Requests" in e or "rate limit" in e.lower():
        _COOLDOWNS[provider] = time.time() + 900   # 15 min de pause
    elif "401" in e or "403" in e or "invalid" in e.lower():
        _COOLDOWNS[provider] = time.time() + 3600  # cle morte -> 1h (ou jamais)
    else:
        # echec reseau/5xx -> pause courte, exponentielle avec le nb d'echecs
        _COOLDOWNS[provider] = time.time() + min(5 * (2 ** n), 300)

def _marquer_succes(provider):
    _ECHECS[provider] = 0
    _COOLDOWNS.pop(provider, None)   # un succes leve le cooldown

def repondre(prompt, usage="ecriture", systeme=None, max_tokens=500,
             temperature=0.7, max_secondes=0, silencieux=False):
    """Cascade INFINIE et DYNAMIQUE : a CHAQUE tentative on re-trie les
    providers (prioritaires hors cooldown d'abord) et on prend le meilleur
    disponible. Si le provider n1 revient pendant qu'on etait sur le secours,
    la tentative suivante repart direct sur le n1 (on ne finit pas la passe).
    0 = infini (jusqu'a ce que le job timeout)."""
    messages = []
    if systeme:
        messages.append({"role": "system", "content": systeme})
    messages.append({"role": "user", "content": prompt})
    config = CONFIG.get(usage, CONFIG["ecriture"])
    rang = {m: i for i, (p, m) in enumerate(config)}
    t0 = time.time()
    tentatives = 0
    while True:
        # Re-trie A CHAQUE tentative : dispo (hors cooldown) en premier,
        # dans l'ordre de priorite config, puis ceux en cooldown.
        dispo = [(p, m) for (p, m) in config if not _en_cooldown(p)]
        en_pause = [(p, m) for (p, m) in config if _en_cooldown(p)]
        ordre = dispo + en_pause
        tentatives += 1
        for provider, modele in ordre:
            if _en_cooldown(provider):
                continue
            try:
                j = _call_provider(provider, modele, messages, max_tokens, temperature)
                rep = _extract(j)
                _marquer_succes(provider)
                return rep
            except Exception as e:
                _marquer_echec(provider, e)
                if not silencieux:
                    sys.stderr.write("[tentative %d][%s/%s] %s\n"
                                     % (tentatives, provider, modele, str(e)[:80]))
                time.sleep(0.5)
                # Un provider prioritaire est-il revenu pendant l'appel ?
                # -> on re-trie immediatement (prochaine iteration du while)
                meilleur = min(dispo, key=lambda pm: rang[pm[1]]) if dispo else None
                if meilleur and rang[meilleur[1]] < rang[modele] and not _en_cooldown(meilleur[0]):
                    break
        if max_secondes > 0 and time.time() - t0 >= max_secondes:
            raise RuntimeError("Timeout %ds: toutes les IA gratuites ont echoue."
                               % max_secondes)
        # Tous en echec cette passe -> courte pause puis on RETENTE (boucle)
        time.sleep(min(1 + tentatives * 0.5, 20))

def tester_modeles(usage="ecriture", silencieux=True):
    """Ping tous les modeles gratuits de la config avec une micro-requete,
    mesure latence + succes, retourne un classement. 1 req/modele, delai entre
    chaque pour ne pas se faire bannir."""
    import random
    config = CONFIG.get(usage, CONFIG["ecriture"])
    resultats = []
    for i, (provider, modele) in enumerate(config):
        try:
            t = time.time()
            j = _call_provider(provider, modele,
                               [{"role": "user", "content": "Reponds juste: ok"}],
                               8, 0.0)
            latence = time.time() - t
            rep = _extract(j)
            resultats.append({"provider": provider, "modele": modele,
                              "ok": True, "latence_s": round(latence, 1),
                              "extrait": rep[:40]})
        except Exception as e:
            resultats.append({"provider": provider, "modele": modele,
                              "ok": False, "erreur": str(e)[:60]})
        if i < len(config) - 1:
            time.sleep(2 + random.random() * 3)   # espace les tests (anti-ban)
    # classement : ok d'abord, puis par latence croissante
    classement = sorted(resultats, key=lambda r: (not r.get("ok"), r.get("latence_s", 999)))
    with open(os.path.join(BASE, "classement_modeles.json"), "w", encoding="utf-8") as f:
        json.dump(classement, f, ensure_ascii=False, indent=1)
    return classement

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "Dis juste OUI"
    u = sys.argv[2] if len(sys.argv) > 2 else "ecriture"
    try:
        print("REPONSE:", repondre(q, usage=u))
    except Exception as e:
        print("ERREUR:", e); sys.exit(1)
