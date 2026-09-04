#!/bin/bash
# Verifie l'etat de la relance 3 Rouxel dans campagne_state.json
cd "C:/Users/ulamb/Bureau/prospection/github-campagne"
grep -o '"relance3[^"]*"[^,}]*' campagne_state.json | head -10
echo "---- cle 3 ----"
grep -o '"3": {[^}]*}' campagne_state.json | head -c 1500
