#!/usr/bin/env python3
"""Keep the complete Summary page 2 item list and contain saved Summary page 2
inside A4 in every Journal/BoS print route.

The active saved-spell print routes use bosSnapshotDoc() inside both Journal and
Book of Shadows. Entry print and full-book print share that same renderer. Its
Summary page 2 fitter measured the required scale, then overrode the result with
a hard 0.46 minimum. If the real page needed less than 46%, the bottom was
clipped/bled even though the measurement had already found the correct scale.

Only Summary page 2 loses that artificial floor. Other saved pages keep their
existing anti-miniature floors, so the already-repaired tiny-page behaviour is
not reopened.
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

def esc(t):
    return t.replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')

def replace_serialized_page(raw_json, before, after, page_name):
    old_json = esc(json.dumps(before, ensure_ascii=False, separators=(',', ':')))
    new_json = esc(json.dumps(after, ensure_ascii=False, separators=(',', ':')))
    if raw_json.count(old_json) != 1:
        raise SystemExit('serialized PAGES.' + page_name + ' anchor changed')
    return raw_json.replace(old_json, new_json, 1)

# ---------------------------------------------------------------------------
# 1. Summary page 2 Item List: remove the four-row data-loss cap.
# ---------------------------------------------------------------------------
page_before = obj.get('spellBuilder')
if not isinstance(page_before, str):
    raise SystemExit('missing PAGES.spellBuilder')

old = ("all.slice(0,4).forEach(([l,it],i)=>{const n=i?i+1:''; setIn(root,'itemName'+n,name(it)); "
       "setIn(root,'yeOlde'+n,old(it)); setIn(root,'magicalUse'+n,spellUse(it,sp)); "
       "setIn(root,'greenmanEnergy'+n,gmField(it,sd)); setIn(root,'powers'+n,powers(it));});")
count = page_before.count(old)

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
if count == 1:
    page_after = page_before.replace(old, new, 1)
elif count == 0 and "root.querySelector('#summary-item-4')" in page_before:
    page_after = page_before
else:
    raise SystemExit(f'fillPrintStack item-list anchor count was {count}, and repaired row-cloning marker was not present')

if 'all.slice(0,4).forEach(([l,it],i)=>{const n=i?i+1' in page_after:
    raise SystemExit('original 4-item cap survived')
if "root.querySelector('#summary-item-4')" not in page_after:
    raise SystemExit('row-cloning replacement missing')
obj['spellBuilder'] = page_after
if page_after != page_before:
    raw = replace_serialized_page(raw, page_before, page_after, 'spellBuilder')

# ---------------------------------------------------------------------------
# 2. Saved Summary page 2: Journal + BoS, Entry + Full Book.
# ---------------------------------------------------------------------------
# Both Entry and Full routes call bosSnapshotDoc() through
# renderBosSnapshotInto/appendBosSnapshotInto. Keep the anti-miniature floors
# for every other page. Summary page 2 alone gets a low sanity backstop, so the
# real measured scale is allowed to contain the whole page.
patterns = {
    'journal': (
        r"sc=Math\.max\(summaryPage2\s*\?\s*\.46\s*:\s*\(isSummary\s*\?\s*\.54\s*:\s*\.70\),sc\);",
        "sc=summaryPage2 ? Math.max(.20,sc) : Math.max(isSummary ? .54 : .70,sc);"
    ),
    'bos': (
        r"sc=Math\.max\(summaryPage2\s*\?\s*\.46\s*:\s*\(summary\s*\?\s*\.54\s*:\s*\.70\),sc\);",
        "sc=summaryPage2 ? Math.max(.20,sc) : Math.max(summary ? .54 : .70,sc);"
    ),
}

for page_name, (pat, repl) in patterns.items():
    before = obj.get(page_name)
    if not isinstance(before, str):
        raise SystemExit('missing PAGES.' + page_name)
    if 'function bosSnapshotDoc(' not in before:
        raise SystemExit(page_name + ' bosSnapshotDoc owner missing')
    if 'renderBosSnapshotInto(' not in before or 'appendBosSnapshotInto(' not in before:
        raise SystemExit(page_name + ' saved snapshot Entry/Full route missing')
    after, n = re.subn(pat, repl, before, count=1)
    if n != 1:
        raise SystemExit(page_name + ' Summary page 2 hard-floor anchor count was ' + str(n) + ', expected 1')
    if re.search(pat, after):
        raise SystemExit(page_name + ' 0.46 Summary page 2 floor survived')
    if "summaryPage2 ? Math.max(.20,sc)" not in after:
        raise SystemExit(page_name + ' Summary page 2 adaptive containment marker missing')
    obj[page_name] = after
    raw = replace_serialized_page(raw, before, after, page_name)

# The protected embedded-script boundary must remain intact.
if raw.lower().count('</script>') != 0:
    raise SystemExit('unsafe inner </script> present after repair')

obj2, end2 = json.JSONDecoder().raw_decode(raw)
if obj2 != obj or end2 != len(raw):
    raise SystemExit('decoded embedded pages changed during boundary repair')

# Only the intended three embedded pages may differ.
for key in obj:
    if key not in ('spellBuilder', 'journal', 'bos') and obj2[key] != obj[key]:
        raise SystemExit('unexpected embedded page changed: ' + key)

s2 = s[:start] + raw + s[start + end:]
out.write_text(s2, encoding='utf-8')
print('Summary Item List: 4-row cap removed')
print('Summary page 2 containment: Journal Entry + Full Book and BoS Entry + Full Book now use the measured scale below 0.46 when required')
print('Other saved pages retain their anti-miniature scale floors')
