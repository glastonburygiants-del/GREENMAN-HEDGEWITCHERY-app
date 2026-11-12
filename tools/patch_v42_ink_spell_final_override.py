#!/usr/bin/env python3
"""V42: restore the Ink Pot's Print Spell tab after a late compatibility override.
Touch only the JSON-embedded Scribe HTML. No native, key, storage or data changes.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ANCHORS=("function __gmLazyScribeSrc(){return ","PAGES.scribe = ")
OLD="""      if(key==='print') renderInkPrintRoom();
      if(key==='books') renderInkScribePrint();
    };"""
NEW="""      if(key==='print') renderInkPrintRoom();
      if(key==='books') renderInkScribePrint();
      if(key==='symbols' && typeof renderInkSpellPrint==='function') renderInkSpellPrint();
    };"""
MARK="GM_INK_PRINT_SPELL_FINAL_OVERRIDE_V42"

def patch(source: str) -> str:
    found=[a for a in ANCHORS if source.count(a)]
    if len(found)!=1 or source.count(found[0])!=1:
        raise ValueError("Expected one JSON-embedded Scribe page")
    start=source.index(found[0])+len(found[0])
    page,consumed=json.JSONDecoder().raw_decode(source[start:])
    if not isinstance(page,str):raise ValueError("Scribe must be a string")
    if MARK in page:raise ValueError("V42 already applied")
    if page.count("gmInkSetTab=function(name){")!=1:
        raise ValueError("Expected exactly one late Ink Pot tab override")
    if page.count(OLD)!=1:raise ValueError("Late Ink Pot override differs from known safe version")
    if page.count("function renderInkSpellPrint(){")!=1:
        raise ValueError("Required spell catalog renderer missing")
    if "GM_BOS.spellCatalog()" not in page or "gmInkSpellList" not in page:
        raise ValueError("Spell catalog/list unavailable")
    # Existing handler keeps Bound Book / Scribe Copies behaviour.
    page=page.replace(OLD,NEW+"/* "+MARK+" */",1)
    if page.count(MARK)!=1 or page.count(NEW)!=1:
        raise ValueError("V42 did not make exactly one change")
    encoded=json.dumps(page,ensure_ascii=False,separators=(",",":"))
    encoded=re.sub(r"</script",r"<\/script",encoded,flags=re.I)
    out=source[:start]+encoded+source[start+consumed:]
    if out[:start]!=source[:start] or out[start+len(encoded):]!=source[start+consumed:]:
        raise ValueError("Outer application changed")
    return out

def main():
    if len(sys.argv)!=3:
        raise SystemExit("Usage: patch_v42_ink_spell_final_override.py INPUT.html OUTPUT.html")
    src=Path(sys.argv[1])
    Path(sys.argv[2]).write_text(patch(src.read_text(encoding="utf-8")),encoding="utf-8")
    print("V42 Ink Pot: final tab override now refreshes Print Spell without modifying Bound Book or Scribe Copies")

if __name__=="__main__":
    main()
