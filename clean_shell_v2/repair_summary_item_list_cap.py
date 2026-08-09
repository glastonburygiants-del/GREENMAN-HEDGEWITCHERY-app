#!/usr/bin/env python3
"""The Summary page 2 "Item List" table has exactly 4 hardcoded row
templates in the static HTML (id="summary-item-1".."summary-item-4"), and
fillPrintStack() populates it via all.slice(0,4) - both the template and
the population logic have always capped the item list at 4 rows, in every
version of this baseline, regardless of how many items the spell actually
has (candle, up to 4 elemental herbs, any number of extra spell herbs,
crystal, rune, goddess, god, oil can easily total well past 4). Anything
beyond the 4th item was never written into the DOM at all - not shrunk,
not overflowed, simply never populated. This has nothing to do with any of
the scale/fit repairs already applied.

This clones the row template for every item beyond the first 4 and
populates each clone directly (not via id lookup, since ids must stay
unique), so the full item list renders regardless of length.
"""
from pathlib import Path
import json, re, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: repair_summary_item_list_cap.py INPUT OUTPUT')

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

old = ("all.slice(0,4).forEach(([l,it],i)=>{const n=i?i+1:''; setIn(root,'itemName'+n,name(it)); "
       "setIn(root,'yeOlde'+n,old(it)); setIn(root,'magicalUse'+n,spellUse(it,sp)); "
       "setIn(root,'greenmanEnergy'+n,gmField(it,sd)); setIn(root,'powers'+n,powers(it));});")
count = page_before.count(old)
if count != 1:
    raise SystemExit(f'fillPrintStack item-list anchor count was {count}, expected 1')

new = (
    "all.forEach(([l,it],i)=>{"
    "if(i<4){const n=i?i+1:''; setIn(root,'itemName'+n,name(it)); setIn(root,'yeOlde'+n,old(it)); "
    "setIn(root,'magicalUse'+n,spellUse(it,sp)); setIn(root,'greenmanEnergy'+n,gmField(it,sd)); setIn(root,'powers'+n,powers(it));"
    "return;}"
    "var tpl=root.querySelector('#summary-item-4')||root.querySelector('#summary-item-1');if(!tpl)return;"
    "var container=tpl.parentNode;if(!container)return;"
    "var row=tpl.cloneNode(true);row.removeAttribute('id');"
    "var qa1=function(sel){return row.querySelectorAll(sel);};"
    "var nameEl=row.querySelector('.item-name span');if(nameEl){nameEl.removeAttribute('id');nameEl.textContent=txt(name(it));}"
    "var oldEl=row.querySelector('.item-old span');if(oldEl){oldEl.removeAttribute('id');oldEl.textContent=txt(old(it));}"
    "var textEls=qa1('.item-text span');"
    "if(textEls[0]){textEls[0].removeAttribute('id');textEls[0].textContent=txt(spellUse(it,sp));}"
    "if(textEls[1]){textEls[1].removeAttribute('id');textEls[1].textContent=txt(powers(it));}"
    "var greenEl=row.querySelector('.item-green span');if(greenEl){greenEl.removeAttribute('id');greenEl.textContent=txt(gmField(it,sd));}"
    "container.appendChild(row);"
    "});"
)
page_after = page_before.replace(old, new, 1)

if page_after == page_before:
    raise SystemExit('no change applied to spellBuilder')
if 'all.slice(0,4).forEach(([l,it],i)=>{const n=i?i+1' in page_after:
    raise SystemExit('original 4-item cap survived')
if "root.querySelector('#summary-item-4')" not in page_after:
    raise SystemExit('row-cloning replacement missing')

obj['spellBuilder'] = page_after

esc = lambda t: t.replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')
old_json = esc(json.dumps(page_before, ensure_ascii=False, separators=(',', ':')))
new_json = esc(json.dumps(page_after, ensure_ascii=False, separators=(',', ':')))
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
print('Summary Item List: 4-row hard cap removed, extra items now cloned into new rows')
