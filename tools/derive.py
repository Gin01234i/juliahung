#!/usr/bin/env python3
"""Turn the archived originals into the images the site actually ships.

The archive holds 6000px, multi-megabyte masters. The largest slot on the
site is 8 of 12 columns inside a 1180px page — about 770 CSS px, so 1600px
covers a 2x display and 2400px would be dead weight on every page load.

Emits, per selected image, four files under assets/img/:

    <year>_<slug>_<nn>-800.jpg / .webp
    <year>_<slug>_<nn>-1600.jpg / .webp

Spec naming: year_work-slug_nn. Filenames are never displayed; alt text and
captions come from the record.

Usage:  python3 tools/derive.py [--force]
"""
import json, os, re, sys, glob
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_archive", "originals")
OUT = os.path.join(ROOT, "assets", "img")
WIDTHS = (800, 1600)
JPEG_Q = 80
WEBP_Q = 80

sel = json.load(open(os.path.join(ROOT, "content", "selection.json"),
                     encoding="utf-8"))


def safe_year(rec):
    return re.sub(r"[^0-9]", "", (rec.get("year") or "nd"))[:4] or "nd"


def derive(src_id, stem, force):
    """Write the four derivatives for one original. Returns the srcset stem."""
    src = os.path.join(SRC, src_id)
    if not os.path.exists(src):
        print(f"  ! missing original {src_id}", file=sys.stderr)
        return None

    made = []
    for w in WIDTHS:
        jpg = os.path.join(OUT, f"{stem}-{w}.jpg")
        webp = os.path.join(OUT, f"{stem}-{w}.webp")
        if not force and os.path.exists(jpg) and os.path.exists(webp):
            made.append(w)
            continue
        with Image.open(src) as im:
            # Honour EXIF orientation, then drop the tag so viewers agree.
            im = ImageOps.exif_transpose(im)
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            if max(im.size) > w:
                scale = w / max(im.size)
                im = im.resize((max(1, round(im.width * scale)),
                                max(1, round(im.height * scale))),
                               Image.LANCZOS)
            os.makedirs(os.path.dirname(jpg), exist_ok=True)
            im.save(jpg, "JPEG", quality=JPEG_Q, optimize=True,
                    progressive=True, subsampling=1)
            im.save(webp, "WEBP", quality=WEBP_Q, method=5)
        made.append(w)
    return stem if made else None


def process(kind, slugs, limit, force):
    index = {}
    for slug in slugs:
        path = os.path.join(ROOT, "content", kind, f"{slug}.json")
        if not os.path.exists(path):
            print(f"  ! no record for {kind}/{slug}", file=sys.stderr)
            continue
        rec = json.load(open(path, encoding="utf-8"))
        year = safe_year(rec)
        cover = rec.get("cover_image") or {}
        if cover.get("media"):
            derive(cover["media"], f"{kind}/{slug}/{year}_{slug}_cover", force)
        picked = []
        image_limit = rec.get("image_limit", limit)
        for n, img in enumerate((rec.get("images") or [])[:image_limit], 1):
            stem = f"{kind}/{slug}/{year}_{slug}_{n:02d}"
            if derive(img["media"], stem, force):
                picked.append(dict(
                    stem=stem,
                    width=img.get("width"),
                    height=img.get("height"),
                    caption=img.get("caption", ""),
                    parsed=img.get("parsed", {}),
                ))
        index[slug] = picked
        print(f"  {kind}/{slug:34} {len(picked)} images")
    return index


def main():
    force = "--force" in sys.argv
    os.makedirs(OUT, exist_ok=True)

    works = process("works", sel["works_featured"],
                    sel["max_images_work"], force)

    ex_slugs = sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(ROOT, "content", "exhibitions", "*.json"))
        if not os.path.basename(p).startswith("_"))
    shows = process("exhibitions", ex_slugs,
                    sel["max_images_exhibition"], force)

    with open(os.path.join(ROOT, "content", "images.json"), "w",
              encoding="utf-8") as f:
        json.dump({"works": works, "exhibitions": shows}, f,
                  ensure_ascii=False, indent=2)

    n = sum(len(v) for v in works.values()) + sum(len(v) for v in shows.values())
    total = sum(os.path.getsize(p)
                for p in glob.glob(os.path.join(OUT, "**", "*.*"), recursive=True))
    print(f"\n{n} images -> {n * 4} files, {total / 1e6:.1f} MB in assets/img")


if __name__ == "__main__":
    main()
