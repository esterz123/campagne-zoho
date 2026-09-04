#!/bin/bash
# Verifie le site rouxel-mold.com en live : titre, description, marques
OUT="$LOCALAPPDATA/Temp/rouxel_home.html"
curl -s --compressed --max-time 25 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "https://www.rouxel-mold.com/" -o "$OUT"
echo "== taille =="
wc -c "$OUT"
echo "== title =="
grep -o "<title>[^<]*</title>" "$OUT"
echo "== description =="
grep -io 'name="description" content="[^"]*"' "$OUT" | head -c 700
echo ""
echo "== marques =="
grep -ioc "RMB" "$OUT"
grep -ioc "ROUXEL GROUP" "$OUT"
grep -ioc "Rouxel Mold" "$OUT"
