#!/usr/bin/env python3
import json, sys, hashlib
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_v2729_hotfix.py INPUT.html OUTPUT.html')

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

# Whole Book remains a direct copy of the completed bound original.
# Filtered Chapters / Pages / Spells are rebuilt from exactly the selected flat pages.
_s, _n, scribe = decode_page(src, 'scribe')
active_start = scribe.find("async function gmInkPrintBound(){\n const cat=gmInkBoundCatalog();")
if active_start < 0:
    raise SystemExit('V2.7.28 active Ink Pot handler not found')
active_end = scribe.find('function gmBosBoundText', active_start)
if active_end < 0:
    raise SystemExit('Ink Pot handler end anchor not found')

active_new = r'''async function gmInkPrintBound(){
 const cat=gmInkBoundCatalog();if(!cat){gmInkSetStatus('No bound Book of Shadows','Bind the book from BoS → Main Contents first.','error');return}
 const keys=gmInkChosenPageKeys(cat);if(!keys.length){gmInkSetStatus('Nothing selected','Choose Whole Book, Chapters, Pages or Spells first.','error');return}
 const nums=keys.map(k=>(cat.pages||[]).findIndex(p=>p.key===k)+1).filter(n=>n>0),indexes=nums.map(n=>n-1),ranges=gmInkPageRanges(nums),full=indexes.length===(cat.pages||[]).length,file=full?(cat.fileName||gmBosOriginalFileName()):gmInkSelectionPdfFileName(),btn=$('#gmInkPrintBoundBtn');
 if(btn)btn.disabled=true;
 try{
   let saved=null;
   if(full){
     gmInkSetStatus('Saving whole bound PDF','Copying the completed '+indexes.length+'-page bound original directly to '+GM_INK_OUTPUT_DIR+'.','saving');
     if(!GM_BOS.inkExportWhole(file)){const detail=typeof GM_BOS.inkNativeLastError==='function'?GM_BOS.inkNativeLastError():'';throw new Error(detail||'Android could not save the whole bound PDF')}
     saved={saved:true,fileName:file,path:GM_INK_OUTPUT_DIR+' / '+file,pageCount:indexes.length};
   }else{
     gmInkSetStatus('Building filtered PDF','Taking exactly '+indexes.length+' selected bound pages · '+ranges+'.','saving');
     saved=await GM_BOS.inkMakeSelection(indexes,file,{onProgress:(stage,done,total)=>{
       if(stage==='reading')gmInkSetStatus('Reading bound PDF','Opening the completed bound PDF · '+Math.round((done/Math.max(1,total))*100)+'%.','saving');
       else if(stage==='filtering')gmInkSetStatus('Filtering bound PDF','Taking '+indexes.length+' selected pages · '+ranges+'.','saving');
       else if(stage==='saving')gmInkSetStatus('Saving filtered PDF','Writing the '+indexes.length+'-page copy to '+GM_INK_OUTPUT_DIR+' · '+done+'/'+total+'.','saving');
     }});
     if(!saved)throw new Error('The filtered PDF was not created');
     saved.pageCount=indexes.length;
   }
   const path=saved.path||GM_INK_OUTPUT_DIR+' / '+file;
   gmInkSetStatus(full?'Whole PDF saved ✓':'Filtered PDF saved ✓',(full?indexes.length+' bound pages':'Exactly '+indexes.length+' selected pages')+' · '+path,'saved');
   gmBosShowJobNotice('Book of Shadows PDF',full?'Whole bound PDF saved':'Filtered '+indexes.length+'-page PDF saved',path);
 }catch(err){
   console.error('Ink Pot PDF failed',err);
   gmInkSetStatus('PDF could not be saved',String(err&&err.message||err),'error');
   gmBosShowJobNotice('Book of Shadows PDF','PDF could not be saved',String(err&&err.message||err));
 }finally{gmInkUpdatePrintSummary(gmInkBoundCatalog());if(btn&&gmInkBoundCatalog())btn.disabled=false}
}
'''
scribe = scribe[:active_start] + active_new + scribe[active_end:]

old_marker = '<!-- INKPOT FIX V2.7.28: one active handler; whole-book direct copy; chapter/page/spell selections cut natively from the stored bound PDF. -->'
new_marker = '<!-- INKPOT FIX V2.7.29: whole-book direct copy; filtered chapter/page/spell PDFs rebuilt from exactly the selected bound flat pages. -->'
if old_marker not in scribe:
    raise SystemExit('V2.7.28 Ink Pot marker not found')
scribe = scribe.replace(old_marker, new_marker, 1)
if scribe.count('async function gmInkPrintBound(){') != 1:
    raise SystemExit('Expected one active gmInkPrintBound handler after hotfix')
src = replace_page(src, 'scribe', scribe)

# V2.7.28 accidentally placed this CSS after </style>, making it visible page text.
# Contain that same geometry CSS properly. Do not change furniture order or artwork.
_s, _n, cupboard = decode_page(src, 'cupboard')
raw_css = '''/* TOP FURNITURE JOIN V2.7.28: the lower cupboards and drawers physically meet the Supply/Spell cupboard row. */
.door-bank-top{margin-bottom:0!important;padding-bottom:0!important}
#hedgeShelves{margin-top:-1px!important}
#hedgeShelves>.feature-room-row:first-child{margin-top:-1px!important;margin-bottom:0!important;border-top-width:5px!important}
#hedgeShelves>.feature-room-row + .incense-drawer-row{margin-top:-1px!important}
#hedgeShelves>.incense-drawer-row + .daily-drawer-row{margin-top:-1px!important}
#hedgeShelves>.daily-drawer-row + .shelf.hedge-owned-shelf{margin-top:10px!important}

<!-- CUPBOARD LAYOUT FIX V2.7.28: Bower/Scribe and drawers joined directly beneath Supply/Spell. -->'''
fixed_css = '''<style id="gmTopFurnitureJoin2729">
/* TOP FURNITURE JOIN V2.7.29: lower cupboards and drawers meet the Supply/Spell cupboard row. */
.door-bank-top{margin-bottom:0!important;padding-bottom:0!important}
#hedgeShelves{margin-top:-1px!important}
#hedgeShelves>.feature-room-row:first-child{margin-top:-1px!important;margin-bottom:0!important;border-top-width:5px!important}
#hedgeShelves>.feature-room-row + .incense-drawer-row{margin-top:-1px!important}
#hedgeShelves>.incense-drawer-row + .daily-drawer-row{margin-top:-1px!important}
#hedgeShelves>.daily-drawer-row + .shelf.hedge-owned-shelf{margin-top:10px!important}
</style>
<!-- CUPBOARD LAYOUT FIX V2.7.29: furniture order unchanged; join CSS is now correctly contained in style. -->'''
if raw_css not in cupboard:
    raise SystemExit('Visible V2.7.28 cupboard CSS block not found')
cupboard = cupboard.replace(raw_css, fixed_css, 1)
src = replace_page(src, 'cupboard', cupboard)

outer_old = '<!-- FV 2.7.28 PDF + CUPBOARD FIX: native selected-page PDF export; joined top furniture stack. -->'
outer_new = '<!-- FV 2.7.29 HOTFIX: filtered PDF uses exact selected bound pages; cupboard join CSS contained correctly. -->'
if outer_old in src:
    src = src.replace(outer_old, outer_new, 1)
elif outer_new not in src:
    src = src.replace('</head>', outer_new + '\n</head>', 1)

Path(sys.argv[2]).write_text(src, encoding='utf-8')
data = src.encode('utf-8')
print('bytes', len(data))
print('sha256', hashlib.sha256(data).hexdigest())
