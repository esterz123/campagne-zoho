#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot10 : analyse vision des captures avec pixtral (fallback Portal bloque)."""
import base64, json, os, sys, time, urllib.request

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
CAP = os.path.join(BASE, "captures")

with open(BASE + r"\.ia_tokens.json", encoding="utf-8") as f:
    MISTRAL = json.load(f)["mistral"]

PROMPT_VISION = (
    "Tu es un directeur artistique senior. Analyse cette capture d'ecran d'un "
    "site web d'entreprise. Reponds en francais, concret, sans jargon inutile. "
    "Structure ta reponse en 3 parties :\n"
    "1. CONSTATS VISUELS : ce que tu vois reellement (design date ou moderne, "
    "couleurs, typographie, hierarchie, photos, espacement, professionalisme).\n"
    "2. PROBLEMES : les 2-3 defauts visuels les plus visibles qui nuisent a la "
    "credibilite (ex: logo pixelise, texte illisible, couleurs criardes, page "
    "vide, mise en page annee 2000, pas de coherence).\n"
    "3. VERDICT : note de 1 a 5 (1 = tres moche, 3 = moyen, 5 = tres beau) "
    "sur une ligne au format 'VERDICT: X/5'.\n"
    "Sois honnete et precis. Si le site est beau, dis-le (ne pas inventer de "
    "defauts). Ne reponds rien d'autre."
)

def analyse(png_path):
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = {
        "model": "pixtral-12b-2409",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT_VISION},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
        ]}],
        "max_tokens": 700,
        "temperature": 0.2,
    }
    req = urllib.request.Request("https://api.mistral.ai/v1/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": "Bearer " + MISTRAL, "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                j = json.loads(r.read().decode())
            return j["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 2:
                return "ERREUR: " + str(e)[:150]
            time.sleep(3)

out = {}
try:
    out = json.load(open(BASE + r"\_lot10_vision_tmp.json", encoding="utf-8"))
except Exception:
    out = {}

files = sorted(f for f in os.listdir(CAP) if f.startswith("lot10_") and f.endswith(".png"))
for fn in files:
    name = fn[6:-4]
    if name in out:
        continue
    txt = analyse(os.path.join(CAP, fn))
    out[name] = txt
    print("=" * 70, flush=True)
    print(name.upper(), flush=True)
    print(txt[:900], flush=True)
    json.dump(out, open(BASE + r"\_lot10_vision_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(1)
print("TERMINE", len(out), "analyses")
