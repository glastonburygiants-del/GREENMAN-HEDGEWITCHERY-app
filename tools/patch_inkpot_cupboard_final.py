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

# Native selected-page exporter. The full bound book is copied byte-for-byte;
# chapter/page/spell selections are cut by Android from the stored bound PDF.
whole_fn = "function gmBosInkExportWhole(fileName){const api=gmBosNativeFiles();try{if(api&&typeof api.hasLastBoundPdf==='function'&&api.hasLastBoundPdf()){if(typeof api.exportLastBoundPdfAs==='function')return !!api.exportLastBoundPdfAs(fileName);if(typeof api.exportLastBoundPdf==='function')return !!api.exportLastBoundPdf()}}catch(_e){}return false}"
if whole_fn not in scribe:
    raise SystemExit('gmBosInkExportWhole anchor not found')
native_helpers = whole_fn + r'''
function gmBosInkExportNativeSelection(pageIndexes,fileName){const api=gmBosNativeFiles();try{if(!api||typeof api.hasLastBoundPdf!=='function'||!api.hasLastBoundPdf()||typeof api.exportSelectedPagesAs!=='function')return false;return !!api.exportSelectedPagesAs(fileName,(pageIndexes||[]).join(','))}catch(_e){return false}}
function gmBosInkNativeLastError(){const api=gmBosNativeFiles();try{return api&&typeof api.lastError==='function'?String(api.lastError()||''):''}catch(_e){return ''}}
'''
scribe = scribe.replace(whole_fn, native_helpers, 1)

old_return = "inkGetBoundPdf:gmBosInkGetBoundPdf,inkMakeSelection:gmBosInkMakeSelection,inkExportWhole:gmBosInkExportWhole,inkPreviewPage:gmBosInkPreviewPage"
new_return = "inkGetBoundPdf:gmBosInkGetBoundPdf,inkMakeSelection:gmBosInkMakeSelection,inkExportWhole:gmBosInkExportWhole,inkExportNativeSelection:gmBosInkExportNativeSelection,inkNativeLastError:gmBosInkNativeLastError,inkPreviewPage:gmBosInkPreviewPage"
if old_return not in scribe:
    raise SystemExit('GM_BOS return export anchor not found')
scribe = scribe.replace(old_return, new_return, 1)

active_start = scribe.find("async function gmInkPrintBound(){const cat=gmInkBoundCatalog();")
if active_start < 0:
    raise SystemExit('Active Ink Pot PDF handler not found')
active_end = scribe.find("function gmBosBoundText", active_start)
if active_end < 0:
    raise SystemExit('Active Ink Pot PDF handler end anchor not found')
active_new = r'''async function gmInkPrintBound(){
 const cat=gmInkBoundCatalog();if(!cat){gmInkSetStatus('No bound Book of Shadows','Bind the book from BoS → Main Contents first.','error');return}
 const keys=gmInkChosenPageKeys(cat);if(!keys.length){gmInkSetStatus('Nothing selected','Choose Whole Book, Chapters, Pages or Spells first.','error');return}
 const nums=keys.map(k=>(cat.pages||[]).findIndex(p=>p.key===k)+1).filter(n=>n>0),indexes=nums.map(n=>n-1),ranges=gmInkPageRanges(nums),full=nums.length===(cat.pages||[]).length,file=full?(cat.fileName||gmBosOriginalFileName()):gmInkSelectionPdfFileName(),btn=$('#gmInkPrintBoundBtn');
 if(btn)btn.disabled=true;
 try{
   let ok=false;
   if(full){
     gmInkSetStatus('Saving whole bound PDF','Copying the completed '+nums.length+'-page bound original directly to '+GM_INK_OUTPUT_DIR+'.','saving');
     ok=!!GM_BOS.inkExportWhole(file);
   }else{
     gmInkSetStatus('Saving selected bound pages','Android is taking pages '+ranges+' directly from the completed bound PDF.','saving');
     ok=typeof GM_BOS.inkExportNativeSelection==='function'&&!!GM_BOS.inkExportNativeSelection(indexes,file);
   }
   if(!ok){const detail=typeof GM_BOS.inkNativeLastError==='function'?GM_BOS.inkNativeLastError():'';throw new Error(detail||'Android could not save the PDF copy')}
   const path=GM_INK_OUTPUT_DIR+' / '+file;
   gmInkSetStatus('PDF saved ✓',path,'saved');
   gmBosShowJobNotice('Book of Shadows PDF',full?'Whole bound PDF saved':'Selected bound pages saved',path);
 }catch(err){
   console.error('Ink Pot native PDF failed',err);
   gmInkSetStatus('PDF could not be saved',String(err&&err.message||err),'error');
   gmBosShowJobNotice('Book of Shadows PDF','PDF could not be saved',String(err&&err.message||err));
 }finally{gmInkUpdatePrintSummary(gmInkBoundCatalog());if(btn&&gmInkBoundCatalog())btn.disabled=false}
}
'''
scribe = scribe[:active_start] + active_new + scribe[active_end:]
if scribe.count('async function gmInkPrintBound(){') != 1:
    raise SystemExit('Ink Pot still has more than one active gmInkPrintBound handler')

scribe = scribe.replace('</head>', '<!-- INKPOT FIX V2.7.28: one active handler; whole-book direct copy; chapter/page/spell selections cut natively from the stored bound PDF. -->\n</head>', 1)
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
  /* One continuous furniture stack: Supply/Spell doors, then Bower/Scribe cupboards, then the drawers. Item shelves start underneath. */
  appendBowerScribeRooms();
  appendIncenseDrawerFront();
  appendDailyDrawers();
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
/* TOP FURNITURE JOIN V2.7.28: the lower cupboards and drawers physically meet the Supply/Spell cupboard row. */
.door-bank-top{margin-bottom:0!important;padding-bottom:0!important}
#hedgeShelves{margin-top:-1px!important}
#hedgeShelves>.feature-room-row:first-child{margin-top:-1px!important;margin-bottom:0!important;border-top-width:5px!important}
#hedgeShelves>.feature-room-row + .incense-drawer-row{margin-top:-1px!important}
#hedgeShelves>.incense-drawer-row + .daily-drawer-row{margin-top:-1px!important}
#hedgeShelves>.daily-drawer-row + .shelf.hedge-owned-shelf{margin-top:10px!important}
'''
cupboard = cupboard.replace('</head>', css + '\n<!-- CUPBOARD LAYOUT FIX V2.7.28: Bower/Scribe and drawers joined directly beneath Supply/Spell. -->\n</head>', 1)
src = replace_page(src, 'cupboard', cupboard)

outer_marker = '<!-- FV 2.7.28 PDF + CUPBOARD FIX: native selected-page PDF export; joined top furniture stack. -->'
if outer_marker not in src:
    src = src.replace('</head>', outer_marker + '\n</head>', 1)

Path(sys.argv[2]).write_text(src, encoding='utf-8')
print('bytes', len(src.encode('utf-8')))
print('sha256', hashlib.sha256(src.encode('utf-8')).hexdigest())
