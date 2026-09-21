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

NAV = [("/artworks/", "Works"), ("/exhibitions/", "Exhibitions"),
       ("/news/", "News"), ("/blog/", "Press"),
       ("/about/", "About"), ("/contact/", "Contact")]


def header(active=None):
    cur = ' aria-current="page"'
    items = "\n".join(
        f'    <a href="{href}"{cur if href == active else ""}>{label}</a>'
        for href, label in NAV)
    return f"""<header class="hdr">
  <a class="hdr__mark" href="/">Julia Hung</a>
  <nav class="hdr__nav t-meta" aria-label="Main">
{items}
  </nav>
</header>"""


def document(*, title, desc, path, body, og_image=None, jsonld=None,
             noindex=False, active=None, family="index"):
    canonical = SITE + path
    og = og_image or "/assets/img/works/untamed/2023_untamed_01-1600.jpg"
    head = [
        '<!doctype html>',
        '<html lang="en">',
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
    return "\n".join(head + [header(active), "", body, "",
                             "</div>", "</body>", "</html>", ""])


def write(path, content):
    dest = os.path.join(ROOT, path.strip("/"), "index.html") if path != "/" \
        else os.path.join(ROOT, "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(content)
    return dest


# --- Imagery -------------------------------------------------------------- #

def picture(stem, ratio, alt, caption=None, sizes="100vw", eager=False):
    """<picture> with a WebP source and a JPEG fallback, fixed ratio, no
    rounding, caption outside the frame."""
    cap = ""
    if caption:
        cap = f"\n    <figcaption>{esc(caption)}</figcaption>"
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

    meta_rows = []
    for label, val in (
        ("Material", rec.get("material")),
        ("Series", rec.get("series")),
        ("Dimensions", tidy_dims(rec.get("dimensions"))),
    ):
        if val:
            meta_rows.append(f"    <dt>{label}</dt>\n"
                             f"    <dd>{esc(val)}</dd>")

    def shown_list(items):
        return ", ".join(
            f'<a class="lnk" href="{local_href(i["href"])}">{esc(i["text"])}</a>'
            if local_href(i["href"]) else esc(i["text"]) for i in items)

    # A few records carry the credit only in the Chinese field — 21g's sole
    # entry ("Voices") lives there. Fall back to it so the row survives.
    shown = rec.get("exhibitions") or rec.get("exhibitions_zh") or []
    if shown:
        meta_rows.append(f'    <dt>Shown</dt>\n'
                         f'    <dd>{shown_list(shown)}</dd>')

    note = ""
    st_en = rec.get("statement") or []
    lead_en = first_statement(st_en)
    if lead_en:
        note = f'\n  <p class="meta__note">{esc(lead_en)}</p>'

    # Image stack: one 4/3 primary, then 1/1 pairs.
    def cap(p):
        return tidy_dims(p.get("parsed", {}).get("raw")) or None

    stack = []
    if pics:
        p = pics[0]
        stack.append(picture(p["stem"], "4-3", alt_for(rec, 1, "works"), cap(p),
                             sizes="(max-width: 900px) 100vw, 70vw", eager=True))
    rest = pics[1:]
    for i in range(0, len(rest), 2):
        pair = rest[i:i + 2]
        inner = "\n".join(
            picture(p["stem"], "1-1", alt_for(rec, i + j + 2, "works"),
                    cap(p), sizes="(max-width: 600px) 100vw, 35vw")
            for j, p in enumerate(pair))
        stack.append(f'  <div class="pair">\n{inner}\n  </div>')

    body_paras = "\n".join(
        f'    <p class="t-body">{esc(l)}</p>'
        for l in st_en if l != lead_en)

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
    <h1 class="t-display">{esc(title)}</h1>
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


def ext_attrs(href):
    """Links that leave the site open in a new tab.

    A visitor following a gallery's own page for a show has not finished with
    this one. mailto: and internal paths are untouched.
    """
    h = (href or "").lower()
    if not h.startswith(("http://", "https://")):
        return ""
    if h.startswith(("https://jujuhung.com", "https://www.jujuhung.com",
                     "http://jujuhung.com", "http://www.jujuhung.com")):
        return ""
    return ' target="_blank" rel="noopener"'


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
{picture(p["stem"], "", alt_for(rec, 1, "works"), sizes="(max-width: 900px) 46vw, 30vw")}
    <p class="card__title">{esc(rec["title"])}</p>
    <p class="card__year">{esc(year_label(rec.get("year")))}</p>
  </a>""")

    filters = "\n".join(
        f'    <button type="button" data-filter="{k}">'
        f'{k.replace("-", " ").title()}</button>'
        for k in CATS)
    body = f"""<section class="s-index stack">
  <h1 class="t-label">Works</h1>
  <div class="filters t-meta" role="group" aria-label="Filter works">
    <button type="button" data-filter="all" aria-pressed="true">All</button>
{filters}
  </div>
</section>

<section class="s-index grid" data-grid>
{chr(10).join(cards)}
</section>

<script src="/assets/js/filter.js" defer></script>"""
    return document(
        title="Works — Julia Hung",
        desc="Selected works by Julia Hung — sculpture and installation in "
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

    # Same card grid as the works index. The tiles are 4/3 rather than the
    # works square: an install view is a room, and a centre crop to square
    # throws the room away.
    cards = []
    for slug in slugs:
        rec = load("exhibitions", slug)
        pics = imgs["exhibitions"].get(slug, [])
        if not pics:
            continue
        solo = bool(rec.get("solo"))
        chip = '<span class="chip">Solo</span>' if solo else ""
        # Anything not a solo show files under Group — the fairs, festivals
        # and collaborations keep their own label on the exhibition page.
        cat = "solo" if solo else "group"
        # Venue and year take separate lines: one venue is "Soka Art · Tainan",
        # so any middot joining them would read as part of the name.
        cards.append(f"""  <a class="card" href="/exhibitions/{slug}/" data-cat="{cat}">
{picture(pics[0]["stem"], "", alt_for(rec, 1, "exhibitions"), sizes="(max-width: 900px) 46vw, 30vw")}
    <p class="card__title">{esc(rec["title"])}{chip}</p>
    <p class="card__venue">{esc(show_venue(rec))}</p>
    <p class="card__year">{esc(year_range(rec))}</p>
  </a>""")

    body = f"""<section class="s-index stack">
  <h1 class="t-label">Exhibitions</h1>
  <div class="filters t-meta" role="group" aria-label="Filter exhibitions">
    <button type="button" data-filter="all" aria-pressed="true">All</button>
    <button type="button" data-filter="solo">Solo</button>
    <button type="button" data-filter="group">Group</button>
  </div>
</section>

<section class="s-index grid grid--wide" data-grid>
{chr(10).join(cards)}
</section>

<section class="s-index">
  <p class="t-body">Earlier exhibitions are listed in the
    <a class="lnk" href="/about/">CV</a>.</p>
</section>

<script src="/assets/js/filter.js" defer></script>"""
    return document(
        title="Exhibitions — Julia Hung",
        desc="Solo and selected group exhibitions by Julia Hung, 2017 to present.",
        path="/exhibitions/", body=body, active="/exhibitions/")


def exhibition_detail(slug):
    rec = load("exhibitions", slug)
    pics = imgs["exhibitions"].get(slug, [])
    # dates is [year, venue] in every record — the Wix export packed the venue
    # in beside the year. year_range takes the date half and nothing else.
    dates_en = year_range(rec)

    # Same rhythm as a work page: one large primary, then pairs. The
    # proportions stay landscape — an install view is a room, and the square
    # the works grid uses would crop the room out of it.
    stack = []
    if pics:
        stack.append(picture(pics[0]["stem"], "16-10",
                             alt_for(rec, 1, "exhibitions"),
                             sizes="(max-width: 900px) 100vw, 70vw", eager=True))
    rest_pics = pics[1:]
    for i in range(0, len(rest_pics), 2):
        pair = rest_pics[i:i + 2]
        inner = "\n".join(
            picture(p["stem"], "4-3", alt_for(rec, i + j + 2, "exhibitions"),
                    sizes="(max-width: 600px) 100vw, 35vw")
            for j, p in enumerate(pair))
        stack.append(f'  <div class="pair">\n{inner}\n  </div>')

    # The text sits under the images. Exhibition texts run long — one lead
    # paragraph of a thousand characters would not fit the meta column.
    # The venue's own page for the show, carried over from the Wix site. The
    # label varies by record — a festival and a fair are not "exhibitions".
    link = rec.get("link") or {}
    view = (f'\n    <p><a class="lnk" href="{esc(link["href"])}"'
            f'{ext_attrs(link["href"])}>'
            f'{esc(link["text"])} →</a></p>') if link.get("href") else ""

    text_en = rec.get("text") or []
    paragraphs = "\n".join(
        [f'    <p class="t-lead">{esc(text_en[0])}</p>']
        + [f'    <p class="t-body">{esc(l)}</p>' for l in text_en[1:]]
    ) if text_en else ""

    work_rows = []
    for w in rec.get("works") or []:
        href = local_href(w["href"])
        if not href:
            continue
        wslug = href.strip("/").split("/")[-1]
        wr = load("works", wslug)
        work_rows.append(f"""    <a class="row" href="{href}">
      <span class="row__title t-row">{esc(wr["title"])}</span>
      <span class="row__venue">{esc(wr.get("material") or "")}</span>
      <span class="row__year">{esc(year_label(wr.get("year")))}</span>
    </a>""")
    works_block = ""
    if work_rows:
        works_block = f"""
<section class="s-detail">
  <p class="t-label">Works shown</p>
  <div class="rows">
{chr(10).join(work_rows)}
  </div>
</section>"""

    body = f"""<article class="s-detail detail">

  <div class="detail__meta stack--tight">
    <p class="t-label">{esc(show_kind(rec))}</p>
    <h1 class="t-display">{esc(rec["title"])}</h1>
    <p class="t-body">{esc(show_venue(rec))}</p>
    <p class="t-body">{esc(dates_en)}</p>{view}
  </div>

  <div class="stack">
{chr(10).join(stack)}
{paragraphs}
  </div>

</article>{works_block}

<nav class="nextprev t-meta" aria-label="More exhibitions">
  <a class="lnk" href="/exhibitions/">All exhibitions →</a>
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

    # Portrait: 3/4 left. The CMS holds no portrait, so the file is named
    # directly — it is the one image on the site that is of Julia, not by her.
    fig = picture("about/2022_julia-hung-portrait", "3-4",
                  "Portrait of Julia Hung in front of one of her works.",
                  sizes="(max-width: 900px) 100vw, 30vw", eager=True)

    statement = "\n".join(
        f'    <p class="t-lead t-lead--sm">{esc(pgraph)}</p>'
        for pgraph in cv["statement"])

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

    links = [(cv.get("cv_pdf"), "CV (PDF) ↓"),
             (cv.get("press_pdf"), "Selected Press (PDF) ↓")]
    offered = "\n".join(f'    <a class="lnk" href="{href}" download>{label}</a>'
                        for href, label in links if href)
    downloads = f'\n  <p class="downloads">\n{offered}\n  </p>' if offered else ""

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
  <p class="t-body">{esc(cv["born"])}</p>{downloads}
</section>

{chr(10).join(blocks)}"""

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

# The three marks, drawn rather than linked: an icon font or an SVG sprite
# would be the first external dependency on the site. They inherit
# currentColor, so they take the same mute -> ink hover as every other link.
SOCIAL_ICONS = {
    "instagram":
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="1.5" aria-hidden="true">'
        '<rect x="3" y="3" width="18" height="18" rx="5"/>'
        '<circle cx="12" cy="12" r="4.2"/>'
        '<circle cx="17.2" cy="6.8" r="1.15" fill="currentColor" stroke="none"/>'
        '</svg>',
    "facebook":
        '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
        '<path d="M13.6 21v-8.2h2.7l.4-3.2h-3.1V7.5c0-.9.3-1.6 1.6-1.6h1.7V3.1'
        'C16.6 3 15.6 3 14.5 3c-2.4 0-4 1.5-4 4.2v2.4H7.7v3.2h2.8V21h3.1z"/>'
        '</svg>',
    # Linktree's mark as the reference design draws it: a six-spoke asterisk.
    "linktree":
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"'
        ' stroke-width="1.6" stroke-linecap="round" aria-hidden="true">'
        '<path d="M12 3.6v16.8"/><path d="M4.7 7.8l14.6 8.4"/>'
        '<path d="M19.3 7.8 4.7 16.2"/></svg>',
}


def field(name, label, *, kind="text", placeholder="", required=True,
          options=None, rows=None):
    """One form row: a label over a rule you can type into.

    Deliberately the same shape as a .meta row — label in the mute register,
    value in ink, a hairline under it — so the form reads as part of the site
    rather than as a widget dropped into it.
    """
    req = " required" if required else ""
    if options:
        opts = "\n".join(f'        <option value="{esc(v)}">{esc(t)}</option>'
                         for v, t in options)
        control = (f'      <select id="{name}" name="{name}">\n'
                   f'{opts}\n      </select>')
    elif rows:
        control = f'      <textarea id="{name}" name="{name}" rows="{rows}"{req}></textarea>'
    else:
        ph = f' placeholder="{esc(placeholder)}"' if placeholder else ""
        control = f'      <input id="{name}" name="{name}" type="{kind}"{ph}{req}>'
    return (f'    <div class="field">\n'
            f'      <label class="t-label" for="{name}">{esc(label)}</label>\n'
            f'{control}\n'
            f'    </div>')


def contact():
    data = json.load(open(f"{ROOT}/content/contact.json", encoding="utf-8"))
    email = data["email"]
    form = data["form"]

    marks = "\n".join(
        f'      <a href="{esc(s["href"])}" aria-label="{esc(s["name"])}"'
        f'{ext_attrs(s["href"])}>{SOCIAL_ICONS[s["icon"]]}</a>'
        for s in data["socials"])

    def indent(s):
        return "\n".join("  " + ln for ln in s.split("\n"))

    rows = [
        f'    <div class="field-pair">\n'
        f'{indent(field("name", "Name", placeholder="First and last"))}\n'
        f'{indent(field("email", "Email", kind="email", placeholder="you@studio.com"))}\n'
        f'    </div>',
        field("enquiry", form["enquiry_label"],
              options=[(o["value"], o["label"])
                       for o in form["enquiry_options"]]),
        field("message", "Message", rows=7),
    ]

    # No backend. The action is the honest fallback — a browser with no
    # JavaScript posts the fields to the same address as plain text —
    # and contact.js replaces it with a composed subject and body.
    fallback = f"mailto:{email}?subject=Enquiry%20via%20jujuhung.com"

    body = f"""<section class="s-index contact">

  <div class="contact__card">
    <h1 class="vh">Contact</h1>
    <a class="contact__email" href="mailto:{esc(email)}">{esc(email)}</a>
    <div class="socials">
{marks}
    </div>
  </div>

  <form class="form" data-mailto="{esc(email)}"
        action="{esc(fallback)}" method="post" enctype="text/plain">
{chr(10).join(rows)}
    <div class="form__actions">
      <p class="form__note" data-note hidden>Opening your email app with this
        message ready to send. If nothing happens, write to
        <a class="lnk-inline" href="mailto:{esc(email)}">{esc(email)}</a>.</p>
      <button class="btn" type="submit">Send</button>
    </div>
  </form>

</section>

<script src="/assets/js/contact.js" defer></script>"""
    return document(
        title="Contact — Julia Hung",
        desc=f"Contact Julia Hung — {email}. Enquiries about exhibitions, "
             "commissions, press and gallery representation.",
        path="/contact/", body=body, active="/contact/")


# --- News ----------------------------------------------------------------- #

WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
         6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
         11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen",
         15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen",
         19: "Nineteen", 20: "Twenty"}


def news_lead(it):
    """The newest entry, set at reading size with a summary and its own rule
    above it. One per page — the thing a visitor came to find out."""
    when = f'{it["label"]} · {it["month"]} {it["year"]}' if it.get("month") \
        else f'{it["label"]} · {it["year"]}'
    out = [f'      <p class="t-label">{esc(when)}</p>',
           f'      <h2 class="news-lead__title">{it["en"]}</h2>']
    if it.get("summary_en"):
        out.append(f'      <p class="t-body news-lead__sum">{it["summary_en"]}</p>')
    if it.get("link"):
        out.append(f'      <p><a class="lnk" href="{esc(it["link"]["href"])}">'
                   f'{esc(it["link"]["text"])} →</a></p>')
    return '    <article class="news-lead">\n' + "\n".join(out) + '\n    </article>'


def news_row(it):
    """Every other entry: month in the gutter, one line of text, one link."""
    link = ""
    if it.get("link"):
        link = (f'\n        <p><a class="lnk" href="{esc(it["link"]["href"])}">'
                f'{esc(it["link"]["text"])} →</a></p>')
    return f"""    <article class="news-row">
      <p class="news-row__when">{esc(it.get("month", "")[:3])}</p>
      <div>
        <p class="t-row">{it["en"]}</p>{link}
      </div>
    </article>"""


def news_year(year, items):
    """One year: a numeral, a count, an ink rule, then the entries on the left
    and the single picture that illustrates the year on the right."""
    note = "Upcoming" if any(i.get("upcoming") for i in items) else (
        "One entry" if len(items) == 1
        else f"{WORDS.get(len(items), len(items))} entries")

    entries = "\n".join(news_lead(it) if it.get("lead") else news_row(it)
                         for it in items)

    fig = ""
    shot = next((i["image"] for i in items if i.get("image")), None)
    if shot:
        block = picture(shot["stem"], "4-3", shot["alt"],
                        caption=shot.get("caption"),
                        sizes="(max-width: 900px) 100vw, 400px")
        fig = "\n" + "\n".join("  " + ln for ln in block.split("\n"))

    return f"""<section class="news-year">
  <div class="news-year__head">
    <p class="news-year__n">{esc(year)}</p>
    <p class="t-label">{esc(note)}</p>
  </div>
  <hr class="rule rule--ink">
  <div class="news-year__cols">
    <div class="news-year__list">
{entries}
    </div>{fig}
  </div>
</section>"""


def news():
    """Grouped by year, newest first, the newest entry led. Entries carry
    their own year and month; the page does no date arithmetic, so an entry
    reads the same in five years as it does the week it is written."""
    data = json.load(open(f"{ROOT}/content/news.json", encoding="utf-8"))

    years = []
    for it in data["items"]:
        if not years or years[-1][0] != it["year"]:
            years.append((it["year"], []))
        years[-1][1].append(it)

    body = """<section class="s-index stack--tight">
  <h1 class="t-label">News</h1>
</section>

""" + "\n\n".join(news_year(y, items) for y, items in years)

    return document(
        title="News — Julia Hung",
        desc="Exhibition announcements, awards, residencies and studio news from Julia Hung.",
        path="/news/", body=body, active="/news/")


# --- Press ---------------------------------------------------------------- #

def press_when(p):
    """2025-09-10 -> 2025.09. The day is noise in a citation list."""
    parts = (p.get("published") or "").split("-")
    return ".".join(parts[:2])


def press_row(p):
    """Outlet and date in the gutter, headline beside them."""
    outlet = p.get("outlet") or p["excerpt"]
    return f"""    <a class="prow" href="/post/{esc(p["slug"])}/">
      <div>
        <p class="prow__outlet">{esc(outlet)}</p>
        <p class="prow__when">{esc(press_when(p))}</p>
      </div>
      <p class="prow__title t-row">{esc(p["title"])}</p>
    </a>"""


def press_index():
    press = load_press()
    rows = "\n".join(press_row(p) for p in press)
    count = f"{WORDS.get(len(press), len(press))} pieces"

    body = f"""<section class="s-index">
  <div class="press-head">
    <h1 class="t-label">Selected Press</h1>
    <p class="t-label">{esc(count)}</p>
  </div>
  <div class="rows mt-2">
{rows}
  </div>
</section>"""
    return document(
        title="Press — Julia Hung",
        desc="Reviews, interviews and features on Julia Hung in Whitehot Magazine, GQ, Prestige, IW and others.",
        path="/blog/", body=body, active="/blog/")


MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def press_date(p):
    """2023-06-05 -> 5 June 2023, the date style the rest of the site uses."""
    try:
        y, m, d = (p.get("published") or "").split("-")
        return f"{int(d)} {MONTHS[int(m) - 1]} {y}"
    except (ValueError, IndexError):
        return p.get("published") or ""


def post_links(h):
    """Outbound links inside recovered body copy open in a new tab; links back
    to jujuhung.com become site-relative so they stay on this site."""
    def one(m):
        href = re.sub(r"^https?://(?:www\.)?jujuhung\.com", "", m.group(1)) or "/"
        return (f'<a class="lnk-inline" href="{href}"'
                f'{ext_attrs(html.unescape(href))}>')
    return re.sub(r'<a href="([^"]+)">', one, h)


def post_body(blocks):
    """Render the recovered blocks. Consecutive list items share one <ul>;
    an image without a local derivative is dropped rather than hotlinked."""
    out, bullets = [], []

    def close_list():
        if bullets:
            items = "\n".join(f"      <li>{post_links(b)}</li>" for b in bullets)
            out.append(f'    <ul class="post__list">\n{items}\n    </ul>')
            bullets.clear()

    for b in blocks:
        if b["type"] == "li":
            bullets.append(b["html"])
            continue
        close_list()
        if b["type"] == "h":
            out.append(f'    <h2 class="post__h">{post_links(b["html"])}</h2>')
        elif b["type"] == "p":
            out.append(f'    <p class="t-body">{post_links(b["html"])}</p>')
        elif b["type"] == "img" and b.get("stem"):
            fig = picture(b["stem"], "", b.get("alt") or "",
                          sizes="(max-width: 900px) 100vw, 70vw")
            if b.get("logo"):     # a masthead is a mark, not a picture
                fig = fig.replace('class="fig fig--"', 'class="fig fig--mark"')
            out.append(fig)
    close_list()
    return "\n".join(out)


def press_stub(p):
    """The post as it stood on the Wix blog: the body copy Julia published
    there, with its links to the publisher intact.

    An earlier pass cut these to a citation and a short summary. They were
    restored on the site owner's instruction; the copy and the outbound links
    are the publisher's and are reproduced as they were.
    """
    blocks = p.get("body") or []
    if blocks:
        inner = post_body(blocks)
    else:
        # One post is missing from the archive; it keeps the citation form.
        summary = re.sub(r"\s+", " ", p.get("summary") or p.get("plain") or "").strip()
        inner = (f'    <p class="t-lead">{esc(summary[:300])}</p>\n'
                 f'    <p class="t-body">Published by {esc(p["excerpt"])}.</p>')

    first = next((re.sub(r"<[^>]+>", "", b["html"])
                  for b in blocks if b["type"] == "p"), "")
    desc = (first or p.get("plain") or p["title"]).strip()

    body = f"""<article class="s-detail detail">

  <div class="detail__meta stack--tight">
    <p class="t-label">{esc(p.get("outlet") or p["excerpt"])}</p>
    <h1 class="t-display">{esc(p["title"])}</h1>
    <p class="t-body">{esc(press_date(p))}</p>
  </div>

  <div class="stack post">
{inner}
  </div>

</article>

<nav class="nextprev t-meta" aria-label="More press">
  <a class="lnk" href="/blog/">All press →</a>
</nav>"""
    return document(
        title=f'{p["title"]} — Julia Hung',
        desc=desc[:300],
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
  <p><a class="lnk" href="/blog/">All press →</a></p>
</section>"""
    doc = document(title="Curator's Pick — Julia Hung",
                   desc="Press index for Julia Hung.",
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
        f'    <p class="t-body">{it["en"]}</p>' for it in news_items)

    body = f"""<section class="split split--bottom">
{picture(pics[0]["stem"], "16-10", alt_for(rec, 1, "exhibitions"),
         sizes="(max-width: 900px) 100vw, 66vw", eager=True).replace(
             'class="fig fig--16-10"', 'class="fig fig--16-10 col-8"')}
  <div class="col-4 stack--tight">
    <p class="t-label">{label}</p>
    <h1 class="t-display">{esc(rec["title"])}</h1>
    <p class="t-body">{esc(show_venue(rec))}</p>
    <p class="t-body">20 December 2025 – 13 February 2026</p>
    <p><a class="lnk" href="/exhibitions/{lead_slug}/">Exhibition →</a></p>
  </div>
</section>

<hr class="rule rule--ink">

<section class="split">
  <div class="col-8">
    <p class="t-lead">Julia Hung works with enamelled copper wire, discarded
      plastics and ordinary objects, using techniques drawn from domestic
      labour — cooking, ironing, weaving — to build biomorphic forms that hold
      a material somewhere between solid and fluid.</p>
  </div>
  <div class="col-4 stack--tight">
    <p class="t-label">News</p>
{lines}
    <p><a class="lnk" href="/news/">All news →</a></p>
  </div>
</section>"""

    return document(
        title="Julia Hung",
        desc="Julia Hung (b. 1986, Taipei) makes installations and "
             "sculptures in enamelled copper wire and reclaimed material, "
             "working between Taipei and New York.",
        path="/", body=body, family="home",
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
