#!/usr/bin/env python3
"""Fail-closed V45 book typesetting regression checks."""
import importlib.util,json
from pathlib import Path
base=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v45",base/"tools/patch_v45_bos_manuscript.py")
v45=importlib.util.module_from_spec(spec);spec.loader.exec_module(v45)
css=(base/"tools/bos_manuscript_v45.css").read_text(encoding="utf-8")
assert "gmBosContentsActions" in css
assert "gmBosTocItemLabelBtn" in css
assert "gmChapterCard:only-child" in css
assert "gmBosTocSelect input[type=checkbox]" in css
assert "content:'×'" not in css, "Brown X button must not return"
assert "rubricated pen-ticks" in css
assert "V46: manuscript composition" in css
assert "input[type=checkbox]:checked{background:transparent" in css
assert "border-left:.52mm solid #934636" in css
assert "background:transparent!important;border-color:#8d493c" in css
assert "url(" not in css.lower() and "@import" not in css.lower()
assert "gm-bos-compositor-folio-v45" not in css
markup=('<html><head><style id="gm-bos-manuscript-v39"></style></head>'
'<body>gmBosChapterContentsPage gmBosTocChapterText gmChapterOpening gmChapterCardGrid '
'gmChapterCardName gmBosTocItemLabelBtn GM_INK_A4_SVG_PAINT_PAGINATION_V43 '
'<button data-chapter-jump="spell-list">Open</button><input type="checkbox" data-chapter-check="spell-list">'
'<script>function gmBosChapterTargetLabel(p,c,seq){ '+v45.FALLBACK+' }</script>'
'<script>'+v45.TITLE+'; '+v45.DEST+';</script></body></html>')
source='ORIGINAL_ANDROID '+v45.ANCHORS[0]+json.dumps(markup)+';KEEP_ANDROID_BYTES'
out=v45.patch(source,css)
start=out.index(v45.ANCHORS[0])+len(v45.ANCHORS[0])
changed,n=json.JSONDecoder().raw_decode(out[start:])
assert changed.count(v45.MARK)==1
assert v45.NEW_TITLE in changed
assert v45.NEW_FALLBACK in changed
assert v45.ENTRY in changed
assert "GM_INK_A4_SVG_PAINT_PAGINATION_V43" in changed
assert "data-chapter-check" in changed and 'data-chapter-jump="spell-list"' in changed
assert out.startswith("ORIGINAL_ANDROID ") and out.endswith(";KEEP_ANDROID_BYTES")
revert=(changed.replace('<style id="'+v45.MARK+'">'+css.strip()+'</style>','',1)
             .replace(v45.NEW_TITLE,v45.TITLE,1)
             .replace(v45.NEW_FALLBACK,v45.FALLBACK,1)
             .replace(v45.ENTRY,v45.DEST,1))
assert revert==markup,"Anything beyond manuscript styling and three display labels changed"
for candidate in (out,source.replace('gmBosTocItemLabelBtn','unknown')):
 try:v45.patch(candidate,css)
 except ValueError:pass
 else:raise AssertionError("Fail-closed patch accepted duplicate or missing source")
print("PASS V45: chapter/TOC visuals and one-spell label; binder, events and outer app unchanged")
