#!/usr/bin/env python3
"""Fix: after restoring a parked-during-bind Scribe iframe, the live
bind-progress popup (#gmBosBindModal) can render invisible/collapsed
instead of the fixed-position overlay it is meant to be, making it look
like navigation "took you to Study" instead of the bind progress popup.

Real-device report (2026-09): tapping the persistent "Binding Book of
Shadows · X/Y" status pill (which calls showPage('scribe') to restore the
parked, still-binding Scribe iframe - see gmBosRestoreScribeFrame()) was
expected to show the live bind-progress popup, but instead showed the
Study view with no popup visible.

Root cause candidate, confirmed by reading the real code: #gmBosBindModal
is `.modal{position:fixed;inset:0;...display:none}` / `.modal.open{display
:flex}` - a full-viewport overlay, independent of which `.view` is active,
so its 'open' class (added for the whole duration of a bind and never
removed until completion/cancel) should make it visible regardless of
Study vs BOS view. But gmBosParkScribeFrame() gives the iframe an off-
screen layout for the whole parked duration (`position:absolute;
left:-200%;width:100%;height:100%`), and gmBosRestoreScribeFrame() only
removes that inline style - it never signals the iframe's own document to
recompute layout. A `position:fixed` overlay computed while its containing
iframe was off-screen at an unusual box can retain stale/collapsed layout
metrics on some WebView engines until something forces a reflow inside
that specific document, which would visually present as "the modal isn't
there" even though `.open` is still set - leaving whatever ordinary
(non-fixed, naturally-reflowing) view is behind it, e.g. Study, as the only
thing visibly showing.

Fix: right where showPage() already forces the *outer* shell's viewport to
reset after a restore (`gmResetAppViewport`), also dispatch a `resize`
event on the restored frame's own contentWindow, at the same two delays
already used for the outer reset. This is a minimal, defensive addition -
it does not change any application state, it only asks the restored
document to recompute any layout (including a fixed-position modal) that
may have gone stale while off-screen. If the modal was actually rendering
fine, this is a harmless no-op resize.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_bos_restore_reflow.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')

anchor = (
    "  if(gmRestoredBackgroundScribe){\n"
    "    try{const sd=f.contentWindow.document,study=sd.getElementById('studyView');document.body.classList.toggle('gm-scribe-study-root',!!(study&&study.classList.contains('active')))}catch(_e){document.body.classList.remove('gm-scribe-study-root')}\n"
    "    setTimeout(function(){gmResetAppViewport(false)},0);setTimeout(function(){gmResetAppViewport(false)},120);requestNativeImmersive();setTimeout(requestNativeImmersive,180);return;\n"
    "  }\n"
)
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'expected exactly 1 occurrence of the restored-Scribe-frame anchor, found {count}')

start = text.index(anchor)

reflow = "try{f.contentWindow.dispatchEvent(new Event('resize'))}catch(_gmRestoreReflowErr){}"
replacement = (
    "  if(gmRestoredBackgroundScribe){\n"
    "    try{const sd=f.contentWindow.document,study=sd.getElementById('studyView');document.body.classList.toggle('gm-scribe-study-root',!!(study&&study.classList.contains('active')))}catch(_e){document.body.classList.remove('gm-scribe-study-root')}\n"
    f"    setTimeout(function(){{gmResetAppViewport(false);{reflow}}},0);setTimeout(function(){{gmResetAppViewport(false);{reflow}}},120);requestNativeImmersive();setTimeout(requestNativeImmersive,180);return;\n"
    "  }\n"
)

patched = text[:start] + replacement + text[start + len(anchor):]

if patched == text:
    raise SystemExit('no change applied')
if patched.count("dispatchEvent(new Event('resize'))") != 2:
    raise SystemExit("expected exactly 2 occurrences of the restored-frame resize dispatch")

if patched[:start] != text[:start]:
    raise SystemExit('content before the anchor changed unexpectedly')
if patched[start + len(replacement):] != text[start + len(anchor):]:
    raise SystemExit('content after the anchor changed unexpectedly')

out.write_text(patched, encoding='utf-8')
print('Restored Scribe frame now forces an internal resize/reflow so a stale-layout bind-progress modal is not left invisible')
