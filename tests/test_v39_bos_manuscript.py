#!/usr/bin/env python3
"""Contract tests for V39: presentation only, fail closed, no key/storage mutations."""
import importlib.util
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("patch_v39", root / "tools/patch_v39_bos_manuscript.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
css = (root / "tools/bos_manuscript_v39.css").read_text(encoding="utf-8")
assert "url(" not in css.lower()
assert "@import" not in css.lower()
assert "<script" not in css.lower()
assert ".gmChapterHeroGlyph{display:none!important}" in css
assert "gmBosTocChapterText" in css
assert "gmChapterCardName" in css
assert "gmChapterCardGrid" in css

script = ("const existingBookKey = 'gm_scribe_bos_selected_items_v1';"
          "const nestedPrint = '<html><head>Print</head><body>Book</body></html>';")
page = ('<!doctype html><html><head><meta charset="utf-8"></head>'
        '<body><div class="gmBosTocChapterText"></div>'
        '<div class="gmChapterHero"><div class="gmChapterCardGrid"></div></div>'
        '<button data-chapter-jump="spell-list">Open chapter</button>'
        + mod.OLD_LABEL + '<script>' + script + '</script></body></html>')

for anchor in mod.ANCHORS:
    source = "KEEP_OUTER_PREFIX\n" + anchor + json.dumps(page, ensure_ascii=False) + ";\nKEEP_OUTER_SUFFIX"
    patched = mod.patch(source, css)
    start, decoded, consumed = mod.scribe_location(patched)
    assert decoded.count(mod.STYLE_ID) == 1
    assert mod.NEW_LABEL in decoded
    assert mod.OLD_LABEL not in decoded
    assert script in decoded
    assert 'data-chapter-jump="spell-list"' in decoded
    assert "KEEP_OUTER_PREFIX" in patched and patched.endswith("KEEP_OUTER_SUFFIX")
    assert "</script>" not in patched[start:start+consumed]
    assert "gm_scribe_bos_selected_items_v1" in decoded
    try:
        mod.patch(patched, css)
        raise AssertionError("Duplicate injection should fail")
    except ValueError:
        pass

try:
    mod.patch("no scribe anchor", css)
    raise AssertionError("Missing source should fail")
except ValueError:
    pass

try:
    mod.patch("PAGES.scribe = "+json.dumps(page.replace(mod.OLD_LABEL,"unexpected"))+";", css)
    raise AssertionError("Changed source should fail")
except ValueError:
    pass

print("PASS: V39 preserves navigation, script, identifiers, body data and source boundaries")
