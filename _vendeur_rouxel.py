# -*- coding: utf-8 -*-
import sys, re, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
html = open(sys.argv[1], encoding="utf-8", errors="replace").read()
imgs = re.findall(r"<img\b[^>]*>", html, re.I)
noalt = [i for i in imgs if "alt=" not in i.lower()]
emptyalt = [i for i in imgs if re.search(r"alt=[\"\x27]\s*[\"\x27]", i, re.I)]
print("img total:", len(imgs), "| sans alt:", len(noalt), "| alt vide:", len(emptyalt))
print("slides:", re.findall(r"slide-\d+\.jpg", html))
h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
print("h1:", [re.sub(r"<[^>]+>", "", h).strip()[:80] for h in h1])
vp = re.findall(r'name="viewport"[^>]*', html, re.I)
print("viewport:", vp[:1])
print("title-len chars:", len(re.findall(r"<title>(.*?)</title>", html, re.I | re.S)[0]))
