#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot 16 : ecriture de lot16_candidats.json (4 candidats qualifies)."""
import json

OFFRE = ("**Ce que je vous propose, gratuitement et sans engagement :**\n"
         "Un diagnostic de votre image digitale (10 pages) : l'état de votre présence en ligne point par point "
         "(disponibilité, sécurité, design), la comparaison avec 2 de vos concurrents, et 5 recommandations "
         "concrètes. Vous gardez le document.\n\n"
         "Il me suffit d'une réponse à cet email pour vous l'envoyer sous 3 jours.\n\n"
         "Cordialement,\nMahdi\nPortfolio : mahdi-design.com")

c1 = {
    "numero": 1,
    "entreprise": "OMEDEC (Outillage Mécanique Découpage)",
    "site": "omedec.com",
    "dirigeant": "Xavier PINGRET (Président de SAS, chaîne QUARFLOC)",
    "email": "contact@omedec.com",
    "constat": "Site Oxatis (générateur e-commerce), aucune balise viewport dans le code (vérifié en direct) : rendu bureau dézoomé sur mobile, illisible. SIREN 311666077 vérifié en mentions légales, email contact@omedec.com publié sur toutes les pages. Effectif 20-49 (API).",
    "email_redige": {
        "subject": "Votre site est illisible sur mobile",
        "body": ("Bonjour M. Pingret,\n\n"
                 "Je suis Mahdi, brand designer spécialisé dans les entreprises industrielles. En préparant un panorama des sous-traitants en découpe de précision du Haut-Doubs, je suis tombé sur omedec.com, et un point m'a immédiatement frappé.\n\n"
                 "**Votre site ne contient aucune balise viewport : sur un téléphone, la page s'affiche en pleine largeur d'écran d'ordinateur, dézoomée, avec des textes minuscules impossibles à lire sans agrandir à la main.** Le site tourne par ailleurs sur le générateur Oxatis, un outil conçu pour les boutiques en ligne, pas pour valoriser un savoir-faire de découpe et d'emboutissage de haute précision.\n\n"
                 "Concrètement, un donneur d'ordre qui vérifie un sous-traitant depuis son mobile, là où se font les premières vérifications, se retrouve face à une page illisible et peut passer à un concurrent sans même lire votre offre de rotors, de stators et d'électro-aimants.\n\n"
                 + OFFRE),
    },
    "statut": "confirme",
}

c2 = {
    "numero": 2,
    "entreprise": "SMG Tolerie (SMG)",
    "site": "smg-decoupage-tolerie.com",
    "dirigeant": "Laurent CONFRERE (Président Directeur Général de SMG Confrère, holding du groupe)",
    "email": "louis.sitkiewiez@smgconfrere.com",
    "constat": "Aucune balise viewport sur l'ensemble du site (vérifié en direct, curl) : pas de version mobile, mise en page déformée sur téléphone. Thème WordPress Divi en configuration standard. Mentions légales du site : SMG Confrère, PDG Laurent Confrère, emails @smgconfrere.com publiés. Effectif 20-49 (API).",
    "email_redige": {
        "subject": "Votre site SMG n'est pas adapté au mobile",
        "body": ("Bonjour M. Confrère,\n\n"
                 "Je suis Mahdi, brand designer spécialisé dans les entreprises industrielles. En préparant un tour des sous-traitants en tôlerie, découpe et emboutissage de l'Oise et de Picardie, je suis tombé sur smg-decoupage-tolerie.com, et j'ai constaté un point simple à vérifier en quelques secondes.\n\n"
                 "**Votre site ne contient aucune balise viewport : la version mobile n'existe pas, et sur un téléphone la page s'affiche déformée, avec une mise en page qui déborde de l'écran.** Le site tourne aussi sur le thème WordPress Divi dans sa configuration standard, sans personnalisation visible de l'identité de votre atelier de Saint-Paul.\n\n"
                 "Concrètement, les acheteurs industriels qui comparent des sous-traitants depuis leur mobile, ce qui est devenu le réflexe avant un premier rendez-vous, verront une page qui ne tient pas dans l'écran, un détail qui joue contre votre savoir-faire avant même le premier échange.\n\n"
                 + OFFRE),
    },
    "statut": "confirme",
}

c3 = {
    "numero": 3,
    "entreprise": "Baxter Injection",
    "site": "baxter-injection.com",
    "dirigeant": "Patrick GINOUVIER (Président de Baxter Injection, via HOLDING PG)",
    "email": "info@baxter-injection.com",
    "constat": "Version française : copyright 2021 et dernière actualité du 6 septembre 2020 (vérifiés en direct) ; libellés en portugais non traduits (Setores de Atividade, Ver todas as notícias, Política de Proteção de Dados). Email info@baxter-injection.com publié sur la page contact. Effectif 20-49 (API).",
    "email_redige": {
        "subject": "Votre site affiche des textes en portugais",
        "body": ("Bonjour M. Ginouvier,\n\n"
                 "Je suis Mahdi, brand designer spécialisé dans les entreprises industrielles. En préparant un panorama des plasturgistes d'Auvergne-Rhône-Alpes, je suis passé sur la version française de baxter-injection.com, et plusieurs détails ont attiré mon attention.\n\n"
                 "**La dernière actualité publiée sur votre site date du 6 septembre 2020 et le copyright affiche toujours 2021 : votre vitrine annonce elle-même cinq ans d'inactivité.** La version française contient par ailleurs des libellés en portugais non traduits (Setores de Atividade, Ver todas as notícias, Política de Proteção de Dados), ce qui donne l'impression d'un site laissé en l'état.\n\n"
                 "Concrètement, un donneur d'ordre qui découvre votre activité d'injection de pièces techniques en Isère se demande si l'entreprise a encore investi dans son image, alors que votre portfolio client et votre parc machine montrent le contraire.\n\n"
                 + OFFRE),
    },
    "statut": "confirme",
}

c4 = {
    "numero": 4,
    "entreprise": "Outillage Progress",
    "site": "outillageprogress.com",
    "dirigeant": "Arnault BREDIF (Gérant, via AMBOISIENNE INVESTISSEMENT)",
    "email": "a.bredif@outillageprogress.com",
    "constat": "La page d'accueil propose en téléchargement la plaquette 2016 (Plaquette2016-OUTILLAGE-PROGRESS.pdf, lien vérifié en direct) ; site catalogue PrestaShop avec huit adresses de contact, sans page vitrine du savoir-faire. SIREN 338896426 vérifié en mentions légales. Effectif 20-49 (API).",
    "email_redige": {
        "subject": "Votre plaquette en ligne date de 2016",
        "body": ("Bonjour M. Bredif,\n\n"
                 "Je suis Mahdi, brand designer spécialisé dans les entreprises industrielles. En préparant un tour des fondeurs sous pression de Touraine, je suis tombé sur outillageprogress.com, et un détail m'a marqué.\n\n"
                 "**La page d'accueil de votre site propose encore en téléchargement votre plaquette de 2016 : dix ans après, c'est le document le plus récent présenté à vos visiteurs.** Le site fonctionne par ailleurs comme un catalogue de boutique (PrestaShop) avec huit adresses de contact, sans aucune page qui raconte votre savoir-faire de fondeur zamak, vos moyens techniques ou vos certifications.\n\n"
                 "Concrètement, un prospect qui découvre votre fonderie via une plaquette de 2016 se demande légitimement si l'atelier de Nazelles-Négron a évolué depuis, alors que votre gamme de loqueteaux et de pièces techniques tourne visiblement à plein régime.\n\n"
                 + OFFRE),
    },
    "statut": "confirme",
}

candidats = [c1, c2, c3, c4]
path = "lot16_candidats.json"
with open(path, "w", encoding="utf-8") as f:
    json.dump(candidats, f, ensure_ascii=False, indent=1)

# Validation machine
raw = open(path, encoding="utf-8").read()
assert "\u2014" not in raw, "tiret long U+2014 present"
assert "\u2013" not in raw, "tiret U+2013 present"
assert "\u2019" not in raw, "apostrophe typographique U+2019 presente"
assert len(candidats) == 4
for c in candidats:
    assert set(["numero", "entreprise", "site", "dirigeant", "email", "constat", "email_redige", "statut"]) <= set(c.keys())
    assert c["email_redige"]["body"].endswith("Portfolio : mahdi-design.com")
    assert "Bonjour M." in c["email_redige"]["body"]
    assert "Je suis Mahdi, brand designer spécialisé dans les entreprises industrielles." in c["email_redige"]["body"]
    assert "Concrètement, " in c["email_redige"]["body"]
    assert "gratuitement et sans engagement" in c["email_redige"]["body"]
    assert "é" in c["email_redige"]["body"] or "è" in c["email_redige"]["body"] or "à" in c["email_redige"]["body"]
print("OK : 4 candidats ecrits, validation machine passee.")
