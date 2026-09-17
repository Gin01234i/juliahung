#!/usr/bin/env python3
"""Stamp the repetitive pages from the templates and the content records.

This is an AUTHORING tool, not a build step. It writes plain static HTML that
is committed to the repo and deploys with no dependencies; editing any output
file by hand afterwards is entirely fine and nothing here will silently
overwrite it unless you rerun the script. Its only job is to keep header,
footer and template markup byte-identical across ~50 files so a nav change
stays one `sed`.

Usage:  python3 tools/stamp.py
"""
import html, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.jujuhung.com"

sel = json.load(open(f"{ROOT}/content/selection.json", encoding="utf-8"))
imgs = json.load(open(f"{ROOT}/content/images.json", encoding="utf-8"))
FEATURED = sel["works_featured"]
CATS = sel["categories"]


def esc(s):
    return html.escape(s or "", quote=True)


def load_press():
    """content/press.json leads with a comment object; drop it."""
    with open(f"{ROOT}/content/press.json", encoding="utf-8") as f:
        return [r for r in json.load(f) if r.get("slug")]


def load(kind, slug):
    with open(f"{ROOT}/content/{kind}/{slug}.json", encoding="utf-8") as f:
        return json.load(f)


# --- Shared chrome -------------------------------------------------------- #
# Canonical copies live in PARTIALS.md. Change them in one place, rerun, and
# every page moves together.

NAV = [("/artworks/", "Works", "作品"), ("/exhibitions/", "Exhibitions", "展覽"),
       ("/news/", "News", "消息"), ("/blog/", "Press", "媒體"),
       ("/about/", "About", "關於"), ("/contact/", "Contact", "聯絡")]

# Label column of the meta block, and the handful of standing UI words.
UI = {
    "Material": "媒材", "Series": "系列", "Dimensions": "尺寸", "Shown": "展出",
    "Works": "作品", "Exhibitions": "展覽", "News": "消息", "Press": "媒體",
    "Contact": "聯絡", "Works shown": "展出作品", "All press": "所有報導",
    "All exhibitions": "所有展覽", "All news": "所有消息", "More": "詳見",
    "Selected press": "精選報導", "Most recent": "最近展出", "On view": "展出中",
    "Solo": "個展", "Group exhibition": "聯展", "Solo exhibition": "個展",
    "Art fair": "藝術博覽會", "Art Festival": "藝術節", "Collaboration": "合作計畫",
    "Not found": "找不到頁面", "Commission guide": "委託創作說明",
}


def header(active=None, home=False):
    mark = ('<a class="hdr__mark" href="/">Julia Hung'
            + ('<span class="hdr__mark-zh">洪郁雯</span>' if home else "")
            + "</a>")
    cur = ' aria-current="page"'
    items = "\n".join(
        f'    <a href="{href}"{cur if href == active else ""}>'
        f'{bi_span(label, zh)}</a>'
        for href, label, zh in NAV)
    return f"""<header class="hdr">
  {mark}
  <nav class="hdr__nav t-meta" aria-label="Main">
{items}
    <span class="hdr__lang" role="group" aria-label="Language">
      <button type="button" data-set-lang="en" aria-pressed="true">EN</button>
      <span aria-hidden="true">/</span>
      <button type="button" data-set-lang="zh" aria-pressed="false">中文</button>
    </span>
  </nav>
</header>"""


def document(*, title, desc, path, body, og_image=None, jsonld=None,
             noindex=False, active=None, home=False, family="index"):
    canonical = SITE + path
    og = og_image or "/assets/img/works/untamed/2023_untamed_01-1600.jpg"
    head = [
        '<!doctype html>',
        '<html lang="en" data-lang="en">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(desc)}">',
    ]
    if noindex:
        head.append('<meta name="robots" content="noindex,nofollow">')
    head += [
        f'<link rel="canonical" href="{canonical}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Julia Hung">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:image" content="{SITE}{og}">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<link rel="stylesheet" href="/assets/css/site.css">',
    ]
    if jsonld:
        head.append('<script type="application/ld+json">')
        head.append(json.dumps(jsonld, ensure_ascii=False, indent=2))
        head.append("</script>")
    cls = "page" + (f" page--{family}" if family != "index" else "")
    head += ["</head>", "<body>", f'<div class="{cls}">', ""]
    return "\n".join(head + [header(active, home), "", body, "",
                             "</div>",
                             '<script src="/assets/js/lang.js" defer></script>',
                             "</body>", "</html>", ""])


def write(path, content):
    dest = os.path.join(ROOT, path.strip("/"), "index.html") if path != "/" \
        else os.path.join(ROOT, "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    return dest


# --- Bilingual helpers ---------------------------------------------------- #

def bi_span(en, zh):
    if not zh:
        return f'<span lang="en" class="is-fallback">{en}</span>'
    return f'<span lang="en">{en}</span><span lang="zh">{zh}</span>'


def paras(lines, cls="t-body", lang=None, limit=None):
    if not lines:
        return ""
    if limit:
        lines = lines[:limit]
    L = f' lang="{lang}"' if lang else ""
    return "\n".join(f'    <p class="{cls}"{L}>{esc(l)}</p>' for l in lines)


# --- Imagery -------------------------------------------------------------- #

def picture(stem, ratio, alt, caption=None, sizes="100vw", eager=False,
            caption_zh=None):
    """<picture> with a WebP source and a JPEG fallback, fixed ratio, no
    rounding, caption outside the frame."""
    cap = ""
    if caption:
        cap = (f"\n    <figcaption>"
               f"{bi_span(esc(caption), esc(caption_zh))}</figcaption>")
    loading = "eager" if eager else "lazy"
    return f"""  <figure class="fig fig--{ratio}">
    <picture>
      <source type="image/webp" sizes="{sizes}"
              srcset="/assets/img/{stem}-800.webp 800w, /assets/img/{stem}-1600.webp 1600w">
      <img src="/assets/img/{stem}-1600.jpg"
           srcset="/assets/img/{stem}-800.jpg 800w, /assets/img/{stem}-1600.jpg 1600w"
           sizes="{sizes}" alt="{esc(alt)}" loading="{loading}" decoding="async">
    </picture>{cap}
  </figure>"""


CREDIT_RE = re.compile(r"^\s*(撰稿人|文[／/]|text by|by |photo)", re.I)


def first_statement(lines):
    """First real paragraph, skipping a writer credit.

    Chinese curatorial texts in the CMS open with "撰稿人/ ..."; the English
    ones do not. Pairing index 0 against index 0 would set a byline opposite a
    statement.
    """
    for l in lines or []:
        if not CREDIT_RE.match(l):
            return l
    return (lines or [None])[0]


def alt_for(rec, n, kind):
    """Written alt text. Never a filename — the spec is explicit about that."""
    title = rec.get("title") or rec["slug"]
    if kind == "exhibitions":
        venue = (rec.get("venue") or "").split("｜")[0].split("|")[0].strip()
        where = f" at {venue}" if venue else ""
        return f"Installation view {n} of {title}{where}."
    mat = (rec.get("material") or "").lower()
    dims = rec.get("dimensions")
    bits = [b for b in (mat, dims) if b]
    bits = [tidy_dims(b) if b == dims else b for b in bits]
    tail = (", " + ", ".join(bits)) if bits else ""
    return f"{title}{tail}." if n == 1 else f"{title}, view {n}{tail}."


# --- Works ---------------------------------------------------------------- #

def tidy_dims(d):
    """Normalise hand-typed dimensions: "H26 xW22 xD21 cm" -> "H26 × W22 × D21 cm"."""
    if not d:
        return d
    d = re.sub(r"\s*[xX×]\s*", " × ", d)
    d = re.sub(r"([HWDhwd])\s+(\d)", r"\1\2", d)   # "H 26" -> "H26"
    return re.sub(r"\s{2,}", " ", d).strip()


def year_label(y):
    return (y or "").replace("-", "–")


def year_range(rec):
    """Exhibitions carry "2025 - 2026" in dates[0]; works carry a bare year."""
    d = rec.get("dates") or []
    first = d[0] if d else rec.get("year")
    return re.sub(r"\s*-\s*", "–", (first or "").strip())


def work_detail(slug, prev_slug, next_slug):
    rec = load("works", slug)
    pics = imgs["works"].get(slug, [])
    title = rec["title"]
    zh = rec.get("title_zh")

    meta_rows = []
    for label, en, zhv in (
        ("Material", rec.get("material"), rec.get("material_zh")),
        ("Series", rec.get("series"), rec.get("series_zh")),
        ("Dimensions", tidy_dims(rec.get("dimensions")), None),
    ):
        if en:
            meta_rows.append(f"    <dt>{bi_span(label, UI.get(label))}</dt>\n"
                             f"    <dd>{bi_span(esc(en), esc(zhv))}</dd>")
    shown = rec.get("exhibitions") or []
    if shown:
        links = ", ".join(
            f'<a class="lnk" href="{local_href(s["href"])}">{esc(s["text"])}</a>'
            if local_href(s["href"]) else esc(s["text"]) for s in shown)
        meta_rows.append(f'    <dt>{bi_span("Shown", UI["Shown"])}</dt>\n'
                         f"    <dd>{links}</dd>")

    note = ""
    st_en = rec.get("statement") or []
    st_zh = rec.get("statement_zh") or []
    lead_en, lead_zh = first_statement(st_en), first_statement(st_zh)
    if lead_en:
        note = (f'\n  <p class="meta__note">'
                f"{bi_span(esc(lead_en), esc(lead_zh))}</p>")

    # Image stack: one 4/3 primary, then 1/1 pairs.
    # The Chinese gallery holds the same images in the same order with the
    # material translated; index into it for the caption pair.
    zh_caps = {i["media"]: i.get("caption", "")
               for i in (rec.get("images_zh") or [])}

    def cap_pair(p):
        raw = json.load
        en = tidy_dims(p.get("parsed", {}).get("raw")) or None
        zh = tidy_dims(zh_caps.get(p.get("media"), "")) or None
        return en, (zh if zh and zh != en else None)

    stack = []
    if pics:
        p = pics[0]
        en, zh = cap_pair(p)
        stack.append(picture(p["stem"], "4-3", alt_for(rec, 1, "works"), en,
                             sizes="(max-width: 900px) 100vw, 70vw", eager=True,
                             caption_zh=zh))
    rest = pics[1:]
    for i in range(0, len(rest), 2):
        pair = rest[i:i + 2]
        inner = "\n".join(
            picture(p["stem"], "1-1", alt_for(rec, i + j + 2, "works"),
                    cap_pair(p)[0], sizes="(max-width: 600px) 100vw, 35vw",
                    caption_zh=cap_pair(p)[1])
            for j, p in enumerate(pair))
        stack.append(f'  <div class="pair">\n{inner}\n  </div>')

    rest_en = [l for l in st_en if l != lead_en]
    rest_zh = [l for l in st_zh if l != lead_zh]
    body_paras = "\n".join(
        f'    <p class="t-body" lang="en">{esc(l)}</p>' for l in rest_en) \
        + ("\n" if rest_en and rest_zh else "") + "\n".join(
        f'    <p class="t-body" lang="zh">{esc(l)}</p>' for l in rest_zh)

    nav = []
    if prev_slug:
        pr = load("works", prev_slug)
        nav.append(f'  <a class="lnk" href="/artworks/{prev_slug}/">'
                   f'← {esc(pr["title"])}</a>')
    if next_slug:
        nx = load("works", next_slug)
        nav.append(f'  <a class="lnk" href="/artworks/{next_slug}/">'
                   f'{esc(nx["title"])} →</a>')

    body = f"""<article class="s-detail detail">

  <div class="detail__meta stack--tight">
    <h1 class="t-display">{bi_span(esc(title), esc(zh))}</h1>
    <p class="t-label">{esc(year_label(rec.get("year")))}</p>
  <dl class="meta">
{chr(10).join(meta_rows)}
  </dl>{note}
  </div>

  <div class="stack">
{chr(10).join(stack)}
{body_paras}
  </div>

</article>

<nav class="nextprev t-meta" aria-label="More works">
{chr(10).join(nav)}
</nav>"""

    desc = (st_en[0] if st_en else f"{title}, {rec.get('material','')}").strip()
    jsonld = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": title,
        "creator": {"@type": "Person", "name": "Julia Hung",
                    "alternateName": "洪郁雯"},
        "dateCreated": (rec.get("year") or "").rstrip("-"),
        "artMedium": rec.get("material"),
        "url": f"{SITE}/artworks/{slug}/",
    }
    if rec.get("dimensions"):
        jsonld["size"] = rec["dimensions"]
    if pics:
        jsonld["image"] = f"{SITE}/assets/img/{pics[0]['stem']}-1600.jpg"

    return document(
        title=f"{title} — Julia Hung",
        desc=desc[:300],
        path=f"/artworks/{slug}/",
        og_image=f"/assets/img/{pics[0]['stem']}-1600.jpg" if pics else None,
        body=body, jsonld=jsonld, active="/artworks/", family="detail")


def local_href(href):
    """Rewrite an absolute jujuhung.com link to a local path, or drop it."""
    if not href:
        return None
    m = re.match(r"https?://(?:www\.)?jujuhung\.com(/.*)", href)
    p = m.group(1) if m else (href if href.startswith("/") else None)
    if not p:
        return None
    p = re.sub(r"^/zh/", "/", p)
    p = p.replace("/artwork/", "/artworks/").replace("/exhibition/", "/exhibitions/")
    if not p.endswith("/"):
        p += "/"
    # Only link to pages that actually exist after the cut.
    if p.startswith("/artworks/"):
        return p if p.strip("/").split("/")[-1] in FEATURED else None
    if p.startswith("/exhibitions/"):
        slug = p.strip("/").split("/")[-1]
        return p if os.path.exists(f"{ROOT}/content/exhibitions/{slug}.json") else None
    return p


def works_index():
    cards = []
    for slug in FEATURED:
        rec = load("works", slug)
        pics = imgs["works"].get(slug, [])
        if not pics:
            continue
        cat = next((k for k, v in CATS.items() if slug in v), "")
        p = pics[0]
        cards.append(f"""  <a class="card" href="/artworks/{slug}/" data-cat="{cat}">
{picture(p["stem"], "", alt_for(rec, 1, "works"), sizes="(max-width: 600px) 100vw, (max-width: 900px) 46vw, 30vw")}
    <p class="card__title">{bi_span(esc(rec["title"]), esc(rec.get("title_zh")))}</p>
    <p class="card__year">{esc(year_label(rec.get("year")))}</p>
  </a>""")

    CAT_ZH = {"sculpture": "雕塑", "installation": "裝置", "public-art": "公共藝術"}
    filters = "\n".join(
        f'    <button type="button" data-filter="{k}">'
        f'{bi_span(k.replace("-", " ").title(), CAT_ZH.get(k))}</button>'
        for k in CATS)
    body = f"""<section class="s-index stack">
  <h1 class="t-label">{bi_span("Works", UI["Works"])}</h1>
  <div class="filters t-meta" role="group" aria-label="Filter works">
    <button type="button" data-filter="all" aria-pressed="true">{bi_span("All", "全部")}</button>
{filters}
  </div>
</section>

<section class="s-index grid" id="works-grid">
{chr(10).join(cards)}
</section>

<script src="/assets/js/filter.js" defer></script>"""
    return document(
        title="Works — Julia Hung",
        desc="Selected works by Julia Hung 洪郁雯 — sculpture and installation in "
             "enamelled copper wire and reclaimed material, 2017 to present.",
        path="/artworks/", body=body, active="/artworks/")


# --- Exhibitions ---------------------------------------------------------- #

def show_venue(rec):
    return (rec.get("venue") or "").strip()


def show_kind(rec):
    cats = rec.get("categories") or []
    if cats:
        return str(cats[0]).rstrip("s").replace("exhibition", "exhibition")
    return "Solo exhibition" if rec.get("solo") else "Group exhibition"


def exhibitions_index():
    slugs = sorted(
        (os.path.splitext(f)[0] for f in os.listdir(f"{ROOT}/content/exhibitions")
         if f.endswith(".json") and not f.startswith("_")),
        key=lambda s: load("exhibitions", s).get("year") or "", reverse=True)

    rows = []
    for slug in slugs:
        rec = load("exhibitions", slug)
        chip = ('<span class="chip">' + bi_span("Solo", "個展") + '</span>'
                if rec.get("solo") else "")
        rows.append(f"""  <a class="row" href="/exhibitions/{slug}/">
    <span class="row__title t-row">{bi_span(esc(rec["title"]), esc(rec.get("title_zh")))}{chip}</span>
    <span class="row__venue">{bi_span(esc(show_venue(rec)), esc((rec.get("dates_zh") or ["", ""])[-1] if len(rec.get("dates_zh") or []) > 1 else None))}</span>
    <span class="row__year">{esc(year_range(rec))}</span>
  </a>""")

    body = f"""<section class="s-index stack--tight">
  <h1 class="t-label">{bi_span("Exhibitions", UI["Exhibitions"])}</h1>
</section>

<section class="s-index">
  <div class="rows">
{chr(10).join(rows)}
  </div>
</section>

<section class="s-index">
  <p class="t-body"><span lang="en">Earlier exhibitions are listed in the
    <a class="lnk" href="/about/">CV</a>.</span><span lang="zh">更早的展覽收錄於
    <a class="lnk" href="/about/">CV</a>。</span></p>
</section>"""
    return document(
        title="Exhibitions — Julia Hung",
        desc="Solo and selected group exhibitions by Julia Hung 洪郁雯, 2017 to present.",
        path="/exhibitions/", body=body, active="/exhibitions/")


def exhibition_detail(slug):
    rec = load("exhibitions", slug)
    pics = imgs["exhibitions"].get(slug, [])
    dates_en = " · ".join(rec.get("dates") or [])
    dates_zh = " · ".join(rec.get("dates_zh") or [])

    stack = "\n".join(
        picture(p["stem"], "16-10", alt_for(rec, n, "exhibitions"),
                sizes="(max-width: 900px) 100vw, 66vw", eager=(n == 1))
        for n, p in enumerate(pics, 1))

    text_en = rec.get("text") or []
    text_zh = rec.get("text_zh") or []
    intro = ""
    if text_en:
        intro = f'  <p class="t-lead">{bi_span(esc(text_en[0]), esc(text_zh[0]) if text_zh else None)}</p>'
    rest = "\n".join(f'  <p class="t-body" lang="en">{esc(l)}</p>' for l in text_en[1:]) \
        + ("\n" if text_en[1:] and text_zh[1:] else "") \
        + "\n".join(f'  <p class="t-body" lang="zh">{esc(l)}</p>' for l in text_zh[1:])

    work_rows = []
    for w in rec.get("works") or []:
        href = local_href(w["href"])
        if not href:
            continue
        wslug = href.strip("/").split("/")[-1]
        wr = load("works", wslug)
        work_rows.append(f"""    <a class="row" href="{href}">
      <span class="row__title t-row">{bi_span(esc(wr["title"]), esc(wr.get("title_zh")))}</span>
      <span class="row__venue">{esc(wr.get("material") or "")}</span>
      <span class="row__year">{esc(year_label(wr.get("year")))}</span>
    </a>""")
    works_block = ""
    if work_rows:
        works_block = f"""
<section class="s-detail">
  <p class="t-label">{bi_span("Works shown", UI["Works shown"])}</p>
  <div class="rows">
{chr(10).join(work_rows)}
  </div>
</section>"""

    body = f"""<article class="s-detail stack">

  <div class="stack--tight">
    <p class="t-label">{bi_span(esc(show_kind(rec)), UI.get(show_kind(rec)))}</p>
    <h1 class="t-display">{bi_span(esc(rec["title"]), esc(rec.get("title_zh")))}</h1>
    <p class="t-body">{bi_span(esc(show_venue(rec)), esc(dates_zh.split(" · ")[-1] if dates_zh else None))}</p>
    <p class="t-body">{bi_span(esc(dates_en), esc(dates_zh))}</p>
  </div>

{intro}
{rest}

{stack}

</article>{works_block}

<nav class="nextprev t-meta" aria-label="More exhibitions">
  <a class="lnk" href="/exhibitions/">{bi_span("All exhibitions →", UI["All exhibitions"] + " →")}</a>
</nav>"""

    desc = (text_en[0] if text_en else
            f'{rec["title"]} at {show_venue(rec)}, {rec.get("year","")}')
    jsonld = {
        "@context": "https://schema.org",
        "@type": "ExhibitionEvent",
        "name": rec["title"],
        "startDate": (rec.get("year") or ""),
        "location": {"@type": "Place", "name": show_venue(rec)},
        "performer": {"@type": "Person", "name": "Julia Hung"},
        "url": f"{SITE}/exhibitions/{slug}/",
    }
    return document(
        title=f'{rec["title"]} — Julia Hung',
        desc=desc[:300],
        path=f"/exhibitions/{slug}/",
        og_image=f"/assets/img/{pics[0]['stem']}-1600.jpg" if pics else None,
        body=body, jsonld=jsonld, active="/exhibitions/", family="detail")


# --- About / CV ----------------------------------------------------------- #

def about():
    cv = json.load(open(f"{ROOT}/content/cv.json", encoding="utf-8"))
    press = load_press()

    # Portrait: 2/3 left. There is no portrait in the CMS, so the page falls
    # back to the most recent install view until Julia supplies one.
    portrait = imgs["exhibitions"].get("the-interval-between", [])
    fig = picture(portrait[0]["stem"], "2-3",
                  "Julia Hung's work installed at Galerie Pierre, Taichung.",
                  sizes="(max-width: 900px) 100vw, 30vw", eager=True) \
        if portrait else ""

    statement = "\n".join(
        f'    <p class="{"t-lead" if i == 0 else "t-body"}">{esc(pgraph)}</p>'
        for i, pgraph in enumerate(cv["statement"]))

    blocks = []
    for sec in cv["sections"]:
        rows = "\n".join(
            f"      <dt>{esc(year)}</dt>\n      <dd>{entry}</dd>"
            for year, entry in sec["entries"])
        blocks.append(f"""  <section class="s-detail">
    <p class="t-label">{esc(sec["heading"])}</p>
    <dl class="cv">
{rows}
    </dl>
  </section>""")

    pdf = ""
    if cv.get("cv_pdf"):
        pdf = (f'\n<section class="s-detail">\n'
               f'  <a class="lnk" href="{cv["cv_pdf"]}">Download CV (PDF) →</a>\n'
               f'</section>')

    press_rows = "\n".join(f"""    <a class="row" href="/post/{esc(p["slug"])}/">
      <span class="row__title t-row">{esc(p["title"])}</span>
      <span class="row__venue">{esc(p["excerpt"])}</span>
      <span class="row__year">{esc((p["published"] or "")[:4])}</span>
    </a>""" for p in press[:6])

    body = f"""<section class="s-index split">
  <div class="col-4">
{fig}
  </div>
  <div class="col-8 stack">
{statement}
  </div>
</section>

<hr class="rule rule--ink">

<section class="s-index stack--tight">
  <h1 class="t-display">{esc(cv["name"])}</h1>
  <p class="t-body">{bi_span(esc(cv["born"]), esc(cv.get("born_zh")))}</p>
</section>

{chr(10).join(blocks)}{pdf}

<hr class="rule">

<section class="s-index">
  <p class="t-label">{bi_span("Selected press", UI["Selected press"])}</p>
  <div class="rows">
{press_rows}
  </div>
  <p class="t-body mt-2"><a class="lnk" href="/blog/">{bi_span("All press →", UI["All press"] + " →")}</a></p>
</section>

<hr class="rule">

<section class="s-index stack--tight">
  <p class="t-label">{bi_span("Contact", UI["Contact"])}</p>
  <p class="t-body"><a class="lnk" href="mailto:atelier@jujuhung.com">atelier@jujuhung.com</a></p>
  <p class="t-body"><a class="lnk" href="/contact/">All contact details →</a></p>
</section>"""

    return document(
        title="About — Julia Hung",
        desc=cv["statement"][0][:300],
        path="/about/", body=body, active="/about/",
        jsonld={
            "@context": "https://schema.org", "@type": "Person",
            "name": "Julia Hung", "alternateName": "洪郁雯",
            "birthDate": "1986", "birthPlace": "Taipei", "jobTitle": "Artist",
            "url": f"{SITE}/about/", "email": "atelier@jujuhung.com",
            "description": cv["statement"][0][:300],
            "sameAs": ["https://www.instagram.com/juju.hung/"],
        })


# --- Contact -------------------------------------------------------------- #

def contact():
    data = json.load(open(f"{ROOT}/content/contact.json", encoding="utf-8"))
    rows = []
    for f in data["fields"]:
        val = bi_span(esc(f["en"]), esc(f.get("zh")))
        if f.get("href"):
            val = f'<a class="lnk" href="{esc(f["href"])}">{val}</a>'
        rows.append(f'    <dt>{esc(f["label"])}</dt>\n    <dd>{val}</dd>')

    body = f"""<section class="s-index split">
  <div class="col-8">
    <h1 class="t-label">{bi_span("Contact", UI["Contact"])}</h1>
  </div>
  <div class="col-4">
  <dl class="meta">
{chr(10).join(rows)}
  </dl>
  </div>
</section>"""
    return document(
        title="Contact — Julia Hung",
        desc="Contact Julia Hung 洪郁雯 — atelier@jujuhung.com. Studio in Taipei and New York.",
        path="/contact/", body=body, active="/contact/")


# --- News ----------------------------------------------------------------- #

def news():
    data = json.load(open(f"{ROOT}/content/news.json", encoding="utf-8"))
    rows = []
    for it in data["items"]:
        text = bi_span(it["en"], it.get("zh"))
        if it.get("href"):
            text += f' <a class="lnk" href="{esc(it["href"])}">{bi_span("More →", UI["More"] + " →")}</a>'
        rows.append(f"""    <div class="row">
      <span class="row__title t-row">{text}</span>
      <span class="row__venue">{esc(it["label"])}</span>
      <span class="row__year">{esc(it["date"])}</span>
    </div>""")

    body = f"""<section class="s-index stack--tight">
  <h1 class="t-label">{bi_span("News", UI["News"])}</h1>
</section>

<section class="s-index">
  <div class="rows">
{chr(10).join(rows)}
  </div>
</section>"""
    return document(
        title="News — Julia Hung",
        desc="Exhibition announcements, awards, residencies and studio news from Julia Hung 洪郁雯.",
        path="/news/", body=body, active="/news/")


# --- Press ---------------------------------------------------------------- #

def press_index():
    press = load_press()
    rows = "\n".join(f"""    <a class="row" href="/post/{esc(p["slug"])}/">
      <span class="row__title t-row">{esc(p["title"])}</span>
      <span class="row__venue">{esc(p["excerpt"])}</span>
      <span class="row__year">{esc((p["published"] or "")[:4])}</span>
    </a>""" for p in press)

    body = f"""<section class="s-index stack--tight">
  <h1 class="t-label">{bi_span("Press", UI["Press"])}</h1>
  <p class="t-body"><span lang="en">Reviews, interviews and features. Each entry
    links to a summary; full articles stay with their original publisher.</span><span lang="zh">評論、專訪與報導。每則連往摘要，全文仍留在原發布媒體。</span></p>
</section>

<section class="s-index">
  <div class="rows">
{rows}
  </div>
</section>"""
    return document(
        title="Press — Julia Hung",
        desc="Reviews, interviews and features on Julia Hung 洪郁雯 in Whitehot Magazine, GQ, Prestige, IW and others.",
        path="/blog/", body=body, active="/blog/")


def press_stub(p):
    """A citation page, not a reprint.

    The Wix blog republished whole articles; the content brief is explicit that
    this should not continue without permission. Each post keeps its URL — they
    are indexed — but carries title, outlet, date and a short summary only.
    """
    # A citation, not an excerpt. The content brief is explicit that lifting
    # large passages from a publisher is the thing to avoid, so this is capped
    # short enough to read as a pointer. Julia can replace it with her own
    # one-line summary in content/press.json.
    summary = re.sub(r"\s+", " ", p.get("summary") or p.get("plain") or "").strip()
    if len(summary) > 180:
        cut = summary[:180]
        summary = cut[:max(cut.rfind("。"), cut.rfind("."), cut.rfind(" "))].strip() + "…"

    if p.get("source_url"):
        src = (f'\n    <p><a class="lnk" href="{esc(p["source_url"])}" '
               f'rel="noopener">{bi_span("Read at " + esc(p["excerpt"]) + " →", "閱讀原文 →")}</a></p>')
    else:
        src = ('\n    <p class="t-body">'
               + bi_span(f"Published by {esc(p['excerpt'])}. "
                         "The full article stays with its publisher.",
                         f"原文刊載於 {esc(p['excerpt'])}，全文請見原發布媒體。")
               + "</p>")

    body = f"""<article class="s-detail split">
  <div class="col-8 stack--tight">
    <p class="t-label">{esc(p["excerpt"])}</p>
    <h1 class="t-display">{esc(p["title"])}</h1>
    <p class="t-body">{esc(p["published"])}</p>
  </div>
  <div class="col-8 stack">
    <p class="t-lead">{esc(summary)}</p>{src}
  </div>
</article>

<nav class="nextprev t-meta" aria-label="More press">
  <a class="lnk" href="/blog/">{bi_span("All press →", UI["All press"] + " →")}</a>
</nav>"""
    return document(
        title=f'{p["title"]} — Julia Hung',
        desc=(summary or p["title"])[:300],
        path=f'/post/{p["slug"]}/', body=body, active="/blog/", family="detail",
        jsonld={
            "@context": "https://schema.org", "@type": "NewsArticle",
            "headline": p["title"],
            "datePublished": p["published"],
            "publisher": {"@type": "Organization", "name": p["excerpt"]},
            "about": {"@type": "Person", "name": "Julia Hung",
                      "alternateName": "洪郁雯"},
            "url": f'{SITE}/post/{p["slug"]}/',
        })


# --- Commission guide (unlisted) ------------------------------------------ #

def commission():
    """Not in the nav, not in the sitemap, noindex.

    This is obscurity, not access control: anyone with the URL can read it, and
    a client-side password would be trivially bypassed by viewing source. If
    the pricing or terms genuinely must be gated, that needs a host that can
    authenticate — static hosting cannot.
    """
    fields = [
        ("Types", "Sculpture and wall works in enamelled copper wire; suspended "
                  "and site-responsive installation; public and architectural "
                  "commissions."),
        ("Process", "Enquiry · site and brief · fee proposal · maquette or "
                    "drawing · fabrication · delivery and installation."),
        ("Information needed", "Site dimensions and photographs, lighting and "
                               "fixing conditions, budget range, and the date "
                               "the work must be in place."),
        ("Proposal", "One concept proposal with up to two rounds of revision. "
                     "Further rounds are quoted separately."),
        ("Lead time", "Four to nine months from signed agreement, depending on "
                      "scale. Hand-woven work cannot be compressed."),
        ("Payment", "50% deposit on agreement, 30% at fabrication, 20% before "
                    "shipping. The deposit reserves studio time and is "
                    "non-refundable."),
        ("Shipping &amp; install", "Crating, freight, insurance and installation "
                                   "are quoted separately and are the "
                                   "commissioner's cost unless agreed otherwise."),
        ("Copyright", "Copyright remains with the artist. The studio retains "
                      "the right to photograph and publish the work; a "
                      "confidentiality period can be agreed in writing."),
        ("Cancellation", "Work cancelled after fabrication begins is invoiced "
                         "for the stage reached."),
    ]
    rows = "\n".join(f"    <dt>{k}</dt>\n    <dd>{v}</dd>" for k, v in fields)
    body = f"""<section class="s-index stack--tight">
  <h1 class="t-display">Commission guide</h1>
  <p class="t-body">Shared on request. Figures are indicative and confirmed per
    project — write to <a class="lnk" href="mailto:atelier@jujuhung.com">atelier@jujuhung.com</a>.</p>
</section>

<section class="s-index split">
  <div class="col-8">
  <dl class="meta">
{rows}
  </dl>
  </div>
</section>"""
    return document(
        title="Commission guide — Julia Hung",
        desc="Commission terms and process. Shared on request.",
        path="/commission/", body=body, noindex=True)


def empty_category():
    """/blog/categories/curator-s-pick — an indexed URL with no posts.

    The category is empty on the live Wix site ("Posts Coming Soon"). Keeping
    the URL alive avoids a 404 on something Google has indexed; canonical and
    noindex point the value at /blog/ where the actual list lives.
    """
    body = """<section class="s-index stack--tight">
  <h1 class="t-label">Curator's Pick</h1>
  <p class="t-body">This category has no entries.</p>
  <p><a class="lnk" href="/blog/">{bi_span("All press →", UI["All press"] + " →")}</a></p>
</section>"""
    doc = document(title="Curator's Pick — Julia Hung",
                   desc="Press index for Julia Hung 洪郁雯.",
                   path="/blog/categories/curator-s-pick/",
                   body=body, noindex=True, active="/blog/")
    # Point the consolidated signal at the real list.
    return doc.replace(
        '<link rel="canonical" href="https://www.jujuhung.com/blog/categories/curator-s-pick/">',
        '<link rel="canonical" href="https://www.jujuhung.com/blog/">')


def not_found():
    body = """<section class="s-index stack--tight">
  <h1 class="t-display">Not found</h1>
  <p class="t-body">That page does not exist, or it moved when the site was
    rebuilt.</p>
  <p><a class="lnk" href="/artworks/">Works →</a></p>
  <p><a class="lnk" href="/exhibitions/">Exhibitions →</a></p>
</section>"""
    return document(title="Not found — Julia Hung",
                    desc="Page not found.", path="/404.html",
                    body=body, noindex=True)


def sitemap(paths):
    urls = "\n".join(
        f"  <url><loc>{SITE}{p}</loc></url>" for p in sorted(paths))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{urls}\n</urlset>\n")


# --- Home ----------------------------------------------------------------- #

def home():
    """Header · most recent exhibition 8/4 · ink rule · statement 8/4 with the
    two most recent news lines. Nothing else, and no footer nav.

    The lead show and the statement are the only hand-written copy on the
    site; everything else comes from content/. Change the label to "On view"
    while a show is actually running.
    """
    news_items = json.load(
        open(f"{ROOT}/content/news.json", encoding="utf-8"))["items"][:2]
    lead_slug = "the-interval-between"
    rec = load("exhibitions", lead_slug)
    pics = imgs["exhibitions"].get(lead_slug, [])
    label = "Most recent"

    lines = "\n".join(
        f'    <p class="t-body">{bi_span(it["en"], it.get("zh"))}</p>'
        for it in news_items)

    body = f"""<section class="split split--bottom">
{picture(pics[0]["stem"], "16-10", alt_for(rec, 1, "exhibitions"),
         sizes="(max-width: 900px) 100vw, 66vw", eager=True).replace(
             'class="fig fig--16-10"', 'class="fig fig--16-10 col-8"')}
  <div class="col-4 stack--tight">
    <p class="t-label">{bi_span(label, UI[label])}</p>
    <h1 class="t-display">{bi_span(esc(rec["title"]), esc(rec.get("title_zh")))}</h1>
    <p class="t-body">{bi_span(esc(show_venue(rec)), esc((rec.get("dates_zh") or [""])[-1]))}</p>
    <p class="t-body">{bi_span("20 December 2025 – 13 February 2026",
                               "2025.12.20 – 2026.02.13")}</p>
    <p><a class="lnk" href="/exhibitions/{lead_slug}/">{bi_span("Exhibition →", "展覽 →")}</a></p>
  </div>
</section>

<hr class="rule rule--ink">

<section class="split">
  <div class="col-8">
    <p class="t-lead">{bi_span(
        "Julia Hung works with enamelled copper wire, discarded plastics and "
        "ordinary objects, using techniques drawn from domestic labour — "
        "cooking, ironing, weaving — to build biomorphic forms that hold a "
        "material somewhere between solid and fluid.",
        "洪郁雯以彩漆銅線、廢棄塑料與日常物件創作，援引烹煮、熨燙、編織等家務勞動的技術，"
        "構築介於固態與流動之間的生物形態。")}</p>
  </div>
  <div class="col-4 stack--tight">
    <p class="t-label">{bi_span("News", UI["News"])}</p>
{lines}
    <p><a class="lnk" href="/news/">{bi_span("All news →", UI["All news"] + " →")}</a></p>
  </div>
</section>"""

    return document(
        title="Julia Hung 洪郁雯",
        desc="Julia Hung 洪郁雯 (b. 1986, Taipei) makes installations and "
             "sculptures in enamelled copper wire and reclaimed material, "
             "working between Taipei and New York.",
        path="/", body=body, family="home", home=True,
        og_image=f'/assets/img/{pics[0]["stem"]}-1600.jpg' if pics else None,
        jsonld={
            "@context": "https://schema.org", "@type": "Person",
            "name": "Julia Hung", "alternateName": "洪郁雯",
            "birthDate": "1986", "birthPlace": "Taipei", "jobTitle": "Artist",
            "url": f"{SITE}/", "email": "atelier@jujuhung.com",
            "sameAs": ["https://www.instagram.com/juju.hung/"],
        })


def main():
    written = []
    written.append(write("/", home()))
    written.append(write("/artworks/", works_index()))
    for i, slug in enumerate(FEATURED):
        prev_s = FEATURED[i - 1] if i else None
        next_s = FEATURED[i + 1] if i + 1 < len(FEATURED) else None
        written.append(write(f"/artworks/{slug}/", work_detail(slug, prev_s, next_s)))

    written.append(write("/exhibitions/", exhibitions_index()))
    for f in sorted(os.listdir(f"{ROOT}/content/exhibitions")):
        if f.endswith(".json") and not f.startswith("_"):
            slug = f[:-5]
            written.append(write(f"/exhibitions/{slug}/", exhibition_detail(slug)))

    written.append(write("/about/", about()))
    written.append(write("/contact/", contact()))
    written.append(write("/news/", news()))
    written.append(write("/blog/", press_index()))
    for p in load_press():
        written.append(write(f'/post/{p["slug"]}/', press_stub(p)))

    written.append(write("/blog/categories/curator-s-pick/", empty_category()))
    written.append(write("/commission/", commission()))

    with open(f"{ROOT}/404.html", "w", encoding="utf-8") as f:
        f.write(not_found())
    written.append(f"{ROOT}/404.html")

    # Public pages only: the commission guide and 404 stay out.
    public = ["/"] + [
        "/" + os.path.relpath(os.path.dirname(p), ROOT).replace(os.sep, "/") + "/"
        for p in written
        if p.endswith("index.html")
        and "/commission/" not in p and "/categories/" not in p]
    with open(f"{ROOT}/sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap(set(public)))

    for p in written:
        print(" ", os.path.relpath(p, ROOT))
    print(f"\n{len(written)} pages, {len(set(public))} in sitemap")


if __name__ == "__main__":
    main()
