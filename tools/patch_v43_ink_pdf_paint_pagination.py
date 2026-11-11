#!/usr/bin/env python3
"""V43: preserve SVG paint in Ink Pot A4 raster images and prevent clipped ceremonies.

The bridge, app identity, signing, data keys and original live spell art are unchanged.
This modifies only the JSON-embedded Scribe document on the isolated preview line.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ANCHORS=("function __gmLazyScribeSrc(){return ","PAGES.scribe = ")
MARK="GM_INK_A4_SVG_PAINT_PAGINATION_V43"
SVG_MARKER="  gmBosUniqueSvgDom(copy,'print_svg_'+token);"
CEREMONY_START="function heartCeremonyPages(e){"
CEREMONY_END="function fitHeartText(root){"
HELPER=r"""
/* Ink Pot PDF only. The SVG is serialized as a separate image where page
   stylesheets are unavailable; embed the resolved paint on every vine path. */
function gmBosV43InlinePrintSvgPaint(source,copy){
 if(!source.classList||(!source.classList.contains('gmStoryVine')&&!source.classList.contains('gmTagBranch')))return;
 const live=[source,...source.querySelectorAll('*')],captured=[copy,...copy.querySelectorAll('*')];
 if(live.length!==captured.length)throw new Error('A4 SVG paint tree changed');
 const props=['fill','fill-opacity','stroke','stroke-opacity','stroke-width',
  'stroke-linecap','stroke-linejoin','stroke-dasharray','stroke-dashoffset',
  'stroke-miterlimit','vector-effect','opacity','color'];
 live.forEach((el,i)=>{
  const computed=getComputedStyle(el),dest=captured[i];
  props.forEach(prop=>{const value=String(computed.getPropertyValue(prop)||'').trim();if(value)dest.style.setProperty(prop,value,'important')});
  dest.style.setProperty('filter','none','important');
 });
}
"""

def replace_one(s,old,new,label):
    count=s.count(old)
    if count!=1:raise ValueError(f"{label}: expected unique anchor, found {count}")
    return s.replace(old,new,1)

def patch(source:str)->str:
    active=[a for a in ANCHORS if source.count(a)]
    if len(active)!=1 or source.count(active[0])!=1:raise ValueError("Expected exactly one Scribe payload")
    start=source.index(active[0])+len(active[0])
    page,consumed=json.JSONDecoder().raw_decode(source[start:])
    if not isinstance(page,str):raise ValueError("Scribe payload was not a string")
    if MARK in page:raise ValueError("V43 already applied")
    for token in (SVG_MARKER,"async function gmBosRasterizeSvg(svg,token,scale,binding){",
                  CEREMONY_START,CEREMONY_END,".gmBosPrintSheet .gmStoryVine"):
        if token not in page:raise ValueError("Source missing "+token[:75])
    # Install the paint inliner before the serializer/rasterizer. The live SVG
    # and its visual styling in the Spell Builder are not modified.
    page=replace_one(page,
        "async function gmBosRasterizeSvg(svg,token,scale,binding){",
        HELPER+"\nasync function gmBosRasterizeSvg(svg,token,scale,binding){","SVG raster helper")
    page=replace_one(page,SVG_MARKER,
        "  gmBosV43InlinePrintSvgPaint(svg,copy);\n"+SVG_MARKER,"SVG serialization hook")
    # Existing cached broken vine/branches cannot be reused.
    page=replace_one(page,
        "cacheKey=sourceKey?(sourceKey+'|'+w+'x'+h+'|'+sc.toFixed(2)):''",
        "cacheKey=sourceKey?(sourceKey+'|'+w+'x'+h+'|'+sc.toFixed(2)+(svg.matches('.gmStoryVine,.gmTagBranch')?'|paint-v43':'')):''",
        "V43 SVG cache separation")
    cstart=page.index(CEREMONY_START)
    cend=page.index(CEREMONY_END,cstart)
    ceremony=page[cstart:cend]
    if ceremony.count("const safeCap=Math.max(1,cap-6);")!=2:
        raise ValueError("Ceremony geometry changed, cannot safely patch")
    ceremony=ceremony.replace("const safeCap=Math.max(1,cap-6);",
                             "const safeCap=Math.max(1,cap-20);")
    ceremony=replace_one(ceremony,"let chosen=null,pageCount=1;",
        "/* A long ceremony must not end with a step clipped at the foot of A4. "
        "Give 13+ full steps at least three sheets. */\n"
        " let chosen=null,pageCount=main.length>=13?3:1;","ceremony minimum pages")
    page=page[:cstart]+ceremony+page[cend:]
    page=replace_one(page,
        "function gmBosV43InlinePrintSvgPaint(source,copy){",
        "/* "+MARK+" */\nfunction gmBosV43InlinePrintSvgPaint(source,copy){",
        "version marker")
    if page.count(MARK)!=1 or page.count("gmBosV43InlinePrintSvgPaint(svg,copy);")!=1:
        raise ValueError("V43 post-condition failed")
    encoded=json.dumps(page,ensure_ascii=False,separators=(",",":"))
    encoded=re.sub(r'</script',r'<\/script',encoded,flags=re.I)
    result=source[:start]+encoded+source[start+consumed:]
    if result[:start]!=source[:start] or result[start+len(encoded):]!=source[start+consumed:]:
        raise ValueError("Unexpected change outside embedded Scribe")
    return result

def main():
    if len(sys.argv)!=3:raise SystemExit("Usage: patch_v43_ink_pdf_paint_pagination.py IN.html OUT.html")
    inp=Path(sys.argv[1]);dest=Path(sys.argv[2])
    dest.write_text(patch(inp.read_text(encoding='utf-8')),encoding='utf-8')
    print("V43 Ink Pot A4: standalone SVG paint embedded; long ceremony pagination guarded")

if __name__=="__main__":main()
