#!/usr/bin/env python3
"""fitness nation | Studio Walk — der Katalog als begehbarer Studio-Rundgang.

Konzept (komplett eigenständig): Man LÄUFT horizontal durch die Zonen eines
Studios (Eingang → Check-in → Fläche → Messraum → Lounge → Corporate).
Jede Zone ist eine Bühne: Wand-Typo, Produkte stehen auf dem Boden (Rotations-
Clips drehen sich, wenn die Zone aktiv ist), an jedem Produkt hängt ein
PREISSCHILD — Klick öffnet das volle Datenblatt als Schublade.

  python3 build/build.py   → site/de|en(+/smart)
"""
import json, html, os, time
try:
    from PIL import Image as _PIL
except Exception:
    _PIL = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = "/home/claude/Claude/_WISSENSDATENBANK"
DOMAIN = "https://fn-studio-walk.vercel.app"
BUILD_V = str(int(time.time()))

def esc(t): return html.escape(str(t), quote=True)

_dims = {}
def dims(rel):
    if not rel or _PIL is None: return ""
    if rel in _dims: return _dims[rel]
    try:
        w, h = _PIL.open(os.path.join(ROOT, "site", rel.lstrip("/"))).size
        r = f' width="{w}" height="{h}"'
    except Exception:
        r = ""
    _dims[rel] = r
    return r

# ---------------------------------------------------------------- Preise (Brain, live)
def _load_pricing():
    pmap = json.load(open(f"{ROOT}/content/PRICING_MAP.json"))
    hw = {p.get("article_number"): p for p in json.load(open(f"{KB}/FN_HARDWARE_MASTERDATA.json"))["products"] if p.get("article_number")}
    md = json.load(open(f"{KB}/FN_MASTERDATA.json"))
    sw = {a["item_number"]: a for a in md["articles"]}
    return pmap, hw, sw, md.get("music_licenses", [])
PRICING = _load_pricing()

def _eur(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

def price_rows(cat_name, sid, lang):
    pmap, hw, sw, music = PRICING
    mon = "/ Monat" if lang == "de" else "/ month"
    rows, notes = [], []
    for ref in pmap.get(cat_name, {}).get(sid) or []:
        if ref == "music":
            for m in music:
                rows.append(("fitness nation | Music — " + m["position"], "FN-SP-5100", f'{esc(m["net_price_de"])} <small>{mon}</small>'))
            continue
        kind, num = ref.split(":", 1)
        if kind == "sw":
            a = sw.get(num)
            if not a: continue
            price = a["net_price_de"]
            if "brutto" in price:
                p0 = price.split(" brutto")[0].strip()
                ex = "brutto / aktiver Nutzer" if lang == "de" else "gross / active user"
                rows.append((a["name"], num, f'{esc(p0)} <small>{ex}</small>'))
            else:
                unit = mon if a.get("billing_cycle") == "monatlich" else esc(a.get("billing_cycle", ""))
                rows.append((a["name"], num, f'{esc(price)} <small>{unit}</small>'))
        else:
            pr = hw.get(num)
            if not pr: continue
            amt = ((pr.get("pricing") or {}).get("rrp_eu_net") or {}).get("amount")
            if amt is None:
                rows.append((pr["display_name"], num, "auf Anfrage" if lang == "de" else "on request"))
            else:
                rows.append((pr["display_name"], num, f'{_eur(amt)} <small>{"UVP" if lang=="de" else "RRP"}</small>'))
            sk = (pr.get("pricing") or {}).get("subscription_kauf")
            if sk and sid == "bodycheck":
                notes.append(("Auch als Subscription-Kauf: {} Anzahlung + {} × {} / Monat."
                              if lang == "de" else
                              "Also available as subscription purchase: {} down payment + {} × {} / month.")
                             .format(_eur(sk["anzahlung_eur"]), sk["anzahl_raten"], _eur(sk["monatliche_rate_eur"])))
    return rows, notes

def tag_price(cat_name, sid, lang):
    rows, _ = price_rows(cat_name, sid, lang)
    if not rows: return None
    import re
    return re.sub(r"\s*<small>.*?</small>", "", rows[0][2])

def tag_unit(cat_name, sid, lang):
    rows, _ = price_rows(cat_name, sid, lang)
    if not rows: return ""
    import re
    m = re.search(r"<small>(.*?)</small>", rows[0][2])
    return m.group(1).strip() if m else ""

# ---------------------------------------------------------------- Zonen-Karte
# Jede Zone: (id, wandwort {de,en}, produkte in Szenen-Reihenfolge, primärer Clip)
ZONES = {
    "gesamt": [
        ("eingang",  {"de": "Eingang",  "en": "Entrance"}, ["locks-gates-access"], "gates"),
        ("checkin",  {"de": "Check-in", "en": "Check-in"}, ["terminal", "membership", "manager"], "kiosk"),
        ("flaeche",  {"de": "Fläche",   "en": "The Floor"}, ["tv", "sound-music", "app", "coach"], "tvstick"),
        ("messraum", {"de": "Messraum", "en": "Body Lab"}, ["bodycheck", "trainer", "dashboard"], "bodycheck"),
        ("lounge",   {"de": "Lounge",   "en": "Lounge"}, ["vending-nutrition", "shop", "marketing"], "vending"),
        ("corporate",{"de": "Corporate","en": "Corporate"}, ["fairtrain"], None),
    ],
    "smart": [
        ("eingang",  {"de": "Eingang",  "en": "Entrance"}, ["gates-access", "locks"], "gates"),
        ("checkin",  {"de": "Check-in", "en": "Check-in"}, ["kiosk"], "kiosk"),
        ("flaeche",  {"de": "Fläche",   "en": "The Floor"}, ["screens", "training-ai", "coach"], None),
        ("messraum", {"de": "Messraum", "en": "Body Lab"}, ["bodycheck", "trainer"], "bodycheck"),
        ("lounge",   {"de": "Lounge",   "en": "Lounge"}, ["vending", "nutrition-ai", "shop"], "vending"),
    ],
}
CLIP_FOR = {
    "gesamt": {"locks-gates-access": "gates", "terminal": "kiosk", "tv": "tvstick",
               "bodycheck": "bodycheck", "vending-nutrition": "vending"},
    "smart": {"gates-access": "gates", "kiosk": "kiosk", "bodycheck": "bodycheck", "vending": "vending"},
}
CUTOUT = {
    "gesamt": {"locks-gates-access": "gates.webp", "terminal": "kiosk.webp", "tv": "screens.webp",
               "bodycheck": "bodycheck_1200.png", "vending-nutrition": "vending.webp",
               "sound-music": "tvstick.webp"},
    "smart": {"gates-access": "gates.webp", "locks": "locks.webp", "kiosk": "kiosk.webp",
              "screens": "screens.webp", "bodycheck": "bodycheck_1200.png", "vending": "vending.webp"},
}
PHONE = {
    "gesamt": {"membership": "app_profile.webp", "manager": "app_chat.webp", "app": "app_home.webp",
               "coach": "app_coach.webp", "trainer": "app_health.webp", "dashboard": "app_score.webp",
               "shop": None, "marketing": None, "fairtrain": None},
    "smart": {"training-ai": "app_chat.webp", "coach": "app_coach.webp", "nutrition-ai": "app_nutrition.webp",
              "trainer": "app_health.webp", "shop": None},
}

def prodname(k):
    if "|" in (k or ""):
        a, b = k.split("|", 1)
        return f'<span translate="no">{esc(a.strip())} <span class="pipe">|</span> <b>{esc(b.strip())}</b></span>'
    return esc(k or "")

def shortname(k):
    return k.split("|")[-1].strip() if "|" in (k or "") else (k or "")

# ---------------------------------------------------------------- Bühnen-Elemente
def price_tag(cat_name, s, lang, cls=""):
    """Hängendes Preisschild — Klick öffnet das Datenblatt."""
    sid = s["id"]
    p = tag_price(cat_name, sid, lang)
    unit = tag_unit(cat_name, sid, lang)
    name = shortname(s.get("kicker") or sid)
    if p:
        val = f'<b>{p}</b><small>{esc(unit)}</small>' if unit else f'<b>{p}</b>'
    else:
        val = f'<b>{"auf Anfrage" if lang == "de" else "on request"}</b>'
    aria = ("Datenblatt öffnen: " if lang == "de" else "Open datasheet: ") + name
    return (f'<button class="tag {cls}" data-sheet="{sid}" aria-label="{esc(aria)}">'
            f'<i class="hole"></i><span class="tname" translate="no">{esc(name)}</span>{val}'
            f'<span class="topen">{"Datenblatt" if lang == "de" else "Datasheet"} →</span></button>')

def stage_item(cat_name, s, lang, primary=False):
    """Ein Produkt auf dem Studioboden: Clip / Freisteller / Phone + Preisschild."""
    sid = s["id"]
    name = s.get("kicker") or sid
    clip = CLIP_FOR.get(cat_name, {}).get(sid)
    cut = CUTOUT.get(cat_name, {}).get(sid)
    ph = PHONE.get(cat_name, {}).get(sid)
    cls = "item primary" if primary else "item"
    if clip: kind = "k-video"
    elif cut: kind = "k-img"
    elif ph: kind = "k-phone"
    else: kind = "k-board"
    cls += " " + kind
    if clip:
        vis = (f'<span class="halo"></span><video muted loop playsinline preload="none" '
               f'poster="/assets/video/{clip}_poster.webp" aria-label="{esc(name)}">'
               f'<source src="/assets/video/{clip}.mp4" type="video/mp4"></video>'
               f'<span class="spin" aria-hidden="true">360°</span>')
    elif cut:
        src = f"/assets/img/{cut}"
        vis = f'<span class="halo"></span><img src="{src}" alt="{esc(name)}"{dims(src)} loading="lazy"><span class="floor"></span>'
    elif ph:
        src = f"/assets/img/{ph}"
        vis = (f'<span class="halo soft"></span><div class="phone"><div class="scr">'
               f'<img src="{src}" alt="{esc(name)}"{dims(src)} loading="lazy"></div></div>')
    else:
        vis = f'<span class="halo soft"></span><div class="board" translate="no"><span class="pipe">|</span> {esc(shortname(name))}</div>'
    return f'<div class="{cls}" data-prod="{sid}">{vis}{price_tag(cat_name, s, lang)}</div>'

def zone_html(cat_name, z, secs_by_id, lang, zi, ztotal):
    zid, word, pids, _ = z
    prods = [secs_by_id[p] for p in pids if p in secs_by_id]
    if not prods: return ""
    lead = ""
    p0 = prods[0]
    if p0.get("sub"):
        lead = str(p0["sub"])
    elif p0.get("body"):
        lead = str(p0["body"][0]).split(". ")[0] + "."
    items = "".join(stage_item(cat_name, s, lang, primary=(i == 0)) for i, s in enumerate(prods))
    return f'''<article class="zone" id="z-{zid}" data-zone="{zid}" style="--zi:{zi}">
<span class="wall" aria-hidden="true">{esc(word[lang])}</span>
<header class="zhead"><span class="zno">{zi+1:02d}/{ztotal:02d}</span><h2>{esc(word[lang])}</h2><p>{esc(lead)}</p></header>
<div class="scene">{items}</div>
</article>'''

# ---------------------------------------------------------------- Datenblatt-Schubladen
def sheet_html(cat_name, s, lang):
    sid = s["id"]
    name = s.get("kicker") or sid
    body = "".join(f"<p>{esc(p)}</p>" for p in s.get("body") or [])
    stmt = f'<p class="statement">{esc(s["statement"])}</p>' if s.get("statement") else ""
    feats, ai = "", ""
    for b in s.get("blocks") or []:
        if b.get("kind") == "list" and not feats:
            chips = "".join(f"<span>{esc(i)}</span>" for i in b.get("items", []))
            lab = b.get("title") or ("Funktionen" if lang == "de" else "Features")
            feats = f'<h4>{esc(lab)}</h4><div class="chips">{chips}</div>'
        if b.get("kind") == "ai_badge" and not ai:
            chips = "".join(f"<span>{esc(i)}</span>" for i in b.get("items", []))
            ai = f'<h4>AI-powered</h4><div class="chips ai">{chips}</div>'
    rows, notes = price_rows(cat_name, sid, lang)
    price = ""
    if rows:
        tr = "".join(f'<tr><td translate="no">{esc(n)}</td><td class="art">{esc(a)}</td><td class="pr">{p}</td></tr>' for n, a, p in rows)
        nt = "".join(f'<p class="note">{esc(n)}</p>' for n in notes)
        legal = "Alle Preise zzgl. MwSt.; Hardware zzgl. Lieferung." if lang == "de" else "All prices plus VAT; hardware plus delivery."
        price = (f'<h4>{"Preise (netto)" if lang == "de" else "Pricing (net)"}</h4>'
                 f'<table><tbody>{tr}</tbody></table>{nt}<p class="note">{legal}</p>')
    return (f'<template id="sheet-{sid}"><div class="sh-head"><h3 translate="no">{prodname(name)}</h3></div>'
            f'<h2>{esc(s.get("headline",""))}</h2>{body}{stmt}{feats}{ai}{price}</template>')

# ---------------------------------------------------------------- Preisliste (Abschluss)
def pricelist_html(cat_name, prods, lang):
    rows = ""
    for s in prods:
        pr, _ = price_rows(cat_name, s["id"], lang)
        for n, a, p in pr:
            rows += f'<tr><td translate="no">{esc(n)}</td><td class="art">{esc(a)}</td><td class="pr">{p}</td></tr>'
        if not pr:
            rows += (f'<tr><td translate="no">{esc(s.get("kicker") or s["id"])}</td><td class="art">—</td>'
                     f'<td class="pr">{"auf Anfrage" if lang == "de" else "on request"}</td></tr>')
    t = {"de": ("Die Preisliste", "Alles aus dem Rundgang, auf einen Blick.", "Alle Preise zzgl. MwSt.; Hardware zzgl. Lieferung."),
         "en": ("The price list", "Everything from the walk, at a glance.", "All prices plus VAT; hardware plus delivery.")}[lang]
    return (f'<section class="pricelist" id="preisliste"><div class="plwrap">'
            f'<h2>{t[0]}</h2><p class="pllead">{t[1]}</p>'
            f'<table><tbody>{rows}</tbody></table><p class="note">{t[2]}</p></div></section>')

# ---------------------------------------------------------------- Seite
def page(cat, lang, cat_name, paths):
    meta = cat["meta"]
    secs_by_id = {s["id"]: s for s in cat["sections"]}
    prods = [s for s in cat["sections"] if s.get("type") == "product"]
    zones = ZONES[cat_name]
    ztotal = len(zones)
    zones_html = "".join(zone_html(cat_name, z, secs_by_id, lang, i, ztotal) for i, z in enumerate(zones))
    sheets = "".join(sheet_html(cat_name, s, lang) for s in prods)
    cover = next((s for s in cat["sections"] if s.get("type") == "cover"), {})
    closing = next((s for s in cat["sections"] if s.get("type") == "closing"), {})
    c = meta.get("contact", {})
    contact_lines = "<br>".join(esc(x) for x in (c.get("company"), c.get("street"), c.get("city"), c.get("hotline"), c.get("email")) if x)
    ui = {"de": {"start": "Rundgang starten", "walkhint": "Scrollen = durchs Studio laufen", "present": "Präsentation",
                 "frame": "Der Katalog als Rundgang durch dein Studio.", "tags": "Preisschild antippen = Datenblatt",
                 "pl": "Preisliste", "contact": "Kontakt", "close": "Schließen"},
          "en": {"start": "Start the walk", "walkhint": "Scroll to walk through the studio", "present": "Present",
                 "frame": "The catalog as a walk through your studio.", "tags": "Tap a price tag for the datasheet",
                 "pl": "Price list", "contact": "Contact", "close": "Close"}}[lang]
    other_lang = "en" if lang == "de" else "de"
    cat_label = {"gesamt": "smart", "smart": ("Gesamtkatalog" if lang == "de" else "Full catalog")}[cat_name]
    dots = "".join(f'<button data-go="{i}" aria-label="{esc(z[1][lang])}"><i></i><span>{esc(z[1][lang])}</span></button>'
                   for i, z in enumerate(zones))
    title = f'{meta.get("brand","fitness nation")} — Studio Walk' + ("" if cat_name == "gesamt" else " · smart")
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(meta.get('subline',''))}">
<meta name="robots" content="noindex">
<meta name="theme-color" content="#0f1518">
<link rel="alternate" hreflang="{lang}" href="{DOMAIN}{paths[lang]}">
<link rel="alternate" hreflang="{other_lang}" href="{DOMAIN}{paths[other_lang]}">
<link rel="alternate" hreflang="x-default" href="{DOMAIN}{paths['de']}">
<link rel="preload" as="font" type="font/woff2" href="/assets/fonts/outfit.woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/walk.css?v={BUILD_V}">
</head>
<body>
<header class="topbar">
  <a class="brand" href="#top" translate="no">{prodname(meta.get("brand","fitness nation"))}</a>
  <nav class="topnav">
    <a class="tbtn" href="#preisliste">{ui["pl"]}</a>
    <a class="tbtn" href="{paths["othercat"]}" translate="no">{esc(cat_label)}</a>
    <a class="tbtn" href="{paths[other_lang]}">{other_lang.upper()}</a>
    <button class="tbtn solid" id="present">{ui["present"]} ⌁ F</button>
  </nav>
</header>

<section class="cover" id="top">
  <p class="frame">{ui["frame"]}</p>
  <h1>{esc(cover.get("headline", meta.get("brand","")))}</h1>
  <p class="sub">{esc(cover.get("sub",""))}</p>
  <a class="startbtn" href="#walk"><span>{ui["start"]}</span><i>→</i></a>
  <p class="hintline">{ui["walkhint"]} · {ui["tags"]}</p>
</section>

<section class="walk" id="walk" style="--zones:{ztotal}">
  <div class="viewport">
    <div class="track">{zones_html}</div>
    <div class="floorline" aria-hidden="true"></div>
  </div>
</section>

{pricelist_html(cat_name, prods, lang)}

<section class="outro">
  <h2>{esc(closing.get("headline",""))}</h2>
  <div class="outgrid">
    <p class="statement">{esc(closing.get("statement",""))}</p>
    <div><h4>{ui["contact"]}</h4><p class="ctxt">{contact_lines}</p></div>
  </div>
  <div class="bigword" translate="no">fitness nation<span class="pipe">|</span></div>
</section>

<nav class="map" aria-label="Zonen">{dots}</nav>

<div class="drawer" id="drawer" aria-hidden="true">
  <div class="d-back" data-close></div>
  <aside class="d-panel" role="dialog" aria-modal="true" aria-label="Datenblatt">
    <button class="d-close" data-close aria-label="{ui["close"]}">✕</button>
    <div class="d-body" id="d-body"></div>
  </aside>
</div>
{sheets}
<div class="blackout"></div>
<script src="/assets/js/walk.js?v={BUILD_V}" defer></script>
</body>
</html>'''

def build():
    for cat_name in ("gesamt", "smart"):
        for lang in ("de", "en"):
            cat = json.load(open(f"{ROOT}/content/{cat_name}/{lang}.json"))
            base = {"de": "/de", "en": "/en"} if cat_name == "gesamt" else {"de": "/de/smart", "en": "/en/smart"}
            paths = dict(base)
            paths["othercat"] = ("/de/smart" if lang == "de" else "/en/smart") if cat_name == "gesamt" else ("/de" if lang == "de" else "/en")
            out = f"{ROOT}/site{base[lang]}/index.html"
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w").write(page(cat, lang, cat_name, paths))
            print("→", out)

if __name__ == "__main__":
    build()
