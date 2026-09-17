#!/usr/bin/env python3
"""Archive the live Wix site before the CDN images go away.

Reads seo/url-map.csv, fetches every KEEP url, and writes:

    _archive/html/<key>.html        raw response, so re-parsing needs no network
    _archive/originals/<id>.<ext>   full-resolution source images
    content/<kind>/<slug>.json      extracted text + ordered image ids

content/ is the authoring source for the hand-written pages. Nothing here runs
at request time; the built site has no dependency on this script.

Usage:  python3 tools/scrape.py [--skip-images] [--only PREFIX]
"""
import csv, html, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCH = os.path.join(ROOT, "_archive")
BASE = "https://www.jujuhung.com"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}

# Chrome in the footer/header of every page. Stripped so the extracted text is
# just the record. Order matters: longest first.
CHROME = [
    "top of page", "bottom of page", "JULIA  HUNG", "JULIA HUNG",
    "Thanks for subscribing!", "Subscribe", "Sign up",
    "To play, press and hold the enter key. To stop, release the enter key.",
    "English | 中文", "EN | 中文",
    "Home", "About", "Artwork", "Exhibitions", "Press", "Contact",
]

MEDIA_RE = re.compile(
    r"https://static\.wixstatic\.com/media/"
    r"([A-Za-z0-9_]+~mv2\.(?:jpg|jpeg|png|webp|gif))", re.I)

# The site logo and other furniture live under a different Wix account prefix
# than the artwork media; excluding by id prefix is the only reliable filter.
FURNITURE_PREFIXES = ("ccce62_",)


def fetch(url, tries=3):
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except Exception as e:
            if n == tries - 1:
                print(f"  ! {url} -> {e}", file=sys.stderr)
                return None
            time.sleep(2 * (n + 1))


def page_text(raw):
    """Visible text of the content region, with site chrome removed."""
    s = raw[raw.find("<body"):]
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S)
    # Keep block boundaries so paragraphs survive as separate lines.
    s = re.sub(r"</(p|div|h[1-6]|li|tr|section|span)>", "\n", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    lines = []
    for ln in s.split("\n"):
        ln = re.sub(r"[ \t ]+", " ", ln).strip()
        if ln and ln not in CHROME:
            lines.append(ln)
    # Collapse the runs of repeated nav items that survive as fragments.
    out = []
    for ln in lines:
        if out and out[-1] == ln:
            continue
        out.append(ln)
    return out


def meta(raw, key):
    m = re.search(r'<meta[^>]+(?:name|property)="%s"[^>]*content="([^"]*)"'
                  % re.escape(key), raw)
    return html.unescape(m.group(1)) if m else None


def media_ids(raw):
    """Ordered, de-duplicated artwork media ids for one page."""
    seen, out = set(), []
    for mid in MEDIA_RE.findall(raw):
        if mid in seen or mid.startswith(FURNITURE_PREFIXES):
            continue
        seen.add(mid)
        out.append(mid)
    return out


def keep_rows():
    with open(os.path.join(ROOT, "seo", "url-map.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["action"].startswith("KEEP"):
                yield row["path_decoded"]


def kind_and_slug(path):
    p = path.strip("/")
    if not p:
        return "page", "home"
    for prefix, kind in (("artworks/", "works"), ("exhibitions/", "exhibitions"),
                         ("post/", "press")):
        if p.startswith(prefix):
            return kind, p[len(prefix):]
    if p in ("artworks", "exhibitions", "blog"):
        return "index", p
    return "page", p.replace("/", "_")


def main():
    skip_images = "--skip-images" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    os.makedirs(f"{ARCH}/html", exist_ok=True)
    os.makedirs(f"{ARCH}/originals", exist_ok=True)

    paths = [p for p in keep_rows() if not only or p.startswith(only)]
    print(f"{len(paths)} KEEP urls")

    all_media, records = set(), []
    for i, path in enumerate(paths, 1):
        kind, slug = kind_and_slug(path)
        key = f"{kind}__{slug}".replace("/", "_")
        cached = f"{ARCH}/html/{key}.html"

        if os.path.exists(cached) and os.path.getsize(cached) > 1000:
            raw = open(cached, encoding="utf-8", errors="replace").read()
        else:
            url = BASE + urllib.parse.quote(path, safe="/")
            body = fetch(url)
            if not body:
                continue
            raw = body.decode("utf-8", "replace")
            open(cached, "w", encoding="utf-8").write(raw)
            time.sleep(0.4)

        rec = {
            "path": path,
            "kind": kind,
            "slug": slug,
            "title": (re.search(r"<title>(.*?)</title>", raw, re.S).group(1).strip()
                      if "<title>" in raw else ""),
            "description": meta(raw, "description"),
            "og_image": meta(raw, "og:image"),
            "images": media_ids(raw),
            "text": page_text(raw),
        }
        records.append(rec)
        all_media.update(rec["images"])

        out = os.path.join(ROOT, "content", kind)
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, f"{slug}.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        print(f"[{i:3}/{len(paths)}] {path}  ({len(rec['images'])} img, "
              f"{len(rec['text'])} lines)")

    with open(os.path.join(ROOT, "content", "_index.json"), "w",
              encoding="utf-8") as f:
        json.dump([{k: r[k] for k in ("path", "kind", "slug", "title", "images")}
                   for r in records], f, ensure_ascii=False, indent=2)

    if skip_images:
        print(f"\n{len(all_media)} images found, skipped (--skip-images)")
        return

    print(f"\ndownloading {len(all_media)} originals")
    for i, mid in enumerate(sorted(all_media), 1):
        dest = f"{ARCH}/originals/{mid}"
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            continue
        # Stripping the /v1/<transform>/ segment yields the untouched upload.
        body = fetch(f"https://static.wixstatic.com/media/{mid}")
        if body:
            open(dest, "wb").write(body)
            print(f"  [{i:3}/{len(all_media)}] {mid}  {len(body)//1024}kB")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
