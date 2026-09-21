# Partials

Every page carries the same header markup. Nothing enforces that at runtime —
the site is plain static HTML — so this file is the reference copy. If you
change the navigation, change it here and in every page, or rerun
`python3 tools/stamp.py`.

`tools/check_site.py` fails if any page's header drifts from the others, which
is the practical safety net. One page is exempt and named in that script:
`stage/index.html`, the alternative home, carries its own header laid over the
image. A nav change has to be made there by hand as well — it is the only
place the six links are duplicated outside this partial.

## Header

One variant is intentional: the current page's nav link carries
`aria-current="page"`.

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

## Changing the navigation by hand

Add a link to every page in one pass:

```bash
# from the repo root
grep -rl '<nav class="hdr__nav' --include=index.html . | \
  xargs sed -i '' 's|<a href="/about/">|<a href="/new-page/">New</a>\n    <a href="/about/">|'
python3 tools/check_site.py     # confirms all 55 headers still match
```

The `sed` only works because the header is byte-identical everywhere. Keep it
that way.

## Closing markup

Every page ends the same way:

```html
</div>
</body>
</html>
```

There is no footer. The spec removes it: "Nothing else, no footer nav."
