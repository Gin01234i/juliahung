#!/usr/bin/env python3
"""Join the raw Wix collections into one clean record per work / exhibition.

The Wix CMS keeps English and Chinese in *separate* collections with opaque
names, cross-linked by id:

    Portfolio  (20, EN works)   <- i0yv91e2 (23, ZH works)      via .reference
    Recipes    (13, EN shows)   <- Items    (12, ZH shows)      via .TitleForUrl2
    About      (7  CV sections)
    Blog/Posts (18 press)

Output: content/works/<slug>.json, content/exhibitions/<slug>.json,
content/about.json, content/press.json — the authoring source for the
hand-written pages. Nothing is read at request time.

Usage:  python3 tools/normalize.py
"""
import html, json, os, re, sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMS = os.path.join(ROOT, "content", "cms")


def load(name):
    with open(os.path.join(CMS, name.replace("/", "-") + ".json"), encoding="utf-8") as f:
        return json.load(f)


def strip_html(s):
    """Rich text -> list of paragraphs, links preserved as (text, href)."""
    if not s:
        return []
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</(p|h[1-6]|div|li)>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return [p.strip() for p in re.split(r"\n\s*\n", s) if p.strip()]


def links_in(s):
    if not s:
        return []
    return [{"text": html.unescape(re.sub(r"<[^>]+>", "", t)).strip(), "href": h}
            for h, t in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', s, re.S)]


def slug_from(path, prefix):
    """'/artworks/untamed' -> 'untamed'."""
    if not path:
        return None
    p = path.strip("/")
    return p[len(prefix):].strip("/") if p.startswith(prefix) else p


def tidy(s):
    """Collapse the stray spacing the CMS carries around separators."""
    s = re.sub(r"\s+", " ", (s or "")).strip()
    s = re.sub(r"\s*([,，])\s*", r"\1 ", s)
    s = re.sub(r"\s*[・·]\s*", " \u00b7 ", s)
    return re.sub(r"\s{2,}", " ", s).strip(" ,")


def norm_slug(s):
    """Slug key tolerant of the trailing-hyphen and spacing drift in the CMS."""
    if not s:
        return None
    return re.sub(r"[^a-z0-9]+", "-", s.strip().lower()).strip("-") or None


def gallery(rec, *fields):
    """Best image gallery on a record, normalised.

    Wix keeps two or three near-duplicate galleries per record (imageGallery,
    imageGallery2, imageGallery3) and the captions are not always on the same
    one — imageGallery3 is often the longest but has empty descriptions while
    imageGallery carries the material and dimensions. Score by captions first,
    then by length, rather than trusting field order.
    """
    best, best_score = None, (-1, -1)
    for f in fields:
        items = rec.get(f)
        if not (isinstance(items, list) and items):
            continue
        out = []
        for it in items:
            if not isinstance(it, dict) or it.get("type") not in (None, "image"):
                continue
            media = it.get("slug") or ""
            if not media:
                continue
            st = it.get("settings") or {}
            out.append(OrderedDict(
                media=media,
                width=st.get("width"),
                height=st.get("height"),
                # This is where material + dimensions actually live.
                caption=(it.get("description") or "").strip(),
                title=(it.get("title") or "").strip(),
                filename=(it.get("fileName") or "").strip(),
            ))
        if not out:
            continue
        score = (sum(1 for i in out if i["caption"]), len(out))
        if score > best_score:
            best, best_score = out, score
    if best:
        return best
    # Single-image fields are stored as a wix:image:// uri instead.
    for f in ("image", "newField5", "coverImage"):
        uri = rec.get(f)
        if isinstance(uri, str) and uri.startswith("wix:image://"):
            m = re.match(r"wix:image://v1/([^/]+)/", uri)
            if m:
                return [OrderedDict(media=m.group(1), width=None, height=None,
                                    caption="", title="", filename="")]
    return []


YEAR_RE = re.compile(r"^\(?(19|20)\d{2}\s*[-–—]?\)?$")
DIM_RE = re.compile(
    r"\d\s*[x×]\s*\d"                       # 9 x 3 x 3
    r"|[HWDhwdØø]\s*\d"                       # H26 W22 D21
    r"|\d+\s*(?:cm|mm|m\b|公分|公尺)"          # 130 cm
    r"|dimensions?\s+variable|size\s+var|variable\s+dimensions"
    r"|\u5c3a\u5bf8[\u4e0d\u53ef]", re.I)   # 尺寸不定 / 尺寸可變


def parse_caption(cap):
    """Split an image description into material / dimensions / year.

    Captions are hand-typed and inconsistent — comma-separated, newline
    separated, year present or absent, dimensions sometimes written as
    "Dimensions variable". Classify each part rather than matching a shape.
    """
    if not cap:
        return {}
    raw = re.sub(r"[ \t]+", " ", cap).strip().strip(",")
    parts = [p.strip(" ,;") for p in re.split(r"[,\n]", raw)]
    parts = [p for p in parts if p]

    material, dims, year = [], [], None
    for p in parts:
        if YEAR_RE.match(p):
            year = re.sub(r"[()]", "", p)
        elif DIM_RE.search(p):
            dims.append(p)
        else:
            material.append(p)
    out = {"raw": re.sub(r"\s*\n\s*", ", ", raw)}
    if material:
        out["material"] = ", ".join(material)
    if dims:
        out["dims"] = ", ".join(dims)
    if year:
        out["year"] = year
    return out


def year_of(v):
    """Wix stores `year` as a date string, a {"$date": ...} wrapper, or a list."""
    if isinstance(v, dict):
        v = v.get("$date") or ""
    if isinstance(v, list):
        v = v[0] if v else ""
    m = re.search(r"\d{4}", str(v or ""))
    return m.group(0) if m else None


def date_of(v):
    """Wix dates arrive as a plain ISO string or a {"$date": ...} wrapper."""
    if isinstance(v, dict):
        v = v.get("$date") or ""
    return str(v or "")[:10] or None


def join_material(tags):
    """all02/media hold material tags and the year in no fixed order."""
    if not isinstance(tags, list):
        return None
    mats = [t for t in tags if isinstance(t, str) and not YEAR_RE.match(t.strip())]
    return ", ".join(t.strip() for t in mats) or None


def first(*vals):
    for v in vals:
        if isinstance(v, str) and v.strip():
            return re.sub(r"\s{2,}", " ", v.strip())
        if isinstance(v, list) and v:
            return v[0]
    return None


def build_works():
    en = load("Portfolio")
    zh_by_ref = {}
    for z in load("i0yv91e2"):
        if z.get("reference"):
            zh_by_ref[z["reference"]] = z

    out = []
    for e in en:
        slug = slug_from(e.get("link-portfolio-title"), "artworks")
        if not slug:
            continue
        z = zh_by_ref.get(e["_id"], {})
        imgs = gallery(e, "imageGallery3", "imageGallery2", "imageGallery", "media")
        zimgs = gallery(z, "mediagallery", "mediagallery1", "copy")

        # Dimensions are per image; the parse of the first is the work's own.
        parsed = [parse_caption(i["caption"]) for i in imgs]
        lead = next((p for p in parsed if p.get("dims")), {})

        rec = OrderedDict(
            slug=slug,
            # `title` is the display title; `title1` is a degraded, spacing-
            # stripped copy ("BeingasaWoman") that several records carry.
            title=first(e.get("title"), e.get("title1")),
            title_zh=first(z.get("title")),
            year=first(e.get("year1"), (e.get("all02") or [None, None])[1:],
                       year_of(e.get("year"))),
            material=join_material(e.get("all02")) or lead.get("material"),
            material_zh=join_material(z.get("media")) or join_material(z.get("all")),
            series=first(e.get("text")),
            series_zh=first(z.get("series"), z.get("exhibition")),
            dimensions=lead.get("dims"),
            statement=strip_html(e.get("richtext")),
            statement_zh=strip_html(z.get("richtext")),
            exhibitions=links_in(e.get("linkOfExhibition")),
            exhibitions_zh=links_in(z.get("text2")),
            video=e.get("video") or None,
            images=[dict(i, parsed=p) for i, p in zip(imgs, parsed)],
            images_zh=zimgs,
            source="Portfolio/" + e["_id"],
        )
        out.append(rec)
    out.sort(key=lambda r: (r["year"] or ""), reverse=True)
    return out


def build_exhibitions():
    en = load("Recipes")
    # The Chinese collection keys on the *orphan* /exhibition/ slug, which
    # differs from the live /exhibitions/ slug in two records: a stray trailing
    # hyphen, and 未央夜 vs whennightfalls. Its TitleForUrl2 field confirms
    # those two are the same show — settling an open question in seo/.
    zh_by_slug = {}
    for z in load("Items"):
        key = norm_slug(slug_from(z.get("link-items-title"), "exhibition"))
        alt = norm_slug(z.get("TitleForUrl2"))
        for k in (key, alt):
            if k:
                zh_by_slug.setdefault(k, z)

    out = []
    for e in en:
        slug = slug_from(e.get("link-recipes-title"), "exhibitions")
        if not slug:
            continue
        title = first(e.get("title"), e.get("title3"))
        z = zh_by_slug.get(norm_slug(slug), {}) or \
            zh_by_slug.get(norm_slug(title), {})

        # title2 is "Soka Art · Tainan | Solo Exhibition"
        venue, _, kind = (e.get("title2") or "").partition("|")
        # date is "2023\nSoka Art ・Tainan , Tainan"
        date_lines = [tidy(l) for l in (e.get("date") or "").split("\n") if l.strip()]

        rec = OrderedDict(
            slug=slug,
            title=title,
            title_zh=first(z.get("title")),
            venue=(date_lines[1] if len(date_lines) > 1 else venue.strip()) or None,
            venue_raw=venue.strip() or None,
            kind=kind.strip() or None,
            # `category` is the authoritative field; title2 is free text and
            # says "Solo Exhibition" on at least one group show.
            solo=any("solo" in str(c).lower()
                     for c in (e.get("category") or e.get("all") or [])),
            year=first([y for y in (e.get("all") or []) if re.fullmatch(r"\d{4}", y)]),
            dates=date_lines,
            dates_zh=[l.strip() for l in (z.get("dateandlocation") or "").split("\n")
                      if l.strip()],
            categories=e.get("category") or e.get("all") or [],
            text=strip_html(e.get("richtext")),
            text_zh=strip_html(z.get("exhibitiontext")),
            detail=strip_html(e.get("shortDescription1")),
            detail_zh=strip_html(z.get("newField1")),
            works=links_in(e.get("linkToArtworkPage")),
            images=gallery(e, "mediagallery", "mediagallery1", "image"),
            images_zh=gallery(z, "gallery1", "gallery2"),
            order=e.get("order"),
            source="Recipes/" + e["_id"],
        )
        out.append(rec)
    out.sort(key=lambda r: (r["year"] or ""), reverse=True)
    return out


def build_about():
    secs = sorted(load("About"), key=lambda r: r.get("number") or 0)
    return [OrderedDict(
        order=s.get("number"),
        heading=s.get("title"),
        body=strip_html(s.get("richtext")) or
             [l for l in (s.get("text") or "").split("\n") if l.strip()],
    ) for s in secs]


def build_press():
    out = []
    for p in load("Blog/Posts"):
        out.append(OrderedDict(
            slug=p.get("slug"),
            title=p.get("title"),
            excerpt=(p.get("excerpt") or "").strip(),
            published=date_of(p.get("publishedDate")),
            categories=[c.get("label") if isinstance(c, dict) else c
                        for c in (p.get("categories") or [])],
            tags=p.get("hashtags") or p.get("tags") or [],
            url=p.get("postPageUrl"),
            cover=gallery(p, "coverImage"),
            plain=(p.get("plainContent") or "").strip(),
        ))
    out.sort(key=lambda r: r["published"] or "", reverse=True)
    return out


def write(path, data):
    dest = os.path.join(ROOT, "content", path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    works = build_works()
    shows = build_exhibitions()
    for w in works:
        write(f"works/{w['slug']}.json", w)
    for s in shows:
        write(f"exhibitions/{s['slug']}.json", s)
    write("about.json", build_about())
    write("press.json", build_press())
    write("works/_all.json", works)
    write("exhibitions/_all.json", shows)

    print(f"works        {len(works)}")
    for w in works:
        print(f"  {w['year'] or '----'}  {w['slug']:26} {len(w['images']):2} img  "
              f"zh={'y' if w['title_zh'] else '-'}  "
              f"dim={'y' if w['dimensions'] else '-'}  mat={w['material'] or '-'}")
    print(f"\nexhibitions  {len(shows)}")
    for s in shows:
        print(f"  {s['year'] or '----'}  {s['slug']:38} {len(s['images']):2} img  "
              f"zh={'y' if s['title_zh'] else '-'}  {'SOLO' if s['solo'] else ''}")


if __name__ == "__main__":
    main()
