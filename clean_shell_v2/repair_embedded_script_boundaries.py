#!/usr/bin/env python3
from pathlib import Path
import json, re, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: repair_embedded_script_boundaries.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')
marker = 'const PAGES = '
start = s.index(marker) + len(marker)
obj, end = json.JSONDecoder().raw_decode(s[start:])
raw = s[start:start+end]

# BoS Print All must use the same saved-snapshot renderer as Print Entry.
# The important difference is that the completed book is NOT sent through a
# second whole-book fit pass after the entries have been assembled.
def replace_function(text, name, new_code):
    m = re.search(r'function\s+' + re.escape(name) + r'\s*\(', text)
    if not m:
        raise SystemExit('function not found: ' + name)
    begin = m.start()
    brace = text.find('{', m.end())
    if brace < 0:
        raise SystemExit('opening brace missing: ' + name)
    depth = 0
    i = brace
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ''
        if line_comment:
            if c == '\n':
                line_comment = False
        elif block_comment:
            if c == '*' and n == '/':
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == quote:
                quote = None
        else:
            if c == '/' and n == '/':
                line_comment = True
                i += 1
            elif c == '/' and n == '*':
                block_comment = True
                i += 1
            elif c in ("'", '"', '`'):
                quote = c
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return text[:begin] + new_code + text[i + 1:]
        i += 1
    raise SystemExit('closing brace missing: ' + name)

bos_before = obj.get('bos')
if not isinstance(bos_before, str):
    raise SystemExit('missing PAGES.bos')

bos_after = replace_function(
    bos_before,
    'printAll',
    '''function printAll(){
  if(bosIsLiteMode())return;
  const list=entries(),area=qs('#printArea');
  area.innerHTML='';
  if(!list.length){
    area.innerHTML='<section class="a4-page active"><div class="a4-content">No Book of Shadows entries saved.</div></section>';
    setTimeout(()=>window.print(),180);
    return;
  }
  list.forEach(function(e){
    if(hasBosSnapshot(e)){
      appendBosSnapshotInto(area,e,null);
      return;
    }
    const tmp=document.createElement('div');
    tmp.innerHTML=buildEntryPages(e);
    fitSummaryPages(tmp);
    fitGrimoirePages(tmp);
    while(tmp.firstChild)area.appendChild(tmp.firstChild);
  });
  setTimeout(()=>window.print(),180);
}'''
)

if bos_after == bos_before:
    raise SystemExit('BoS Print All owner was not changed')
for required in ('appendBosSnapshotInto(area,e,null)', 'fitSummaryPages(tmp)', 'fitGrimoirePages(tmp)', 'setTimeout(()=>window.print(),180)'):
    if required not in bos_after:
        raise SystemExit('BoS Print All owner missing: ' + required)
for forbidden in ('fitSummaryPages(area)', 'fitGrimoirePages(area)', 'gmFlatPrint(area)', 'appendFlatSnapshot(area,e,null)'):
    if forbidden in bos_after[bos_after.find('function printAll'):]:
        raise SystemExit('whole-book print pass survived: ' + forbidden)
obj['bos'] = bos_after

# Replace only the serialized BoS page inside the compact PAGES JSON. Every
# other embedded page remains byte-for-byte unchanged.
old_bos_json = json.dumps(bos_before, ensure_ascii=False, separators=(',', ':'))
new_bos_json = json.dumps(bos_after, ensure_ascii=False, separators=(',', ':'))
if raw.count(old_bos_json) != 1:
    raise SystemExit('serialized PAGES.bos anchor changed')
raw = raw.replace(old_bos_json, new_bos_json, 1)

unsafe = raw.lower().count('</script>')
if unsafe == 0:
    raise SystemExit('boundary repair expected unsafe inner </script> tags but found 0')

# Preserve the decoded embedded pages exactly apart from the intentional BoS
# Print All owner change. Protect only the outer parser boundary here.
fixed = raw.replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')

if fixed.lower().count('</script>') != 0:
    raise SystemExit('unsafe inner </script> remains after repair')

obj2, end2 = json.JSONDecoder().raw_decode(fixed)
if obj2 != obj or end2 != len(fixed):
    raise SystemExit('decoded embedded pages changed during boundary repair')
for key in obj:
    if key != 'bos' and obj2[key] != obj[key]:
        raise SystemExit('unexpected embedded page changed: ' + key)

s2 = s[:start] + fixed + s[start+end:]
out.write_text(s2, encoding='utf-8')
print('BoS Print All now composes the same saved-entry renderer as Print Entry')
print('No second whole-book fit pass is applied after composition')
print(f'Repaired embedded script boundaries: {unsafe} unsafe closers -> 0')
print(f'Protected inner closers now present: {fixed.lower().count("<\\/script>")}')
