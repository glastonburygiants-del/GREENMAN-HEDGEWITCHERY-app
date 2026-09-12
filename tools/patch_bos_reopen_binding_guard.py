#!/usr/bin/env python3
"""Fix: reopening the live Book of Shadows (BOS) view while a background
bind is active silently halts the bind and shows stale/frozen progress.

Real-device evidence (screenshot + description, 2026-09): a persistent
pill reading "Binding Book of Shadows · 69/99" is shown outside Scribe
(visible on the Admin page) while a bind runs in the background. Tapping
it, then tapping back into the Book of Shadows, was reported to "reload"
the page and stop the X/99 counter from incrementing, with no bind-progress
popup shown afterwards - i.e. the bind appears to actually halt, not just
the UI glitching.

Root cause, confirmed by reading the real code (GM_BOS's `open()` inside
PAGES.scribe):

    function open(){build();bindBosSwipe();$$showView();requestAnimationFrame(()=>fit(true))}

Every call to open() (which is what re-entering the Book of Shadows runs,
e.g. via openBos()) unconditionally calls build() first. build() does:

    pages=[];const pool=$('#gmBosPagePool');pool.innerHTML='';
    addCover(); addContents(); addSpellList(); ... (rebuilds every BOS page)

This wipes and fully rebuilds every page element in #gmBosPagePool from
scratch and resets the module-level `pages` array - including the exact
page elements an in-progress bind (GM_BOS.bindSelected()/flattenBound()/
startNativeBind()) is actively iterating and capturing. The bind's own
progress modal (#gmBosBindModal) lives outside #gmBosPagePool and survives
the rebuild, but the underlying page content being captured does not - so
the running bind loses the content it was working from mid-capture, and
its progress silently stops advancing (the modal itself is not
re-initialized by open(), so it is left showing its last-written, now
frozen, progress text).

The outer shell already has a `gmBosBackgroundBindingActive()`-aware guard
for the analogous problem at the iframe-teardown layer (see
patch_showpage_duplicate_nav_guard.py). This is the same class of bug one
layer deeper: GM_BOS's own open()/build() is not aware that a bind may
already be using the exact content it is about to discard and rebuild.

Fix: skip the destructive build() when a bind is currently active
(window.gmBosBackgroundBindingActive() - the same flag the outer shell
already relies on, backed by the real gmBosActiveBindCancel token). The
view still shows correctly (bindBosSwipe()/$$showView()/fit() are
unaffected and still run), it just does not discard the live pages/pool
out from under the running bind. Once the bind completes, that flag is
false again and open() rebuilds normally as before - so a genuinely stale
BOS view (e.g. after the user has actually edited entries elsewhere) is
still refreshed on next open once no bind is in flight.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_bos_reopen_binding_guard.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')

anchor = 'function open(){build();bindBosSwipe();$$showView();requestAnimationFrame(()=>fit(true))}'
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'expected exactly 1 occurrence of GM_BOS open() anchor, found {count}')

start = text.index(anchor)

replacement = (
    "function open(){"
    "if(!window.gmBosBackgroundBindingActive||!window.gmBosBackgroundBindingActive()){build();}"
    "bindBosSwipe();$$showView();requestAnimationFrame(()=>fit(true))}"
)

patched = text[:start] + replacement + text[start + len(anchor):]

if patched == text:
    raise SystemExit('no change applied')
if patched.count('gmBosBackgroundBindingActive') < 2:
    raise SystemExit('expected the binding-active guard to reference gmBosBackgroundBindingActive at least twice')
if anchor in patched:
    raise SystemExit('original unguarded open() anchor still present after patch')

# Everything before/after the anchor region must be byte-identical.
if patched[:start] != text[:start]:
    raise SystemExit('content before the anchor changed unexpectedly')
if patched[start + len(replacement):] != text[start + len(anchor):]:
    raise SystemExit('content after the anchor changed unexpectedly')

out.write_text(patched, encoding='utf-8')
print('GM_BOS.open() no longer rebuilds (and discards) live BOS pages while a bind is actively using them')
