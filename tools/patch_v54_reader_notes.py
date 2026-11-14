#!/usr/bin/env python3
"""Repair V51 reader paging, the empty Deities opener and reference notes."""
import json
import re
import sys
from pathlib import Path

MARK = 'gm-bos-reader-notes-v54'
RUNTIME = r'''
function gmV54ReferenceHTML(html,source,index){
 const doc=new DOMParser().parseFromString(html,'text/html');
 doc.querySelectorAll('.phase-note').forEach((area,n)=>{
  if(area.querySelector('textarea,[contenteditable]'))return;
  const field=doc.createElement('textarea');field.dataset.note='reference_'+source+'_'+index+'_phase_'+n;
  field.setAttribute('aria-label','My notes');
  field.style.cssText='position:relative;z-index:1;display:block;width:100%;height:100%;min-height:12mm;margin:6mm 0 0;padding:0;border:0;resize:none;background:transparent;font:8pt/5mm Georgia,serif;color:#33271b';
  area.append(field);
 });
 doc.querySelectorAll('textarea').forEach((field,n)=>{
  if(!field.dataset.note&&!field.dataset.save)field.dataset.note='reference_'+source+'_'+index+'_'+n;
  if(!field.getAttribute('aria-label'))field.setAttribute('aria-label','Notes');
  if(!field.placeholder)field.placeholder='Tap here to write your notes';
 });
 return '<!doctype html>'+doc.documentElement.outerHTML;
}
function gmV54FinishReaderPages(){
 const ordinals={};
 pages.forEach(p=>{
  if(!p.matches('.gmBosPlanetSavedPage,.gmBosMoonPhaseCombinedPage,.gmBosMoonPhaseContinuation'))return;
  const base=p.dataset.chapter+':'+p.dataset.title,ordinal=ordinals[base]||0;ordinals[base]=ordinal+1;
  const key='gm_bos_reference_notes_v1:'+base+':'+ordinal;
  const pane=document.createElement('section');pane.className='gmV54PageNotes';
  const label=document.createElement('b');label.textContent='My notes';
  const field=document.createElement('div');field.className='gmV54NotesEdit';field.contentEditable='true';field.setAttribute('role','textbox');field.setAttribute('aria-multiline','true');field.setAttribute('aria-label','Notes for '+p.dataset.title);field.dataset.placeholder='Tap here to write your notes';
  try{field.textContent=localStorage.getItem(key)||''}catch(_e){}
  field.addEventListener('input',()=>{try{localStorage.setItem(key,field.innerText||'')}catch(_e){}});
  const hasItems=!!p.querySelector('[data-entry-id]');p.classList.add('gmV54NotesPage');if(!hasItems)p.classList.add('gmV54NotesRoomy');
  pane.append(label,field);p.querySelector('.gmBosPaper').append(pane);
 });
}
'''
CSS = r'''
.gmV54PageNotes{position:absolute;z-index:6;left:14mm;right:13mm;bottom:12mm;height:21mm;padding:1.8mm 2.5mm 1mm;border:.25mm solid #b6a17d;border-radius:2mm;background:#f5ecd8;box-sizing:border-box;display:flex;flex-direction:column;gap:1mm;color:#453522}
.gmV54PageNotes>b{font:700 7.5pt/1.2 Georgia,serif;letter-spacing:.04em}
.gmV54NotesEdit{flex:1;min-height:0;width:100%;overflow:auto;outline:none;white-space:pre-wrap;font:italic 9pt/5mm Georgia,serif;background:repeating-linear-gradient(to bottom,transparent 0,transparent calc(5mm - 1px),#bfae8b calc(5mm - 1px),#bfae8b 5mm);box-sizing:border-box}
.gmV54NotesEdit:empty:before{content:attr(data-placeholder);color:#958361;pointer-events:none}
.gmV54NotesRoomy .gmV54PageNotes{height:55mm}
@media print{.gmV54NotesEdit:empty:before{content:none}.gmV54NotesEdit{overflow:hidden}}
'''

def once(source,old,new):
    if source.count(old)!=1:
        raise ValueError(f'Expected one anchor: {old[:100]} (found {source.count(old)})')
    return source.replace(old,new,1)

def patch(source):
    if MARK in source: raise ValueError('V54 already applied')
    anchors=[a for a in ('function __gmLazyScribeSrc(){return ','PAGES.scribe = ') if a in source]
    if len(anchors)!=1: raise ValueError('Expected embedded Scribe document')
    pos=source.index(anchors[0])+len(anchors[0])
    scribe,consumed=json.JSONDecoder().raw_decode(source[pos:])
    scribe=once(scribe,'.gmBosPage.gmBosScribeLetterPage{display:block!important;','.gmBosPage.gmBosScribeLetterPage{')
    scribe=once(scribe,'const W=794,H=1123;','const W=794,H=1123;\n'+RUNTIME)
    scribe=once(scribe,' gmV51AddScribeLettersPages();\n addChapterContentsPages();',' gmV51AddScribeLettersPages();\n gmV54FinishReaderPages();\n addChapterContentsPages();')
    # Existing illustrated-page notes must use their original saved-note keys.
    old='textarea[data-note],input[data-save]'
    if scribe.count(old)!=2: raise ValueError('Expected reader and print note bindings')
    scribe=scribe.replace(old,'textarea[data-note],textarea[data-save],input[data-save]')
    start=scribe.index('function addRefs(chapter,source,start,end){')
    end=scribe.index('\nconst GM_HEART_PLANETS',start)
    refs=scribe[start:end]
    if refs.count('decode64(b64)')!=2: raise ValueError('Unexpected reference decoding')
    refs=refs.replace('decode64(b64)','gmV54ReferenceHTML(decode64(b64),source,i)')
    scribe=scribe[:start]+refs+scribe[end:]
    # Empty Deities was wrongly treated as an already-designed chapter opener.
    start=scribe.index('function addDeityJourneyPages(){')
    a=scribe.index("const h=p.querySelector('.gmBosChapterHead');",start)
    b=scribe.index(";return;}['goddess','god','pair']",a)
    replacement=r'''p.classList.add('gmBosV47Page','gmV47ChapterPage');const h=p.querySelector('.gmBosChapterHead');if(h){h.innerHTML='';h.setAttribute('data-gm-chapter-number','11')}body(p).innerHTML='<div class="gmV47ChapterOpener"><div class="gmV47ChapterTitleBlock">'+gmV47Initial('D')+'<div class="gmV47MainTitle"><div class="gmV47Kicker">Chapter 11</div><h1 class="gmV47TitleText">Deities</h1><div class="gmV47TitleCaption">The deities you have gathered, kept by tradition, origin and divine character.</div></div></div>'+gmV47VineRule()+'<div class="gmBosEmpty">No deities have been gathered into this Book of Shadows yet.</div></div>' '''.rstrip()
    scribe=scribe[:a]+replacement+scribe[b:]
    scribe=scribe.replace('</head>','<style id="'+MARK+'">'+CSS+'</style></head>',1)
    encoded=json.dumps(scribe,ensure_ascii=False,separators=(',',':'))
    encoded=re.sub(r'</script',r'<\/script',encoded,flags=re.I)
    return source[:pos]+encoded+source[pos+consumed:]

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: patch_v54_reader_notes.py INPUT.html OUTPUT.html')
    Path(sys.argv[2]).write_text(patch(Path(sys.argv[1]).read_text()),encoding='utf-8')
    print('V54 reader paging, Deities opener, Moon/Planet notes and reference note persistence applied')
