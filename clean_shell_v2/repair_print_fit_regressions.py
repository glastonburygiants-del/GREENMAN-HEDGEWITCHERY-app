#!/usr/bin/env python3
"""Restore real adaptive A4 fit measurement to BoS/Journal print, which the
2.7.8/2.7.11 patches had each replaced with a rigid floor/ceiling:

  fitGrimoirePages (BoS): 2.7.11 deleted the whole-page scale calculation
  entirely and left --grimoire-fit-scale hard-set to 1, relying only on
  per-box text shrinking with no fallback. Long entries (e.g. ACORN) bleed
  off the page because nothing shrinks the page itself when box-shrinking
  alone cannot make the content fit.

  fitFlatPages (BoS + Journal): 2.7.8 replaced the original binary-search
  best-fit measurement with a single measurement clamped to a hard-coded
  0.82 minimum scale, on the assumption stored A4 snapshots never
  legitimately need to shrink further. That fixed one over-shrunk ("tiny")
  case but now bleeds any page that genuinely needs less than 82% to fit.

Both fixes keep the genuinely good part of the newer patches (stale-data
cleanup via gmRecoverBosSnapshotPage, per-box text shrinking via
fitAllGrimoireInfoBoxes) and restore the original's adaptive binary-search
measurement underneath as the real safety net, instead of a fixed number.
"""
from pathlib import Path
import json, re, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: repair_print_fit_regressions.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')
marker = 'const PAGES = '
start = s.index(marker) + len(marker)
obj, end = json.JSONDecoder().raw_decode(s[start:])
raw = s[start:start+end]


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


def has_function(text, name):
    return re.search(r'function\s+' + re.escape(name) + r'\s*\(', text) is not None


FIT_FLAT_PAGES = '''function fitFlatPages(root){
  qsa('.gm-flat .true-page',root).forEach(function(pg){
    gmRecoverBosSnapshotPage(pg);
    var c=pg.querySelector(':scope > .true-content')||pg.querySelector('.true-content')||pg.firstElementChild; if(!c)return;
    var cs=c.style;
    cs.setProperty('transform','none','important');
    cs.setProperty('transform-origin','top left','important');
    cs.setProperty('width','100%','important');
    cs.setProperty('height','auto','important');
    cs.setProperty('min-height','0','important');
    cs.setProperty('max-height','none','important');
    pg.style.setProperty('--summary-fit-scale','1','important');
    var inner=pg.querySelector('.a4-content');
    if(inner){inner.style.setProperty('transform','none','important');
      inner.style.setProperty('width','100%','important');
      inner.style.setProperty('height','auto','important');}
    var avail=pg.clientHeight; if(!avail)return;
    /* Binary search for the LARGEST scale that still fits, between a
       guaranteed-fit floor and 1. A fixed 0.25 floor (as before) still lost
       content outright on exceptionally long entries: whole-page scale alone
       can always make content fit given a small enough number, so rather
       than cap the search and accept overflow, first shrink the floor itself
       until it measurably fits, then binary-search upward from there for the
       largest scale that still contains everything. Losing readability is
       acceptable; losing content is not. */
    var lo=0.25,hi=1,best=0,mid,h,i,floorGuard=0;
    cs.setProperty('width',(100/lo).toFixed(3)+'%','important');
    cs.setProperty('height','auto','important');
    h=c.scrollHeight*lo;
    while(h>avail-4 && lo>0.02 && floorGuard++<20){
      lo=Math.max(0.02,lo*0.7);
      cs.setProperty('width',(100/lo).toFixed(3)+'%','important');
      h=c.scrollHeight*lo;
    }
    best=lo;
    for(i=0;i<10;i++){
      mid=(lo+hi)/2;
      cs.setProperty('width',(100/mid).toFixed(3)+'%','important');
      cs.setProperty('height','auto','important');
      h=c.scrollHeight*mid;
      if(h<=avail-4){best=mid;lo=mid;}else{hi=mid;}
    }
    var s=best||0.25;
    cs.setProperty('width',(100/s).toFixed(3)+'%','important');
    cs.setProperty('transform','scale('+s.toFixed(4)+')','important');
    pg.setAttribute('data-gm-print-fit',s.toFixed(4));
  });
}'''

FIT_GRIMOIRE_PAGES = '''function fitGrimoirePages(root=document){
  qsa('.grimoire-page',root).forEach(page=>{
    page.style.setProperty('--grimoire-fit-scale','1');
    fitAllGrimoireInfoBoxes(page);
    requestAnimationFrame(()=>{
      fitAllGrimoireInfoBoxes(page);
      /* Per-box text shrinking runs first so a normal entry keeps its full
         one-page size. Only if the page STILL overflows after that does the
         whole page shrink, as a safety net instead of silently bleeding. */
      const c=qs('.a4-content',page);
      if(!c)return;
      const needH=c.scrollHeight||1123;
      const needW=c.scrollWidth||794;
      const scale=Math.min(1,1123/Math.max(1123,needH),794/Math.max(794,needW));
      if(scale<1){
        /* No hard minimum here: clamping to a "normal" floor (as a prior
           patch did) still lost content outright on exceptionally long
           entries once the real requirement fell below that floor. 0.15 is
           only a sanity backstop against a zero/negative scale, not a
           readability target - losing content is worse than small text. */
        page.style.setProperty('--grimoire-fit-scale',Math.max(0.15,scale-.008).toFixed(3));
        requestAnimationFrame(()=>fitAllGrimoireInfoBoxes(page));
      }
    });
  });
}'''

changed_pages = []
for page_name in ('journal', 'bos'):
    page_before = obj.get(page_name)
    if not isinstance(page_before, str):
        raise SystemExit('missing PAGES.' + page_name)
    page_after = page_before

    if has_function(page_after, 'fitFlatPages'):
        page_after = replace_function(page_after, 'fitFlatPages', FIT_FLAT_PAGES)

    if page_name == 'bos' and has_function(page_after, 'fitGrimoirePages'):
        page_after = replace_function(page_after, 'fitGrimoirePages', FIT_GRIMOIRE_PAGES)

    if page_after == page_before:
        raise SystemExit('no change applied to page: ' + page_name)
    obj[page_name] = page_after
    changed_pages.append(page_name)

    def escape_for_raw(text):
        return text.replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')

    old_json = escape_for_raw(json.dumps(page_before, ensure_ascii=False, separators=(',', ':')))
    new_json = escape_for_raw(json.dumps(page_after, ensure_ascii=False, separators=(',', ':')))
    if raw.count(old_json) != 1:
        raise SystemExit('serialized PAGES.' + page_name + ' anchor changed')
    raw = raw.replace(old_json, new_json, 1)

# Guardrails: the 0.82 hard floor with no adaptive search must be gone from
# fitFlatPages, and fitGrimoirePages must compute a real scale again.
for page_name in changed_pages:
    body = obj[page_name]
    if 'scale=Math.max(.82,scale*.995)' in body:
        raise SystemExit('hard-coded 0.82 floor survived in ' + page_name)
    if page_name == 'bos' and "page.style.setProperty('--grimoire-fit-scale','1');\\n    fitAllGrimoireInfoBoxes(page);\\n    requestAnimationFrame(()=>fitAllGrimoireInfoBoxes(page));\\n    setTimeout(()=>fitAllGrimoireInfoBoxes(page),80);\\n  });" in body:
        raise SystemExit('no-op fitGrimoirePages survived in ' + page_name)
    if page_name == 'bos' and "Math.max(minScale,scale-.008)" in body:
        raise SystemExit('clamped grimoire minScale floor survived in ' + page_name)
    if 'lo=0.25,hi=1,best=0,mid,h,i;\\n    for(i=0;i<10' in body:
        raise SystemExit('capped-at-0.25 fitFlatPages search survived in ' + page_name)

fixed = raw

if fixed.lower().count('</script>') != 0:
    raise SystemExit('unsafe inner </script> remains after repair')

obj2, end2 = json.JSONDecoder().raw_decode(fixed)
if obj2 != obj or end2 != len(fixed):
    raise SystemExit('decoded embedded pages changed during boundary repair')
for key in obj:
    if key not in changed_pages and obj2[key] != obj[key]:
        raise SystemExit('unexpected embedded page changed: ' + key)

s2 = s[:start] + fixed + s[start + end:]
out.write_text(s2, encoding='utf-8')
print('Restored adaptive fitFlatPages measurement in:', ', '.join(changed_pages))
print('Restored fitGrimoirePages whole-page safety-net scale in: bos')
