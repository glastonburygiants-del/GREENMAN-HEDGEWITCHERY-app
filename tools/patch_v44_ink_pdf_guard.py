#!/usr/bin/env python3
"""V44: export-only Ink Pot SVG guard, fresh page rebuild, PDF source marker."""
import json,re,sys
from pathlib import Path
ANCHORS=("function __gmLazyScribeSrc(){return ","PAGES.scribe = ")
MARK="GM_INK_A4_PRINT_GUARD_V44"
HELPER=r'''
/* V44: embed resolved paint in PDF-only SVG markup; refuse a failed vine image. */
function gmBosV44PrepareVineForPdf(svg){
 if(!svg||!svg.classList||!svg.matches('.gmStoryVine,.gmTagBranch'))return;
 const paths=[...svg.querySelectorAll('path')];
 if(!paths.length)throw new Error('A4 vine drawing has no paths');
 const props=['fill','stroke','stroke-width','stroke-linecap','stroke-linejoin',
  'stroke-opacity','fill-opacity','stroke-dasharray','stroke-dashoffset','opacity','color'];
 paths.forEach(path=>{
  const computed=getComputedStyle(path);
  props.forEach(prop=>{
   const value=String(computed.getPropertyValue(prop)||'').trim();
   if(value){path.setAttribute(prop,value);path.style.setProperty(prop,value,'important')}
  });
  path.setAttribute('vector-effect','none');
  path.style.setProperty('vector-effect','none','important');
  path.style.setProperty('filter','none','important');
  if(path.matches('.vine-shadow,.vine-stem,.vine-bark,.vine-highlight,.vine-vein,.vine-tendril,.branch-shadow,.branch-stem')){
   path.setAttribute('fill','none');path.style.setProperty('fill','none','important');
   if(!path.getAttribute('stroke')||path.getAttribute('stroke')==='none')
    throw new Error('A4 vine stroke colour is unavailable');
  }
 });
 svg.style.setProperty('filter','none','important');
 svg.setAttribute('data-gm-pdf-vine-paint','v44');
}
'''
def one(s,a,b,label):
    n=s.count(a)
    if n!=1:raise ValueError(f"{label}: expected one anchor, found {n}")
    return s.replace(a,b,1)
def patch(src):
    aa=[a for a in ANCHORS if src.count(a)]
    if len(aa)!=1 or src.count(aa[0])!=1:raise ValueError("Expected one embedded Scribe source")
    pos=src.index(aa[0])+len(aa[0])
    page,n=json.JSONDecoder().raw_decode(src[pos:])
    if not isinstance(page,str) or MARK in page:raise ValueError("Unexpected Scribe source or duplicate patch")
    for t in ("GM_INK_A4_SVG_PAINT_PAGINATION_V43","async function gmBosPreparePrintPage(page,idx,total,binding,printMap){",
              "async function printSpell(options){","async function gmBosRasterizeSvg(svg,token,scale,binding){"):
        if t not in page:raise ValueError("Expected original renderer missing: "+t)
    anchor="async function gmBosPreparePrintPage(page,idx,total,binding,printMap){"
    page=one(page,anchor,"/* "+MARK+" */\n"+HELPER+"\n"+anchor,"helper")
    before="  const fitMs=Date.now()-phase;[...stage.querySelectorAll('svg:not(.gmInkScriptWordSvg)')].forEach(svg=>{"
    page=one(page,before,"  [...clone.querySelectorAll('svg.gmStoryVine,svg.gmTagBranch')].forEach(gmBosV44PrepareVineForPdf);\n"+before,"inline print paint")
    old="for(let j=0;j<svgs.length;j++){await gmBosRasterizeSvg(svgs[j],idx+'_'+j,total>100?1.12:(total>40?1.25:1.45),binding);if(j%8===7)await new Promise(r=>setTimeout(r,0))}"
    new="for(let j=0;j<svgs.length;j++){const important=svgs[j].matches('.gmStoryVine,.gmTagBranch');const ok=await gmBosRasterizeSvg(svgs[j],idx+'_'+j,total>100?1.12:(total>40?1.25:1.45),binding);if(important&&(!ok||svgs[j].isConnected||clone.contains(svgs[j])))throw new Error('The A4 vine failed to render. No incomplete PDF was saved.');if(j%8===7)await new Promise(r=>setTimeout(r,0))}"
    page=one(page,old,new,"fail closed on vine")
    page=one(page,"?'|paint-v43':''","?'|paint-v44':''","art cache version")
    page=one(page,"options=options||{};if(!pages.length)build();const ix=Number(options.spellIndex)",
             "options=options||{};build();const ix=Number(options.spellIndex)","rebuild print pages")
    page=one(page,"push('%PDF-1.4\\n%Greenman Flat A4\\n');",
             "push('%PDF-1.4\\n%Greenman Flat A4 V44\\n');","PDF identification")
    if page.count(MARK)!=1 or page.count("gmBosV44PrepareVineForPdf")<2:raise ValueError("V44 source guard failed")
    encoded=json.dumps(page,ensure_ascii=False,separators=(",",":"))
    encoded=re.sub(r'</script',r'<\/script',encoded,flags=re.I)
    out=src[:pos]+encoded+src[pos+n:]
    if out[:pos]!=src[:pos] or out[pos+len(encoded):]!=src[pos+n:]:raise ValueError("Outer app changed unexpectedly")
    return out
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("Usage: patch_v44_ink_pdf_guard.py INPUT.html OUTPUT.html")
    Path(sys.argv[2]).write_text(patch(Path(sys.argv[1]).read_text(encoding="utf-8")),encoding="utf-8")
    print("V44: vine SVGs checked, freshly generated pages, PDF source tag")
