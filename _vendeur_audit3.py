# -*- coding: utf-8 -*-
# VENDEUR: audit live de la home rouxel-mold.html (deja telechargee via curl)
import re, io, sys, json
sys.stdout.reconfigure(encoding='utf-8')
h = io.open(r"C:\Users\ulamb\Bureau\prospection\github-campagne\_v_rouxel.html", encoding='utf-8', errors='replace').read()

def grab(pat, flags=0):
    m = re.search(pat, h, flags)
    return m.group(1).strip() if m else None

print("TITLE:", grab(r'<title>(.*?)</title>', re.S))
print("META DESC:", grab(r'<meta name="description" content="(.*?)"', re.I))
print("GENERATOR:", re.findall(r'<meta name="generator" content="(.*?)"', h, re.I))
print("VIEWPORT:", grab(r'<meta name="viewport" content="(.*?)"', re.I))
print("CHARSET:", grab(r'charset=["\']?([\w-]+)'))
imgs = re.findall(r'<img\b[^>]*>', h, re.I)
noalt = [i for i in imgs if not re.search(r'alt="[^"]+"', i)]
print("IMG total:", len(imgs), "| sans alt valide:", len(noalt))
fonts = set(re.findall(r'font-family\s*:\s*([A-Za-z ,\-\"]+)', h))
print("FONT-FAMILIES brutes:", len(fonts))
for f in sorted(fonts)[:15]: print("  -", f[:80])
print("COPYRIGHT:", re.findall(r'[Cc]opyright[^\n<]{0,80}', h)[:3])
print("YEARS:", sorted(set(re.findall(r'(?:&copy;|\(c\)|©|Copyright[^0-9]{0,10})(\d{4})', h))))
print("TABLES layout:", len(re.findall(r'<table', h, re.I)))
print("IFRAMES:", len(re.findall(r'<iframe', h, re.I)))
print("H1:", re.findall(r'<h1[^>]*>(.*?)</h1>', h, re.S)[:3])
txt = re.sub(r'<[^>]+>', ' ', h)
txt = re.sub(r'\s+', ' ', txt)
print("TEXT echantillon:", txt[1200:2600])
