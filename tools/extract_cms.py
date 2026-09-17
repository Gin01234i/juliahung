#!/usr/bin/env python3
"""Pull the embedded Wix CMS records out of the archived HTML.

Every Wix page ships its datasets inline as `dataStore.recordsByCollectionId`.
That blob carries far more than the rendered page shows — notably the full
image gallery for each record, and each image's `description`, which is where
the material and dimensions live ("Enamelled copper wire, H26 x W22 x D21 cm,
2023"). Those are the Meta block fields the rendered site never displays.

Writes content/cms/<Collection>.json — one merged record set per collection,
deduplicated by _id across every archived page.

Usage:  python3 tools/extract_cms.py
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "_archive", "html")
OUT = os.path.join(ROOT, "content", "cms")

KEY = '"recordsByCollectionId":'


def balanced(s, start):
    """Slice the JSON object beginning at s[start] == '{', respecting strings."""
    depth, i, in_str, esc = 0, start, False, False
    while i < len(s):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
        i += 1
    return None


def records_in(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    i = raw.find(KEY)
    if i < 0:
        return {}
    blob = balanced(raw, raw.index("{", i + len(KEY)))
    if not blob:
        return {}
    # The blob sits inside a JS string literal in the page, already
    # JSON-escaped; json.loads handles it directly.
    try:
        return json.loads(blob)
    except json.JSONDecodeError as e:
        print(f"  ! {os.path.basename(path)}: {e}", file=sys.stderr)
        return {}


def main():
    merged = {}
    files = sorted(f for f in os.listdir(HTML) if f.endswith(".html"))
    for f in files:
        for coll, items in records_in(os.path.join(HTML, f)).items():
            merged.setdefault(coll, {}).update(items)

    os.makedirs(OUT, exist_ok=True)
    for coll, items in sorted(merged.items()):
        dest = os.path.join(OUT, coll.replace("/", "-") + ".json")
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(list(items.values()), fh, ensure_ascii=False, indent=2)
        fields = sorted({k for it in items.values() for k in it})
        print(f"{coll:24} {len(items):4} records  {len(fields)} fields")
        print(f"    {', '.join(fields)}")


if __name__ == "__main__":
    main()
