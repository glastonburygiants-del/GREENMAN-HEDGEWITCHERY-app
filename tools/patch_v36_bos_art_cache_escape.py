#!/usr/bin/env python3
"""Fix the APK-only Book of Shadows artwork raster cache.

Real-device diagnostics from the installed Action 166 build repeatedly report
artCache: 0. Inspection of that exact APK shows why.

The Scribe source contains this guard in gmBosArtCachePut():

    !/^data:image//i.test(String(url||''))

That is valid JavaScript syntax, but it is NOT the intended regular expression.
At runtime it is parsed as a regex followed by division through the identifier
`i`, so calling gmBosArtCachePut() throws "ReferenceError: i is not defined".

Why the plain HTML build can still look much faster:
- Browser fallback rasterisation returns blob: URLs and therefore does not call
  gmBosArtCachePut() for those prepared SVGs.
- The APK path deliberately returns data:image/... URLs so the prepared artwork
  can survive the isolated A4 capture frame. That path DOES call
  gmBosArtCachePut(), hits the malformed guard, and the surrounding rasteriser
  catches the exception and returns false.
- Result: the prepared PNG is discarded, the SVG remains live for html2canvas
  to process again, and the bind-wide artRasterCache never fills.

This patch changes only the escaped slash in the OUTER reconstructed HTML so
that the decoded Scribe script contains the intended:

    /^data:image\//i

No binder flow, artwork, dimensions, JPEG quality, page layout, native storage,
Rune Hall, Crystal Tumbler, or UI code is changed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


BROKEN_RAW = "!/^data:image//i.test(String(url||''))"
# current.html stores Scribe as a JavaScript/JSON string. Two backslashes in
# the outer file decode to one backslash in the inner Scribe JavaScript.
FIXED_RAW = r"!/^data:image\\//i.test(String(url||''))"
FIXED_INNER = r"!/^data:image\//i.test(String(url||''))"


def extract_scribe(text: str) -> str:
    eager = "PAGES.scribe = "
    lazy = "function __gmLazyScribeSrc(){return "
    if eager in text:
        pos = text.index(eager) + len(eager)
    elif lazy in text:
        pos = text.index(lazy) + len(lazy)
    else:
        raise SystemExit("PAGES.scribe not found in eager or lazy form")
    value, _ = json.JSONDecoder().raw_decode(text[pos:])
    if not isinstance(value, str):
        raise SystemExit("Decoded PAGES.scribe value is not text")
    return value


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_v36_bos_art_cache_escape.py INPUT.html OUTPUT.html")

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    text = src.read_text(encoding="utf-8")

    broken_count = text.count(BROKEN_RAW)
    fixed_count = text.count(FIXED_RAW)
    if broken_count != 1:
        raise SystemExit(
            f"BoS art-cache broken guard: expected exactly 1 occurrence, found {broken_count}"
        )
    if fixed_count:
        raise SystemExit(
            f"BoS art-cache fixed guard already present {fixed_count} time(s)"
        )

    patched = text.replace(BROKEN_RAW, FIXED_RAW, 1)

    if patched.count(BROKEN_RAW):
        raise SystemExit("Broken BoS art-cache guard survived")
    if patched.count(FIXED_RAW) != 1:
        raise SystemExit("Fixed outer BoS art-cache guard is missing or duplicated")

    scribe = extract_scribe(patched)
    if BROKEN_RAW in scribe:
        raise SystemExit("Broken guard survived in decoded Scribe source")
    if scribe.count(FIXED_INNER) != 1:
        raise SystemExit(
            "Decoded Scribe source does not contain exactly one corrected data:image regex"
        )
    if "function gmBosArtCachePut(binding,key,url)" not in scribe:
        raise SystemExit("gmBosArtCachePut function is missing")
    if "artRasterCache:new Map()" not in scribe:
        raise SystemExit("Bind-wide artRasterCache initialisation is missing")
    if "artCache:binding&&binding.artRasterCache?binding.artRasterCache.size:0" not in scribe:
        raise SystemExit("BoS art-cache diagnostics marker is missing")

    out.write_text(patched, encoding="utf-8")
    print("BoS APK artwork cache repaired: data:image raster results can now enter the bind-wide cache.")


if __name__ == "__main__":
    main()
