#!/usr/bin/env python3
"""Fix "flashing/blank brown screens" during a Scribe bind (Ink Pot "Save
Bound PDF Copy") caused by redundant, back-to-back showPage() calls for the
page already showing.

Real-device diagnostics (2026-09) showed this exact sequence while a
background Scribe bind was still running its per-page BIND CAPTURE loop:

    [149] showPage(scribe)  page: home
    [152] showPage(scribe)  page: scribe
    [160] showPage(scribe)  page: scribe
    [164] showPage(scribe)  page: scribe
    [167] FRAME LOOP: Rapid page-frame replacement detected. Detected 4
          occurrences within 1800 ms.

Root cause, confirmed by reading showPage() directly: when a Scribe bind is
active, leaving Scribe correctly "parks" its live iframe under the id
gmBosBackgroundFrame (see gmBosParkScribeFrame/gmBosShellBindingActive).
Navigating back to Scribe once correctly restores that exact parked frame
via gmBosRestoreScribeFrame() without touching the running bind. But that
restore path is keyed on document.getElementById('gmBosBackgroundFrame')
existing - and gmBosRestoreScribeFrame renames the restored frame back to
id="pageFrame" as part of showing it. So the *next* call to
showPage('scribe') (each extra tap while the user thinks the UI is frozen,
since a 16+ second single bind-capture step can block the main thread) no
longer finds a "gmBosBackgroundFrame" element, falls into the plain
"create a brand-new iframe and replace the old one" branch, and tears down
the very iframe that is running the live bind - discarding it and forcing
a full re-render of the ~15MB Scribe page from scratch. That teardown/
rebuild is the DOM FRAME CHANGE + SHELL FRAME SWAP + LONG TASK burst the
FRAME LOOP detector caught, and what the user described as "blank brown
screens ... looks like the app's dying".

Fix: showPage() already knows, at the very top of the function, which page
is currently showing (`currentPage`) before it does any of that teardown
work. Add a narrow guard there: if this call's target page is the same
page currently on screen *and* a live #pageFrame already exists, and the
previous showPage() call landed on that same page less than ~700ms ago,
treat this as a redundant duplicate (an extra tap during perceived lag, or
a re-fired handler) and return immediately - before anything is torn down.
A genuine navigation to a *different* page, or a same-page call more than
700ms after the last one, is completely unaffected: it still assigns
currentPage, updates tabs, and rebuilds the frame exactly as before, so a
user can always still navigate normally, and can always still leave
Scribe entirely (the guard never fires for a page change).
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
    "  if(page===currentPage && document.getElementById('pageFrame') && "
    "(window.__gmShowPageLastTs||0) && (Date.now()-window.__gmShowPageLastTs)<700 && "
    "window.__gmShowPageLastPage===page){\n"
    "    /* Redundant duplicate call for the page already on screen (an extra tap\n"
    "       during perceived lag, or a re-fired handler). Ignoring it here, before\n"
    "       any teardown, prevents tearing down a live frame (e.g. an active Scribe\n"
    "       bind's parked iframe) and rebuilding it from scratch on every duplicate\n"
    "       call - see patch_showpage_duplicate_nav_guard.py for the full trace. */\n"
    "    return;\n"
    "  }\n"
    "  window.__gmShowPageLastTs=Date.now();\n"
    "  window.__gmShowPageLastPage=page;\n"
)

replacement = anchor + guard
patched = text[:start] + replacement + text[start + len(anchor):]

if patched == text:
    raise SystemExit('no change applied')
if patched.count('__gmShowPageLastTs') != 3:
    raise SystemExit('expected exactly 3 occurrences of __gmShowPageLastTs (guard read + 2 writes... )')
if 'function showPage(page){\n  page=normalizeTarget' not in patched:
    raise SystemExit('showPage() header missing after patch')

# Everything before/after the anchor region must be byte-identical.
if patched[:start] != text[:start]:
    raise SystemExit('content before the anchor changed unexpectedly')
if patched[start + len(replacement):] != text[start + len(anchor):]:
    raise SystemExit('content after the anchor changed unexpectedly')

out.write_text(patched, encoding='utf-8')
print('showPage() duplicate-navigation guard applied: redundant same-page calls within 700ms are now ignored before any frame teardown')
