# -*- coding: utf-8 -*-
import sys, re, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
T = r"C:SERSLAMBAPPDATAocal/temp\rouxel.html"
html = open(T, encoding="utf-8", errors="replace").read()
print("== RSP mentions ==")
for m in re.findall(r"[Rr][Ss][Pp][^\"<>]{0,60}", html)[:8]:
    print(repr(m[:80]))
print("== H2/H3 ==")
for m in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", html, re.I | re.S)[:12]:
    print(re.sub(r"<[^>]+>", "", m).strip()[:90])
print("== liens internes ==")
links = sorted(set(re.findall(r'href="(https://www\.rouxel-mold\.com[^"]*)"', html)))
for l in links[:15]:
    print(l)
