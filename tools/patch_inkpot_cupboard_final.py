#!/usr/bin/env python3
import json, re, sys, hashlib
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_inkpot_cupboard_final.py INPUT.html OUTPUT.html')

src = Path(sys.argv[1]).read_text(encoding='utf-8')

def decode_page(doc, key):
    marker = f'PAGES.{key} = '
    start = doc.index(marker) + len(marker)
    value, consumed = json.JSONDecoder().raw_decode(doc[start:])
    return start, consumed, value

def replace_page(doc, key, value):
    start, consumed, _old = decode_page(doc, key)
    literal = json.dumps(value, separators=(',', ':'))
    literal = literal.replace('</script', '<\\/script').replace('</SCRIPT', '<\\/SCRIPT')
    return doc[:start] + literal + doc[start + consumed:]

_s, _n, scribe = decode_page(src, 'scribe')
pat = re.compile(r'async function gmInkPrintBound\s*\(\)')
found = list(pat.finditer(scribe))
if len(found) != 3:
    raise SystemExit(f'Expected 3 gmInkPrintBound definitions in pinned source, found {len(found)}')
for m, name in sorted([
    (found[0], 'gmInkPrintBoundLegacyPreInkpot'),
    (found[2], 'gmInkPrintBoundLegacyNativeCutDisabled'),
], key=lambda x: x[0].start(), reverse=True):
    replacement = f'async function {name}()'
    scribe = scribe[:m.start()] + replacement + scribe[m.end():]

render_anchor = "function renderInkPrintRoom(){const line=$('#gmInkBoundBookLine')"
idx = scribe.find(render_anchor)
if idx < 0:
    raise SystemExit('Newest renderInkPrintRoom anchor not found')
helper = r'''let GM_INK_BOUND_PROBE_TOKEN=0;
async function gmInkEnsureBoundPdfReady(cat){
  const token=++GM_INK_BOUND_PROBE_TOKEN;
  if(!cat||!cat.pages||!cat.pages.length)return false;
  const wait=$('#gmInkBoundPreviewWait'),box=$('#gmInkBoundPreview');
  if(box)box.classList.add('ready');
  if(wait){wait.style.display='block';wait.textContent='Opening the completed bound PDF from Greenman storage…'}
  try{
    const rec=await GM_BOS.inkGetBoundPdf({onProgress:(stage,done,total)=>{
      if(token!==GM_INK_BOUND_PROBE_TOKEN||!wait)return;
      if(stage==='reading')wait.textContent='Opening bound PDF · '+Math.round((done/Math.max(1,total))*100)+'%';
    }});
    if(token!==GM_INK_BOUND_PROBE_TOKEN)return false;
    if(!rec||!rec.blob||!rec.blob.size)throw new Error('The bound PDF file is missing from Greenman storage');
    gmInkSetStatus('Bound PDF is ready',cat.pages.length+' A4 pages are available. Choose Whole Book, Chapters, Pages or Spells, then make a PDF copy. Copies go to '+GM_INK_OUTPUT_DIR+'.');
    await gmInkRenderPreview(cat,GM_INK_PREVIEW.index);
    return true;
  }catch(err){
    if(token!==GM_INK_BOUND_PROBE_TOKEN)return false;
    if(wait){wait.style.display='block';wait.textContent='Bound PDF could not be opened · '+String(err&&err.message||err)}
    gmInkSetStatus('Bound catalogue found, but its PDF could not be opened',String(err&&err.message||err),'error');
    return false;
  }
}
'''
scribe = scribe[:idx] + helper + scribe[idx:]

old_tail = "gmInkRenderPicker(cat);gmInkBindPickerEvents(cat);gmInkUpdatePrintSummary(cat);gmBosRenderNativeStatus();gmInkRenderPreview(cat,GM_INK_PREVIEW.index);gmInkSnapshot('Original BoS Print Room rendered')"
new_tail = "gmInkRenderPicker(cat);gmInkBindPickerEvents(cat);gmInkUpdatePrintSummary(cat);if(cat){gmInkEnsureBoundPdfReady(cat)}else{gmBosRenderNativeStatus();gmInkRenderPreview(null,0)}gmInkSnapshot('Original BoS Print Room rendered')"
if old_tail not in scribe:
    raise SystemExit('Ink Pot render tail not found')
scribe = scribe.replace(old_tail, new_tail, 1)

active_start = "async function gmInkPrintBound(){const cat=gmInkBoundCatalog();if(!cat)return;const keys=gmInkChosenPageKeys(cat);if(!keys.length)return;"
active_new = "async function gmInkPrintBound(){const cat=gmInkBoundCatalog();if(!cat){gmInkSetStatus('No bound Book of Shadows','Bind the book from BoS → Main Contents first.','error');return}const keys=gmInkChosenPageKeys(cat);if(!keys.length){gmInkSetStatus('Nothing selected','Choose Whole Book, Chapters, Pages or Spells first.','error');return}"
if active_start not in scribe:
    raise SystemExit('Active Ink Pot PDF handler start not found')
scribe = scribe.replace(active_start, active_new, 1)
if scribe.count('async function gmInkPrintBound(){') != 1:
    raise SystemExit('Ink Pot still has more than one active gmInkPrintBound handler')

scribe = scribe.replace('</head>', '<!-- INKPOT FIX: single active PDF handler, native bound PDF preview, filtered copies saved from already-bound pages. -->\n</head>', 1)
src = replace_page(src, 'scribe', scribe)

_s, _n, cupboard = decode_page(src, 'cupboard')
old_order = """function renderHedgewitch(){
  hedgeShelvesEl.innerHTML='';
  /* Crystal bags and herb jars return to the upper shelves. Scrolls and runes move below the incense area. */
  appendOwnedShelf('Crystals','Crystal','Crystal');
  appendOwnedShelf('Herbs','Herb','Herb');
  appendOwnedShelf('Oils','Oil','Oil');
  appendBowerScribeRooms();
  appendIncenseDrawerFront();
  appendDailyDrawers();
  appendIncenseBlendShelf();
  appendBosShelf();
  appendOwnedShelf('Runes','Rune','Rune');
  renderIncenseDrawer();
  requestAnimationFrame(restoreTrackScrolls);
}"""
new_order = """function renderHedgewitch(){
  hedgeShelvesEl.innerHTML='';
  /* Cabinet furniture stays together at the top: doors, drawers and room fronts first; owned items sit underneath. */
  appendIncenseDrawerFront();
  appendDailyDrawers();
  appendBowerScribeRooms();
  appendOwnedShelf('Crystals','Crystal','Crystal');
  appendOwnedShelf('Herbs','Herb','Herb');
  appendOwnedShelf('Oils','Oil','Oil');
  appendIncenseBlendShelf();
  appendBosShelf();
  appendOwnedShelf('Runes','Rune','Rune');
  renderIncenseDrawer();
  requestAnimationFrame(restoreTrackScrolls);
}"""
if old_order not in cupboard:
    raise SystemExit('Hedgewitch cupboard render order not found')
cupboard = cupboard.replace(old_order, new_order, 1)
css = '''
/* TOP FIXTURES: keep every cupboard/drawer/room front together before item shelves. */
.door-bank-top{margin-bottom:0!important}
#hedgeShelves{margin-top:0!important}
#hedgeShelves>.incense-drawer-row:first-child{margin-top:0!important;border-top-width:5px!important}
#hedgeShelves>.incense-drawer-row + .daily-drawer-row{margin-top:-1px!important}
#hedgeShelves>.daily-drawer-row + .feature-room-row{margin-top:-1px!important}
#hedgeShelves>.feature-room-row + .shelf.hedge-owned-shelf{margin-top:10px!important}
'''
cupboard = cupboard.replace('</head>', css + '\n<!-- CUPBOARD LAYOUT FIX: all doors/drawers together at top; owned-item shelves below. -->\n</head>', 1)
src = replace_page(src, 'cupboard', cupboard)

outer_marker = '<!-- FV 2.7.27 INKPOT + CUPBOARD FIX: one active Ink Pot PDF handler; native bound preview/filter; top fixtures grouped above owned shelves. -->'
if outer_marker not in src:
    src = src.replace('</head>', outer_marker + '\n</head>', 1)

Path(sys.argv[2]).write_text(src, encoding='utf-8')
print('bytes', len(src.encode('utf-8')))
print('sha256', hashlib.sha256(src.encode('utf-8')).hexdigest())
