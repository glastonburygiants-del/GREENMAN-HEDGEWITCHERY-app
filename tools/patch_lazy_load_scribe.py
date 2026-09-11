#!/usr/bin/env python3
"""Keep the successful Ogham Treehouse tablet optimisation, preserve the
proven lazy-loaded BoS binder, and apply two narrow presentation fixes.

Real tablet testing showed:
1. the Ogham wheel optimisation is worth keeping;
2. the binder itself should stay on the restored baseline path;
3. the finished-bind modal still shows a redundant Cancel button;
4. live Contents selection checkboxes are being flattened into the PDF.

This patch therefore changes only those two presentation details inside the
Scribe string before applying the existing one-shot lazy wrapper. It does not
change capture scale, html2canvas options, page timing, PDF storage, or any
other binding behaviour.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MARKER = "GM_FV3_TABLET_PERF_OGHAM_ONLY_V2"
SCRIBE_UI_MARKER = "GM_FV3_BIND_UI_CLEANUP_V1"


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

    perf_css = r"""
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
"""
    tree = replace_once(tree, "</head>", perf_css + "</head>", "Treehouse performance CSS")

    old_mount = "const spoke=document.createElement('span'); spoke.className='spoke'; spoke.style.transform=`rotate(${a-90}deg)`; wheel.appendChild(spoke); wheelSpokes.push(spoke);"
    new_mount = "const spoke=document.createElement('span'); spoke.className='spoke'; spoke.dataset.parity=String(i&1); spoke.style.transform=`rotate(${a-90}deg)`; wheel.appendChild(spoke); wheelSpokes.push(spoke);"
    tree = replace_once(tree, old_mount, new_mount, "Treehouse spoke parity")

    old_shade = r"""function shadeWheelStep(stepNo){
  wheelPairs.forEach((pair,i)=>{
    pair.spoke.classList.toggle('stepLight',((i+stepNo)&1)===0);
    pair.spoke.classList.toggle('stepDark',((i+stepNo)&1)===1);
  });
}"""
    new_shade = r"""function shadeWheelStep(stepNo){
  /* One parent attribute replaces forty child class mutations. */
  wheel.dataset.stepParity=String(stepNo&1);
}"""
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
        raise SystemExit("unterminated PAGES.scribe string literal")

    quote_end = i + 1
    if quote_end >= len(text) or text[quote_end] != ";":
        raise SystemExit('PAGES.scribe string literal not followed by ";" as expected')
    return start, quote_start, quote_end, quote_end + 1


def patch_scribe_literal_ui(text: str) -> str:
    """Patch only the raw Scribe literal, preserving all other bytes exactly."""
    start, quote_start, quote_end, statement_end = find_scribe_literal(text)
    literal = text[quote_start:quote_end]

    if SCRIBE_UI_MARKER in literal:
        raise SystemExit("Scribe UI cleanup patch is already present")

    # 1) Finished binding modal: remove only the redundant final Cancel button.
    # Use the three visible labels from the completed modal to avoid touching the
    # genuine Cancel control shown while a bind is still in progress.
    title_pos = literal.find("Book of Shadows Bound")
    if title_pos < 0:
        raise SystemExit("Completed-bind modal title not found")
    stay_pos = literal.find("Stay Editing BoS", title_pos, title_pos + 20000)
    go_pos = literal.find("Go to Ink Pot BoS", stay_pos, stay_pos + 12000) if stay_pos >= 0 else -1
    cancel_pos = literal.find("Cancel", go_pos, go_pos + 8000) if go_pos >= 0 else -1
    if min(stay_pos, go_pos, cancel_pos) < 0:
        raise SystemExit("Completed-bind modal buttons not found in expected order")

    button_start = literal.rfind("<button", go_pos, cancel_pos + 1)
    button_end = literal.find("</button>", cancel_pos)
    if button_start < 0 or button_end < 0 or button_end - cancel_pos > 3000:
        raise SystemExit("Completed-bind Cancel button boundaries not found")
    button_end += len("</button>")
    cancel_button = literal[button_start:button_end]
    if cancel_button.count("Cancel") != 1:
        raise SystemExit("Completed-bind Cancel button match is ambiguous")

    literal = literal[:button_start] + literal[button_end:]

    # 2) Binding clone only: remove interactive checkboxes before html2canvas.
    # This keeps the live Contents page selectable while preventing selection
    # ticks from appearing in the flattened A4 PDF.
    clone_anchor = (
        " if(printMap)gmBosApplyPrintMap(page,clone,printMap);\\n"
        " const stage=document.createElement('div');"
    )
    clone_replacement = (
        " if(printMap)gmBosApplyPrintMap(page,clone,printMap);\\n"
        f" /* {SCRIBE_UI_MARKER}: live selection controls never belong in the flat PDF. */"
        " if(clone&&clone.querySelectorAll){clone.querySelectorAll('input[type=checkbox]').forEach(function(cb){"
        "var p=cb.parentElement;if(p&&p.tagName==='LABEL'&&!String(p.textContent||'').trim()){p.remove();}else{cb.remove();}});}\\n"
        " const stage=document.createElement('div');"
    )
    count = literal.count(clone_anchor)
    if count != 1:
        raise SystemExit(f"BoS clone checkbox-cleanup anchor: expected 1 match, found {count}")
    literal = literal.replace(clone_anchor, clone_replacement, 1)

    # Decode the patched literal as JSON to catch any escaping mistake before CI
    # goes on to package the APK.
    try:
        decoded = json.loads(literal)
    except Exception as exc:
        raise SystemExit(f"Patched Scribe literal is not valid JSON string data: {exc}") from exc

    if "Book of Shadows Bound" not in decoded:
        raise SystemExit("Completed-bind modal disappeared unexpectedly")
    if SCRIBE_UI_MARKER not in decoded:
        raise SystemExit("Scribe UI cleanup marker missing after patch")
    if "querySelectorAll('input[type=checkbox]')" not in decoded:
        raise SystemExit("Bound-copy checkbox cleanup missing after patch")

    return text[:quote_start] + literal + text[quote_end:]


def lazy_wrap_scribe_exact(text: str) -> str:
    """Wrap the already-patched Scribe literal without re-encoding it."""
    start, quote_start, quote_end, statement_end = find_scribe_literal(text)
    literal = text[quote_start:quote_end]

    replacement = (
        "function __gmLazyScribeSrc(){return " + literal + ";}\n"
        'Object.defineProperty(PAGES,"scribe",{configurable:true,enumerable:true,'
        "get:function(){var v=__gmLazyScribeSrc();"
        'Object.defineProperty(PAGES,"scribe",{value:v,configurable:true,writable:true,enumerable:true});'
        "return v;}});"
    )

    patched = text[:start] + replacement + text[statement_end:]
    if 'PAGES.scribe = "' in patched:
        raise SystemExit("direct PAGES.scribe assignment survived")
    if patched.count("__gmLazyScribeSrc") != 2:
        raise SystemExit("expected exactly 2 occurrences of __gmLazyScribeSrc")
    if literal not in patched:
        raise SystemExit("patched Scribe string literal was not preserved byte-for-byte")
    return patched


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_lazy_load_scribe.py INPUT OUTPUT")

    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    text = src.read_text(encoding="utf-8")

    if "function __gmLazyScribeSrc(){return " in text:
        raise SystemExit("Scribe is already lazy-loaded; expected eager reconstruction input")

    # Keep the proven wheel optimisation in Bower/Treehouse.
    bower, _, _ = decode_json_value(text, "PAGES.bower = ", "Bower page")
    text = replace_json_value(text, "PAGES.bower = ", patch_bower(bower), "Bower page")

    # Only presentation cleanup inside Scribe. Binder timing/rendering code stays
    # on the restored baseline path.
    text = patch_scribe_literal_ui(text)
    patched = lazy_wrap_scribe_exact(text)

    if patched.count(MARKER) != 1:
        raise SystemExit(f"expected exactly one Ogham marker, found {patched.count(MARKER)}")
    if patched.count(SCRIBE_UI_MARKER) != 1:
        raise SystemExit(f"expected exactly one Scribe UI marker, found {patched.count(SCRIBE_UI_MARKER)}")
    if "captureChapter==='index'?1.35" in patched or "data-gm-bind-perf" in patched:
        raise SystemExit("regressed BoS bind optimisation survived unexpectedly")
    if "#wheelStation.threadMoving .wheelStave{filter:none!important" not in patched:
        raise SystemExit("Treehouse shadow suppression missing from final app")

    out.write_text(patched, encoding="utf-8")
    print("PAGES.scribe deferred with restored binder timings/rendering untouched")
    print("Ogham wheel tablet optimisation kept")
    print("Completed-bind Cancel button removed")
    print("Bound-copy checkboxes removed from capture clone only")


if __name__ == "__main__":
    main()
