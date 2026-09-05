#!/usr/bin/env python3
"""Spell Builder's own A4 Pack print (physicalPrint, used by the "A4 Pack"
nav button) computes the correct fit scale for each sheet, then throws that
calculation away with a hard Math.max(.38, sc) floor. Any page that
genuinely needs to shrink below 38% to fit (a long Summary page 2 item
list, for example) gets stuck at 38% and bleeds off the sheet - this is the
same pattern already fixed in fitFlatPages/fitGrimoirePages, but living in
a completely separate function in the spellBuilder page, so that earlier
fix never touched it.
"""
from pathlib import Path
import json, re, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: repair_pack_scale_floor.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')
marker = 'const PAGES = '
start = s.index(marker) + len(marker)
obj, end = json.JSONDecoder().raw_decode(s[start:])
raw = s[start:start + end]

page_before = obj.get('spellBuilder')
if not isinstance(page_before, str):
    raise SystemExit('missing PAGES.spellBuilder')

old = "co.style.transform='scale('+Math.max(.38,sc).toFixed(5)+')'"
if page_before.count(old) != 1:
    raise SystemExit('physicalPrint scale-floor anchor count was ' + str(page_before.count(old)) + ', expected 1')

# Losing content is worse than small text: only a sanity backstop against a
# zero/negative scale remains, not a "reasonable minimum" that can still
# force overflow on unusually long pages.
new = "co.style.transform='scale('+Math.max(.05,sc).toFixed(5)+')'"
page_after = page_before.replace(old, new, 1)

if page_after == page_before:
    raise SystemExit('no change applied to spellBuilder')
if 'Math.max(.38,sc)' in page_after:
    raise SystemExit('0.38 floor survived')
if 'Math.max(.05,sc)' not in page_after:
    raise SystemExit('replacement scale floor missing')

obj['spellBuilder'] = page_after

old_json = json.dumps(page_before, ensure_ascii=False, separators=(',', ':')).replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')
new_json = json.dumps(page_after, ensure_ascii=False, separators=(',', ':')).replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')
if raw.count(old_json) != 1:
    raise SystemExit('serialized PAGES.spellBuilder anchor changed')
raw = raw.replace(old_json, new_json, 1)

if raw.lower().count('</script>') != 0:
    raise SystemExit('unsafe inner </script> present after repair')

obj2, end2 = json.JSONDecoder().raw_decode(raw)
if obj2 != obj or end2 != len(raw):
    raise SystemExit('decoded embedded pages changed during boundary repair')
for key in obj:
    if key != 'spellBuilder' and obj2[key] != obj[key]:
        raise SystemExit('unexpected embedded page changed: ' + key)

s2 = s[:start] + raw + s[start + end:]
out.write_text(s2, encoding='utf-8')
print('A4 Pack physicalPrint scale floor: 0.38 (could still bleed) -> 0.05 (sanity backstop only)')
