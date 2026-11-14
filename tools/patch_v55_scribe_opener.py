#!/usr/bin/env python3
"""One Scribe opener, illuminated S and a clear creative-lettering introduction."""
import json,re,sys
from pathlib import Path

RUNTIME=r'''
function gmV55ScribeOpener(){
 const p=pages.find(p=>p.dataset.chapter==='scribe-letters'&&p.classList.contains('gmBosChapterContentsPage'));if(!p)return;
 p.classList.add('gmV55ScribeOpener');
 const initial=p.querySelector('.gmV47Initial');if(initial)initial.outerHTML=gmV47Initial('S');
 const caption=p.querySelector('.gmV47TitleCaption');if(caption)caption.textContent='Nineteen creative alphabets and symbol sets for making English writing look magical.';
 const intro=document.createElement('section');intro.className='gmV55CreativeIntro';
 intro.innerHTML='<h2>For creative enjoyment</h2><p>Give your English words a magical appearance. Explore these creative alphabets and symbol sets for names, intentions, journal pages, labels and imaginative inscriptions.</p><p><strong>Your words remain English when you change their lettering. This is not a teaching guide, a language course, a translation guide or a guide to historically accurate writing.</strong> The English letter keys are creative writing aids, not complete historical alphabets.</p><p>These designs draw on historic scripts, magical traditions and imagined worlds. Each leaf brings together the Scribe’s letter shapes, a short description and its feather artwork, with space for your own notes. Enjoy the shapes and make the writing your own.</p>';
 p.querySelector('.gmV47ChapterPrelude').before(intro);
}
'''
CSS=r'''
.gmBosV47Page.gmV55ScribeOpener .gmV47ChapterTitleBlock{min-height:43mm!important;padding:1mm 0 3mm!important;grid-template-columns:28mm minmax(0,1fr)!important;column-gap:5mm!important}
.gmBosV47Page.gmV55ScribeOpener .gmV47ChapterTitleBlock .gmV47Initial{width:28mm!important;height:36mm!important}
.gmBosV47Page.gmV55ScribeOpener .gmV47TitleCaption{font-size:10pt!important;line-height:1.3!important;margin-top:2mm!important}
.gmBosV47Page.gmV55ScribeOpener .gmV47VineRule{height:6mm!important;margin:2mm 0!important}
.gmV55CreativeIntro{padding:2mm 1mm 1mm;color:#51412f}
.gmV55CreativeIntro h2{font:600 9pt/1.2 Georgia,serif;color:#803e32;letter-spacing:.07em;text-transform:uppercase;margin:0 0 2mm}
.gmV55CreativeIntro p{font:9pt/1.3 Georgia,serif;margin:0 0 2mm}
.gmV55CreativeIntro strong{font-weight:700}
.gmBosV47Page.gmV55ScribeOpener .gmV47ChapterPrelude{min-height:0!important;padding:2mm 1mm!important}
.gmBosV47Page.gmV55ScribeOpener .gmV47ChapterPrelude p{font-size:9pt!important;line-height:1.3!important}
.gmBosV47Page.gmV55ScribeOpener .gmV47ChapterEntriesTitle{margin:2mm 0 0!important;font-size:7.5pt!important}
.gmBosV47Page.gmV55ScribeOpener .gmV47ChapterEntries{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:0 5mm!important;margin:1.5mm 0 0!important}
.gmBosV47Page.gmV55ScribeOpener .gmV47Entry{grid-template-columns:7mm minmax(0,1fr) 12mm!important;gap:1mm!important;padding:1.2mm 0!important;min-height:8mm!important}
.gmBosV47Page.gmV55ScribeOpener .gmV47EntryText{font-size:9pt!important;line-height:1.16!important}
.gmBosV47Page.gmV55ScribeOpener .gmV47EntryNumber,.gmBosV47Page.gmV55ScribeOpener .gmV47EntryPage{font-size:7pt!important}
'''

def once(s,a,b):
 if s.count(a)!=1:raise ValueError('Expected one anchor: '+a[:90])
 return s.replace(a,b,1)

def patch(s):
 anchor='function __gmLazyScribeSrc(){return ';pos=s.index(anchor)+len(anchor)
 doc,n=json.JSONDecoder().raw_decode(s[pos:])
 if 'gm-bos-reader-notes-v54' not in doc:raise ValueError('V54 base required')
 if 'gm-bos-scribe-opener-v55' in doc:raise ValueError('V55 already applied')
 doc=once(doc,' sheets.forEach((sheet,i)=>{',' sheets.forEach((sheet,i)=>{\n  if(i===0)return; // The chapter register is the single Scribe opener.')
 doc=once(doc,"cleanText(sheet.dataset.script||'Letter reference')","cleanText((sheet.querySelector('h1')||{}).textContent||sheet.dataset.script||'Letter reference').replace(/_/g,' ')")
 doc=once(doc,'const W=794,H=1123;','const W=794,H=1123;\n'+RUNTIME)
 doc=once(doc,' addChapterContentsPages();\n addReferenceIndex();',' addChapterContentsPages();\n gmV55ScribeOpener();\n addReferenceIndex();')
 doc=doc.replace('</head>','<style id="gm-bos-scribe-opener-v55">'+CSS+'</style></head>',1)
 enc=re.sub(r'</script',r'<\/script',json.dumps(doc,ensure_ascii=False,separators=(',',':')),flags=re.I)
 return s[:pos]+enc+s[pos+n:]

if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('Usage: patch_v55_scribe_opener.py INPUT OUTPUT')
 Path(sys.argv[2]).write_text(patch(Path(sys.argv[1]).read_text()),encoding='utf-8')
 print('V55: one Scribe opener, S initial, 19 leaves, creative-lettering introduction')
