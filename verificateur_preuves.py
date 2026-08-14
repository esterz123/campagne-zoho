#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICATEUR DE PREUVES — verifie les faits d'un site dans son HTML reel.
========================================================================
Pour chaque site confirme, extrait le HTML et cherche les preuves :
prix/tarifs, reservation, horaires, avis, design.
Un fait (ex: "aucun prix") n'est JAMAIS ecrit sans preuve negative verifiee
dans le contenu complet (pas seulement une capture).
"""
import json, os, re, urllib.request, urllib.parse, ssl

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

MARQUEURS = {
    'prix': [r'prix', r'tarif', r'\b\d+\s*€', r'\beuros?\b', r'\bEUR\b'],
    'reservation': [r'réserv', r'reserv', r'rendez[- ]vous', r'rdv', r'booking', r'planity', r'treatwell', r'doctolib', r'calendly', r'bookings?'],
    'horaires': [r'horaire', r'ouvert\b', r'fermé', r'ferme\b', r'\blun?d[iy]', r'\bmard[iy]', r'\bmercredi', r'\bjeud[iy]', r'\bvendredi', r'\bsamedi', r'\bdimanche'],
    'avis': [r'avis', r'témoignage', r'temoignage', r'google\s*review', r'note\s*[0-9]', r'[0-9]\.[0-9]\s*[★☆]', r'\bavisgo\b', r'trustpilot'],
    'reseau_social': [r'instagram\.com', r'facebook\.com', r'tiktok\.com'],
    'mail': [r'@\w+\.\w+'],
    'tel': [r'0\d(?:\s?\d){8}'],
}

def extraire_html(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    try:
        return urllib.request.urlopen(req, timeout=timeout, context=CTX).read().decode('utf-8', 'ignore')
    except Exception as e:
        return None

def analyser(url):
    html = extraire_html(url)
    if html is None:
        return {'erreur': 'page inaccessible'}
    texte = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>', ' ', html)
    texte = re.sub(r'\s+', ' ', texte).lower()
    res = {}
    for cat, patterns in MARQUEURS.items():
        trouves = set()
        for p in patterns:
            for m in re.finditer(p, texte):
                trouves.add(m.group(0)[:40])
                if len(trouves) >= 5:
                    break
            if len(trouves) >= 5:
                break
        res[cat] = sorted(trouves)
    res['taille_html'] = len(html)
    return res

def main():
    d = json.load(open(os.path.join(BASE, "kit_dm_masse.json"), encoding="utf-8"))
    for x in d:
        w = x.get("website")
        if not w:
            continue
        r = analyser(w)
        print("=== %s -> %s" % (x.get("nom", "?")[:30], w))
        if 'erreur' in r:
            print("   ", r['erreur'])
            continue
        print("   prix:", len(r['prix']), "| reservation:", len(r['reservation']),
              "| horaires:", len(r['horaires']), "| avis:", len(r['avis']),
              "| insta:", len(r['reseau_social']), "| tel:", len(r['tel']))
        print("   ex prix:", r['prix'][:3], "| ex resa:", r['reservation'][:3], "| ex avis:", r['avis'][:3])

if __name__ == "__main__":
    main()
