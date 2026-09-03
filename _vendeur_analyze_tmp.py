import re, json, os
os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")

def analyze(fname, label):
    h = open(fname, encoding='utf-8', errors='ignore').read()
    out = {"label": label, "bytes": len(h)}
    t = re.search(r"<title[^>]*>(.*?)</title>", h, re.S|re.I)
    out["title"] = re.sub(r"\s+", " ", t.group(1)).strip()[:120] if t else None
    md = re.search(r'name="description"\s+content="([^"]*)"', h, re.I)
    out["meta_desc"] = (md.group(1)[:160] if md else None)
    gens = list(set(re.findall(r'content="WordPress\s+([\d.]+)"', h, re.I)))
    out["wp_version"] = gens
    out["is_wordpress"] = ("wp-content" in h)
    themes = sorted(set(re.findall(r'wp-content/themes/([a-zA-Z0-9_\-]+)', h)))
    out["themes"] = themes
    fonts = sorted(set(re.findall(r'font-family\s*:\s*([A-Za-z0-9 ,\-\\"\']+)', h)))
    fams = set()
    for f in fonts:
        for part in re.split(r",(?![^(]*\))", f):
            p = part.strip().strip('"\';').split("(")[0].strip()
            if p and p.lower() not in ("sans-serif","serif","inherit","initial","cursive","fantasy","monospace","system-ui"):
                fams.add(p)
    out["distinct_font_families"] = sorted(fams)
    out["n_fonts"] = len(fams)
    out["viewport"] = ('name="viewport"' in h)
    out["favicon"] = bool(re.search(r'rel="(?:shortcut )?icon"', h, re.I))
    out["https_links_http"] = len(re.findall(r'"http://', h))
    out["generator_other"] = list(set(re.findall(r'<meta name="generator" content="([^"]+)"', h)))[:5]
    out["locomotive"] = ("locomotive" in h.lower())
    out["elementor"] = ("elementor" in h.lower())
    out["divi"] = ("Divi" in h)
    out["wix"] = ("wixstatic" in h.lower() or "wix.com" in h.lower())
    out["shopify"] = ("cdn.shopify" in h.lower())
    out["tilda"] = ("tilda" in h.lower())
    out["joomla"] = ("/media/system/" in h.lower() or "Joomla" in h)
    out["last_mod_hint"] = list(set(re.findall(r'(?:copyright|©|&copy;)\s*(?:&copy;)?\s*(?:©)?\s*(\d{4})', h, re.I)))[:5]
    return out

print(json.dumps(analyze("_vendeur_neyrial_tmp.html", "slicom->neyrial"), ensure_ascii=False, indent=1))
