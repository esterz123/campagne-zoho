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
FREE_SUFFIX_PROVIDERS = {"portal", "nous", "openrouter"}

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
    tok = charger_tokens()
    key = tok.get(provider)
    if not key:
        raise RuntimeError("Pas de cle pour %s" % provider)
    if provider in FREE_SUFFIX_PROVIDERS and not modele.endswith(":free"):
        raise ValueError("Modele refuse pour %s (doit finir par :free) : %s"
                         % (provider, modele))
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

def repondre(prompt, usage="ecriture", systeme=None, max_tokens=500,
             temperature=0.7):
    messages = []
    if systeme:
        messages.append({"role": "system", "content": systeme})
    messages.append({"role": "user", "content": prompt})
    for provider, modele in CONFIG.get(usage, CONFIG["ecriture"]):
        try:
            j = _call_provider(provider, modele, messages, max_tokens, temperature)
            return _extract(j)
        except Exception as e:
            sys.stderr.write("[%s/%s] %s\n" % (provider, modele, str(e)[:80]))
            time.sleep(1)
    raise RuntimeError("Toutes les IA gratuites ont echoue. Aucun credit consomme.")

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "Dis juste OUI"
    u = sys.argv[2] if len(sys.argv) > 2 else "ecriture"
    try:
        print("REPONSE:", repondre(q, usage=u))
    except Exception as e:
        print("ERREUR:", e); sys.exit(1)
