#!/usr/bin/env python3
"""Force the Spell Summary print pack (#gm-v40-print-stack) to plain
single-colour ink when printed, without touching the Book of Shadows /
Journal colour cover print (.bos-cover), which is intentionally decorative.

The Summary print pack always printed in plain black-on-white until a
later Android print pipeline change stopped stripping the app's own
decorative parchment/gold theme out of the captured print HTML. This adds
that stripping back as a dedicated @media print rule scoped only to the
Summary print container.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_summary_print_monochrome.py index.html")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

old = (
    "body.gm-v40-print-all #gm-v40-print-stack .gm-v40-print-page:last-child"
    "{page-break-after:auto;break-after:auto;}\\n"
    "        body.gm-v40-print-lite #gm-print-nav{display:none!important;}\\n"
    "      }"
)
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected exactly one print-stack closing gate, found {count}")

new = old.rstrip("}") + (
    "\\n        /* Summary print pack must stay plain single-colour ink, unlike the BoS colour cover. */\\n"
    "        #gm-v40-print-stack .true-page{background:#fff!important;box-shadow:none!important;border-color:#000!important;}\\n"
    "        #gm-v40-print-stack .true-page:before,#gm-v40-print-stack .true-page:after{display:none!important;background:none!important;content:none!important;}\\n"
    "        #gm-v40-print-stack .true-box,#gm-v40-print-stack .ac{background:#fff!important;border-color:#000!important;}\\n"
    "        #gm-v40-print-stack *{color:#000!important;background-image:none!important;text-shadow:none!important;}\\n"
    "      }"
)
text = text.replace(old, new, 1)

# Guardrails: must not have touched the BoS colour cover.
if text.count("gm-v40-print-stack *{color:#000!important") != 1:
    raise SystemExit("unexpected monochrome rule count")
if ".bos-cover{" not in text:
    raise SystemExit("bos-cover rule missing after patch (unexpected file shape)")

path.write_text(text, encoding="utf-8")
print("Summary print pack forced to plain single-colour ink (BoS/Journal cover left untouched).")
