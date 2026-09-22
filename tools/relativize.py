#!/usr/bin/env python3
"""Make every internal URL relative to the page that carries it.

The site has to serve from two different roots: https://jujuhung.com/ when it
is live, and https://<user>.github.io/juliahung/ while it is being reviewed.
A root-absolute `/assets/css/site.css` only works on the first — under a
project path it resolves to github.io's own root and 404s. A page-relative
`../../assets/css/site.css` works on both, with no build step, no <base> tag
and no JavaScript.

So: `/assets/...` becomes `../../assets/...` on a page two directories deep,
and stays `assets/...` at the root. Absolute URLs to jujuhung.com — canonical,
og:url, og:image, the JSON-LD — are left alone on purpose: those name the
production page and must not follow the preview host.

Usage:  python3 tools/relativize.py          # rewrite every page in place
        python3 tools/relativize.py --check  # report, change nothing
"""
import glob, os, posixpath, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 404.html is served for any missing path, so the browser's location — and
# with it the meaning of "relative" — is whatever was typed. It resolves its
# own root instead; see the script in its <head>.
SKIP = {"404.html"}

URL_ATTR = re.compile(r'\b(href|src)="(/[^/"][^"]*|/)"')
# `imagesrcset` on a <link rel=preload> is a srcset too — stage/ uses one.
SRCSET_ATTR = re.compile(r'\b((?:image)?srcset)="([^"]*)"')


def depth(page):
    """Directories between the site root and the page. index.html -> 0."""
    return page.replace(os.sep, "/").count("/")


def rel(url, d):
    """/assets/x.css at depth 2 -> ../../assets/x.css"""
    out = "../" * d + url.lstrip("/")
    return out or "./"


def relativize(html, d):
    """Rewrite the root-absolute internal URLs in one page. Idempotent."""
    html = URL_ATTR.sub(lambda m: f'{m.group(1)}="{rel(m.group(2), d)}"', html)

    def srcset(m):
        out = []
        for cand in m.group(2).split(","):
            cand = cand.strip()
            if not cand:
                continue
            url, _, desc = cand.partition(" ")
            if url.startswith("/") and not url.startswith("//"):
                url = rel(url, d)
            out.append(f"{url} {desc}".strip())
        return f'{m.group(1)}="' + ", ".join(out) + '"' 

    return SRCSET_ATTR.sub(srcset, html)


def absolutize(url, page):
    """The inverse, for the checkers: a page's link as a site path."""
    if url.startswith("/"):
        return url
    return posixpath.normpath(
        posixpath.join("/" + posixpath.dirname(page.replace(os.sep, "/")), url)
    ) + ("/" if url.endswith("/") else "")


def pages():
    return sorted(
        f for f in glob.glob("**/*.html", recursive=True)
        if not f.startswith(("_archive", "tools")))


def main():
    os.chdir(ROOT)
    check = "--check" in sys.argv
    changed = []
    for f in pages():
        if f in SKIP:
            continue
        before = open(f, encoding="utf-8").read()
        after = relativize(before, depth(f))
        if after != before:
            changed.append(f)
            if not check:
                open(f, "w", encoding="utf-8").write(after)
    verb = "would rewrite" if check else "rewrote"
    print(f"{verb} {len(changed)} of {len(pages()) - len(SKIP)} pages")
    for f in changed[:10]:
        print(f"  {f}")
    if len(changed) > 10:
        print(f"  … and {len(changed) - 10} more")
    return 1 if (check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
