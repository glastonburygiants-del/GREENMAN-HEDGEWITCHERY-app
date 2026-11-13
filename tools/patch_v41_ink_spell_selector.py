#!/usr/bin/env python3
"""V41: Restore Print Spell selection when the late Ink Pot tab handler overrides V37.
Scribe JSON payload only. No storage, Android identity, signing or permissions changed.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ANCHORS=("function __gmLazyScribeSrc(){return ","PAGES.scribe = ")
LATE="if(key==='print')renderInkPrintRoom();if(key==='books'){renderInkScribePrint();renderBosConversion()}}"
FIXED="if(key==='print')renderInkPrintRoom();if(key==='books'){renderInkScribePrint();renderBosConversion()}if(key==='symbols'&&typeof renderInkSpellPrint==='function')renderInkSpellPrint()}"
MARKER="GM_INK_SPELL_SELECTOR_RESTORE_V41"

def patch(source:str)->str:
    anchors=[a for a in ANCHORS if source.count(a)]
    if len(anchors)!=1 or source.count(anchors[0])!=1:
        raise ValueError("Expected exactly one JSON-embedded Scribe document")
    pos=source.index(anchors[0])+len(anchors[0])
    scribe,end=json.JSONDecoder().raw_decode(source[pos:])
    if not isinstance(scribe,str):
        raise ValueError("Expected Scribe document string")
    if MARKER in scribe:
        raise ValueError("V41 already applied, refusing duplicate patch")
    if scribe.count("function gmInkSetTab(")!=2:
        raise ValueError("Expected original and overriding Ink Pot tab handler")
    if scribe.count(LATE)!=1:
        raise ValueError("Late Ink Pot tab handler has changed")
    if scribe.count("function renderInkSpellPrint(){")!=1:
        raise ValueError("Print Spell list renderer not found uniquely")
    if "GM_BOS.spellCatalog()" not in scribe or "gmInkSpellList" not in scribe:
        raise ValueError("Print Spell catalog or destination missing")
    # The first function already handles the symbols tab correctly. The final
    # definition shadows it, preventing radio options from ever being rendered.
    scribe=scribe.replace(LATE,FIXED+"/* "+MARKER+" */",1)
    if scribe.count(MARKER)!=1 or scribe.count(FIXED)!=1:
        raise ValueError("Print Spell handler correction not unique")
    encoded=json.dumps(scribe,ensure_ascii=False,separators=(",",":"))
    encoded=re.sub(r"</script",r"<\/script",encoded,flags=re.I)
    output=source[:pos]+encoded+source[pos+end:]
    if output[:pos]!=source[:pos] or output[pos+len(encoded):]!=source[pos+end:]:
        raise ValueError("Outer app modified unexpectedly")
    return output

if __name__=="__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: patch_v41_ink_spell_selector.py INPUT.html OUTPUT.html")
    src=Path(sys.argv[1]); out=Path(sys.argv[2])
    out.write_text(patch(src.read_text(encoding="utf-8")),encoding="utf-8")
    print("V41: Print Spell tab now refreshes gathered spell list; no saved data changed")
