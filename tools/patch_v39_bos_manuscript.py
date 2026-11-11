#!/usr/bin/env python3
"""Patch ONLY the embedded Scribe Book of Shadows presentation.
Preserves the Android shell, signing, permissions, data, JS handlers and keys.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

STYLE_ID = "gm-bos-manuscript-v39"
ANCHORS = ("function __gmLazyScribeSrc(){return ", "PAGES.scribe = ")
OLD_LABEL = "<span>Paths through this chapter</span>"
NEW_LABEL = "<span>Entries in this chapter</span>"

def scribe_location(source: str) -> tuple[int, str, int]:
    found = [(a, source.count(a)) for a in ANCHORS]
    active = [a for a, count in found if count]
    if len(active) != 1 or source.count(active[0]) != 1:
        raise ValueError(f"Expected exactly one Scribe embedding: {found}")
    pos = source.index(active[0]) + len(active[0])
    scribe, consumed = json.JSONDecoder().raw_decode(source[pos:])
    if not isinstance(scribe, str):
        raise ValueError("Embedded Scribe is not a JSON string")
    return pos, scribe, consumed

def patch(source: str, css: str) -> str:
    start, page, consumed = scribe_location(source)
    if STYLE_ID in source:
        raise ValueError("V39 is already present; duplicate style injection refused")
    for expected in ("gmBosTocChapterText", "gmChapterCardGrid", "gmChapterHero"):
        if expected not in page:
            raise ValueError(f"V38 Book of Shadows contract missing: {expected}")
    first_head = page.find("</head>")
    first_body = page.find("<body")
    # Printed documents and templates inside Scribe may also contain </head>.
    # Inject only at the real outer Scribe head, before its first <body>.
    if first_head < 0 or first_body < 0 or first_head > first_body:
        raise ValueError("Could not identify the outer Scribe document head")
    if page.count(OLD_LABEL) != 1:
        raise ValueError(f"Expected one V38 chapter caption, found {page.count(OLD_LABEL)}")
    if "<script" in css.lower() or "@import" in css.lower() or "url(" in css.lower():
        raise ValueError("Style must not load script or remote resources")
    css = css.strip()
    original = page
    style = '<style id="' + STYLE_ID + '">' + css + '</style>'
    page = page.replace(OLD_LABEL, NEW_LABEL, 1)
    page = page.replace("</head>", style + "</head>", 1)
    if page.replace(style, "", 1).replace(NEW_LABEL, OLD_LABEL, 1) != original:
        raise ValueError("Unexpected modification outside CSS and chapter caption")
    encoded = json.dumps(page, ensure_ascii=False, separators=(",", ":"))
    encoded = re.sub(r"</script", r"<\/script", encoded, flags=re.I)
    output = source[:start] + encoded + source[start + consumed:]
    if output.count(STYLE_ID) != 1:
        raise ValueError("Nonunique style identifier")
    if output[:start] != source[:start] or output[start + len(encoded):] != source[start + consumed:]:
        raise ValueError("Outer application changed outside the Scribe literal")
    return output

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_v39_bos_manuscript.py INPUT.html OUTPUT.html")
    src, dst = map(Path, sys.argv[1:])
    css = Path(__file__).with_name("bos_manuscript_v39.css").read_text(encoding="utf-8")
    output = patch(src.read_text(encoding="utf-8"), css)
    dst.write_text(output, encoding="utf-8")
    print("V39 BoS manuscript styling applied; no Android code, identifiers or keys modified.")

if __name__ == "__main__":
    main()
