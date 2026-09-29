#!/usr/bin/env python3
from __future__ import annotations
import base64
import re
import sys
from pathlib import Path

MARKER = "GM_SCRIBE_NON_OGHAM_RENDER_GUARD_FV35"
DESK_RE = re.compile(r'const DESK_B64=\\\"([A-Za-z0-9+/=]+)\\\"')

OLD_FUNCTION_START = 'function updatePrintReserve(){'
OLD_FUNCTION_END = '\n\n\n/* FV3 SCRIBE RESTORE: direct writing hands only. */'

OLD_RENDER_BLOCK = '''  output.innerHTML="";selectedGlyphs.clear();
  if(sid!=="Ogham" && showEnglish && input.value.trim())printEnglishBlock.textContent=input.value.trim();else printEnglishBlock.textContent="";
  updatePrintReserve();'''

NEW_FUNCTION = r'''/* GM_SCRIBE_NON_OGHAM_RENDER_GUARD_FV35
   Print-reserve measurement must never be able to stop the live Scribe renderer.
   Android WebView may occasionally refuse a temporary 2D canvas context; when
   that happens use a conservative text-length estimate instead. */
function updatePrintReserve(){
  const root=document.getElementById("printRoot");
  if(!root)return;
  if(scriptSelect.value==="Ogham"){
    root.style.removeProperty("--english-reserve");
    return;
  }

  const value=(showEnglish && input.value.trim()) ? input.value.trim() : "";
  if(printEnglishBlock)printEnglishBlock.textContent=value;

  if(!value){
    root.style.setProperty("--english-reserve","8mm");
    return;
  }

  let lines=0;
  try{
    const canvas=updatePrintReserve.canvas||(updatePrintReserve.canvas=document.createElement("canvas"));
    const ctx=(canvas&&typeof canvas.getContext==="function")?canvas.getContext("2d"):null;
    if(!ctx||typeof ctx.measureText!=="function")throw new Error("2D text measurement unavailable");
    ctx.font='17.333px Georgia, "Times New Roman", serif';
    const maxPx=194/25.4*96;

    value.split(/\n/).forEach(raw=>{
      if(raw===""){lines++;return}
      const words=raw.split(/\s+/);
      let width=0;
      let lineStarted=false;
      words.forEach(word=>{
        const ww=ctx.measureText((lineStarted?" ":"")+word).width;
        if(lineStarted && width+ww>maxPx){
          lines++;
          width=ctx.measureText(word).width;
        }else{
          width+=ww;
        }
        lineStarted=true;
      });
      lines++;
    });
  }catch(_gmScribeReserveError){
    /* This estimate is deliberately conservative. It affects only the amount
       of A4 space reserved for the optional English block, never the script. */
    lines=0;
    value.split(/\n/).forEach(raw=>{
      lines+=Math.max(1,Math.ceil(Math.max(1,raw.length)/76));
    });
  }

  const lineMm=13*0.352778*1.35;
  const blockMm=Math.min(90,Math.max(14,lines*lineMm+4));
  root.style.setProperty("--english-reserve",(blockMm+10)+"mm");
}'''

NEW_RENDER_BLOCK = r'''  output.innerHTML="";selectedGlyphs.clear();
  /* Screen glyph rendering is independent of A4 English-reserve sizing. */
  try{
    if(printEnglishBlock){
      if(sid!=="Ogham" && showEnglish && input.value.trim())printEnglishBlock.textContent=input.value.trim();else printEnglishBlock.textContent="";
    }
    updatePrintReserve();
  }catch(_gmScribeReserveRenderError){
    /* Never leave a selected non-Ogham hand with a blank parchment merely
       because print-only reserve measurement failed. */
  }'''


def patch_desk(desk: str) -> str:
    if MARKER in desk:
        raise SystemExit(f"{MARKER} already present; refusing duplicate patch")
    if desk.count(OLD_FUNCTION_START) != 1:
        raise SystemExit(f"expected exactly one updatePrintReserve(), found {desk.count(OLD_FUNCTION_START)}")
    start = desk.index(OLD_FUNCTION_START)
    end = desk.find(OLD_FUNCTION_END, start)
    if end < 0:
        raise SystemExit("updatePrintReserve end anchor not found")
    old_fn = desk[start:end]
    for required in (
        'const canvas=updatePrintReserve.canvas',
        'const ctx=canvas.getContext("2d")',
        'ctx.measureText',
        'root.style.setProperty("--english-reserve"',
    ):
        if required not in old_fn:
            raise SystemExit(f"unexpected updatePrintReserve body; missing {required!r}")
    desk = desk[:start] + NEW_FUNCTION + desk[end:]

    if desk.count(OLD_RENDER_BLOCK) != 1:
        raise SystemExit(f"expected exactly one render reserve block, found {desk.count(OLD_RENDER_BLOCK)}")
    desk = desk.replace(OLD_RENDER_BLOCK, NEW_RENDER_BLOCK, 1)

    if MARKER not in desk:
        raise SystemExit("marker missing after patch")
    if 'if(!ctx||typeof ctx.measureText!=="function")' not in desk:
        raise SystemExit("2D canvas fallback guard missing")
    if 'catch(_gmScribeReserveRenderError)' not in desk:
        raise SystemExit("render isolation guard missing")
    return desk


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} INPUT.html OUTPUT.html")
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    app = src.read_text(encoding="utf-8")
    matches = list(DESK_RE.finditer(app))
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one escaped DESK_B64 payload, found {len(matches)}")
    m = matches[0]
    desk = base64.b64decode(m.group(1), validate=True).decode("utf-8")
    patched = patch_desk(desk)
    b64 = base64.b64encode(patched.encode("utf-8")).decode("ascii")
    out = app[:m.start(1)] + b64 + app[m.end(1):]
    dst.write_text(out, encoding="utf-8")

    check = dst.read_text(encoding="utf-8")
    mm = DESK_RE.search(check)
    if not mm:
        raise SystemExit("DESK_B64 missing after write")
    desk_check = base64.b64decode(mm.group(1), validate=True).decode("utf-8")
    assert MARKER in desk_check
    assert desk_check.count('function updatePrintReserve(){') == 1
    assert desk_check.count('function render(){') == 1
    print(f"Scribe non-Ogham guard applied: {src.name} -> {dst.name}")


if __name__ == "__main__":
    main()
