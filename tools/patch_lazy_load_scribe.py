#!/usr/bin/env python3
"""Defer Scribe's large payload until first navigation and apply two narrow
real-device tablet performance fixes before it is wrapped lazily.

1. Ogham Treehouse wheel: during the physical spin, stop repainting twenty
   live stave drop-shadows and twenty spoke shadows on every 18 degree click.
   The full carved artwork and selected-stave glow return when the wheel stops.
   One parent parity attribute replaces forty spoke class mutations.
2. BoS binding: only Ritual Tools and Reference Index pages use a slightly
   lighter A4 raster scale. The live BoS remains untouched. Reference Index
   dotted row rules become equivalent solid hairlines only in the flattened
   copy, reducing html2canvas work on the text-dense end pages.

The existing lazy-Scribe behaviour is preserved: the finished Scribe string is
wrapped in __gmLazyScribeSrc() and cached by the PAGES.scribe getter.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MARKER = "GM_FV3_TABLET_PERF_OGHAM_BOS_V1"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


def decode_json_value(text: str, marker: str, label: str) -> tuple[str, int, int]:
    pos = text.find(marker)
    if pos < 0:
        raise SystemExit(f"{label}: marker not found: {marker}")
    if text.find(marker, pos + 1) != -1:
        raise SystemExit(f"{label}: marker is not unique: {marker}")
    start = pos + len(marker)
    value, used = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(value, str):
        raise SystemExit(f"{label}: expected JSON string, got {type(value).__name__}")
    return value, start, start + used


def js_string_literal(value: str) -> str:
    # A raw </script> inside a JavaScript string still terminates the containing
    # HTML script element. JSON permits escaped '/', so preserve browser-safe
    # inline-script encoding when rebuilding giant page strings.
    literal = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return re.sub(r"</script", r"<\\/script", literal, flags=re.IGNORECASE)


def replace_json_value(text: str, marker: str, value: str, label: str) -> str:
    _, start, end = decode_json_value(text, marker, label)
    return text[:start] + js_string_literal(value) + text[end:]


def patch_treehouse(tree: str) -> str:
    if MARKER in tree:
        raise SystemExit("Treehouse performance patch is already present")

    perf_css = r'''
<style id="gm-fv3-tablet-performance-v1">
/* GM_FV3_TABLET_PERF_OGHAM_BOS_V1
   Tablet wheel: keep the carved artwork, but do not repaint twenty live
   drop-shadows and spoke shadows while the rigid wheel is moving. */
#wheelStation.threadMoving .wheelStave{filter:none!important;transition:none!important}
#wheelStation.threadMoving .spoke{filter:none!important;opacity:1!important;box-shadow:none!important;transition:none!important}
#wheel[data-step-parity="0"] .spoke[data-parity="0"],
#wheel[data-step-parity="1"] .spoke[data-parity="1"]{filter:brightness(1.14);opacity:1}
#wheel[data-step-parity="0"] .spoke[data-parity="1"],
#wheel[data-step-parity="1"] .spoke[data-parity="0"]{filter:brightness(.86);opacity:.92}
</style>
'''
    tree = replace_once(tree, "</head>", perf_css + "</head>", "Treehouse performance CSS")

    old_mount = "const spoke=document.createElement('span'); spoke.className='spoke'; spoke.style.transform=`rotate(${a-90}deg)`; wheel.appendChild(spoke); wheelSpokes.push(spoke);"
    new_mount = "const spoke=document.createElement('span'); spoke.className='spoke'; spoke.dataset.parity=String(i&1); spoke.style.transform=`rotate(${a-90}deg)`; wheel.appendChild(spoke); wheelSpokes.push(spoke);"
    tree = replace_once(tree, old_mount, new_mount, "Treehouse spoke parity")

    old_shade = r'''function shadeWheelStep(stepNo){
  wheelPairs.forEach((pair,i)=>{
    pair.spoke.classList.toggle('stepLight',((i+stepNo)&1)===0);
    pair.spoke.classList.toggle('stepDark',((i+stepNo)&1)===1);
  });
}'''
    new_shade = r'''function shadeWheelStep(stepNo){
  /* One parent attribute replaces forty child class mutations. */
  wheel.dataset.stepParity=String(stepNo&1);
}'''
    tree = replace_once(tree, old_shade, new_shade, "Treehouse spoke shading")

    # Keep the stopper flick on every physical click, but do not alter child
    # spoke paint on every step. The final selected step still sets the shade.
    step_pattern = "    setWheelAngle(stepNo*18);\n    shadeWheelStep(stepNo);\n    flapOnce(false,delay);"
    count = tree.count(step_pattern)
    if count != 2:
        raise SystemExit(f"Treehouse spin loop: expected 2 step patterns, found {count}")
    tree = tree.replace(step_pattern, "    setWheelAngle(stepNo*18);\n    flapOnce(false,delay);", 2)

    if tree.count(MARKER) != 1:
        raise SystemExit("Treehouse performance marker is missing or duplicated")
    if "classList.toggle('stepLight'" in tree or "classList.toggle('stepDark'" in tree:
        raise SystemExit("Old per-spoke class toggling survived")
    return tree


def patch_bower(bower: str) -> str:
    tree, _, _ = decode_json_value(bower, "frame.srcdoc=", "Ogham Treehouse srcdoc")
    return replace_json_value(bower, "frame.srcdoc=", patch_treehouse(tree), "Ogham Treehouse srcdoc")


def patch_scribe(scribe: str) -> str:
    if MARKER in scribe:
        raise SystemExit("Scribe performance patch is already present")

    old_scale = "const scale=1.5,minimumWidth=Math.floor(794*scale)-2,minimumHeight=Math.floor(1123*scale)-2;phase=Date.now();const canvas=await window.html2canvas(sheet,{backgroundColor:'#f4ecd8',width:794,height:1123,scale:scale,"
    new_scale = "/* GM_FV3_TABLET_PERF_OGHAM_BOS_V1: keep full A4 content; lighten only text-heavy end-page raster work. */const captureChapter=String(sheet&&sheet.dataset&&sheet.dataset.chapter||''),scale=captureChapter==='index'?1.35:(captureChapter==='tools'?1.40:1.5),minimumWidth=Math.floor(794*scale)-2,minimumHeight=Math.floor(1123*scale)-2;phase=Date.now();const canvas=await window.html2canvas(sheet,{backgroundColor:'#f4ecd8',width:794,height:1123,scale:scale,"
    scribe = replace_once(scribe, old_scale, new_scale, "BoS targeted capture scale")

    old_map = " if(printMap)gmBosApplyPrintMap(page,clone,printMap);\n const stage=document.createElement('div');"
    new_map = " if(printMap)gmBosApplyPrintMap(page,clone,printMap);\n if(clone.dataset.chapter==='index'){const perf=document.createElement('style');perf.setAttribute('data-gm-bind-perf','reference-index');perf.textContent='.gmBosIndexRow{border-bottom:.22mm solid rgba(185,163,126,.66)!important}.gmBosIndexRows{contain:layout style!important}';clone.append(perf)}\n const stage=document.createElement('div');"
    scribe = replace_once(scribe, old_map, new_map, "BoS reference-index print simplification")

    old_diag = "jpegMs:jpegMs,jpegMethod:encoded&&encoded.method||'unknown',reusedCaptureFrame:!!binding,durationMs:Date.now()-captureStarted"
    new_diag = "jpegMs:jpegMs,jpegMethod:encoded&&encoded.method||'unknown',captureScale:scale,captureChapter:captureChapter,reusedCaptureFrame:!!binding,durationMs:Date.now()-captureStarted"
    scribe = replace_once(scribe, old_diag, new_diag, "BoS capture diagnostics")

    if scribe.count(MARKER) != 1:
        raise SystemExit("Scribe performance marker is missing or duplicated")
    if "captureChapter==='index'?1.35:(captureChapter==='tools'?1.40:1.5)" not in scribe:
        raise SystemExit("Targeted BoS scale rule missing")
    if "data-gm-bind-perf','reference-index'" not in scribe:
        raise SystemExit("Reference Index flattened-copy simplification missing")
    return scribe


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_lazy_load_scribe.py INPUT OUTPUT")

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    text = src.read_text(encoding="utf-8")

    if "function __gmLazyScribeSrc(){return " in text:
        raise SystemExit("Scribe is already lazy-loaded; expected eager reconstruction input")

    # Patch only the Bower's embedded Treehouse source.
    bower, _, _ = decode_json_value(text, "PAGES.bower = ", "Bower page")
    bower_patched = patch_bower(bower)
    text = replace_json_value(text, "PAGES.bower = ", bower_patched, "Bower page")

    # Patch Scribe while it is still in the eager assignment form, then wrap
    # the completed string with the same one-shot lazy getter used previously.
    scribe, scribe_start, scribe_end = decode_json_value(text, "PAGES.scribe = ", "Scribe page")
    scribe_patched = patch_scribe(scribe)
    literal = js_string_literal(scribe_patched)

    assignment_start = text.rfind("PAGES.scribe = ", 0, scribe_start)
    if assignment_start < 0:
        raise SystemExit("PAGES.scribe assignment start not found")
    statement_end = scribe_end
    if statement_end >= len(text) or text[statement_end] != ';':
        raise SystemExit('PAGES.scribe string literal not followed by ";" as expected')
    statement_end += 1

    replacement = (
        'function __gmLazyScribeSrc(){return ' + literal + ';}\n'
        'Object.defineProperty(PAGES,"scribe",{configurable:true,enumerable:true,'
        'get:function(){var v=__gmLazyScribeSrc();'
        'Object.defineProperty(PAGES,"scribe",{value:v,configurable:true,writable:true,enumerable:true});'
        'return v;}});'
    )
    patched = text[:assignment_start] + replacement + text[statement_end:]

    if "PAGES.scribe = " in patched:
        raise SystemExit("direct PAGES.scribe assignment survived")
    if patched.count("__gmLazyScribeSrc") != 2:
        raise SystemExit("expected exactly 2 occurrences of __gmLazyScribeSrc (definition + call)")
    if patched.count(MARKER) != 2:
        raise SystemExit(f"expected 2 tablet-performance markers in final app, found {patched.count(MARKER)}")
    if "#wheelStation.threadMoving .wheelStave{filter:none!important" not in patched:
        raise SystemExit("Treehouse shadow suppression missing from final app")
    if "captureScale:scale,captureChapter:captureChapter" not in patched:
        raise SystemExit("BoS performance diagnostics missing from final app")

    out.write_text(patched, encoding="utf-8")
    print("PAGES.scribe deferred: parsed/constructed on first navigation to Scribe, not at app startup")
    print("Ogham wheel tablet path: live child shadows suppressed only while spinning; stopper/winch unchanged")
    print("BoS tablet bind path: Ritual Tools 1.40x; Reference Index 1.35x; live BoS unchanged")


if __name__ == "__main__":
    main()
