# -*- coding: utf-8 -*-
"""Complements verification rouxel-mold.com : tel publie, texte visible home."""
import urllib.request, re, ssl, html

URL = "https://www.rouxel-mold.com/"
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0 Safari/537.36"})
body = urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()).read().decode("utf-8", errors="replace")

tel = re.findall(r"(?:\+33|0)[1-9](?:[\s.\-]?\d{2}){4}", re.sub(r"<script.*?</script>", "", body, flags=re.S))
print("NUMEROS TEL visibles:", tel if tel else "AUCUN")

text = re.sub(r"<script.*?</script>|<style.*?</style>", "", body, flags=re.S)
text = html.unescape(re.sub(r"<[^>]+>", " ", text))
text = re.sub(r"\s+", " ", text).strip()
print("TEXTE HOME (900 car):", text[:900])
