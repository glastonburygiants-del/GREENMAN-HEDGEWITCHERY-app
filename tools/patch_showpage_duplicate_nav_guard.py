#!/usr/bin/env python3
"""Fix "flashing/blank brown screens" during a Scribe bind (Ink Pot "Save
Bound PDF Copy") caused by redundant showPage('scribe') calls tearing down
the live, actively-binding Scribe iframe.

Real-device diagnostics (2026-09) showed this exact sequence while a
background Scribe bind was still running its per-page BIND CAPTURE loop:

    [149] showPage(scribe)  page: home
    [152] showPage(scribe)  page: scribe
    [160] showPage(scribe)  page: scribe
    [164] showPage(scribe)  page: scribe
    [167] FRAME LOOP: Rapid page-frame replacement detected. Detected 4
          occurrences within 1800 ms.

Root cause, confirmed by reading showPage() directly: when a Scribe bind is
active and the user navigates away, the live Scribe iframe is correctly
"parked" under id="gmBosBackgroundFrame" (gmBosParkScribeFrame /
gmBosShellBindingActive). The *first* showPage('scribe') afterwards
correctly restores that exact parked frame via gmBosRestoreScribeFrame()
without disturbing the running bind - but that restore renames the frame
back to id="pageFrame" as part of showing it. Every *subsequent*
showPage('scribe') call (each extra tap while the UI looked frozen) then
finds no "gmBosBackgroundFrame" element, falls into the plain "create a
brand-new iframe and replace the old one" branch, and tears down the very
iframe running the live bind - forcing a full re-render of the ~15MB
Scribe page from scratch. That teardown/rebuild burst is the DOM FRAME
CHANGE + SHELL FRAME SWAP + LONG TASK sequence the FRAME LOOP detector
caught, and what the user described as "blank brown screens ... looks like
the app's dying".

REVISION NOTE (superseding an earlier version of this patch): the first
version of this fix added a time-boxed (~700ms) same-page debounce. A
follow-up real-device log proved that guard insufficient - duplicate
showPage('scribe') calls during a bind landed anywhere from 430ms to 27s
apart (the main thread being intermittently blocked by the bind itself
means "rapid" taps do not reliably land close together in wall-clock
time), so most repeats fell outside the 700ms window and still tore the
frame down every time. A blanket "same page as currentPage, no time
limit" guard was considered instead, but showPage() also has a legitimate,
intentional same-page call path - `function refreshCurrent(){
showPage(currentPage); }` - used elsewhere to force a real reload of the
current page's content; unconditionally no-op'ing any showPage(currentPage)
call would silently break that.

Fix (time-independent, scoped to the actual failure mode instead of a
generic timer): showPage() already knows, at the very top of the function,
which page is currently showing (`currentPage`). Add a narrow guard there
that fires only when ALL of the following hold: the target page is
'scribe', 'scribe' is already the current page, the live #pageFrame exists,
and gmBosShellBindingActive() reports a bind genuinely still running in
that exact frame right now. In that specific state there is nothing to
gain from tearing the frame down - the user is already looking at the live,
binding Scribe page - so the call is ignored before any teardown, no
matter how long it has been since the last identical call. Every other
case is completely unaffected: navigating to a different page still works
normally (currentPage differs), navigating to Scribe when no bind is
running still rebuilds normally, and refreshCurrent() still works for
every page (including Scribe once its bind has finished, since
gmBosShellBindingActive() then reports false).
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_showpage_duplicate_nav_guard.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')

anchor = "function showPage(page){\n  page=normalizeTarget(page||'home');\n  if(!PAGES[page]) page='home';\n  const previousPage=currentPage;\n"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'expected exactly 1 occurrence of showPage() header anchor, found {count}')

start = text.index(anchor)

guard = (
    "  if(page==='scribe' && currentPage==='scribe'){\n"
    "    const gmDupScribeFrame=document.getElementById('pageFrame');\n"
    "    if(gmDupScribeFrame && gmBosShellBindingActive(gmDupScribeFrame)){\n"
    "      /* A Scribe bind is genuinely still running in the exact frame already on\n"
    "         screen. Ignoring this redundant navigation call here, before any\n"
    "         teardown, prevents tearing down that live frame and rebuilding the\n"
    "         ~15MB Scribe page from scratch on every extra tap/re-fired handler -\n"
    "         see patch_showpage_duplicate_nav_guard.py for the full trace. This is\n"
    "         time-independent (no debounce window) since duplicate calls during a\n"
    "         bind can land any distance apart once the main thread is contended. */\n"
    "      return;\n"
    "    }\n"
    "  }\n"
)

replacement = anchor + guard
patched = text[:start] + replacement + text[start + len(anchor):]

if patched == text:
    raise SystemExit('no change applied')
if patched.count('gmDupScribeFrame') != 3:
    raise SystemExit('expected exactly 3 occurrences of gmDupScribeFrame (declaration + 2 uses)')
if 'function showPage(page){\n  page=normalizeTarget' not in patched:
    raise SystemExit('showPage() header missing after patch')

# Everything before/after the anchor region must be byte-identical.
if patched[:start] != text[:start]:
    raise SystemExit('content before the anchor changed unexpectedly')
if patched[start + len(replacement):] != text[start + len(anchor):]:
    raise SystemExit('content after the anchor changed unexpectedly')

out.write_text(patched, encoding='utf-8')
print('showPage() Scribe-bind duplicate-navigation guard applied (time-independent, scoped to active binds)')
