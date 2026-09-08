#!/usr/bin/env python3
import json, sys, hashlib
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_v2730_hotfix.py INPUT.html OUTPUT.html')

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

ui_start = '<div class="inkPrintStep"><b class="inkPrintStepTitle">1 · Filter this bound PDF</b>'
ui_end = '<div class="inkPrintActions v29">'
start = scribe.find(ui_start)
end = scribe.find(ui_end, start)
if start < 0 or end < 0:
    raise SystemExit('V2.7.29 Ink Pot filter UI not found')
new_ui = '''<div class="inkSingleOption"><div class="inkPrintField"><b>Save bound PDF copy</b><small id="gmInkPrintSummary">Nothing is bound yet.</small><span class="inkOutputNote">This saves an exact copy of the completed bound PDF to <b>Downloads / Greenman HedgeWitchery</b>. The bound original stays safely inside Greenman.</span></div></div>'''
scribe = scribe[:start] + new_ui + scribe[end:]

old_button = '<button id="gmInkPrintBoundBtn" class="brassBtn inkPrintPrimary" type="button" disabled>Make PDF</button>'
new_button = '<button id="gmInkPrintBoundBtn" class="brassBtn inkPrintPrimary" type="button" disabled>Save Bound PDF Copy</button>'
if old_button not in scribe:
    raise SystemExit('Ink Pot Make PDF button not found')
scribe = scribe.replace(old_button, new_button, 1)

summary_start = scribe.rfind('function gmInkUpdatePrintSummary(cat){')
summary_end = scribe.find('function gmBosRenderNativeStatus()', summary_start)
if summary_start < 0 or summary_end < 0:
    raise SystemExit('Newest Ink Pot summary function not found')
summary_new = r'''function gmInkUpdatePrintSummary(cat){
 const summary=$('#gmInkPrintSummary'),btn=$('#gmInkPrintBoundBtn'),status=GM_BOS.jobStatus(),busy=gmBosBusyState(status.state)||!!GM_BOS_UI.packing;
 if(summary)summary.textContent=cat?(cat.pages.length+' bound A4 pages will be copied exactly as already bound.'):'Nothing is bound yet.';
 if(btn){btn.disabled=!cat||busy;btn.textContent='Save Bound PDF Copy'}
}
'''
scribe = scribe[:summary_start] + summary_new + scribe[summary_end:]

old_native_status = "if(cat){gmInkSetStatus('Bound original is ready','Use Whole Book, Chapters, Pages or Spells above. PDF copies are saved to '+GM_INK_OUTPUT_DIR+'.');if(find)find.style.display='none'}"
new_native_status = "if(cat){gmInkSetStatus('Bound PDF is ready','Save an exact copy of the completed bound PDF to '+GM_INK_OUTPUT_DIR+'.');if(find)find.style.display='none'}"
if old_native_status not in scribe:
    raise SystemExit('Native Ink Pot status wording not found')
scribe = scribe.replace(old_native_status, new_native_status, 1)

old_ready = "gmInkSetStatus('Bound PDF is ready',cat.pages.length+' A4 pages are available. Choose Whole Book, Chapters, Pages or Spells, then make a PDF copy. Copies go to '+GM_INK_OUTPUT_DIR+'.');"
new_ready = "gmInkSetStatus('Bound PDF is ready',cat.pages.length+' A4 pages are complete. Save an exact copy to '+GM_INK_OUTPUT_DIR+'.');"
if old_ready not in scribe:
    raise SystemExit('Bound PDF ready wording not found')
scribe = scribe.replace(old_ready, new_ready, 1)

render_start = scribe.rfind('function renderInkPrintRoom(){')
render_end = scribe.find('async function gmInkPrintBound(){', render_start)
if render_start < 0 or render_end < 0:
    raise SystemExit('Newest Ink Pot render function not found')
render_new = r'''function renderInkPrintRoom(){
 const line=$('#gmInkBoundBookLine'),btn=$('#gmInkPrintBoundBtn'),back=$('#gmInkReturnLiveBtn'),find=$('#gmInkFindBoundPdfBtn'),pick=$('#gmInkFindBoundPdfInput');
 if(!line||!btn)return;
 btn.onclick=gmInkPrintBound;if(back)back.onclick=openBos;
 if(find)find.onclick=()=>{if(pick){pick.value='';pick.click()}};
 if(pick&&!pick.__gmBoundPdfBound){pick.__gmBoundPdfBound=true;pick.addEventListener('change',async()=>{const f=pick.files&&pick.files[0];if(f)await gmInkAttachExistingBoundPdf(f)})}
 const cat=gmInkBoundCatalog(),desk=btn.closest('.inkPrintDesk');if(desk)desk.classList.toggle('inkNoBound',!cat);
 if(!cat){line.className='inkBoundBookLine empty';line.innerHTML='<strong>No bound Book of Shadows yet</strong>Go to BoS → Main Contents, choose chapters, then press Bind Book. The completed PDF will appear here.'}
 else{line.className='inkBoundBookLine';line.innerHTML='<strong>'+cat.pages.length+' A4 pages are bound</strong>'+esc((cat.chapterNames||[]).join(' · '))}
 gmInkUpdatePrintSummary(cat);
 if(cat){gmInkEnsureBoundPdfReady(cat)}else{gmBosRenderNativeStatus();gmInkRenderPreview(null,0)}
 gmInkSnapshot('Bound PDF copy room rendered')
}
'''
scribe = scribe[:render_start] + render_new + scribe[render_end:]

print_start = scribe.find('async function gmInkPrintBound(){', render_start)
print_end = scribe.find('function gmBosBoundText', print_start)
if print_start < 0 or print_end < 0:
    raise SystemExit('Active Ink Pot PDF handler not found')
print_new = r'''async function gmInkPrintBound(){
 const cat=gmInkBoundCatalog();if(!cat){gmInkSetStatus('No bound Book of Shadows','Bind the book from BoS → Main Contents first.','error');return}
 const file=cat.fileName||gmBosOriginalFileName(),btn=$('#gmInkPrintBoundBtn');if(btn)btn.disabled=true;
 try{
   gmInkSetStatus('Saving bound PDF copy','Copying the completed '+cat.pages.length+'-page bound PDF directly to '+GM_INK_OUTPUT_DIR+'.','saving');
   if(!GM_BOS.inkExportWhole(file)){const detail=typeof GM_BOS.inkNativeLastError==='function'?GM_BOS.inkNativeLastError():'';throw new Error(detail||'Android could not save the bound PDF copy')}
   const path=GM_INK_OUTPUT_DIR+' / '+file;
   gmInkSetStatus('Bound PDF copy saved ✓',cat.pages.length+' pages · '+path,'saved');
   gmBosShowJobNotice('Book of Shadows PDF','Bound PDF copy saved',path);
 }catch(err){
   console.error('Ink Pot bound PDF copy failed',err);
   gmInkSetStatus('PDF could not be saved',String(err&&err.message||err),'error');
   gmBosShowJobNotice('Book of Shadows PDF','PDF could not be saved',String(err&&err.message||err));
 }finally{gmInkUpdatePrintSummary(gmInkBoundCatalog());if(btn&&gmInkBoundCatalog())btn.disabled=false}
}
'''
scribe = scribe[:print_start] + print_new + scribe[print_end:]

old_marker = '<!-- INKPOT FIX V2.7.29: whole-book direct copy; filtered chapter/page/spell PDFs rebuilt from exactly the selected bound flat pages. -->'
new_marker = '<!-- INKPOT V2.7.30: Ink Pot saves only an exact copy of the completed bound PDF; all chapter/page/spell filtering removed from this room. -->'
if old_marker not in scribe:
    raise SystemExit('V2.7.29 Ink Pot marker not found')
scribe = scribe.replace(old_marker, new_marker, 1)

if '1 · Filter this bound PDF' in scribe:
    raise SystemExit('Filter heading still present')
for label in ['data-gm-print-mode="chapters"','data-gm-print-mode="pages"','data-gm-print-mode="spells"']:
    if label in scribe:
        raise SystemExit('Filter button still present: '+label)
if scribe.count('async function gmInkPrintBound(){') != 1:
    raise SystemExit('Expected one active gmInkPrintBound handler')

src = replace_page(src, 'scribe', scribe)
outer_old = '<!-- FV 2.7.29 HOTFIX: filtered PDF uses exact selected bound pages; cupboard join CSS contained correctly. -->'
outer_new = '<!-- FV 2.7.30: Ink Pot is bound-PDF-copy only; no filtering/rebuilding in Scribe. -->'
if outer_old in src:
    src = src.replace(outer_old, outer_new, 1)
elif outer_new not in src:
    src = src.replace('</head>', outer_new+'\n</head>', 1)

Path(sys.argv[2]).write_text(src, encoding='utf-8')
data=src.encode('utf-8')
print('bytes',len(data))
print('sha256',hashlib.sha256(data).hexdigest())
