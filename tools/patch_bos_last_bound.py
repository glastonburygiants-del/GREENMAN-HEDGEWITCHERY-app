#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def extract_function(text: str, signature: str) -> str:
    start = text.find(signature)
    if start < 0:
        raise SystemExit(f"Missing function: {signature}")
    brace = text.find("{", start)
    depth = 0
    quote = None
    escaped = line_comment = block_comment = False
    i = brace
    while i < len(text):
        char = text[i]
        following = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
        elif block_comment:
            if char == "*" and following == "/":
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        else:
            if char == "/" and following == "/":
                line_comment = True
                i += 1
            elif char == "/" and following == "*":
                block_comment = True
                i += 1
            elif char in "'\"`":
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        i += 1
    raise SystemExit(f"Unclosed function: {signature}")


CAPTURE = r'''async function gmBosFlatBlobFromSheet(sheet,index,total,binding){
 const captureStarted=Date.now();
 if(binding&&binding.registry&&binding.registry.defs&&binding.registry.defs.parentNode)sheet.prepend(binding.registry.defs.parentNode.cloneNode(true));
 if(typeof window.html2canvas!=='function')throw new Error('The mobile page-capture engine did not load');
 await gmBosInlineBlobImages(sheet);
 const host=document.createElement('div');host.setAttribute('aria-hidden','true');host.style.cssText='position:fixed;left:0;top:0;width:794px;height:1123px;margin:0;padding:0;overflow:hidden;pointer-events:none;z-index:-2147483648;background:#f4ecd8;display:block';host.append(sheet);document.body.append(host);
 try{
  await Promise.all(qa('img',sheet).map(gmBosWaitImage));try{if(document.fonts&&document.fonts.ready)await document.fonts.ready}catch(_e){}await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const scale=1.5,minimumWidth=Math.floor(794*scale)-2,minimumHeight=Math.floor(1123*scale)-2,canvas=await window.html2canvas(sheet,{backgroundColor:'#f4ecd8',width:794,height:1123,scale:scale,useCORS:true,allowTaint:false,logging:false,removeContainer:true,imageTimeout:20000,scrollX:0,scrollY:0,windowWidth:794,windowHeight:1123});if(!canvas||canvas.width<minimumWidth||canvas.height<minimumHeight)throw new Error('A4 page '+(index+1)+' returned an incomplete image'+(canvas?' ('+canvas.width+' × '+canvas.height+')':''));
  const width=canvas.width,height=canvas.height,quality=total>300?.72:total>120?.74:.77,blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',quality));canvas.width=1;canvas.height=1;if(!blob)throw new Error('A4 page '+(index+1)+' could not be compressed');gmBosDiag('BIND CAPTURE','A4 image completed',{page:index+1,total:total,width:width,height:height,jpegBytes:blob.size,durationMs:Date.now()-captureStarted});return {blob:blob,width:width,height:height}
 }finally{host.remove()}
}'''


NATIVE_HELPERS = r'''function gmBosNativeFiles(){
 try{if(window.GreenmanFiles)return window.GreenmanFiles}catch(_e){}try{if(parent&&parent.GreenmanFiles)return parent.GreenmanFiles}catch(_e2){}return null
}
function gmBosStoredBookAvailable(){
 const api=gmBosNativeFiles();try{return !!(api&&typeof api.hasLastBoundPdf==='function'&&api.hasLastBoundPdf())}catch(_e){return false}
}
async function gmBosStoreLastBoundPdf(blob,options){
 const api=gmBosNativeFiles();if(!api||typeof api.beginLastBoundPdf!=='function'||typeof api.appendLastBoundPdfChunk!=='function')return false;
 if(!api.beginLastBoundPdf(blob.size))throw new Error('Android could not open the Last Bound Book file');
 try{
  const saveStarted=Date.now(),step=393216,total=Math.max(1,Math.ceil(blob.size/step));gmBosDiag('BIND STORAGE','Native PDF save started',{pdfBytes:blob.size,chunks:total});
  for(let offset=0,part=0;offset<blob.size;offset+=step,part++){
   const slice=blob.slice(offset,Math.min(blob.size,offset+step),'application/octet-stream'),data=await gmBosBlobDataUrl(slice),encoded=data.slice(data.indexOf(',')+1),last=offset+step>=blob.size;
   if(!api.appendLastBoundPdfChunk(encoded,last))throw new Error('Android could not finish the Last Bound Book file');
   if(options&&typeof options.onStorageProgress==='function')options.onStorageProgress(part+1,total);await new Promise(r=>setTimeout(r,0))
  }
  gmBosDiag('BIND STORAGE','Native PDF save completed',{pdfBytes:blob.size,chunks:total,durationMs:Date.now()-saveStarted});return true
 }catch(err){try{if(typeof api.abortLastBoundPdf==='function')api.abortLastBoundPdf()}catch(_e){}throw err}
}
function gmBosExportStoredBook(){
 const api=gmBosNativeFiles();if(!api||typeof api.exportLastBoundPdf!=='function'||!gmBosStoredBookAvailable()){alert('No Last Bound Book PDF is stored yet.');return false}
 const ok=!!api.exportLastBoundPdf();alert(ok?'Last Bound Book copied to Downloads / Greenman HedgeWitchery.':'The Last Bound Book could not be copied.');return ok
}
'''


FLATTEN_BOUND = r'''async function flattenBound(options){
 options=options||{};if(!boundPlan||!boundPlan.rows.length)return null;const bindStarted=Date.now(),chosen=boundPlan.rows.map(r=>r.page),map=gmBosBuildPrintMap(chosen),btn=options.button||null,old=btn?btn.textContent:'';gmBosClearPrintRoot();if(btn){btn.disabled=true;btn.textContent='Flattening 0/'+chosen.length}gmBosDiag('BIND START','Binding selected BoS pages',{pages:chosen.length})
 try{
  const flats=await gmBosFlattenNodes(chosen,'original',options,map);flats.forEach((flat,i)=>boundPlan.rows[i].flat=flat);boundPlan.flatReady=flats.length===chosen.length;if(!boundPlan.flatReady)return null;
  const native=gmBosNativeFiles();if(native){if(btn)btn.textContent='Saving Last Bound Book…';if(typeof options.onSaving==='function')options.onSaving();const pdf=await gmBosBuildFlatPdf(flats);boundPlan.nativeSaved=await gmBosStoreLastBoundPdf(pdf,options);boundPlan.nativePdfSize=pdf.size}else{boundPlan.nativeSaved=false}
  gmBosDiag('BIND COMPLETE','Selected BoS pages were bound',{pages:chosen.length,nativeSaved:!!boundPlan.nativeSaved,pdfBytes:Number(boundPlan.nativePdfSize||0),durationMs:Date.now()-bindStarted});return getBoundCatalog()
 }catch(err){gmBosDiag('BIND ERROR','Binding failed',{message:String(err&&err.message||err),durationMs:Date.now()-bindStarted},true);console.error('Greenman BoS binding failed',err);boundPlan=null;const detail=String(err&&err.message||err||'Page capture failed');alert('The selected pages could not be bound.\n\n'+detail);return null}finally{if(btn){btn.disabled=false;btn.textContent=old||'Bind Book'}}
}'''


INK_DIAGNOSTICS = r'''function gmBosDiag(level,message,detail,severe){
 try{const api=parent&&parent.gmTabletDiagnosticsV1;if(api&&typeof api.add==='function')api.add(level,'Scribe BoS / Ink Pot',message,detail||'','',!!severe)}catch(_e){}
}
function gmInkTargetInfo(target){
 try{const el=target&&target.closest?target.closest('button,a,input,select,label,[role="button"]'):target;if(!el)return {target:'none'};const style=getComputedStyle(el),r=el.getBoundingClientRect();return {tag:el.tagName||'',id:el.id||'',className:String(el.className||''),text:String(el.textContent||el.value||'').trim().slice(0,90),disabled:!!el.disabled,pointerEvents:style.pointerEvents,display:style.display,visibility:style.visibility,rect:{left:Math.round(r.left),top:Math.round(r.top),width:Math.round(r.width),height:Math.round(r.height)}}}catch(err){return {inspectionError:String(err&&err.message||err)}}
}
function gmInkSnapshot(reason){
 try{const cat=gmInkBoundCatalog(),modal=document.querySelector('.modal.open'),desk=$('.inkPrintDesk'),ids=['gmInkPrintBoundBtn','gmInkExportLastBoundBtn','gmInkReturnLiveBtn'],controls={};ids.forEach(id=>{const el=$('#'+id);controls[id]=el?Object.assign(gmInkTargetInfo(el),{handler:typeof el.onclick==='function'}):{missing:true}});gmBosDiag('INK STATE',reason,{activeViews:$$('.view.active').map(x=>x.id),modal:modal?{id:modal.id,className:modal.className}:null,deskClass:desk&&desk.className||'',catalog:cat?{pages:cat.pages.length,chapters:cat.chapters.length,nativeSaved:!!cat.nativeSaved,nativePdfSize:Number(cat.nativePdfSize||0)}:null,mode:GM_INK_PRINT.mode,busy:!!GM_INK_PRINT.busy,chosenPages:cat?gmInkChosenPageKeys(cat).length:0,controls:controls})}catch(err){gmBosDiag('INK DIAGNOSTIC ERROR','Ink Pot state inspection failed',String(err&&err.message||err),true)}
}
function gmInkInstallDiagnostics(){
 if(document.__gmInkDiagnosticsV1)return;document.__gmInkDiagnosticsV1=true;
 const active=()=>{const ink=$('#inkView'),modal=$('#gmBosBindModal');return !!((ink&&ink.classList.contains('active'))||(modal&&modal.classList.contains('open')))};
 document.addEventListener('pointerdown',ev=>{if(active())gmBosDiag('INK POINTER','Pointer reached Scribe document',gmInkTargetInfo(ev.target))},true);
 document.addEventListener('click',ev=>{if(active())gmBosDiag('INK CLICK','Click reached Scribe document',gmInkTargetInfo(ev.target))},true);
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')setTimeout(()=>gmInkSnapshot('Scribe became visible again'),0)});
 window.addEventListener('pageshow',()=>setTimeout(()=>gmInkSnapshot('Scribe page shown again'),0));
}
'''


INK_RENDER = r'''function renderInkPrintRoom(){
 const line=$('#gmInkBoundBookLine'),btn=$('#gmInkPrintBoundBtn'),stored=$('#gmInkExportLastBoundBtn'),back=$('#gmInkReturnLiveBtn');if(!line||!btn){gmBosDiag('INK SETUP ERROR','Required Ink Pot controls are missing',{line:!!line,button:!!btn},true);return}
 btn.onclick=gmInkPrintBound;if(back)back.onclick=openBos;
 if(stored){const available=!!(typeof GM_BOS!=='undefined'&&typeof GM_BOS.hasStoredBook==='function'&&GM_BOS.hasStoredBook());stored.disabled=!available;stored.onclick=()=>GM_BOS.exportStoredBook()}
 gmInkBuildHandOptions();const cat=gmInkBoundCatalog();gmInkResetChoices(cat);
 $$('[data-gm-print-mode]').forEach(b=>{b.classList.toggle('active',b.dataset.gmPrintMode===GM_INK_PRINT.mode);b.disabled=!cat;b.onclick=()=>{GM_INK_PRINT.mode=b.dataset.gmPrintMode;renderInkPrintRoom()}});
 if(!cat){line.className='inkBoundBookLine empty';line.innerHTML='<strong>No book bound in this session</strong>Open the live Book, choose chapters on Main Contents, then press Bind Book.'}
 else{line.className='inkBoundBookLine';line.innerHTML='<strong>'+cat.pages.length+' A4 pages are bound</strong>'+esc(cat.chapterNames.join(' · '))}
 gmInkRenderPicker(cat);gmInkBindPickerEvents(cat);gmInkUpdatePrintSummary(cat);gmInkSnapshot('Ink Pot controls rendered')
}'''


INK_PRINT = r'''async function gmInkPrintBound(){
 const btn=$('#gmInkPrintBoundBtn'),sel=$('#gmInkBosHand'),desk=btn&&btn.closest('.inkPrintDesk'),cat=gmInkBoundCatalog();if(!btn||!sel||!cat)return;const pageKeys=gmInkChosenPageKeys(cat);if(!pageKeys.length)return;if(GM_INK_PRINT.busy){gmInkSnapshot('Duplicate PDF tap ignored while busy');return}
 GM_INK_PRINT.busy=true;const started=Date.now(),ready=$('#gmInkPdfReady');if(ready)ready.classList.remove('open');if(desk)desk.classList.add('inkPrintBusy');gmBosDiag('INK PDF','Create Flat A4 PDF started',{pages:pageKeys.length,script:sel.value||'original'});
 try{const result=await GM_BOS.printBound({button:btn,scriptId:sel.value||'original',pageKeys:pageKeys});gmBosDiag('INK PDF','Flat A4 PDF completed',{pages:pageKeys.length,script:sel.value||'original',durationMs:Date.now()-started,result:result||null})}
 finally{GM_INK_PRINT.busy=false;if(desk)desk.classList.remove('inkPrintBusy');gmInkUpdatePrintSummary(gmInkBoundCatalog());gmInkSnapshot('Ink Pot PDF task released controls')}
}'''


OFFER_PDF = r'''function gmBosOfferFlatPdf(blob,filename,pageCount){
 if(gmBosReadyPdfUrl){try{URL.revokeObjectURL(gmBosReadyPdfUrl)}catch(_e){}}gmBosReadyPdfUrl=URL.createObjectURL(blob);const box=$('#gmInkPdfReady'),link=$('#gmInkPdfLink'),note=$('#gmInkPdfReadyText');if(link){link.href=gmBosReadyPdfUrl;link.download=filename;link.target='_blank';link.rel='noopener'}if(note)note.textContent=pageCount+' flat A4 pages · '+(blob.size/1048576).toFixed(1)+' MB';if(box)box.classList.add('open');gmBosDiag('INK PDF','PDF link is ready for a separate tap',{pages:pageCount,pdfBytes:blob.size,filename:filename});return {blob:blob,url:gmBosReadyPdfUrl,filename:filename,size:blob.size}
}'''


def patch_scribe(page: str) -> str:
    page = replace_once(page, "function gmInkSetTab(name){", INK_DIAGNOSTICS + "function gmInkSetTab(name){", "Ink Pot diagnostics")
    page = replace_once(
        page,
        "function openInkpotPrintRoom(){showView('ink');gmInkSetTab('print');renderInkPrintRoom()}",
        "function openInkpotPrintRoom(){showView('ink');gmInkSetTab('print');gmInkInstallDiagnostics();renderInkPrintRoom();gmInkSnapshot('Ink Pot opened')}",
        "Ink Pot opening diagnostics",
    )
    page = replace_once(
        page,
        "const GM_INK_PRINT={mode:'full',token:'',chapterIds:new Set(),pageKeys:new Set(),spellIds:new Set(),spellSections:new Set(['spell-list','altars','summaries','timings','instructions'])};",
        "const GM_INK_PRINT={mode:'full',token:'',busy:false,chapterIds:new Set(),pageKeys:new Set(),spellIds:new Set(),spellSections:new Set(['spell-list','altars','summaries','timings','instructions'])};",
        "Ink Pot busy state",
    )

    old_capture = extract_function(page, "async function gmBosFlatBlobFromSheet(")
    page = replace_once(page, old_capture, CAPTURE, "same-document A4 capture")

    anchor = "async function gmBosFlattenNodes(chosen,scriptId,options,printMap){"
    page = replace_once(page, anchor, NATIVE_HELPERS + anchor, "native PDF helpers")

    old_flatten = extract_function(page, "async function flattenBound(")
    page = replace_once(page, old_flatten, FLATTEN_BOUND, "binding and native save")

    old_offer = extract_function(page, "function gmBosOfferFlatPdf(")
    page = replace_once(page, old_offer, OFFER_PDF, "manual PDF opening")

    old_print = extract_function(page, "async function gmInkPrintBound(")
    page = replace_once(page, old_print, INK_PRINT, "Ink Pot PDF control release")

    old_return = "return {token:boundPlan.token,boundAt:boundPlan.boundAt,pages:pagesOut,chapters:chapters,chapterNames:chapters.map(x=>x.title),spells:boundPlan.spells.map(x=>({id:x.id,name:x.name,title:x.name,detail:Object.values(x.pagesByChapter).reduce((n,a)=>n+a.length,0)+' matching pages',pagesByChapter:x.pagesByChapter}))}"
    new_return = "return {token:boundPlan.token,boundAt:boundPlan.boundAt,nativeSaved:!!boundPlan.nativeSaved,nativePdfSize:Number(boundPlan.nativePdfSize||0),pages:pagesOut,chapters:chapters,chapterNames:chapters.map(x=>x.title),spells:boundPlan.spells.map(x=>({id:x.id,name:x.name,title:x.name,detail:Object.values(x.pagesByChapter).reduce((n,a)=>n+a.length,0)+' matching pages',pagesByChapter:x.pagesByChapter}))}"
    page = replace_once(page, old_return, new_return, "bound catalog native status")

    old_controls = '<div class="inkPrintActions"><button id="gmInkPrintBoundBtn" class="brassBtn inkPrintPrimary" type="button" disabled>Create Flat A4 PDF</button><button id="gmInkReturnLiveBtn" class="tagBtn" type="button">Return to Live Book</button></div><div id="gmInkPdfReady"'
    new_controls = '<div class="inkPrintActions"><button id="gmInkPrintBoundBtn" class="brassBtn inkPrintPrimary" type="button" disabled>Create Flat A4 PDF</button><button id="gmInkExportLastBoundBtn" class="brassBtn" type="button" disabled>Export Last Bound PDF</button><button id="gmInkReturnLiveBtn" class="tagBtn" type="button">Return to Live Book</button></div><div id="gmInkPdfReady"'
    page = replace_once(page, old_controls, new_controls, "Ink Pot stored PDF button")

    old_storage = '<p class="inkPrintStorage"><b>No PDF backup is kept in browser storage.</b> The finished file is offered to the device and remains there only if you save it.</p>'
    new_storage = '<p class="inkPrintStorage"><b>One Last Bound Book PDF is kept in private app storage.</b> A new binding replaces it. It is excluded from the JSON backup.</p>'
    page = replace_once(page, old_storage, new_storage, "storage explanation")

    old_render = extract_function(page, "function renderInkPrintRoom(")
    page = replace_once(page, old_render, INK_RENDER, "Ink Pot stored state and controls")

    old_api = "return {open,close,show,jump,chapterContents,prev,next,bindSelected,flattenBound,getBoundCatalog,printBound,printSelected,get pages(){return pages},get spells(){return spells}};"
    new_api = "return {open,close,show,jump,chapterContents,prev,next,bindSelected,flattenBound,getBoundCatalog,printBound,printSelected,hasStoredBook:gmBosStoredBookAvailable,exportStoredBook:gmBosExportStoredBook,get pages(){return pages},get spells(){return spells}};"
    page = replace_once(page, old_api, new_api, "public native PDF storage interface")

    old_page_loop = "if(progress)progress(0,chosen.length,'flattening');for(let i=0;i<chosen.length;i++){if(btn)btn.textContent='Flattening '+(i+1)+'/'+chosen.length;const sheet=await gmBosPreparePrintPage(chosen[i],i,chosen.length,binding,printMap);out.push(await gmBosFlatBlobFromSheet(sheet,i,chosen.length,binding));gmBosRevokePrintObjectUrls();if(progress)progress(i+1,chosen.length,'flattening');await new Promise(r=>setTimeout(r,0))}return out"
    new_page_loop = "if(progress)progress(0,chosen.length,'flattening');for(let i=0;i<chosen.length;i++){const pageStarted=Date.now();if(btn)btn.textContent='Flattening '+(i+1)+'/'+chosen.length;const sheet=await gmBosPreparePrintPage(chosen[i],i,chosen.length,binding,printMap),flat=await gmBosFlatBlobFromSheet(sheet,i,chosen.length,binding);out.push(flat);gmBosRevokePrintObjectUrls();gmBosDiag('BIND PAGE','A4 page fully prepared and captured',{page:i+1,total:chosen.length,jpegBytes:flat.blob.size,durationMs:Date.now()-pageStarted});if(progress)progress(i+1,chosen.length,'flattening');await new Promise(r=>setTimeout(r,0))}return out"
    page = replace_once(page, old_page_loop, new_page_loop, "per-page binding timing")

    old_call = "const result=await GM_BOS.flattenBound({button:btn,onProgress:(done,total)=>{summary.innerHTML='<strong>Flattening '+done+' of '+total+' A4 pages</strong>The selected chapters are becoming a fixed bound copy.'}});"
    new_call = "const result=await GM_BOS.flattenBound({button:btn,onProgress:(done,total)=>{summary.innerHTML='<strong>Flattening '+done+' of '+total+' A4 pages</strong>The selected chapters are becoming a fixed bound copy.'},onSaving:()=>{summary.innerHTML='<strong>Saving Last Bound Book PDF</strong>The finished flat book is being placed in private app storage.'},onStorageProgress:(done,total)=>{summary.innerHTML='<strong>Saving Last Bound Book PDF · '+done+'/'+total+'</strong>The previous bound PDF will be replaced.'}});"
    page = replace_once(page, old_call, new_call, "binding storage progress")

    old_success = "title.textContent='Book of Shadows Bound';summary.innerHTML='<strong>'+result.pages.length+' A4 pages flattened and bound</strong>No printer has opened. Choose whether to stay in the live book or go to the Ink Pot.'"
    new_success = "title.textContent='Book of Shadows Bound';summary.innerHTML='<strong>'+result.pages.length+' A4 pages flattened and bound</strong>'+(result.nativeSaved?'The Last Bound Book PDF is stored safely in the app. A new binding will replace it.':'The bound copy is ready for the Ink Pot.')"
    page = replace_once(page, old_success, new_success, "binding success message")

    required = [
        "GreenmanFiles",
        "beginLastBoundPdf",
        "appendLastBoundPdfChunk",
        "gmInkExportLastBoundBtn",
        "hasStoredBook:gmBosStoredBookAvailable",
        "PDF link is ready for a separate tap",
        "Ink Pot controls rendered",
        "One Last Bound Book PDF is kept in private app storage.",
        "const host=document.createElement('div')",
    ]
    missing = [item for item in required if item not in page]
    if missing:
        raise SystemExit("Missing V26 BoS requirements: " + ", ".join(missing))
    if "const frame=document.createElement('iframe')" in extract_function(page, "async function gmBosFlatBlobFromSheet("):
        raise SystemExit("Cross-document capture frame remains")
    return page


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_bos_last_bound.py INPUT.html OUTPUT.html")
    source, destination = map(Path, sys.argv[1:])
    text = source.read_text(encoding="utf-8")
    marker = "PAGES.scribe = "
    start = text.index(marker) + len(marker)
    page, consumed = json.JSONDecoder().raw_decode(text[start:])
    page = patch_scribe(page)
    encoded = json.dumps(page, ensure_ascii=False, separators=(",", ":"))
    encoded = re.sub(r"</script", r"<\\/script", encoded, flags=re.IGNORECASE)
    output = text[:start] + encoded + text[start + consumed:]
    destination.write_text(output, encoding="utf-8")
    print("V26 Ink Pot controls, safe PDF opening, and timing diagnostics patch passed.")


if __name__ == "__main__":
    main()
