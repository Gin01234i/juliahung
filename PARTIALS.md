# Partials

Every page carries the same header markup. Nothing enforces that at runtime —
the site is plain static HTML — so this file is the reference copy. If you
change the navigation, change it here and in every page, or rerun
`python3 tools/stamp.py`.

`tools/check_site.py` fails if any page's header drifts from the others, which
is the practical safety net. One page is exempt and named in that script:
`index.html`, the Stage home, carries its own header laid over the
image. A nav change has to be made there by hand as well — it is the only
place the six links are duplicated outside this partial.

## Header

This is the header as it is written in `tools/stamp.py`, with root-absolute
paths:

```html
<header class="hdr">
  <a class="hdr__mark" href="/">Julia Hung</a>
  <nav class="hdr__nav t-meta" aria-label="Main">
    <a href="/artworks/">Works</a>
    <a href="/exhibitions/">Exhibitions</a>
    <a href="/news/">News</a>
    <a href="/blog/">Press</a>
    <a href="/about/">About</a>
    <a href="/contact/">Contact</a>
  </nav>
</header>
```

On disk every path is relative to the page holding it, so the site serves
from a project subpath as well as from the domain root — see
`tools/relativize.py`. The same header two directories down reads:

```html
    <a href="../../artworks/">Works</a>
```

Two variants are therefore intentional: the `../` depth, and the current
page's nav link carrying `aria-current="page"`. `tools/check_site.py` reads
the links back as site paths before comparing, so it still sees one header.

## Changing the navigation by hand

Change `NAV` in `tools/stamp.py` and rerun it — that is the one-pass route,
and it keeps the relative depths right by construction.

By hand, the `../` prefix has to be carried through. Capture it:

```bash
# from the repo root
grep -rl '<nav class="hdr__nav' --include=index.html . | \
  xargs sed -i '' -E 's|<a href="((\.\./)*)about/">|<a href="\1new-page/">New</a>\
    <a href="\1about/">|'
python3 tools/check_site.py     # confirms all 55 headers still match
```

The `sed` only works because the header is identical everywhere but for that
prefix — zero `../` at the root, two on a work page. Keep it that way.
`--include=index.html` misses `404.html`; name it on the `sed` as well.

## Closing markup

Every page ends the same way:

```html
</div>
</body>
</html>
```

There is no footer. The spec removes it: "Nothing else, no footer nav."
