"""Genere les fichiers GO2 manquants (HTML + objet) pour les envois nommes verrouilles.
Reversible : cree seulement les livrables, n'envoie rien.
"""
import html as html_mod
import os

LIV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "livrable")

WRAP = ("<div><p style='margin:10px 0;font-family:Arial,sans-serif;font-size:14px;"
        "color:#222'>{}</p></div>")


def txt_vers_html(txt):
    paras = [p.strip() for p in txt.split("\n\n") if p.strip()]
    out = []
    for p in paras:
        lines = [l.strip() for l in p.split("\n")]
        if all(lines) and all(l.startswith(("-", "1.", "2.", "3.")) for l in lines):
            body = "".join("<li>{}</li>".format(html_mod.escape(l.lstrip("- "))) for l in lines)
            out.append("<ul style='margin:10px 0;padding-left:20px;font-family:Arial,sans-serif;"
                       "font-size:14px;color:#222'>{}</ul>".format(body))
        else:
            esc = html_mod.escape(" ".join(lines)).replace("\r", "")
            out.append(WRAP.format(esc))
    return "".join(out)


def objet_depuis_txt(txt):
    first = txt.splitlines()[0].strip() if txt else ""
    if first.lower().startswith("objet :"):
        return first[7:].strip()
    raise SystemExit("pas d'objet dans " + path)


def filtre(txt):
    # Regles maison : U+2019 interdit, tiret long interdit, Portfolio en fin.
    txt = txt.replace("\u2019", "'").replace("\u2014", "-").replace("\u2013", "-")
    return txt


def main():
    jobs = [
        ("relance_closing_SIMI.txt", "go2_simi_relance"),
        ("go2_fpsa_relance3.txt", "go2_fpsa_relance3"),
    ]
    for src, slug in jobs:
        src_path = os.path.join(LIV, src)
        if not os.path.exists(src_path):
            print("MANQUE:", src)
            continue
        txt = filtre(open(src_path, encoding="utf-8").read())
        objet = objet_depuis_txt(open(src_path, encoding="utf-8").read())
        html = txt_vers_html(txt)
        with open(os.path.join(LIV, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(html)
        with open(os.path.join(LIV, slug + ".objet"), "w", encoding="utf-8") as f:
            f.write(objet)
        print("OK:", slug, "| objet:", objet[:60], "| html:", len(html), "octets")


if __name__ == "__main__":
    main()
