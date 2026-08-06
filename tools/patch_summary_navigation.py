#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)


def patch_spellbuilder(page: str) -> str:
    # Remove the old visible V79 Summary styling. Its three-page Lite print-data
    # builder is retained below, but V79 must no longer own the visible controls.
    style_re = re.compile(
        r'\n?<!-- V79 single-owner repair:.*?<style id="gm-v79-style">.*?</style>\s*',
        re.S,
    )
    page, count = style_re.subn("\n", page, count=1)
    if count != 1:
        raise SystemExit(
            f"old V79 Summary style: expected exactly 1 block, found {count}"
        )

    start = page.find('<script id="gm-v79-owner">')
    if start < 0:
        raise SystemExit("gm-v79-owner script not found")
    end = page.find("</script>", start)
    if end < 0:
        raise SystemExit("gm-v79-owner closing script not found")
    end += len("</script>")

    block = page[start:end]
    tail_start = block.find("function ownOneButton(){")
    if tail_start < 0:
        raise SystemExit("gm-v79 old navigation owner not found")

    new_block = block[:tail_start] + """/* V79 remains only as the Lite three-page print-data builder.
   It no longer owns, clears, styles or recreates the visible Summary controls.
   The canonical Summary navigation is the only visible owner. */
window.gmV79LitePrint=printLiteThree;
})();
</script>"""
    page = page[:start] + new_block + page[end:]

    page = replace_once(
        page,
        "qa('[data-gm-gather-nav],#gather-spell-btn,.gm-v79-lite-gather')",
        "qa('[data-gm-gather-nav],#gather-spell-btn')",
        "remove stale V79 gather selector",
    )

    forbidden = [
        "PRINT LITE PACK",
        "✦ GATHER SPELL ✦",
        "gm-v79-lite-pack",
        "data-gm-v79-current-lite-nav",
    ]
    remains = [item for item in forbidden if item in page]
    if remains:
        raise SystemExit(
            "old V79 visible Summary controls remain: " + ", ".join(remains)
        )

    required = [
        "window.gmV79LitePrint=printLiteThree",
        "data-gm-a4-page",
        "data-gm-a4-pack",
        "data-gm-gather-nav",
    ]
    missing = [item for item in required if item not in page]
    if missing:
        raise SystemExit(
            "required current Summary route missing: " + ", ".join(missing)
        )
    return page


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: patch_summary_navigation.py INPUT.html OUTPUT.html"
        )

    src, dst = map(Path, sys.argv[1:])
    text = src.read_text(encoding="utf-8")
    marker = "const PAGES = "
    start = text.index(marker) + len(marker)
    pages, used = json.JSONDecoder().raw_decode(text[start:])
    end = start + used

    pages["spellBuilder"] = patch_spellbuilder(pages["spellBuilder"])

    encoded = json.dumps(pages, ensure_ascii=False, separators=(",", ":"))
    encoded = re.sub(r"</script", r"<\\/script", encoded, flags=re.IGNORECASE)
    dst.write_text(text[:start] + encoded + text[end:], encoding="utf-8")
    print(
        "Summary navigation patch passed: old V79 controls removed; "
        "canonical controls retained."
    )


if __name__ == "__main__":
    main()
