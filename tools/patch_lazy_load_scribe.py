#!/usr/bin/env python3
"""Keep the proven Greenman tablet performance path and apply two tiny BoS
presentation fixes without changing the binder's rendering/timing behaviour.

Kept:
- lazy Scribe loading;
- Ogham Treehouse wheel paint optimisation;
- exact baseline BoS capture scale/html2canvas/storage path.

Changed only:
1. hide the bind Cancel button after a successful completed bind, while restoring
   it when a new bind begins;
2. remove checkbox inputs from the already-cloned print page before rasterising,
   so live Contents remains selectable but bound A4 Contents pages print cleanly.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MARKER = "GM_FV3_TABLET_PERF_OGHAM_ONLY_V2"
UI_MARKER = "GM_FV3_BIND_UI_CLEANUP_V2"


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
    literal = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return re.sub(r"</script", r"<\\/script", literal, flags=re.IGNORECASE)


def replace_json_value(text: str, marker: str, value: str, label: str) -> str:
    _, start, end = decode_json_value(text, marker, label)
    return text[:start] + js_string_literal(value) + text[end:]


def patch_treehouse(tree: str) -> str:
    if MARKER in tree:
        raise SystemExit("Treehouse performance patch is already present")

    perf_css = r'''
<style id="gm-fv3-tablet-performance-v2">
/* GM_FV3_TABLET_PERF_OGHAM_ONLY_V2
   Keep the carved wheel, but do not repaint twenty live stave drop-shadows
   and spoke shadows while the rigid wheel is physically moving. */
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


def find_scribe_literal(text: str) -> tuple[int, int, int, int]:
    marker = 'PAGES.scribe = "'
    start = text.find(marker)
    if start < 0:
        raise SystemExit('PAGES.scribe = "..." assignment not found')
    if text.find(marker, start + 1) != -1:
        raise SystemExit('PAGES.scribe = "..." assignment anchor is not unique')

    quote_start = start + len(marker) - 1
    i = quote_start + 1
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            break
        i += 1
    if i >= n:
        raise SystemExit('unterminated PAGES.scribe string literal')

    quote_end = i + 1
    if quote_end >= len(text) or text[quote_end] != ';':
        raise SystemExit('PAGES.scribe string literal not followed by ";" as expected')
    return start, quote_start, quote_end, quote_end + 1


def raw_json_fragment(value: str) -> str:
    """Encode only the inside of a JSON string, preserving the rest verbatim."""
    return json.dumps(value, ensure_ascii=False)[1:-1]


def patch_raw_scribe_literal(text: str) -> str:
    """Replace three unique escaped fragments inside PAGES.scribe only.

    This avoids decoding/re-encoding the 15MB Scribe payload. Every byte other
    than the three deliberately changed fragments remains exactly as rebuilt.
    """
    start, quote_start, quote_end, _ = find_scribe_literal(text)
    literal = text[quote_start:quote_end]
    if UI_MARKER in literal:
        raise SystemExit("BoS UI cleanup is already present")

    replacements = [
        (
            "if(cancelBtn){cancelBtn.disabled=false;cancelBtn.textContent='Cancel'}",
            "if(cancelBtn){cancelBtn.style.display='';cancelBtn.disabled=false;cancelBtn.textContent='Cancel'}",
            "new-bind Cancel reset",
        ),
        (
            "lsSet(SKEYS.boundCatalog,JSON.stringify(result));title.textContent='Book of Shadows Bound';summary.innerHTML='<strong>'+result.pages.length+' A4 pages completed</strong>The bound book is ready in the Ink Pot.';gmBosNotifyShell('complete',{done:result.pages.length,total:result.pages.length,state:'ready',nativeSaved:!!result.nativeSaved});return",
            "if(cancelBtn)cancelBtn.style.display='none';lsSet(SKEYS.boundCatalog,JSON.stringify(result));title.textContent='Book of Shadows Bound';summary.innerHTML='<strong>'+result.pages.length+' A4 pages completed</strong>The bound book is ready in the Ink Pot.';gmBosNotifyShell('complete',{done:result.pages.length,total:result.pages.length,state:'ready',nativeSaved:!!result.nativeSaved});return",
            "completed-bind Cancel hide",
        ),
        (
            "qa('input',root).forEach(i=>{i.setAttribute('readonly','readonly');if(i.type!=='checkbox'&&i.type!=='radio')i.setAttribute('value',i.value||'')});",
            "/* "+UI_MARKER+" */qa('input',root).forEach(i=>{if(i.type==='checkbox'){i.remove();return}i.setAttribute('readonly','readonly');if(i.type!=='radio')i.setAttribute('value',i.value||'')});",
            "print-clone checkbox removal",
        ),
    ]

    for old_decoded, new_decoded, label in replacements:
        old = raw_json_fragment(old_decoded)
        new = raw_json_fragment(new_decoded)
        count = literal.count(old)
        if count != 1:
            raise SystemExit(f"{label}: expected 1 escaped Scribe match, found {count}")
        literal = literal.replace(old, new, 1)

    # Validate that the edited raw literal still decodes to the intended Scribe.
    try:
        decoded = json.loads(literal)
    except Exception as exc:
        raise SystemExit(f"edited PAGES.scribe literal is invalid: {exc}") from exc

    checks = (
        "cancelBtn.style.display='';cancelBtn.disabled=false",
        "if(cancelBtn)cancelBtn.style.display='none';lsSet(SKEYS.boundCatalog",
        UI_MARKER,
        "if(i.type==='checkbox'){i.remove();return}",
    )
    for token in checks:
        if token not in decoded:
            raise SystemExit(f"missing BoS UI cleanup token after validation: {token}")

    return text[:quote_start] + literal + text[quote_end:]


def lazy_wrap_scribe_exact(text: str) -> str:
    """Wrap the patched Scribe literal without decoding/re-encoding it."""
    start, quote_start, quote_end, statement_end = find_scribe_literal(text)
    literal = text[quote_start:quote_end]
    replacement = (
        'function __gmLazyScribeSrc(){return ' + literal + ';}\n'
        'Object.defineProperty(PAGES,"scribe",{configurable:true,enumerable:true,'
        'get:function(){var v=__gmLazyScribeSrc();'
        'Object.defineProperty(PAGES,"scribe",{value:v,configurable:true,writable:true,enumerable:true});'
        'return v;}});'
    )
    patched = text[:start] + replacement + text[statement_end:]
    if 'PAGES.scribe = "' in patched:
        raise SystemExit('direct PAGES.scribe assignment survived')
    if patched.count('__gmLazyScribeSrc') != 2:
        raise SystemExit('expected exactly 2 occurrences of __gmLazyScribeSrc')
    if literal not in patched:
        raise SystemExit('patched Scribe literal was not preserved byte-for-byte')
    return patched


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_lazy_load_scribe.py INPUT OUTPUT")

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    text = src.read_text(encoding="utf-8")

    if "function __gmLazyScribeSrc(){return " in text:
        raise SystemExit("Scribe is already lazy-loaded; expected eager reconstruction input")

    # Proven wheel optimisation only.
    bower, _, _ = decode_json_value(text, "PAGES.bower = ", "Bower page")
    text = replace_json_value(text, "PAGES.bower = ", patch_bower(bower), "Bower page")

    # Three tiny presentation edits inside the raw Scribe literal. No binder
    # scaling, html2canvas, page-generation or storage code is changed.
    text = patch_raw_scribe_literal(text)
    patched = lazy_wrap_scribe_exact(text)

    if patched.count(MARKER) != 1:
        raise SystemExit(f"expected exactly one Ogham marker, found {patched.count(MARKER)}")
    if patched.count(UI_MARKER) != 1:
        raise SystemExit(f"expected exactly one BoS UI cleanup marker, found {patched.count(UI_MARKER)}")
    if "captureChapter==='index'?1.35" in patched or "data-gm-bind-perf" in patched:
        raise SystemExit("old regressed BoS performance patch survived unexpectedly")
    if "#wheelStation.threadMoving .wheelStave{filter:none!important" not in patched:
        raise SystemExit("Treehouse shadow suppression missing from final app")

    out.write_text(patched, encoding="utf-8")
    print("PAGES.scribe remains lazy with all untouched bytes preserved")
    print("Ogham wheel tablet optimisation kept")
    print("Completed-bind Cancel hides only after successful completion")
    print("Contents checkboxes removed from flattened print clone only")


if __name__ == "__main__":
    main()
