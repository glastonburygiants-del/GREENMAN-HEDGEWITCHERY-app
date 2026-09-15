#!/usr/bin/env python3
"""Fix: Rune Hall / Crystal Tumbler memory not released, slowing later binds.

Real-device evidence (two diagnostics logs, same 132-page bind, same
device): a bind run cold (fresh app session) took 293,985ms with no
page-capture spikes. A bind run after the user had visited Rune Hall then
Crystal Tumbler earlier in the SAME session took 463,952ms - 65% slower -
with individual page captures spiking to 5-9 seconds in the back half.
Nothing else differed between the two runs.

Root cause confirmed by reading PAGES.cupboard's setCupboardView(): when
leaving Rune Hall or Crystal Tumbler, the code only does
`frame.removeAttribute('srcdoc')` before clearing `dataset.loaded` (so the
room reloads fresh next time it's opened). Removing the srcdoc content
attribute does not reliably force Android WebView to actually navigate the
iframe away from its current (heavy) document - this is a known WebView
inconsistency; unlike a normal top-level navigation, the previous
document's canvas/image memory can remain resident until something
explicitly navigates the frame elsewhere. Both rooms embed large decoded
HTML documents (base64, several hundred KB, with imagery/canvas work), so
whatever stayed resident competed with a later bind for the same limited
memory.

Fix: after removing srcdoc, explicitly navigate the frame to about:blank
before clearing dataset.loaded. This forces a real navigation away from
the heavy document, giving the WebView an unambiguous point to release the
previous document's memory. loadDailyRoom() unconditionally sets
`frame.srcdoc=...` again on next entry, which correctly navigates the
frame away from about:blank into the freshly decoded room content - no
other change needed there.

Applied last, after every existing content-verification assertion, so
this only touches the two known unload call sites in PAGES.cupboard's
setCupboardView().
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_v35_daily_room_hard_unload.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
original = text

anchor = (
    "if(gmWasRuneHall&&next!=='runeHall'&&runeHallFrame){\\n"
    "    try{runeHallFrame.removeAttribute('srcdoc');delete runeHallFrame.dataset.loaded;}catch(_gmUnloadErr){}\\n"
    "  }\\n"
    "  if(gmWasCrystalTumbler&&next!=='crystalTumbler'&&crystalTumblerFrame){\\n"
    "    try{crystalTumblerFrame.removeAttribute('srcdoc');delete crystalTumblerFrame.dataset.loaded;}catch(_gmUnloadErr){}\\n"
    "  }"
)
replacement = (
    "if(gmWasRuneHall&&next!=='runeHall'&&runeHallFrame){\\n"
    "    try{runeHallFrame.removeAttribute('srcdoc');runeHallFrame.src='about:blank';delete runeHallFrame.dataset.loaded;}catch(_gmUnloadErr){}\\n"
    "  }\\n"
    "  if(gmWasCrystalTumbler&&next!=='crystalTumbler'&&crystalTumblerFrame){\\n"
    "    try{crystalTumblerFrame.removeAttribute('srcdoc');crystalTumblerFrame.src='about:blank';delete crystalTumblerFrame.dataset.loaded;}catch(_gmUnloadErr){}\\n"
    "  }"
)

count = text.count(anchor)
if count != 1:
    raise SystemExit(f'daily-room unload block: expected exactly 1 occurrence of anchor, found {count}')
text = text.replace(anchor, replacement, 1)

if text == original:
    raise SystemExit('no changes applied')

out.write_text(text, encoding='utf-8')
print(f'wrote {out} bytes={len(text)}')
print('Rune Hall / Crystal Tumbler now hard-navigate to about:blank on leave, '
      'forcing the previous heavy room document to actually unload instead of '
      'just losing its srcdoc attribute.')
