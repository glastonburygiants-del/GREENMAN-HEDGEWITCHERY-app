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


WAIT_IMAGE = r'''function gmBosWaitImage(img){
 if(!img)return Promise.resolve();
 if(img.complete&&img.naturalWidth)return Promise.resolve();
 return new Promise(resolve=>{
  let settled=false,timer=0;
  const done=()=>{if(settled)return;settled=true;if(timer)clearTimeout(timer);try{img.removeEventListener('load',done);img.removeEventListener('error',done)}catch(_e){}resolve()};
  try{img.addEventListener('load',done,{once:true});img.addEventListener('error',done,{once:true})}catch(_e){}
  try{if(img.decode)img.decode().then(done,done)}catch(_e){}
  timer=setTimeout(done,2500)
 })
}'''


INLINE_BLOB_IMAGES = r'''async function gmBosInlineBlobImages(root){
 const imgs=qa('img',root).filter(img=>/^blob:/i.test(img.currentSrc||img.src||''));
 await Promise.all(imgs.map(async img=>{const src=img.currentSrc||img.src||'';try{img.src=await gmBosBlobDataUrl(await fetch(src).then(r=>r.blob()))}catch(_e){}}))
}'''


CAPTURE = r'''async function gmBosFlatBlobFromSheet(sheet,index,total,binding,options){
 const captureStarted=Date.now();
 gmBosThrowIfCancelled(options);
 if(binding&&binding.registry&&binding.registry.defs&&binding.registry.defs.parentNode)sheet.prepend(binding.registry.defs.parentNode.cloneNode(true));
 if(typeof window.html2canvas!=='function')throw new Error('The mobile page-capture engine did not load');
 const frame=document.createElement('iframe');frame.setAttribute('aria-hidden','true');frame.style.cssText='position:fixed;left:-14000px;top:0;width:794px;height:1123px;border:0;margin:0;padding:0;overflow:hidden;pointer-events:none;opacity:.01;z-index:-1';document.body.append(frame);
 try{
  const fd=frame.contentDocument;if(!fd)throw new Error('The isolated A4 page could not be opened');fd.open();fd.write('<!doctype html><html><head><meta charset="utf-8"></head><body></body></html>');fd.close();const st=fd.createElement('style');st.textContent=gmBosRasterStyles();fd.head.append(st);sheet=fd.adoptNode(sheet);fd.body.style.cssText='margin:0;padding:0;width:794px;height:1123px;overflow:hidden;background:#f4ecd8';fd.body.append(sheet);
  let phase=Date.now();await gmBosInlineBlobImages(sheet);const inlineMs=Date.now()-phase;gmBosThrowIfCancelled(options);
  phase=Date.now();await Promise.all(qa('img',sheet).map(gmBosWaitImage));const imageReadyMs=Date.now()-phase;gmBosThrowIfCancelled(options);
  phase=Date.now();try{if(fd.fonts&&fd.fonts.ready)await Promise.race([fd.fonts.ready,new Promise(resolve=>setTimeout(resolve,2500))])}catch(_e){}const fontReadyMs=Date.now()-phase;gmBosThrowIfCancelled(options);
  phase=Date.now();const raf=fd.defaultView&&fd.defaultView.requestAnimationFrame?fd.defaultView.requestAnimationFrame.bind(fd.defaultView):requestAnimationFrame;await new Promise(r=>raf(()=>raf(r)));const settleMs=Date.now()-phase;gmBosThrowIfCancelled(options);
  const scale=1.5,minimumWidth=Math.floor(794*scale)-2,minimumHeight=Math.floor(1123*scale)-2;phase=Date.now();const canvas=await window.html2canvas(sheet,{backgroundColor:'#f4ecd8',width:794,height:1123,scale:scale,useCORS:true,allowTaint:false,logging:false,removeContainer:true,imageTimeout:20000,scrollX:0,scrollY:0,windowWidth:794,windowHeight:1123}),canvasMs=Date.now()-phase;if(!canvas||canvas.width<minimumWidth||canvas.height<minimumHeight)throw new Error('A4 page '+(index+1)+' returned an incomplete image'+(canvas?' ('+canvas.width+' × '+canvas.height+')':''));
  if(gmBosIsCancelled(options)){canvas.width=1;canvas.height=1;gmBosThrowIfCancelled(options)}
  const width=canvas.width,height=canvas.height,quality=total>300?.72:total>120?.74:.77;phase=Date.now();const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',quality)),jpegMs=Date.now()-phase;canvas.width=1;canvas.height=1;if(!blob)throw new Error('A4 page '+(index+1)+' could not be compressed');gmBosDiag('BIND CAPTURE','A4 image completed',{page:index+1,total:total,width:width,height:height,jpegBytes:blob.size,inlineMs:inlineMs,imageReadyMs:imageReadyMs,fontReadyMs:fontReadyMs,settleMs:settleMs,canvasMs:canvasMs,jpegMs:jpegMs,durationMs:Date.now()-captureStarted});return {blob:blob,width:width,height:height}
 }finally{frame.remove()}
}'''


NATIVE_HELPERS = r'''function gmBosNativeFiles(){
 try{if(window.GreenmanFiles)return window.GreenmanFiles}catch(_e){}try{if(parent&&parent.GreenmanFiles)return parent.GreenmanFiles}catch(_e2){}return null
}
function gmBosStoredBookAvailable(){
 const api=gmBosNativeFiles();try{return !!(api&&typeof api.hasLastBoundPdf==='function'&&api.hasLastBoundPdf())}catch(_e){return false}
}
function gmBosIsCancelled(options){return !!(options&&options.cancelToken&&options.cancelToken.cancelled)}
function gmBosThrowIfCancelled(options){if(!gmBosIsCancelled(options))return;const err=new Error('Binding cancelled');err.gmBosCancelled=true;throw err}
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
 }catch(err){if(err&&err.gmBosCancelled){gmBosDiag('BIND CANCELLED','Binding stopped safely',{durationMs:Date.now()-bindStarted});boundPlan=null;return {cancelled:true}}gmBosDiag('BIND ERROR','Binding failed',{message:String(err&&err.message||err),durationMs:Date.now()-bindStarted},true);console.error('Greenman BoS binding failed',err);boundPlan=null;const detail=String(err&&err.message||err||'Page capture failed');alert('The selected pages could not be bound.\n\n'+detail);return null}finally{if(btn){btn.disabled=false;btn.textContent=old||'Bind Book'}}
}'''


BIND_UI = r'''let gmBosActiveBindCancel=null;
function gmBosCancelCurrentBind(){
 const token=gmBosActiveBindCancel,modal=$('#gmBosBindModal'),title=$('#gmBosBindTitle'),summary=$('#gmBosBindSummary'),btn=$('#gmBosCancelBind');if(!token||token.cancelled)return;
 token.cancelled=true;if(modal)modal.classList.add('cancelling');if(title)title.textContent='Cancelling Binding';if(summary)summary.innerHTML='<strong>Stopping after the current page</strong>The unfinished new book will be discarded. Your previously saved PDF will not be changed.';if(btn){btn.disabled=true;btn.textContent='Cancelling…'}gmBosDiag('BIND CANCEL','Cancel requested by user',{completedPages:Number(token.completedPages||0)})
}
async function gmBosBindCurrentSelection(){
 const cat=GM_BOS.bindSelected(),modal=$('#gmBosBindModal'),title=$('#gmBosBindTitle'),summary=$('#gmBosBindSummary'),btn=$('#gmBosBindBookBtn'),cancelBtn=$('#gmBosCancelBind');if(!cat||!modal||!title||!summary||!btn)return;
 const cancelToken={cancelled:false,completedPages:0};gmBosActiveBindCancel=cancelToken;if(cancelBtn){cancelBtn.disabled=false;cancelBtn.textContent='Cancel Binding'}
 title.textContent='Binding Book of Shadows';summary.innerHTML='<strong>Flattening 0 of '+cat.pages.length+' A4 pages</strong>The Main Contents selection is becoming a fixed bound copy.';modal.classList.remove('cancelling');modal.classList.add('open','binding');
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
 const result=await GM_BOS.flattenBound({button:btn,cancelToken:cancelToken,onProgress:(done,total)=>{cancelToken.completedPages=done;if(!cancelToken.cancelled)summary.innerHTML='<strong>Flattening '+done+' of '+total+' A4 pages</strong>The selected chapters are becoming a fixed bound copy.'},onSaving:()=>{summary.innerHTML='<strong>Saving Last Bound Book PDF</strong>The finished flat book is being placed in private app storage.'},onStorageProgress:(done,total)=>{summary.innerHTML='<strong>Saving Last Bound Book PDF · '+done+'/'+total+'</strong>The previous bound PDF will be replaced.'}});
 gmBosActiveBindCancel=null;modal.classList.remove('binding','cancelling');if(result&&result.cancelled){title.textContent='Binding Cancelled';summary.innerHTML='<strong>No unfinished book was kept</strong>Your previously saved PDF was not changed.';return}if(!result){title.textContent='Binding could not be completed';summary.innerHTML='<strong>No bound copy was kept</strong>Return to Main Contents and try a smaller selection.';return}
 title.textContent='Book of Shadows Bound';summary.innerHTML='<strong>'+result.pages.length+' A4 pages flattened and bound</strong>'+(result.nativeSaved?'The Last Bound Book PDF is stored safely in the app. A new binding will replace it.':'The bound copy is ready for the Ink Pot.')
}'''


INK_DIAGNOSTICS = r'''function gmBosDiag(level,message,detail,severe){
 try{const api=parent&&parent.gmTabletDiagnosticsV1;if(api&&typeof api.add==='function')api.add(level,'Scribe BoS / Ink Pot',message,detail||'','',!!severe)}catch(_e){}
}
function gmInkTargetInfo(target){
 try{const el=target&&target.closest?target.closest('button,a,input,select,label,[role="button"]'):target;if(!el)return {target:'none'};const style=getComputedStyle(el),r=el.getBoundingClientRect();return {tag:el.tagName||'',id:el.id||'',className:String(el.className||''),text:String(el.textContent||el.value||'').trim().slice(0,90),disabled:!!el.disabled,pointerEvents:style.pointerEvents,display:style.display,visibility:style.visibility,rect:{left:Math.round(r.left),top:Math.round(r.top),width:Math.round(r.width),height:Math.round(r.height)}}}catch(err){return {inspectionError:String(err&&err.message||err)}}
}
function gmInkSnapshot(reason){
 try{const cat=gmInkBoundCatalog(),modal=document.querySelector('.modal.open'),desk=$('.inkPrintDesk'),ids=['gmInkPrintBoundBtn','gmScribeConvertBtn','gmScribeCancelJob','gmInkReturnLiveBtn'],controls={};ids.forEach(id=>{const el=$('#'+id);controls[id]=el?Object.assign(gmInkTargetInfo(el),{handler:typeof el.onclick==='function'}):{missing:true}});gmBosDiag('INK STATE',reason,{activeViews:$$('.view.active').map(x=>x.id),modal:modal?{id:modal.id,className:modal.className}:null,deskClass:desk&&desk.className||'',catalog:cat?{pages:cat.pages.length,chapters:cat.chapters.length,nativeSaved:!!cat.nativeSaved,nativePdfSize:Number(cat.nativePdfSize||0)}:null,mode:GM_INK_PRINT.mode,busy:gmBosBusyState((typeof GM_BOS!=='undefined'&&GM_BOS.jobStatus?GM_BOS.jobStatus():{}).state),chosenPages:cat?gmInkChosenPageKeys(cat).length:0,controls:controls})}catch(err){gmBosDiag('INK DIAGNOSTIC ERROR','Ink Pot state inspection failed',String(err&&err.message||err),true)}
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


V29_GET_CATALOG = r'''function getBoundCatalog(){
 if(!boundPlan||!boundPlan.rows||!boundPlan.rows.length){const saved=parse(lsGet(SKEYS.boundCatalog)||'null',null);return saved&&Array.isArray(saved.pages)&&saved.pages.length?saved:null}const chMap=new Map(CHAPTERS.map(c=>[c.id,c]));
 const pagesOut=boundPlan.rows.map((r,i)=>{const c=chMap.get(r.chapterId),chapterTitle=r.chapterId==='cover'?'Front Cover':r.chapterId==='contents'?'Main Contents':c?c.title:r.chapterId||'Book of Shadows';return {key:r.key,title:r.title,chapterId:r.chapterId,sourceIndex:Number.isFinite(r.sourceIndex)?r.sourceIndex:pages.indexOf(r.page),detail:chapterTitle+' · bound page '+(i+1)}});
 const chapters=boundPlan.chapterIds.map(id=>{const c=chMap.get(id);return {id:id,title:c?c.num+' · '+c.title:id,detail:pagesOut.filter(p=>p.chapterId===id).length+' pages'}});
 return {token:boundPlan.token,boundAt:boundPlan.boundAt,nativeSaved:!!boundPlan.nativeSaved,nativePdfSize:Number(boundPlan.nativePdfSize||0),fileName:boundPlan.fileName||'',pages:pagesOut,chapters:chapters,chapterNames:chapters.map(x=>x.title),spells:boundPlan.spells.map(x=>({id:x.id,name:x.name,title:x.name,detail:Object.values(x.pagesByChapter).reduce((n,a)=>n+a.length,0)+' matching pages',pagesByChapter:x.pagesByChapter}))}
}'''


V29_NATIVE_CORE = r'''function gmBosNativeRendererAvailable(){
 const api=gmBosNativeFiles();return !!(api&&typeof api.beginPdfJob==='function'&&typeof api.beginPdfPage==='function'&&typeof api.startPdfJob==='function')
}
function gmBosHasBookPdf(key){const api=gmBosNativeFiles();try{return !!(api&&typeof api.hasBookPdf==='function'&&api.hasBookPdf(key))}catch(_e){return false}}
function gmBosBookPdfInfo(key){const api=gmBosNativeFiles();try{return api&&typeof api.bookPdfInfo==='function'?String(api.bookPdfInfo(key)||''):''}catch(_e){return ''}}
function gmBosExportBookPdf(key,fileName,openAfter){const api=gmBosNativeFiles();if(!api||typeof api.exportBookPdf!=='function'||!gmBosHasBookPdf(key))return false;return !!api.exportBookPdf(key,fileName,openAfter!==false)}
function gmBosCancelNativeJob(){const api=gmBosNativeFiles();try{return !!(api&&typeof api.cancelPdfJob==='function'&&api.cancelPdfJob())}catch(_e){return false}}
function gmBosNativeJobStatus(){const api=gmBosNativeFiles();try{return parse(api&&typeof api.pdfJobStatus==='function'?String(api.pdfJobStatus()||''):'', {state:'idle'})}catch(_e){return {state:'idle'}}}
function gmBosDateStamp(date){const d=date||new Date(),pad=n=>String(n).padStart(2,'0');return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())}
function gmBosSafeFilePart(value){return String(value||'').normalize('NFKD').replace(/[^A-Za-z0-9]+/g,'_').replace(/^_+|_+$/g,'').replace(/_+/g,'_').slice(0,100)||'Book_of_Shadows'}
function gmBosOriginalFileName(){return 'BOS_Greenman_HedgeWitchery_Apothecary_Book_of_Shadows_Original_English_'+gmBosDateStamp()+'.pdf'}
function gmBosScribeFileName(scriptName){return 'BOS_Greenman_HedgeWitchery_Apothecary_Book_of_Shadows_'+gmBosSafeFilePart(scriptName)+'_'+gmBosDateStamp()+'.pdf'}
function gmBosNativeRenderStyles(){return gmBosRasterStyles()+"\n@font-face{font-family:Cinzel;src:url('file:///android_asset/fonts/Cinzel.ttf') format('truetype');font-weight:400 900;font-style:normal;font-display:block}@font-face{font-family:GMCrimson;src:url('file:///android_asset/fonts/CrimsonText-Regular.ttf') format('truetype');font-weight:400;font-style:normal;font-display:block}@font-face{font-family:GMCrimson;src:url('file:///android_asset/fonts/CrimsonText-Bold.ttf') format('truetype');font-weight:700;font-style:normal;font-display:block}.gmInkGlyphSprite{position:absolute!important;width:0!important;height:0!important;overflow:hidden!important;pointer-events:none!important}"}
async function gmBosSendNativeText(api,beginMethod,appendMethod,beginArgs,text,options){
 const blob=new Blob([String(text||'')],{type:'text/plain;charset=utf-8'}),step=262144;if(!api[beginMethod].apply(api,[...beginArgs,blob.size]))throw new Error('Android could not open the gathered page package');
 for(let offset=0;offset<blob.size;offset+=step){gmBosThrowIfCancelled(options);const part=blob.slice(offset,Math.min(blob.size,offset+step),'application/octet-stream'),data=await gmBosBlobDataUrl(part),encoded=data.slice(data.indexOf(',')+1),last=offset+step>=blob.size;if(!api[appendMethod](encoded,last))throw new Error('Android received an incomplete page package');await new Promise(r=>setTimeout(r,0))}
}
async function gmBosPrepareNativePage(page,idx,total,binding,printMap,options){
 gmBosThrowIfCancelled(options);const clone=page.cloneNode(true);clone.classList.remove('active','gmBosPrintSelected');clone.classList.add('gmBosPrintSheet');clone.removeAttribute('style');clone.style.cssText='display:block!important;position:relative!important;width:794px!important;min-width:794px!important;max-width:794px!important;height:1123px!important;min-height:1123px!important;max-height:1123px!important;margin:0!important;padding:0!important;overflow:hidden!important;box-shadow:none!important;transform:none!important;background:#f4ecd8!important;box-sizing:border-box!important';
 if(page._gmStaticHtml||page.querySelector('.gmBosShadowHost'))gmBosStaticReference(page,clone,idx);if(printMap)gmBosApplyPrintMap(page,clone,printMap);const stage=document.createElement('div');stage.style.cssText='position:fixed;left:-12000px;top:0;width:794px;height:1123px;display:block;visibility:hidden;pointer-events:none;z-index:-1;background:#f4ecd8';stage.append(clone);document.body.append(stage);
 try{fitSpellListText(stage);fitAltarText(stage);fitSummaryText(stage);fitHeartText(stage);gmBosFreezeControls(stage);if(binding&&binding.scriptId&&binding.scriptId!=='original'){gmBosApplyScribeHand(clone,binding.scriptId,binding.registry);fitSpellListText(stage);fitAltarText(stage);fitSummaryText(stage);fitHeartText(stage)}gmBosUniqueSvgDom(stage,'nativepage_'+idx);gmBosMoonWhiteRepair(stage);gmBosStripPrintInteractivity(stage);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const canvases=[...clone.querySelectorAll('canvas')];for(let j=0;j<canvases.length;j++)await gmBosRasterizeCanvasNode(canvases[j],idx+'_'+j);await gmBosInlineBlobImages(clone);if(binding&&binding.registry&&binding.registry.defs&&binding.registry.defs.parentNode)clone.prepend(binding.registry.defs.parentNode.cloneNode(true));clone.querySelectorAll('script,iframe,video,audio,noscript').forEach(n=>n.remove());return clone.outerHTML}finally{stage.remove()}
}
function gmBosRowsFromCatalog(cat,pageKeys){
 if(!pages.length)build();const wanted=new Set(Array.isArray(pageKeys)?pageKeys:(cat.pages||[]).map(x=>x.key)),byKey=new Map((cat.pages||[]).map(x=>[x.key,x]));return (cat.pages||[]).filter(x=>wanted.has(x.key)).map(x=>({meta:x,page:pages[Number(x.sourceIndex)]})).filter(x=>x.page)
}
async function gmBosStartNativeJob(config,options){
 options=options||{};if(!gmBosNativeRendererAvailable())throw new Error('This APK does not contain the background BoS renderer');const api=gmBosNativeFiles(),rows=config.rows||[];if(!rows.length)throw new Error('No bound A4 pages were selected');const jobId='bos-'+Date.now()+'-'+Math.random().toString(36).slice(2,8),pending={jobId:jobId,kind:config.kind,storageKey:config.storageKey,title:config.title,scriptId:config.scriptId,scriptName:config.scriptName,fileName:config.fileName,catalog:config.catalog||null,pageKeys:rows.map(x=>x.meta&&x.meta.key||''),startedAt:new Date().toISOString()};
 if(!api.beginPdfJob(jobId,config.storageKey,config.title,config.scriptName,config.fileName,rows.length,config.kind))throw new Error('Another BoS PDF is already being prepared');lsSet(SKEYS.pendingJob,JSON.stringify(pending));const host=document.createElement('div');host.style.cssText='position:fixed;left:-13000px;top:0;width:1px;height:1px;overflow:hidden;pointer-events:none';document.body.append(host);let binding=null;
 try{await gmBosSendNativeText(api,'beginPdfStyle','appendPdfStyleChunk',[],gmBosNativeRenderStyles(),options);if(config.scriptId!=='original')await gmBosEnsureScribeReady();binding={scriptId:config.scriptId,registry:config.scriptId==='original'?null:gmBosCreateScriptRegistry(host,config.scriptId)};const printMap=gmBosBuildPrintMap(rows.map(x=>x.page));for(let i=0;i<rows.length;i++){gmBosThrowIfCancelled(options);const started=Date.now();if(options.onProgress)options.onProgress(i,rows.length,'gathering');const html=await gmBosPrepareNativePage(rows[i].page,i,rows.length,binding,printMap,options);gmBosThrowIfCancelled(options);await gmBosSendNativeText(api,'beginPdfPage','appendPdfPageChunk',[i],html,options);gmBosRevokePrintObjectUrls();gmBosDiag('NATIVE PACKAGE','A4 page gathered for background renderer',{page:i+1,total:rows.length,htmlBytes:new Blob([html]).size,durationMs:Date.now()-started});if(options.onProgress)options.onProgress(i+1,rows.length,'gathering');await new Promise(r=>setTimeout(r,0))}gmBosThrowIfCancelled(options);if(!api.startPdfJob())throw new Error('Android could not start the background PDF');if(options.onQueued)options.onQueued(rows.length);gmBosDiag('NATIVE JOB','Background PDF queued',{jobId:jobId,kind:config.kind,script:config.scriptName,pages:rows.length});return {...pending,background:true,pageCount:rows.length}
 }catch(err){try{api.abortPdfJobSubmission()}catch(_e){}const saved=parse(lsGet(SKEYS.pendingJob)||'null',null);if(saved&&saved.jobId===jobId)lsRemove(SKEYS.pendingJob);if((err&&err.gmBosCancelled)||gmBosIsCancelled(options))return {cancelled:true,jobId:jobId};throw err}finally{host.remove();gmBosRevokePrintObjectUrls()}
}
async function startNativeBind(options){
 if(!boundPlan||!boundPlan.rows||!boundPlan.rows.length)return null;const catalog=getBoundCatalog(),fileName=gmBosOriginalFileName();boundPlan.fileName=fileName;return gmBosStartNativeJob({kind:'bind',storageKey:'bound-original',title:'Greenman HedgeWitchery Apothecary · Book of Shadows',scriptId:'original',scriptName:'Original English',fileName:fileName,catalog:catalog,rows:boundPlan.rows.map(r=>({meta:r,page:r.page}))},options||{})
}
async function startNativeConversion(scriptId,options){
 const cat=getBoundCatalog(),sid=GM_INK_BOS_HANDS.includes(scriptId)?scriptId:'';if(!cat||!sid)return null;const scriptName=(GM_DATA.scripts[sid]||{}).name||sid,rows=gmBosRowsFromCatalog(cat,(cat.pages||[]).map(x=>x.key));return gmBosStartNativeJob({kind:'scribe',storageKey:'bos-'+gmBosSafeFilePart(sid).toLowerCase(),title:'Book of Shadows',scriptId:sid,scriptName:scriptName,fileName:gmBosScribeFileName(scriptName),catalog:cat,rows:rows},options||{})
}
async function startNativeSelection(pageKeys,options){
 const cat=getBoundCatalog();if(!cat)return null;const rows=gmBosRowsFromCatalog(cat,pageKeys),full=rows.length===(cat.pages||[]).length;return gmBosStartNativeJob({kind:full?'bind':'export',storageKey:full?'bound-original':'bound-selection',title:'Greenman HedgeWitchery Apothecary · Book of Shadows',scriptId:'original',scriptName:'Original English',fileName:gmBosOriginalFileName(),catalog:full?cat:null,rows:rows},options||{})
}
function markNativeBoundReady(status){if(boundPlan){boundPlan.nativeSaved=true;boundPlan.nativePdfSize=Number(status&&status.pdfBytes||0);boundPlan.fileName=status&&status.fileName||boundPlan.fileName||''}}
function discardNativeBind(){boundPlan=null}
'''


V29_STYLE = r'''
/* V29: clear separation between the original bound PDF and BoS text conversion. */
.inkHeader{align-items:center}.inkHeader p{max-width:620px}.inkPrintDesk.v29{padding:15px}.inkPrintDesk.v29 h2{font-size:22px}.inkPrintDesk.v29 .inkPrintLead{font-size:11.5px;max-width:760px}.inkPrintStatus{margin-top:8px;padding:8px 10px;border:1px solid #57401f;border-radius:7px;background:#120805;color:#bba16c;font-size:10px;line-height:1.4}.inkPrintStatus strong{display:block;color:#e6cc89}.inkSingleOption{display:grid;grid-template-columns:1fr;gap:8px;margin-top:9px}.inkPrintActions.v29{grid-template-columns:2fr 1fr}.bosConversionDesk{border:1px solid #8b6330;border-radius:12px;padding:14px;background:radial-gradient(circle at 50% 0,#4a2b17 0,#271208 48%,#170904 100%);box-shadow:inset 0 0 28px #0008,0 8px 18px #0008}.bosConversionDesk h2{margin:0;color:#efd793;font-size:22px}.bosConversionIntro{margin:5px 0 11px;color:#c6ad75;font-size:11px;line-height:1.45}.bosConversionGrid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px;margin-top:9px}.bosGlyphPreview{min-height:82px;display:flex;align-items:center;justify-content:center;gap:0;padding:9px;border:1px solid #7c5b30;border-radius:8px;background:#ead8a2;color:#25150d;overflow:hidden}.bosGlyphPreview .bosGlyph{display:inline-flex;width:24px;height:35px;align-items:center;justify-content:center}.bosGlyphPreview .bosGlyph svg{display:block;width:100%;height:100%;color:#25150d}.bosGlyphPreview.ogham{flex-direction:column;min-height:180px}.bosGlyphPreview.ogham .bosGlyph{width:34px;height:34px}.bosGlyphPreview.ogham .bosGlyph svg{transform:rotate(-90deg)}.bosConvertActions{display:grid;grid-template-columns:2fr 1fr;gap:7px;margin-top:10px}.bosJobProgress{display:none;margin-top:10px;padding:10px;border:1px solid #7c6636;border-radius:8px;background:#142017;color:#c6d7aa;font-size:10px;line-height:1.4}.bosJobProgress.open{display:block}.bosJobProgress strong{display:block;color:#edf0b4;font-size:12px}.bosJobProgress progress{display:block;width:100%;height:12px;margin:7px 0;accent-color:#a88439}.bosJobProgress .tagBtn{width:100%;margin-top:5px;border-color:#a46243}.bosConversionFoot{margin:9px 1px 0;color:#9f895d;font-size:9.5px;line-height:1.4}.bosConversionFoot b{color:#d5ba78}.book.bos.dynamic{margin-right:7px}.book.bos.dynamic .bosScriptName{bottom:7px}.gmBosJobModal .modalCard{max-width:520px}.gmBosJobActions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:12px}.gmBosJobActions button:only-child{grid-column:1/-1}.gmBosBindChoices.v29{grid-template-columns:1fr 1fr}.gmBosBindChoices.v29 .gmBosCancelBind{display:block;margin:0;grid-column:1/-1}.gmBosBindList.v29{margin-bottom:4px}#gmBosBindModal.packaging .gmBosBindChoices{display:grid}#gmBosBindModal.packaging .gmBosBindSummary:after{content:'You may continue using the app while the APK finishes the PDF.';display:block;margin-top:6px;color:#9f895d;font-size:9.5px}.inkOutputNote{display:block;margin-top:5px;color:#a99262;font-size:9.5px;line-height:1.35}
.gmBosJobActions{grid-template-columns:repeat(3,minmax(0,1fr))}
@media(max-width:650px){.bosConversionGrid,.bosConvertActions,.inkPrintActions.v29,.gmBosJobActions,.gmBosBindChoices.v29{grid-template-columns:1fr}.gmBosBindChoices.v29 .gmBosCancelBind{grid-column:auto}.bosConversionDesk{padding:10px}.bosConversionDesk h2,.inkPrintDesk.v29 h2{font-size:19px}}
'''


V29_INK_MARKUP = r'''<section id="inkView" class="view"><button class="backBtn" data-back-study>‹ Study</button><div class="inkHeader"><img id="inkMain"><div><h1>The Ink Pot</h1><p>Open the original bound Book of Shadows, or prepare its lettering for a Scribe hand.</p></div></div><div class="inkTabs"><button class="tagBtn active" data-inktab="print">BoS Print Room</button><button class="tagBtn" data-inktab="books">Scribe Books</button><button class="tagBtn" data-inktab="symbols">Read Symbols</button></div><div id="inkPrint" class="inkTabPanel active"><div class="inkPrintDesk v29"><h2>Original Bound Book</h2><p class="inkPrintLead">Main Contents decides what Bind Book gathers. This room opens the latest completed English PDF, or makes a smaller PDF from its bound chapters, pages, or spells.</p><div id="gmInkBoundBookLine" class="inkBoundBookLine empty"><strong>No completed book is bound</strong>Open the live Book, choose chapters on Main Contents, then press Bind Book.</div><div class="inkPrintStep"><b class="inkPrintStepTitle">1 · Choose from the bound book</b><div class="inkPrintModes"><button class="inkPrintMode active" type="button" data-gm-print-mode="full">Whole Bound Book</button><button class="inkPrintMode" type="button" data-gm-print-mode="chapters">Chapters</button><button class="inkPrintMode" type="button" data-gm-print-mode="pages">Individual Pages</button><button class="inkPrintMode" type="button" data-gm-print-mode="spells">Selected Spells</button></div><div id="gmInkPrintPicker" class="inkPrintPicker"><div class="inkPrintPickerHint">Bind the book from its live Main Contents page first.</div></div></div><div class="inkSingleOption"><div class="inkPrintField"><b>2 · Pages ready</b><small id="gmInkPrintSummary">Nothing is bound yet.</small><span class="inkOutputNote">PDF copies are dated and saved in Downloads / Greenman HedgeWitchery.</span></div></div><div class="inkPrintActions v29"><button id="gmInkPrintBoundBtn" class="brassBtn inkPrintPrimary" type="button" disabled>Open / Save Bound PDF</button><button id="gmInkReturnLiveBtn" class="tagBtn" type="button">Return to Live Book</button></div><div id="gmInkNativeStatus" class="inkPrintStatus"><strong>No PDF task active</strong>The APK will show progress here.</div><p class="inkPrintStorage"><b>The app keeps one current original bound PDF.</b> A completed new binding replaces the old one; unfinished files are discarded and PDFs are excluded from JSON backup.</p></div></div><div id="inkBooks" class="inkTabPanel"><div id="gmBosConversionDesk" class="bosConversionDesk"><h2>BoS Text Conversion</h2><p class="bosConversionIntro">Choose a Scribe hand for the pages already gathered by Bind Book. The English meaning stays unchanged; only the lettering changes.</p><div id="gmScribeBoundLine" class="inkBoundBookLine empty"><strong>No completed book is bound</strong>Bind the chosen pages from Main Contents first.</div><div class="bosConversionGrid"><div class="inkPrintField"><label for="gmInkBosHand">1 · Choose text</label><select id="gmInkBosHand"></select><small id="gmInkHandTruth">Choose the lettering for the converted Book of Shadows.</small></div><div class="inkPrintField"><b>2 · Title preview</b><div id="gmInkHandSample" class="bosGlyphPreview">Book of Shadows</div></div></div><div class="inkPrintField" style="margin-top:9px"><b>3 · Bound pages</b><small id="gmScribeConversionSummary">Nothing is bound yet.</small></div><div class="bosConvertActions"><button id="gmScribeConvertBtn" class="brassBtn inkPrintPrimary" type="button" disabled>Convert BoS Text</button><button id="gmScribeReturnLiveBtn" class="tagBtn" type="button">Return to Live Book</button></div><div id="gmScribeJobProgress" class="bosJobProgress"><strong id="gmScribeJobTitle">Preparing Book of Shadows</strong><span id="gmScribeJobText"></span><progress id="gmScribeJobBar" max="1" value="0"></progress><button id="gmScribeCancelJob" class="tagBtn" type="button">Cancel</button></div><p class="bosConversionFoot"><b>When ready:</b> the converted book appears on the Book of Shadows shelf in the main Scribe room. Only the current PDF for each chosen hand is kept.</p></div><div class="shelfBlock"><div class="shelfHead"><h2>Other Scribe Books</h2><div class="shelfNote">Books made at the writing desk</div></div><div id="inkBookShelf" class="bookRow"></div></div></div><div id="inkSymbols" class="inkTabPanel"><div class="parkedReader"><b>Read Symbols</b><br>The clean-image reader remains separate from Book of Shadows binding and conversion.</div></div></section>'''


V29_BIND_MARKUP = r'''<div id="gmBosBindModal" class="modal"><div class="modalCard"><h2 id="gmBosBindTitle">Bind Book of Shadows</h2><div id="gmBosBindSummary" class="gmBosBindSummary"><strong>Ready to gather selected pages</strong>Main Contents decides exactly which chapters are included.</div><ul class="gmBosBindList v29"><li>Bind Book creates the latest flat English A4 PDF.</li><li>A completed binding replaces the previous bound version.</li><li>An unfinished binding never replaces the previous PDF.</li></ul><div class="gmBosBindChoices v29"><button id="gmBosStayEditing" class="tagBtn" type="button">Stay Editing BoS</button><button id="gmBosGoPrintRoom" class="brassBtn" type="button">Choose Scribe Text</button><button id="gmBosCancelBind" class="tagBtn gmBosCancelBind" type="button">Cancel</button></div></div></div><div id="gmBosJobModal" class="modal gmBosJobModal"><div class="modalCard"><h2 id="gmBosJobTitle">Book of Shadows</h2><div id="gmBosJobMessage" class="gmBosBindSummary"><strong>PDF task started</strong>You may continue using the app.</div><div class="gmBosJobActions"><button id="gmBosJobContinue" class="tagBtn" type="button">Continue</button><button id="gmBosJobCancel" class="tagBtn" type="button">Cancel</button><button id="gmBosJobAction" class="brassBtn" type="button">Open PDF</button></div></div></div>'''


V29_GLOBAL = r'''const GM_BOS_UI={cancelToken:null,packing:null,lastStatusSig:'',pollTimer:0};
function gmBosDateStamp(date){const d=date||new Date(),pad=n=>String(n).padStart(2,'0');return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())}
function gmBosOriginalFileName(){return 'BOS_Greenman_HedgeWitchery_Apothecary_Book_of_Shadows_Original_English_'+gmBosDateStamp()+'.pdf'}
function gmBosBusyState(state){return ['receiving','queued','rendering','cancelling'].includes(String(state||''))}
function gmBosPendingJob(){const x=parse(lsGet(SKEYS.pendingJob)||'null',null);return x&&x.jobId?x:null}
function gmBosCompactDerived(list){const by=new Map();(Array.isArray(list)?list:[]).forEach(x=>{if(!x||!x.pdfKey||!x.scriptId)return;by.set(x.scriptId,{id:x.id||'bos-'+x.scriptId,title:'Book of Shadows',scriptId:x.scriptId,scriptName:x.scriptName||x.scriptId,pdfKey:x.pdfKey,fileName:x.fileName||'',pageCount:Number(x.pageCount||0),pdfBytes:Number(x.pdfBytes||0),savedAt:x.savedAt||new Date().toISOString(),renderedTitleHTML:x.renderedTitleHTML||''})});return [...by.values()]}
function writeBosDerived(a){const clean=gmBosCompactDerived(a);lsSet(SKEYS.bosDerived,JSON.stringify(clean));renderAllShelves()}
function storeBosEntry(entry){if(!entry||!entry.scriptId||!entry.pdfKey)return;const copy={...entry,title:'Book of Shadows',id:'bos-'+entry.scriptId,savedAt:entry.savedAt||new Date().toISOString()};copy.scriptName=copy.scriptName||(GM_DATA.scripts[copy.scriptId]||{}).name||copy.scriptId;copy.renderedTitleHTML=scriptTextHTML(copy.scriptId,'Book of Shadows');const next=gmBosCompactDerived(readBosDerived()).filter(x=>x.scriptId!==copy.scriptId&&x.pdfKey!==copy.pdfKey);next.push(copy);writeBosDerived(next)}
function gmBosShowJobNotice(title,strong,body,action,cancellable){const modal=$('#gmBosJobModal'),heading=$('#gmBosJobTitle'),message=$('#gmBosJobMessage'),button=$('#gmBosJobAction'),cancel=$('#gmBosJobCancel');if(!modal)return;if(heading)heading.textContent=title||'Book of Shadows';if(message)message.innerHTML='<strong>'+esc(strong||'')+'</strong>'+esc(body||'');if(button){button.style.display=action?'block':'none';button.textContent=action&&action.label||'Open PDF';button.onclick=()=>{try{if(action&&action.run)action.run()}finally{modal.classList.remove('open')}}}if(cancel){cancel.style.display=cancellable?'block':'none';cancel.disabled=false;cancel.textContent='Cancel';cancel.onclick=()=>{cancel.disabled=true;cancel.textContent='Cancelling…';gmBosCancelActiveTask()}}modal.classList.add('open')}
function gmBosOpenDerivedPdf(entry){if(!entry||!entry.pdfKey)return;const ok=GM_BOS.exportBookPdf(entry.pdfKey,entry.fileName||('BOS_Book_of_Shadows_'+gmBosDateStamp()+'.pdf'),true);if(!ok)gmBosShowJobNotice('Book of Shadows','PDF is not available','Create this Scribe conversion again from the Ink Pot.')}
function renderBosShelf(target){if(!target)return;target.innerHTML='';const live=document.createElement('button');live.className='book bos';live.innerHTML='<span class="bookVisual"><img src="'+BOS_ART+'"></span>';live.setAttribute('aria-label','Live Book of Shadows');live.onclick=openBos;target.append(live);gmBosCompactDerived(readBosDerived()).forEach(entry=>{if(!GM_BOS.hasBookPdf(entry.pdfKey))return;const b=document.createElement('button'),hand=entry.scriptId==='Ogham'?' ogham':'';b.className='book bos dynamic';b.innerHTML='<span class="bookVisual"><img src="'+BOS_ART+'"><span class="bosScriptTitle'+hand+'">'+(bosTitleHTML(entry)||esc(entry.scriptName))+'</span><span class="bosScriptName">'+esc(entry.scriptName)+'</span></span>';b.setAttribute('aria-label',entry.scriptName+' Book of Shadows PDF');b.onclick=()=>gmBosOpenDerivedPdf(entry);target.append(b)})}
function renderAllShelves(){renderFilters();renderScriptShelf($('#scriptShelf'));const ink=$('#inkBookShelf');if(ink)renderScriptShelf(ink);renderBosShelf($('#bosShelf'));if($('#inkView')&&$('#inkView').classList.contains('active')){renderInkPrintRoom();renderBosConversion()}}
function gmInkSetTab(name){const key=String(name||'print').toLowerCase();$$('[data-inktab]').forEach(x=>x.classList.toggle('active',x.dataset.inktab===key));$$('.inkTabPanel').forEach(p=>p.classList.toggle('active',p.id==='ink'+key[0].toUpperCase()+key.slice(1)));if(key==='print')renderInkPrintRoom();if(key==='books')renderBosConversion()}
function openInkpotPrintRoom(){showView('ink');gmInkSetTab('print');gmInkInstallDiagnostics();gmInkSnapshot('Original BoS Print Room opened')}
function openInkpotScribeBooks(){showView('ink');gmInkSetTab('books');gmInkInstallDiagnostics();renderBosConversion();setTimeout(()=>{const desk=$('#gmBosConversionDesk');if(desk)desk.scrollIntoView({behavior:'smooth',block:'start'})},40)}
function gmInkBuildHandOptions(){const sel=$('#gmInkBosHand');if(!sel||sel.__gmInkReady)return;sel.__gmInkReady=true;sel.innerHTML=GM_INK_BOS_HANDS.filter(id=>GM_DATA.scripts[id]).map(id=>'<option value="'+esc(id)+'">'+esc(GM_DATA.scripts[id].name)+'</option>').join('');const saved=lsGet(SKEYS.bindingHand)||GM_INK_BOS_HANDS[0];sel.value=[...sel.options].some(o=>o.value===saved)?saved:GM_INK_BOS_HANDS[0];sel.onchange=()=>{lsSet(SKEYS.bindingHand,sel.value);gmInkRenderHandSample();renderBosConversion()}}
function gmInkRenderHandSample(){const sel=$('#gmInkBosHand'),sample=$('#gmInkHandSample'),truth=$('#gmInkHandTruth');if(!sel||!sample)return;const sid=sel.value,name=(GM_DATA.scripts[sid]||{}).name||sid;if(truth)truth.textContent='English words remain English; '+name+' changes their visible lettering.';sample.classList.toggle('ogham',sid==='Ogham');if(!GM.deskReady){sample.textContent='Preparing '+name+' preview…';ensureDesk();setTimeout(gmInkRenderHandSample,120);return}if(sample.dataset.gmHand===sid)return;sample.dataset.gmHand=sid;sample.innerHTML=scriptTextHTML(sid,'Book of Shadows')||esc(name)}
function gmInkUpdatePrintSummary(cat){const keys=gmInkChosenPageKeys(cat),summary=$('#gmInkPrintSummary'),btn=$('#gmInkPrintBoundBtn'),full=!!(cat&&keys.length===(cat.pages||[]).length),saved=full&&GM_BOS.hasBookPdf('bound-original'),status=GM_BOS.jobStatus(),busy=gmBosBusyState(status.state)||!!GM_BOS_UI.packing;if(summary)summary.textContent=cat?(keys.length+' of '+cat.pages.length+' bound A4 pages selected.'):'Nothing is bound yet.';if(btn){btn.disabled=!cat||!keys.length||busy;btn.textContent=saved?'Open / Save Bound PDF':(full?'Create Bound PDF':'Create Selected Flat PDF')}}
function gmBosRenderNativeStatus(){const box=$('#gmInkNativeStatus'),st=GM_BOS.jobStatus(),cat=gmInkBoundCatalog();if(!box)return;if(gmBosBusyState(st.state)){box.innerHTML='<strong>'+esc(st.message||'Preparing Book of Shadows PDF')+'</strong>'+Number(st.done||0)+' of '+Number(st.total||0)+' pages completed. Use Cancel in BoS Text Conversion if needed.'}else if(cat&&GM_BOS.hasBookPdf('bound-original'))box.innerHTML='<strong>Latest bound English PDF is ready</strong>Open / Save copies it to Downloads / Greenman HedgeWitchery and opens the device PDF viewer.';else box.innerHTML='<strong>No completed bound PDF yet</strong>Bind selected chapters from Main Contents.'}
function renderInkPrintRoom(){const line=$('#gmInkBoundBookLine'),btn=$('#gmInkPrintBoundBtn'),back=$('#gmInkReturnLiveBtn');if(!line||!btn)return;btn.onclick=gmInkPrintBound;if(back)back.onclick=openBos;const cat=gmInkBoundCatalog();gmInkResetChoices(cat);$$('[data-gm-print-mode]').forEach(b=>{b.classList.toggle('active',b.dataset.gmPrintMode===GM_INK_PRINT.mode);b.disabled=!cat;b.onclick=()=>{GM_INK_PRINT.mode=b.dataset.gmPrintMode;renderInkPrintRoom()}});if(!cat){line.className='inkBoundBookLine empty';line.innerHTML='<strong>No completed book is bound</strong>Open the live Book, choose chapters on Main Contents, then press Bind Book.'}else{line.className='inkBoundBookLine';line.innerHTML='<strong>'+cat.pages.length+' A4 pages are bound</strong>'+esc((cat.chapterNames||[]).join(' · '))}gmInkRenderPicker(cat);gmInkBindPickerEvents(cat);gmInkUpdatePrintSummary(cat);gmBosRenderNativeStatus();gmInkSnapshot('Original BoS Print Room rendered')}
function renderBosConversion(){const line=$('#gmScribeBoundLine'),summary=$('#gmScribeConversionSummary'),btn=$('#gmScribeConvertBtn'),back=$('#gmScribeReturnLiveBtn'),progress=$('#gmScribeJobProgress'),bar=$('#gmScribeJobBar'),jobTitle=$('#gmScribeJobTitle'),jobText=$('#gmScribeJobText'),cancel=$('#gmScribeCancelJob');if(!line||!btn)return;gmInkBuildHandOptions();gmInkRenderHandSample();const cat=gmInkBoundCatalog(),st=GM_BOS.jobStatus(),pending=gmBosPendingJob(),packing=GM_BOS_UI.packing,busy=gmBosBusyState(st.state)||!!packing;if(!cat){line.className='inkBoundBookLine empty';line.innerHTML='<strong>No completed book is bound</strong>Bind the chosen pages from Main Contents first.'}else{line.className='inkBoundBookLine';line.innerHTML='<strong>'+cat.pages.length+' bound A4 pages ready for conversion</strong>'+esc((cat.chapterNames||[]).join(' · '));if(summary)summary.textContent='All '+cat.pages.length+' pages will use the chosen Scribe lettering.'}btn.disabled=!cat||busy;btn.onclick=gmBosStartConversionUi;if(back)back.onclick=openBos;if(progress){progress.classList.toggle('open',busy);if(busy){const done=packing?Number(packing.done||0):Number(st.done||0),total=packing?Number(packing.total||1):Math.max(1,Number(st.total||1));if(jobTitle)jobTitle.textContent=packing?'Gathering A4 pages':(st.message||'Preparing Book of Shadows');if(jobText)jobText.textContent=done+' of '+total+' pages · '+((pending&&pending.scriptName)||st.scriptName||'Book of Shadows');if(bar){bar.max=total;bar.value=Math.min(done,total)}}}if(cancel){cancel.disabled=!busy;cancel.onclick=gmBosCancelActiveTask}}
async function gmInkPrintBound(){const btn=$('#gmInkPrintBoundBtn'),cat=gmInkBoundCatalog();if(!btn||!cat)return;const keys=gmInkChosenPageKeys(cat);if(!keys.length)return;const full=keys.length===(cat.pages||[]).length;if(full&&GM_BOS.hasBookPdf('bound-original')){const ok=GM_BOS.exportBookPdf('bound-original',cat.fileName||gmBosOriginalFileName(),true);if(!ok)gmBosShowJobNotice('Bound Book PDF','The PDF could not be opened','Return to Main Contents and bind the book again.');return}if(!GM_BOS.nativeRenderer()){await GM_BOS.printBound({button:btn,scriptId:'original',pageKeys:keys});return}const token={cancelled:false};GM_BOS_UI.cancelToken=token;GM_BOS_UI.packing={done:0,total:keys.length,kind:'export'};gmBosShowJobNotice('Bound Book PDF','Gathering '+keys.length+' A4 pages','You may continue using the app while the PDF is prepared.',null,true);try{const result=await GM_BOS.startNativeSelection(keys,{cancelToken:token,onProgress:(done,total)=>{GM_BOS_UI.packing={done:done,total:total,kind:'export'};renderInkPrintRoom()},onQueued:()=>{GM_BOS_UI.packing=null}});if(result&&result.cancelled)gmBosShowJobNotice('Bound Book PDF','PDF task cancelled','The unfinished file was discarded.')}catch(err){gmBosShowJobNotice('Bound Book PDF','The PDF could not be started',String(err&&err.message||err))}finally{GM_BOS_UI.packing=null;GM_BOS_UI.cancelToken=null;renderInkPrintRoom();renderBosConversion()}}
async function gmBosStartConversionUi(){const cat=gmInkBoundCatalog(),sel=$('#gmInkBosHand');if(!cat||!sel||gmBosBusyState(GM_BOS.jobStatus().state)||GM_BOS_UI.packing)return;const sid=sel.value,name=(GM_DATA.scripts[sid]||{}).name||sid,token={cancelled:false};GM_BOS_UI.cancelToken=token;GM_BOS_UI.packing={done:0,total:cat.pages.length,kind:'scribe'};gmBosShowJobNotice('BoS Text Conversion','Gathering '+cat.pages.length+' bound A4 pages','The '+name+' book will appear on the Book of Shadows shelf when ready. You may continue using the app.',null,true);renderBosConversion();try{const result=await GM_BOS.startNativeConversion(sid,{cancelToken:token,onProgress:(done,total)=>{GM_BOS_UI.packing={done:done,total:total,kind:'scribe'};renderBosConversion()},onQueued:()=>{GM_BOS_UI.packing=null}});if(result&&result.cancelled)gmBosShowJobNotice('BoS Text Conversion','Conversion cancelled','The unfinished file was discarded.');else if(result)gmBosShowJobNotice('BoS Text Conversion',name+' conversion continues in the background','You may use any other part of the app. A message will appear when the book is ready.',null,true)}catch(err){gmBosShowJobNotice('BoS Text Conversion','Conversion could not be started',String(err&&err.message||err))}finally{GM_BOS_UI.packing=null;GM_BOS_UI.cancelToken=null;renderBosConversion();renderInkPrintRoom()}}
function gmBosCancelActiveTask(){if(GM_BOS_UI.cancelToken)GM_BOS_UI.cancelToken.cancelled=true;GM_BOS.cancelJob();const title=$('#gmScribeJobTitle');if(title)title.textContent='Cancelling safely…';gmBosDiag('NATIVE CANCEL','Background PDF cancellation requested',GM_BOS.jobStatus())}
function gmBosCancelCurrentBind(){const token=gmBosActiveBindCancel||GM_BOS_UI.cancelToken,modal=$('#gmBosBindModal'),title=$('#gmBosBindTitle'),summary=$('#gmBosBindSummary'),btn=$('#gmBosCancelBind');if(token)token.cancelled=true;GM_BOS.cancelJob();if(modal)modal.classList.add('cancelling');if(title)title.textContent='Cancelling Binding';if(summary)summary.innerHTML='<strong>Stopping safely</strong>The unfinished new book will be discarded. The previous completed PDF will not change.';if(btn){btn.disabled=true;btn.textContent='Cancelling…'}}
async function gmBosBindCurrentSelection(){if(gmBosBusyState(GM_BOS.jobStatus().state)||GM_BOS_UI.packing){gmBosShowJobNotice('Bind Book of Shadows','Another PDF task is already active','Cancel it or wait for it to finish before starting a new binding.');return}const cat=GM_BOS.bindSelected(),modal=$('#gmBosBindModal'),title=$('#gmBosBindTitle'),summary=$('#gmBosBindSummary'),cancelBtn=$('#gmBosCancelBind');if(!cat||!modal||!title||!summary)return;const token={cancelled:false};gmBosActiveBindCancel=token;GM_BOS_UI.cancelToken=token;GM_BOS_UI.packing={done:0,total:cat.pages.length,kind:'bind'};if(cancelBtn){cancelBtn.disabled=false;cancelBtn.textContent='Cancel'}title.textContent='Binding Book of Shadows';summary.innerHTML='<strong>Gathering 0 of '+cat.pages.length+' A4 pages</strong>The selected pages are being prepared for the APK renderer.';modal.classList.remove('cancelling');modal.classList.add('open','packaging');if(!GM_BOS.nativeRenderer()){modal.classList.add('binding');const result=await GM_BOS.flattenBound({button:$('#gmBosBindBookBtn'),cancelToken:token,onProgress:(done,total)=>{summary.innerHTML='<strong>Flattening '+done+' of '+total+' A4 pages</strong>Please keep this page open.'}});modal.classList.remove('binding','packaging');GM_BOS_UI.packing=null;GM_BOS_UI.cancelToken=null;gmBosActiveBindCancel=null;if(result&&!result.cancelled){lsSet(SKEYS.boundCatalog,JSON.stringify(result));title.textContent='Book of Shadows Bound';summary.innerHTML='<strong>'+result.pages.length+' A4 pages completed</strong>The bound book is ready in the Ink Pot.'}return}try{const result=await GM_BOS.startNativeBind({cancelToken:token,onProgress:(done,total)=>{GM_BOS_UI.packing={done:done,total:total,kind:'bind'};summary.innerHTML='<strong>Gathering '+done+' of '+total+' A4 pages</strong>The APK will render these pages away from the live book.'},onQueued:()=>{GM_BOS_UI.packing=null}});if(result&&result.cancelled){GM_BOS.discardNativeBind();title.textContent='Binding Cancelled';summary.innerHTML='<strong>No unfinished book was kept</strong>The previous completed bound PDF was not changed.'}else if(result){title.textContent='Binding Continues in Background';summary.innerHTML='<strong>'+result.pageCount+' A4 pages gathered</strong>You may continue using the app. A message will appear when the new bound PDF is ready.'}}catch(err){GM_BOS.discardNativeBind();title.textContent='Binding Could Not Start';summary.innerHTML='<strong>The previous bound PDF is unchanged</strong>'+esc(String(err&&err.message||err))}finally{modal.classList.remove('packaging','cancelling');GM_BOS_UI.packing=null;GM_BOS_UI.cancelToken=null;gmBosActiveBindCancel=null;renderInkPrintRoom();renderBosConversion()}}
function gmBosHandleTerminalJob(st,pending){if(!pending||pending.jobId!==st.jobId)return;const bindModal=$('#gmBosBindModal');if(bindModal)bindModal.classList.remove('open','packaging','cancelling');if(st.state==='ready'){if(pending.kind==='bind'){const cat=pending.catalog;if(cat){cat.nativeSaved=true;cat.nativePdfSize=Number(st.pdfBytes||0);cat.fileName=st.fileName||pending.fileName||'';cat.boundAt=cat.boundAt||new Date().toISOString();lsSet(SKEYS.boundCatalog,JSON.stringify(cat));GM_BOS.markBoundReady(st)}}else if(pending.kind==='scribe'){storeBosEntry({scriptId:pending.scriptId,scriptName:pending.scriptName,pdfKey:st.storageKey||pending.storageKey,fileName:st.fileName||pending.fileName,pageCount:Number(st.total||0),pdfBytes:Number(st.pdfBytes||0),savedAt:new Date().toISOString()})}lsRemove(SKEYS.pendingJob);renderAllShelves();gmBosShowJobNotice(pending.kind==='scribe'?'BoS Text Conversion':'Book of Shadows PDF',(pending.scriptName||'Book of Shadows')+' is ready','The dated PDF can be opened now and is kept as the current app copy.',{label:'Open PDF',run:()=>GM_BOS.exportBookPdf(st.storageKey||pending.storageKey,st.fileName||pending.fileName,true)})}else if(st.state==='cancelled'||st.state==='error'){if(pending.kind==='bind')GM_BOS.discardNativeBind();lsRemove(SKEYS.pendingJob);renderAllShelves();gmBosShowJobNotice(pending.kind==='scribe'?'BoS Text Conversion':'Book of Shadows PDF',st.state==='cancelled'?'Task cancelled':'The PDF could not be completed',st.message||'The unfinished file was discarded. The previous completed PDF is unchanged.')}}
function gmBosPollNativeJob(){if(!GM_BOS||!GM_BOS.nativeRenderer())return;const st=GM_BOS.jobStatus(),sig=[st.jobId,st.state,st.done,st.total,st.updatedAt].join('|');if(sig!==GM_BOS_UI.lastStatusSig){GM_BOS_UI.lastStatusSig=sig;gmBosDiag('NATIVE STATUS','Background BoS PDF status',st,st.state==='error')}const pending=gmBosPendingJob();if(pending&&pending.jobId===st.jobId&&['ready','cancelled','error'].includes(st.state))gmBosHandleTerminalJob(st,pending);if($('#inkView')&&$('#inkView').classList.contains('active')){gmBosRenderNativeStatus();renderBosConversion();gmInkUpdatePrintSummary(gmInkBoundCatalog())}}
function gmBosInstallBackgroundJobs(){if(GM_BOS_UI.pollTimer)return;$('#gmBosJobContinue').onclick=()=>$('#gmBosJobModal').classList.remove('open');$('#gmBosJobModal').onclick=ev=>{if(ev.target.id==='gmBosJobModal')ev.currentTarget.classList.remove('open')};$('#gmBosBindModal').onclick=ev=>{if(ev.target.id==='gmBosBindModal'&&!ev.currentTarget.classList.contains('packaging'))ev.currentTarget.classList.remove('open')};GM_BOS_UI.pollTimer=setInterval(gmBosPollNativeJob,850);setTimeout(gmBosPollNativeJob,80)}
'''


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
    page = replace_once(
        page,
        "<!-- V47 MOBILE BIND / INK POT ENGINE: isolated one-page html2canvas-pro capture replaces the Android-rejected SVG foreignObject capture; exact A4 image-only PDF retained. -->",
        "<!-- V29 APK BOS ENGINE: the APK renders one A4 page at a time in an isolated background process; html2canvas remains only as a browser fallback. -->",
        "V29 renderer description",
    )
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

    old_wait_image = extract_function(page, "function gmBosWaitImage(")
    page = replace_once(page, old_wait_image, WAIT_IMAGE, "bounded image readiness wait")

    old_inline_images = extract_function(page, "async function gmBosInlineBlobImages(")
    page = replace_once(page, old_inline_images, INLINE_BLOB_IMAGES, "parallel blob image preparation")

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
    new_page_loop = "if(progress)progress(0,chosen.length,'flattening');for(let i=0;i<chosen.length;i++){gmBosThrowIfCancelled(options);const pageStarted=Date.now();if(btn)btn.textContent='Flattening '+(i+1)+'/'+chosen.length;const sheet=await gmBosPreparePrintPage(chosen[i],i,chosen.length,binding,printMap);gmBosThrowIfCancelled(options);const flat=await gmBosFlatBlobFromSheet(sheet,i,chosen.length,binding,options);gmBosThrowIfCancelled(options);out.push(flat);gmBosRevokePrintObjectUrls();gmBosDiag('BIND PAGE','A4 page fully prepared and captured',{page:i+1,total:chosen.length,jpegBytes:flat.blob.size,durationMs:Date.now()-pageStarted});if(progress)progress(i+1,chosen.length,'flattening');await new Promise(r=>setTimeout(r,0))}return out"
    page = replace_once(page, old_page_loop, new_page_loop, "per-page binding timing")

    old_bind_ui = extract_function(page, "async function gmBosBindCurrentSelection(")
    page = replace_once(page, old_bind_ui, BIND_UI, "cancel-safe binding popup")

    old_bind_markup = '<div id="gmBosBindModal" class="modal"><div class="modalCard"><h2 id="gmBosBindTitle">Book of Shadows Bound</h2><div id="gmBosBindSummary" class="gmBosBindSummary"><strong>Selected chapters flattened</strong>The bound page count will appear here.</div><ul class="gmBosBindList">'
    new_bind_markup = '<div id="gmBosBindModal" class="modal"><div class="modalCard"><h2 id="gmBosBindTitle">Book of Shadows Bound</h2><div id="gmBosBindSummary" class="gmBosBindSummary"><strong>Selected chapters flattened</strong>The bound page count will appear here.</div><button id="gmBosCancelBind" class="tagBtn gmBosCancelBind" type="button">Cancel Binding</button><ul class="gmBosBindList">'
    page = replace_once(page, old_bind_markup, new_bind_markup, "binding cancel button")

    old_bind_css = ".gmBosBindList{margin:8px 0;padding-left:19px;color:#c8af78;font-size:11px;line-height:1.5}#gmBosBindModal.binding .gmBosBindChoices{display:none}"
    new_bind_css = ".gmBosBindList{margin:8px 0;padding-left:19px;color:#c8af78;font-size:11px;line-height:1.5}.gmBosCancelBind{display:none;width:100%;min-height:48px;margin:10px 0;border-color:#ba774f;color:#ffe0c7;background:linear-gradient(#713722,#36170f)}#gmBosBindModal.binding .gmBosCancelBind{display:block}#gmBosBindModal.binding .gmBosBindChoices{display:none}"
    page = replace_once(page, old_bind_css, new_bind_css, "binding cancel button styles")

    old_cancel_handler = "$('#gmBosStayEditing').onclick=()=>$('#gmBosBindModal').classList.remove('open');"
    new_cancel_handler = "$('#gmBosCancelBind').onclick=gmBosCancelCurrentBind;$('#gmBosStayEditing').onclick=()=>$('#gmBosBindModal').classList.remove('open');"
    page = replace_once(page, old_cancel_handler, new_cancel_handler, "binding cancel handler")

    # V29: keep a compact current catalog and one pending-job record. PDF bytes
    # remain in native private files, never localStorage or the JSON backup.
    old_keys = "const SKEYS={books:'gm_scribe_books_v1',counters:'gm_scribe_counters_v1',draft:'gm_scribe_draft_v1',downloads:'gm_scribe_language_pack_state_v2',prefs:'gm_scribe_ui_v2',bosDerived:'gm_scribe_bos_books_v1',altarIntentions:'gm_scribe_bos_altar_intentions_v1',bindingHand:'gm_scribe_bos_binding_hand_v1'};"
    new_keys = "const SKEYS={books:'gm_scribe_books_v1',counters:'gm_scribe_counters_v1',draft:'gm_scribe_draft_v1',downloads:'gm_scribe_language_pack_state_v2',prefs:'gm_scribe_ui_v2',bosDerived:'gm_scribe_bos_books_v2',altarIntentions:'gm_scribe_bos_altar_intentions_v1',bindingHand:'gm_scribe_bos_binding_hand_v1',boundCatalog:'gm_scribe_bos_bound_catalog_v2',pendingJob:'gm_scribe_bos_native_job_v2'};"
    page = replace_once(page, old_keys, new_keys, "compact BoS storage keys")

    old_rows = "rows=chosen.map((p,i)=>({key:'bound-page-'+i,page:p,chapterId:p.dataset.chapter||'',title:p.dataset.title||'Book of Shadows Page'}));"
    new_rows = "rows=chosen.map((p,i)=>({key:'bound-page-'+i,page:p,sourceIndex:pages.indexOf(p),chapterId:p.dataset.chapter||'',title:p.dataset.title||'Book of Shadows Page'}));"
    page = replace_once(page, old_rows, new_rows, "stable bound page locations")

    old_catalog = extract_function(page, "function getBoundCatalog(")
    page = replace_once(page, old_catalog, V29_GET_CATALOG, "persisted bound catalog")

    v28_api = "return {open,close,show,jump,chapterContents,prev,next,bindSelected,flattenBound,getBoundCatalog,printBound,printSelected,hasStoredBook:gmBosStoredBookAvailable,exportStoredBook:gmBosExportStoredBook,get pages(){return pages},get spells(){return spells}};"
    v29_api = "return {open,close,show,jump,chapterContents,prev,next,bindSelected,flattenBound,getBoundCatalog,printBound,printSelected,hasStoredBook:gmBosStoredBookAvailable,exportStoredBook:gmBosExportStoredBook,nativeRenderer:gmBosNativeRendererAvailable,startNativeBind:startNativeBind,startNativeConversion:startNativeConversion,startNativeSelection:startNativeSelection,hasBookPdf:gmBosHasBookPdf,bookPdfInfo:gmBosBookPdfInfo,exportBookPdf:gmBosExportBookPdf,jobStatus:gmBosNativeJobStatus,cancelJob:gmBosCancelNativeJob,markBoundReady:markNativeBoundReady,discardNativeBind:discardNativeBind,get pages(){return pages},get spells(){return spells}};"
    page = replace_once(page, v28_api, V29_NATIVE_CORE + v29_api, "background APK renderer API")

    first_style_end = page.find("</style>")
    if first_style_end < 0:
        raise SystemExit("Scribe stylesheet end was not found")
    page = page[:first_style_end] + V29_STYLE + page[first_style_end:]

    ink_start = page.find('<section id="inkView"')
    ink_end_marker = "</section>\n\n<div id=\"scriptModal\""
    ink_end = page.find(ink_end_marker, ink_start)
    if ink_start < 0 or ink_end < 0:
        raise SystemExit("Ink Pot view boundary was not found")
    page = page[:ink_start] + V29_INK_MARKUP + page[ink_end + len("</section>"):]

    bind_start = page.find('<div id="gmBosBindModal"')
    bind_end_marker = "\n\n<section id=\"bosView\""
    bind_end = page.find(bind_end_marker, bind_start)
    if bind_start < 0 or bind_end < 0:
        raise SystemExit("Bind modal boundary was not found")
    page = page[:bind_start] + V29_BIND_MARKUP + page[bind_end:]

    global_anchor = "const gmBosBackBtn=$('#gmBosBack');"
    page = replace_once(page, global_anchor, V29_GLOBAL + global_anchor, "V29 Ink Pot and shelf controller")

    old_handoff = "$('#gmBosGoPrintRoom').onclick=()=>{$('#gmBosBindModal').classList.remove('open');openInkpotPrintRoom()}"
    new_handoff = "$('#gmBosGoPrintRoom').onclick=()=>{$('#gmBosBindModal').classList.remove('open');openInkpotScribeBooks()}"
    page = replace_once(page, old_handoff, new_handoff, "binding to Choose Text handoff")

    page = replace_once(page, "init();\ntry{if(localStorage", "init();gmBosInstallBackgroundJobs();\ntry{if(localStorage", "background status polling")

    required = [
        "GreenmanFiles",
        "beginLastBoundPdf",
        "appendLastBoundPdfChunk",
        "hasStoredBook:gmBosStoredBookAvailable",
        "PDF link is ready for a separate tap",
        "Ink Pot controls rendered",
        "const frame=document.createElement('iframe')",
        "timer=setTimeout(done,2500)",
        "imageReadyMs:imageReadyMs",
        "id=\"gmBosCancelBind\"",
        "BIND CANCELLED",
        "gmBosThrowIfCancelled(options)",
        "BoS Text Conversion",
        "startNativeConversion",
        "beginPdfPage",
        "gm_scribe_bos_bound_catalog_v2",
        "Choose Scribe Text",
        "Chapter Contents",
        "Only the current PDF for each chosen hand is kept.",
        "Downloads / Greenman HedgeWitchery",
        "gmBosInstallBackgroundJobs",
    ]
    missing = [item for item in required if item not in page]
    if missing:
        raise SystemExit("Missing V28 BoS requirements: " + ", ".join(missing))
    if "const host=document.createElement('div')" in extract_function(page, "async function gmBosFlatBlobFromSheet("):
        raise SystemExit("Whole-document capture host remains")
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
    print("V29 background BoS binding and Scribe conversion patch passed.")


if __name__ == "__main__":
    main()
