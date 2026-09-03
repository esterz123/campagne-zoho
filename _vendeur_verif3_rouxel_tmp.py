# -*- coding: utf-8 -*-
"""Verif page contact rouxel-mold.com : email publie ou formulaire seul ?"""
import urllib.request, re, ssl, html

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36"})
    return urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()).read().decode("utf-8", errors="replace")

# trouver le lien contact dans la home
body = fetch("https://www.rouxel-mold.com/")
links = re.findall(r'href="([^"]*contact[^"]*)"', body, re.I)
print("LIENS CONTACT:", sorted(set(links))[:6])

for u in sorted(set(links))[:3]:
    if u.startswith("http") and "rouxel" not in u:
        continue
    full = u if u.startswith("http") else "https://www.rouxel-mold.com/" + u.lstrip("/")
    try:
        b = fetch(full)
        mails = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.sub(r"<script.*?</script>", "", b, flags=re.S)))
        form = bool(re.search(r"<form\b", b, re.I))
        print(full, "-> statut OK | formulaire:", form, "| emails:", mails if mails else "AUCUN")
    except Exception as ex:
        print(full, "-> ERREUR:", ex)
