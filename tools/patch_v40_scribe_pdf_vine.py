#!/usr/bin/env python3
"""V40: repair native Ink Pot vine strokes and provide offline Scribe A4 PDF.
Only the JSON-embedded Scribe HTML and its already-embedded Desk HTML change.
No new Android components, permissions, signing identity, or storage keys.
"""
from __future__ import annotations
import base64
import json
import re
import sys
from pathlib import Path

ANCHORS=("function __gmLazyScribeSrc(){return ", "PAGES.scribe = ")
STYLE_ID="gm-bos-vine-pdf-v40"
SCRIPT_ID="gm-scribe-a4-pdf-v40"
DESK_PATTERN=r'const DESK_B64="([A-Za-z0-9+/=]+)"'
OLD_DESK_CLICK='document.getElementById("printBtn").onclick=()=>{render();updatePrintReserve();requestAnimationFrame(()=>window.print())};'
NEW_DESK_CLICK=('document.getElementById("printBtn").onclick=()=>{render();updatePrintReserve();'
                'try{const save=window.parent&&window.parent.gmScribeExportA4Pdf;'
                'if(typeof save==="function"){Promise.resolve(save()).catch(e=>console.error("A4 PDF",e));return}}catch(e){}'
                'requestAnimationFrame(()=>window.print())};')
OLD_SAVED='requestAnimationFrame(()=>requestAnimationFrame(()=>{try{window.print()}catch(e){restore();throw e}}));'
NEW_SAVED=('requestAnimationFrame(()=>requestAnimationFrame(()=>{try{'
           'const save=window.parent&&window.parent.gmScribeExportA4Pdf;'
           'if(typeof save==="function")Promise.resolve(save()).finally(restore);'
           'else window.print()}catch(e){restore();throw e}}));')

def exactly(source:str,marker:str,n:int=1)->None:
    found=source.count(marker)
    if found!=n:raise ValueError(f"Expected {n} of {marker[:70]!r}, found {found}")

def patch(source:str,css:str,js:str)->str:
    active=[x for x in ANCHORS if x in source]
    if len(active)!=1:raise ValueError(f"Missing/duplicate Scribe anchor: {active}")
    exactly(source,active[0])
    start=source.index(active[0])+len(active[0])
    doc,consumed=json.JSONDecoder().raw_decode(source[start:])
    if not isinstance(doc,str):raise ValueError("Scribe was not embedded as JSON text")
    if STYLE_ID in doc or SCRIPT_ID in doc:raise ValueError("V40 patch already applied")
    if '<script' in css.lower() or '@import' in css.lower() or 'url(' in css.lower():
        raise ValueError("Vine CSS cannot load remote resources")
    if 'gmScribeExportA4Pdf' not in js or 'gmScribeV40ImagePdf' not in js:
        raise ValueError("A4 export hook missing")
    first_head=doc.find("</head>")
    first_body=doc.find("<body")
    if first_head<0 or first_body<0 or first_head>=first_body:
        raise ValueError("Could not locate Scribe outer document header")
    exactly(doc,"function gmBosRasterStyles(){")
    exactly(doc,"const DESK_B64=")
    if "gmBosPrintSheet" not in doc or "gmStoryVine" not in doc:
        raise ValueError("Required A4 page or vine artwork missing")
    if not re.search(DESK_PATTERN,doc):raise ValueError("Desk base64 not present")
    m=re.search(DESK_PATTERN,doc)
    desk=base64.b64decode(m.group(1)).decode("utf-8")
    exactly(desk,OLD_DESK_CLICK)
    exactly(desk,OLD_SAVED)
    desk=desk.replace(OLD_DESK_CLICK,NEW_DESK_CLICK,1).replace(OLD_SAVED,NEW_SAVED,1)
    encoded_desk=base64.b64encode(desk.encode("utf-8")).decode("ascii")
    doc=doc[:m.start(1)]+encoded_desk+doc[m.end(1):]
    style='<style id="'+STYLE_ID+'">'+css.strip()+'</style>'
    doc=doc.replace("</head>",style+"</head>",1)
    script="/* "+SCRIPT_ID+" */\n"+js.strip()+"\n"
    doc=doc.replace("function gmBosRasterStyles(){",script+"function gmBosRasterStyles(){",1)
    exactly(doc,STYLE_ID)
    exactly(doc,SCRIPT_ID)
    exactly(doc,"function gmScribeExportA4Pdf(){")
    encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':'))
    encoded=re.sub(r'</script',r'<\/script',encoded,flags=re.I)
    output=source[:start]+encoded+source[start+consumed:]
    if output[:start]!=source[:start] or output[start+len(encoded):]!=source[start+consumed:]:
        raise ValueError("Outer application changed beyond embedded Scribe HTML")
    return output

def main():
    if len(sys.argv)!=3:raise SystemExit("Usage: patch_v40_scribe_pdf_vine.py INPUT.html OUTPUT.html")
    source=Path(sys.argv[1]),target=Path(sys.argv[2])
    css=Path(__file__).with_name('bos_vine_pdf_v40.css').read_text(encoding='utf-8')
    js=Path(__file__).with_name('bos_scribe_a4_v40.js').read_text(encoding='utf-8')
    result=patch(source.read_text(encoding='utf-8'),css,js)
    target.write_text(result,encoding='utf-8')
    print("V40 installed: Scribe A4 PDF via existing Downloads bridge; print-only vine stroke fix.")

if __name__=='__main__':
    main()
