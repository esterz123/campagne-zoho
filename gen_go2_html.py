# -*- coding: utf-8 -*-
"""Genere les 2 corps HTML des mails GO nominatifs (SIMI + ITPLAST).
Sortie: livrable/go2_simi.html + livrable/go2_itplast.html
Idempotent, aucune envoi, aucun reseau. U+2019 -> apostrophe droite."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
LIV = os.path.join(BASE, "livrable")


def clean(s):
    return (s.replace("\u2019", "'").replace("\u2018", "'")
             .replace("\u201c", '"').replace("\u201d", '"')
             .replace("\u2014", "-").replace("\u2013", "-"))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para(s):
    return ("<p style='margin:10px 0;font-family:Arial,sans-serif;"
            "font-size:14px;color:#222'>%s</p>" % esc(clean(s)))


# ---- SIMI: mail de livraison + diagnostic complet inline ----
mail1 = open(os.path.join(LIV, "mail_livraison_SIMI.txt"), encoding="utf-8").read()
objet1 = [l for l in mail1.splitlines() if l.startswith("Objet")][0].split(":", 1)[1].strip()
objet1 = clean(objet1).replace("(piece jointe)", "").replace("(pièce jointe)", "").replace("(piece jointe)", "").strip()
if not objet1.endswith("."):
    objet1 += " en ligne"
corps1 = mail1.split("\n", 1)[1].strip()
corps1 = corps1.replace("(piece jointe)", "").replace("(pièce jointe)", "")
corps1 = corps1.replace("dans le document joint", "directement dans ce mail, ci-dessous")
corps1 = corps1.replace("piece jointe", "ci-dessous").replace("pièce jointe", "ci-dessous")

from docx import Document
d = Document(os.path.join(LIV, "diagnostic_1_SIMI.docx"))
paras = [p.text.strip() for p in d.paragraphs if p.text.strip()]

body1 = "<div>" + "".join(para(l) for l in corps1.splitlines() if l.strip())
body1 += "<hr>" + para("DIAGNOSTIC EN LIGNE DE SIMI.FR (31/08/2026)")
body1 += "".join(para(p) for p in paras if not p.strip().startswith("Diagnostic"))
body1 += "</div>"
open(os.path.join(LIV, "go2_simi.html"), "w", encoding="utf-8").write(body1)
open(os.path.join(LIV, "go2_simi.objet"), "w", encoding="utf-8").write(clean(objet1))

# ---- ITPLAST: relance 3 breakup ----
b2 = open(os.path.join(LIV, "relance3_ITPLAST_pour_oui.txt"), encoding="utf-8").read()
objet2 = [l for l in b2.splitlines() if l.strip().startswith("OBJET")][0].split(":", 1)[1].strip().strip("=").strip()
start = b2.index("Bonjour")
rest = b2[start:]
end = rest.index("====") if "====" in rest else len(rest)
corps2 = rest[:end]
body2 = "<div>" + "".join(para(l) for l in corps2.splitlines() if l.strip()) + "</div>"
open(os.path.join(LIV, "go2_itplast.html"), "w", encoding="utf-8").write(body2)
open(os.path.join(LIV, "go2_itplast.objet"), "w", encoding="utf-8").write(clean(objet2))

# ---- controles ----
for name, obj, body, to in (("SIMI", objet1, body1, "adv.simi@id-casting.com"),
                            ("ITPLAST", objet2, body2, "andre.muller@itplast.com")):
    assert "\u2019" not in body and "\u2019" not in obj, name + " U+2019 restant"
    assert "\u2014" not in body, name + " tiret cadratin restant"
    assert "{" not in body or "{{" in body, name + " placeholder ? " + str([w for w in body.split() if w.startswith("{")][:3])
    print("%s: objet='%s' corps=%d octets cible=%s" % (name, clean(obj)[:60], len(body.encode("utf-8")), to))
print("OK 4 fichiers ecrits dans livrable/")
