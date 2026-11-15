#!/usr/bin/env python3
from pathlib import Path
import json, sys

if len(sys.argv)!=3:
    raise SystemExit('usage: install_print_layout_277.py INPUT OUTPUT')

src=Path(sys.argv[1]); out=Path(sys.argv[2])
s=src.read_text(encoding='utf-8')
marker='const PAGES = '
st=s.index(marker)+len(marker)
obj,end=json.JSONDecoder().raw_decode(s[st:])
for k in ('journal','spellBuilder'):
    if k not in obj: raise SystemExit(f'missing PAGES.{k}')
journal=obj['journal']; spell=obj['spellBuilder']

FONT_CSS="""@font-face{font-family:'Cinzel';src:url('https://greenman.local/fonts/Cinzel.ttf') format('truetype');font-style:normal;font-weight:400 900;font-display:block;}@font-face{font-family:'IM Fell English';src:url('https://greenman.local/fonts/IMFellEnglish-Regular.ttf') format('truetype');font-style:normal;font-weight:400;font-display:block;}@font-face{font-family:'IM Fell English';src:url('https://greenman.local/fonts/IMFellEnglish-Italic.ttf') format('truetype');font-style:italic;font-weight:400;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-Regular.ttf') format('truetype');font-style:normal;font-weight:400;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-Italic.ttf') format('truetype');font-style:italic;font-weight:400;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-SemiBold.ttf') format('truetype');font-style:normal;font-weight:600;font-display:block;}@font-face{font-family:'Crimson Text';src:url('https://greenman.local/fonts/CrimsonText-Bold.ttf') format('truetype');font-style:normal;font-weight:700;font-display:block;}"""

def replace_once(text,old,new,label):
    n=text.count(old)
    if n!=1: raise SystemExit(f'{label}: expected 1 anchor, got {n}')
    return text.replace(old,new,1)

# JOURNAL / BoS: do not erase the saved page's own internal fit. The snapshot was
# captured from the proven A4 canvases. Only the outer snapshot content may be
# reduced, and only from real visible bounds. Never let a bad measurement crush
# a page to 25% again.
journal=replace_once(journal,
".gm-flat .a4-content{transform:none!important;width:100%!important;height:auto!important;min-height:0!important;max-height:none!important;}",
".gm-flat .a4-content{max-width:none!important;}",
'Journal flat A4 preserve saved fit')
journal=replace_once(journal,
".gm-flat .summary-page{transform:none!important;width:100%!important;height:auto!important;min-height:0!important;max-height:none!important;background:transparent!important;}",
".gm-flat .summary-page{background:transparent!important;}",
'Journal flat summary preserve saved fit')

fit_start=journal.index('function fitFlatPages(root){')
fit_end=journal.index('\nfunction gmFlatPrint(area){',fit_start)
new_fit=r'''function fitFlatPages(root){
  qsa('.gm-flat .true-page',root).forEach(function(pg){
    var c=pg.querySelector(':scope > .true-content')||pg.querySelector('.true-content')||pg.firstElementChild;if(!c)return;
    var cs=c.style,availH=pg.clientHeight||1058,availW=pg.clientWidth||756;
    cs.setProperty('transform','none','important');
    cs.setProperty('transform-origin','top left','important');
    cs.setProperty('width','100%','important');
    cs.setProperty('max-width','none','important');
    /* Preserve the snapshot's own nested A4/content transforms. They are part of the saved page. */
    void c.offsetHeight;
    var base=c.getBoundingClientRect(),needH=availH,needW=availW,nodes=c.querySelectorAll('*');
    for(var i=0;i<nodes.length;i++){
      var el=nodes[i],r=el.getBoundingClientRect();
      if(!r.width&&!r.height)continue;
      var pos='';try{pos=getComputedStyle(el).position}catch(_e){}
      if(pos==='fixed')continue;
      needH=Math.max(needH,r.bottom-base.top);
      needW=Math.max(needW,r.right-base.left);
    }
    var scale=Math.min(1,(availH-5)/Math.max(1,needH),(availW-5)/Math.max(1,needW));
    /* These are already A4 snapshots. A scale below this means the measurement is bad,
       not that the saved page should become miniature. Prefer clipping a rogue outlier. */
    scale=Math.max(.82,scale*.995);
    if(scale<.997)cs.setProperty('transform','scale('+scale.toFixed(4)+')','important');
    else cs.setProperty('transform','none','important');
    pg.setAttribute('data-gm-print-fit',scale.toFixed(4));
  });
}
'''
journal=journal[:fit_start]+new_fit+journal[fit_end:]

font_helper='''\nfunction gmEnsureJournalPrintFonts(done){
  var id='gm-journal-local-print-fonts',st=document.getElementById(id);
  if(!st){st=document.createElement('style');st.id=id;st.textContent=__FONT_CSS__;document.head.appendChild(st);}
  var fired=false;function go(){if(fired)return;fired=true;requestAnimationFrame(function(){requestAnimationFrame(function(){done();});});}
  try{if(document.fonts&&document.fonts.load){Promise.all([document.fonts.load("700 12px 'Cinzel'"),document.fonts.load("400 12px 'IM Fell English'"),document.fonts.load("400 12px 'Crimson Text'"),document.fonts.load("700 12px 'Crimson Text'")]).then(go,go);setTimeout(go,900);}else go();}catch(_e){go();}
}
window.addEventListener('afterprint',function(){var st=document.getElementById('gm-journal-local-print-fonts');if(st)st.remove();});
'''.replace('__FONT_CSS__',json.dumps(FONT_CSS,ensure_ascii=False))
insert_at=journal.index('\nfunction gmFlatPrint(area){',fit_start)
journal=journal[:insert_at]+font_helper+journal[insert_at:]

old='''function gmFlatPrint(area){
  document.body.classList.add('gm-bos-fitting');
  void document.body.offsetHeight;
  try{fitFlatPages(area);}catch(_e){}
  document.body.classList.remove('gm-bos-fitting');
  setTimeout(function(){window.print();},140);
}'''
new='''function gmFlatPrint(area){
  gmEnsureJournalPrintFonts(function(){
    document.body.classList.add('gm-bos-fitting');
    void document.body.offsetHeight;
    try{fitFlatPages(area);}catch(_e){}
    document.body.classList.remove('gm-bos-fitting');
    setTimeout(function(){window.print();},140);
  });
}'''
journal=replace_once(journal,old,new,'Journal snapshot print wait for local fonts')
old="function printHtml(html){const area=qs('#printArea'); area.innerHTML=html; fitSummaryPages(area); fitInstructionText(); fitFlatPages(area); setTimeout(()=>window.print(),120);}"
new="function printHtml(html){const area=qs('#printArea');area.innerHTML=html;gmEnsureJournalPrintFonts(function(){fitSummaryPages(area);fitInstructionText();fitFlatPages(area);setTimeout(()=>window.print(),120);});}"
journal=replace_once(journal,old,new,'Journal rebuilt print wait for local fonts')
old_start='function printWholeBos(){'
i=journal.index(old_start)
j=journal.index('\nfunction openDeletePopup()',i)
old_whole=journal[i:j]
needle="fitSummaryPages(area);fitInstructionText();fitFlatPages(area);setTimeout(()=>window.print(),180);}"
if needle not in old_whole: raise SystemExit('Journal whole BoS print tail not found')
new_whole=old_whole.replace(needle,"gmEnsureJournalPrintFonts(function(){fitSummaryPages(area);fitInstructionText();fitFlatPages(area);setTimeout(()=>window.print(),180);});}",1)
journal=journal[:i]+new_whole+journal[j:]

# SPELL BUILDER FULL/A4 printer: load the packaged fonts inside the off-screen
# print iframe BEFORE fitPage measures anything. Then contain instruction pages
# as a whole if the intended fonts make their final row taller.
anchor="var printFrame=null, busy=false, oldTitle='';"
font_js="var GM_LOCAL_PRINT_FONT_CSS="+json.dumps(FONT_CSS,ensure_ascii=False)+";\nfunction gmPrintFontsReady(doc,done){var fired=false;function go(){if(fired)return;fired=true;setTimeout(done,35)}try{if(doc.fonts&&doc.fonts.load){Promise.all([doc.fonts.load(\"700 12px 'Cinzel'\"),doc.fonts.load(\"400 12px 'IM Fell English'\"),doc.fonts.load(\"400 12px 'Crimson Text'\"),doc.fonts.load(\"700 12px 'Crimson Text'\")]).then(go,go);setTimeout(go,1100)}else go()}catch(_e){go()}}"
spell=replace_once(spell,anchor,anchor+'\n'+font_js,'Canonical print local font helper')

needle="<style>@page{size:A4 portrait;margin:0}html,body{margin:0;padding:0;background:#fff}"
replace="<style>'+GM_LOCAL_PRINT_FONT_CSS+'@page{size:A4 portrait;margin:0}html,body{margin:0;padding:0;background:#fff}"
spell=replace_once(spell,needle,replace,'Canonical print iframe local fonts')

needle=''' if(isInstructions){
  qa('.gm-step',page).forEach(function(step){
   qa('.gm-making-text,.gm-voice-text',step).forEach(function(box){shrinkBox(box,7.2)});
  });
 }
 if(!isInfo&&!isInstructions){'''
replace=''' if(isInstructions){
  qa('.gm-step',page).forEach(function(step){
   qa('.gm-making-text,.gm-voice-text',step).forEach(function(box){shrinkBox(box,7.2)});
  });
  var instructionContent=q(':scope > .true-content',page)||q('.true-content',page);
  if(instructionContent){
   instructionContent.style.setProperty('transform','none','important');
   instructionContent.style.setProperty('transform-origin','top left','important');
   instructionContent.style.setProperty('width','100%','important');
   void instructionContent.offsetHeight;
   var ib=instructionContent.getBoundingClientRect(),ih=page.clientHeight||1058,iw=page.clientWidth||756,needIH=ih,needIW=iw;
   qa('*',instructionContent).forEach(function(el){var r=el.getBoundingClientRect();if(!r.width&&!r.height)return;needIH=Math.max(needIH,r.bottom-ib.top);needIW=Math.max(needIW,r.right-ib.left)});
   var isc=Math.min(1,(ih-5)/Math.max(1,needIH),(iw-5)/Math.max(1,needIW));
   if(isc<.997){isc=Math.max(.82,isc*.992);instructionContent.style.setProperty('transform','scale('+isc.toFixed(5)+')','important');page.setAttribute('data-gm-instruction-fit',isc.toFixed(5));}
   else page.setAttribute('data-gm-instruction-fit','1.00000');
  }
 }
 if(!isInfo&&!isInstructions){'''
spell=replace_once(spell,needle,replace,'Canonical instruction whole-page containment')

old="setTimeout(function(){try{if(typeof window.gmNumerologyLines==='function')window.gmNumerologyLines(root,sp)}catch(e){}qa('.true-page',d).forEach(fitPage);busy=false;window.gmSetPrintStatus(false);try{printFrame.contentWindow.document.title=title;printFrame.contentWindow.focus();printFrame.contentWindow.print()}catch(e){console.error(e)}},900);"
new="gmPrintFontsReady(d,function(){try{if(typeof window.gmNumerologyLines==='function')window.gmNumerologyLines(root,sp)}catch(e){}qa('.true-page',d).forEach(fitPage);busy=false;window.gmSetPrintStatus(false);try{printFrame.contentWindow.document.title=title;printFrame.contentWindow.focus();printFrame.contentWindow.print()}catch(e){console.error(e)}});"
spell=replace_once(spell,old,new,'Canonical print wait before fit')

obj['journal']=journal;obj['spellBuilder']=spell
new_json=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
s=s[:st]+new_json+s[st+end:]

for term in ('gmEnsureJournalPrintFonts','data-gm-instruction-fit','GM_LOCAL_PRINT_FONT_CSS','gmPrintFontsReady'):
    if term not in s: raise SystemExit('missing guard '+term)
out.write_text(s,encoding='utf-8')
print('Installed 2.7.7 print layout repair: BoS saved-page scale + local-font fit + instruction containment')
