#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 13 : analyse vision pixtral des 10 captures."""
import json, os, base64, urllib.request, time

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
JPEGDIR = os.path.join(BASE, "_lot13_shots", "jpeg")

with open(os.path.join(BASE, ".ia_tokens.json"), encoding="utf-8") as f:
    TOKEN = json.load(f)["mistral"]

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

def analyze(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = {
        "model": "pixtral-12b-2409",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT_VISION},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64}"},
        ]}],
        "max_tokens": 700,
    }
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        j = json.loads(r.read().decode())
    return j["choices"][0]["message"]["content"]

results = {}
for idx in [118, 126, 127, 129, 131, 132, 135, 137, 144, 145]:
    path = os.path.join(JPEGDIR, f"lot13_{idx}.jpg")
    for attempt in range(3):
        try:
            txt = analyze(path)
            results[idx] = txt
            verdict = [l for l in txt.splitlines() if "VERDICT" in l]
            print(f"[{idx}] {verdict}")
            break
        except Exception as e:
            print(f"[{idx}] attempt {attempt}: ERR {str(e)[:120]}")
            time.sleep(3)
    time.sleep(1.5)

with open(os.path.join(BASE, "_lot13_vision_tmp.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print("saved")
