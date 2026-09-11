#!/usr/bin/env python3
"""Keep the successful Ogham Treehouse tablet optimisation while restoring
Scribe/BoS binding byte-for-byte to the proven lazy-load baseline.

Real tablet testing of the previous combined patch showed the wheel became much
smoother, but the BoS binding path regressed badly. This patch therefore:

1. keeps only the Treehouse wheel paint optimisation;
2. does not alter Scribe's capture scale, index styles, binding DOM or logging;
3. wraps the original eager PAGES.scribe string literal byte-for-byte with the
   same lazy getter used by the successful baseline build.

That means the BoS binder is exactly the baseline binder again, while the Ogham
wheel improvement remains.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MARKER = "GM_FV3_TABLET_PERF_OGHAM_ONLY_V2"


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


def lazy_wrap_scribe_exact(text: str) -> str:
    """Wrap the existing Scribe literal without decoding or re-encoding it."""
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

    literal = text[quote_start:quote_end]
    statement_end = quote_end + 1
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
        raise SystemExit('original Scribe string literal was not preserved byte-for-byte')
    return patched


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_lazy_load_scribe.py INPUT OUTPUT")

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    text = src.read_text(encoding="utf-8")

    if "function __gmLazyScribeSrc(){return " in text:
        raise SystemExit("Scribe is already lazy-loaded; expected eager reconstruction input")

    # Keep only the proven wheel optimisation in Bower/Treehouse.
    bower, _, _ = decode_json_value(text, "PAGES.bower = ", "Bower page")
    text = replace_json_value(text, "PAGES.bower = ", patch_bower(bower), "Bower page")

    # Do not touch Scribe content at all. Preserve its exact original literal.
    patched = lazy_wrap_scribe_exact(text)

    if patched.count(MARKER) != 1:
        raise SystemExit(f"expected exactly one Ogham marker, found {patched.count(MARKER)}")
    if "captureChapter==='index'?1.35" in patched or "data-gm-bind-perf" in patched:
        raise SystemExit("regressed BoS bind optimisation survived unexpectedly")
    if "#wheelStation.threadMoving .wheelStave{filter:none!important" not in patched:
        raise SystemExit("Treehouse shadow suppression missing from final app")

    out.write_text(patched, encoding="utf-8")
    print("PAGES.scribe deferred with its original string literal preserved byte-for-byte")
    print("Ogham wheel tablet optimisation kept")
    print("BoS binding restored exactly to the successful pre-wheel baseline")


if __name__ == "__main__":
    main()
