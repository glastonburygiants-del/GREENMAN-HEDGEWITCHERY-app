#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


OLD_PRINT_CALL = """  try{f.contentWindow.focus();f.contentWindow.print();}finally{setTimeout(function(){f.remove();},1800);}"""

NEW_PRINT_CALL = """  var liteHtml='<!doctype html>'+d.documentElement.outerHTML;
  var liteTitle=d.title||((spell||'Greenman Spell')+' Lite Pack');
  if(d.querySelectorAll('.sheet').length!==3){
   try{f.remove();}catch(_e){}
   alert('The Lite Pack did not finish preparing. Please try again.');
   return;
  }
  if(window.GreenmanAndroid&&typeof window.GreenmanAndroid.printHtml==='function'){
   window.__GM_LITE_PRINT_NATIVE_WIRED__=1;
   window.GreenmanAndroid.printHtml(liteHtml,liteTitle);
   setTimeout(function(){try{f.remove();}catch(_e){}},1200);
  }else{
   try{f.contentWindow.focus();f.contentWindow.print();}finally{setTimeout(function(){f.remove();},1800);}
  }"""


def patch_spellbuilder(page: str) -> str:
    count = page.count(OLD_PRINT_CALL)
    if count != 1:
        raise SystemExit(
            f"Lite print handoff: expected exactly 1 old iframe print call, found {count}"
        )

    page = page.replace(OLD_PRINT_CALL, NEW_PRINT_CALL, 1)

    required = [
        "PRINT LITE PACK",
        "gm-v79-lite-pack",
        "function printLiteThree()",
        "window.GreenmanAndroid.printHtml(liteHtml,liteTitle)",
        "window.__GM_LITE_PRINT_NATIVE_WIRED__=1",
    ]
    missing = [item for item in required if item not in page]
    if missing:
        raise SystemExit("Lite print wiring missing: " + ", ".join(missing))

    if page.count("PRINT LITE PACK") != 1:
        raise SystemExit("Lite Summary button count changed")

    return page


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "Usage: patch_lite_print_android.py INPUT.html OUTPUT.html"
        )

    src, dst = map(Path, sys.argv[1:])
    text = src.read_text(encoding="utf-8")
    marker = "const PAGES = "
    start = text.index(marker) + len(marker)
    pages, used = json.JSONDecoder().raw_decode(text[start:])
    end = start + used

    pages["spellBuilder"] = patch_spellbuilder(pages["spellBuilder"])

    encoded = json.dumps(pages, ensure_ascii=False, separators=(",", ":"))
    encoded = re.sub(r"</script", r"<\\/script", encoded, flags=re.IGNORECASE)
    dst.write_text(text[:start] + encoded + text[end:], encoding="utf-8")

    print(
        "Lite print wiring passed: existing three-page pack now uses the Android PDF bridge; "
        "Lite Summary controls retained."
    )


if __name__ == "__main__":
    main()
