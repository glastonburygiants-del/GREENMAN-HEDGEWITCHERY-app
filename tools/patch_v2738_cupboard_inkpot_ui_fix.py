#!/usr/bin/env python3
"""
FV 2.7.38 UI FIX

User report: "I hate all the button presses in the cupboard as they all seem
different and some give horrible blue boxes. The entry to draws and
cupboards and the scribe bos [have this]." and "Theres new version on git
hub and it was ment to remove cancel button when book is bound and not
print the content selection tick boxes."

Root causes found by reading the actual shipped PAGES.cupboard / PAGES.scribe
CSS and JS (see tools/patch_v2738_cupboard_inkpot_ui_fix.py review notes):

1) Cupboard "blue boxes": most Cupboard button classes never suppress the
   default WebView tap-highlight overlay. Only .feature-room-entry (the
   Woods Bower / Scribe's Desk room tiles) carries
   -webkit-tap-highlight-color:transparent. The drawer/cupboard door entries
   (.cupboard-door), the Scribe/BoS scroll popup buttons (.scroll-wood-btn,
   which also backs .add-cupboard-btn/.remove-cupboard-btn/.open-bos-btn),
   the incense builder tabs (.incense-builder-btn), the companion choice
   tiles (.companion-choice-btn) and the spell-instruction button
   (.gm-direct-instruction-btn) do not, so taps on them show the mobile
   browser's default translucent highlight box while feature-room-entry
   does not - exactly the "some give horrible blue boxes... all seem
   different" complaint. Fix: add the same
   -webkit-tap-highlight-color:transparent already used elsewhere to each
   of those base rules. This is a tap-highlight fix only - it does not
   touch outline/:focus-visible, so keyboard focus indication is untouched.

2) Ink Pot cancel button not hidden once bound: the bind modal's Cancel
   button (#gmBosCancelBind) is meant to show only while a bind/packaging
   job is running - the base rule hides it (display:none) and
   `#gmBosBindModal.binding .gmBosCancelBind{display:block}` /
   `#gmBosBindModal.packaging .gmBosBindChoices{display:grid}` reveal it
   only during those states. But the "v29" bind-modal layout carries an
   UNSCOPED override:
     .gmBosBindChoices.v29 .gmBosCancelBind{display:block;margin:0;grid-column:1/-1}
   That selector has higher specificity (3 classes) than the base
   `.gmBosCancelBind{display:none}` (1 class) and is not gated on
   `.binding`/`.packaging` at all, so on the v29 markup actually shipped
   (`class="gmBosBindChoices v29"`) the Cancel button is unconditionally
   visible even after the bind/packaging job has finished and the JS has
   already removed those state classes. Fix: scope that rule to
   `#gmBosBindModal.packaging .gmBosBindChoices.v29 .gmBosCancelBind`, which
   is what the existing (working) JS state-class handling assumes.

3) Ink Pot binding still printed the content-selection tick boxes: the
   `@media print{...display:none!important}` rules for
   .gmBosTocSelect/.gmBosTocItemSelect/.gmBosSpellSelect only apply to an
   actual browser print context. Both A4-page capture routines
   (gmBosPreparePrintPage for the html2canvas browser fallback, and
   gmBosPrepareNativePage for the real APK background renderer) build an
   off-screen clone and call the shared gmBosStripPrintInteractivity(stage)
   to strip interactivity before capture/serialisation - but that function
   only disables buttons/textareas/selects and explicitly skips
   checkboxes, so the tick boxes stay visible and get captured/rendered
   into the bound PDF regardless of @media print, since neither capture
   path is an actual print media context. Fix: make
   gmBosStripPrintInteractivity also force-hide the selection controls
   directly on the cloned DOM (a real visibility toggle, not a CSS
   print-media rule), which both capture routes already call.
"""
import sys, hashlib
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_v2738_cupboard_inkpot_ui_fix.py INPUT.html OUTPUT.html')

src = Path(sys.argv[1]).read_text(encoding='utf-8')

# --- 1) Cupboard tap-highlight consistency -------------------------------

cupboard_fixes = [
    (
        '.cupboard-door{position:relative;min-height:210px;overflow:hidden;border:7px solid #1a0803;border-radius:5px;padding:24px 30px;background:\\n repeating-linear-gradient(88deg,rgba(255,255,255,.025) 0 2px,transparent 2px 24px),\\n radial-gradient(ellipse at 28% 18%,rgba(198,126,58,.24),transparent 30%),\\n linear-gradient(90deg,#2a1006,#713819 8%,#4d220e 47%,#6a3216 82%,#2a1006);\\n box-shadow:inset 0 0 0 3px #8b5127,inset 0 0 0 8px #2b1006,inset 0 0 32px rgba(0,0,0,.68),0 8px 14px rgba(0,0,0,.55);cursor:pointer}',
        '.cupboard-door{position:relative;min-height:210px;overflow:hidden;border:7px solid #1a0803;border-radius:5px;padding:24px 30px;background:\\n repeating-linear-gradient(88deg,rgba(255,255,255,.025) 0 2px,transparent 2px 24px),\\n radial-gradient(ellipse at 28% 18%,rgba(198,126,58,.24),transparent 30%),\\n linear-gradient(90deg,#2a1006,#713819 8%,#4d220e 47%,#6a3216 82%,#2a1006);\\n box-shadow:inset 0 0 0 3px #8b5127,inset 0 0 0 8px #2b1006,inset 0 0 32px rgba(0,0,0,.68),0 8px 14px rgba(0,0,0,.55);cursor:pointer;-webkit-tap-highlight-color:transparent}',
    ),
    (
        '.scroll-wood-btn{padding:11px 18px;border:0;border-radius:14px;background:linear-gradient(180deg,#6e4321,#3c1d0d);color:#fff0c5;font:700 14px Georgia,\\"Times New Roman\\",serif;letter-spacing:.08em;text-transform:uppercase;box-shadow:inset 0 0 0 1px rgba(245,206,140,.22),0 6px 14px rgba(0,0,0,.25);cursor:pointer}',
        '.scroll-wood-btn{padding:11px 18px;border:0;border-radius:14px;background:linear-gradient(180deg,#6e4321,#3c1d0d);color:#fff0c5;font:700 14px Georgia,\\"Times New Roman\\",serif;letter-spacing:.08em;text-transform:uppercase;box-shadow:inset 0 0 0 1px rgba(245,206,140,.22),0 6px 14px rgba(0,0,0,.25);cursor:pointer;-webkit-tap-highlight-color:transparent}',
    ),
    (
        '.incense-builder-btn{flex:1;padding:9px 10px;border:2px solid #c99857;border-radius:7px;color:#fff1c8;font:900 11px Georgia,\\"Times New Roman\\",serif;text-transform:uppercase;letter-spacing:.04em;cursor:pointer}',
        '.incense-builder-btn{flex:1;padding:9px 10px;border:2px solid #c99857;border-radius:7px;color:#fff1c8;font:900 11px Georgia,\\"Times New Roman\\",serif;text-transform:uppercase;letter-spacing:.04em;cursor:pointer;-webkit-tap-highlight-color:transparent}',
    ),
    (
        '.companion-choice-btn{min-height:68px;border:3px solid #70431d;border-radius:12px;background:linear-gradient(#8a5529,#3b190a);color:#fff0c5;font:900 16px/1.15 Georgia,\\"Times New Roman\\",serif;box-shadow:inset 0 0 0 2px #281006,0 4px 8px rgba(0,0,0,.38);cursor:pointer}',
        '.companion-choice-btn{min-height:68px;border:3px solid #70431d;border-radius:12px;background:linear-gradient(#8a5529,#3b190a);color:#fff0c5;font:900 16px/1.15 Georgia,\\"Times New Roman\\",serif;box-shadow:inset 0 0 0 2px #281006,0 4px 8px rgba(0,0,0,.38);cursor:pointer;-webkit-tap-highlight-color:transparent}',
    ),
    (
        'gm-direct-instruction-btn{\\n  display:block!important;\\n  width:100%!important;\\n  min-height:58px!important;\\n  padding:14px 12px!important;\\n  border:3px solid #8a6030!important;\\n  border-radius:10px!important;\\n  background:linear-gradient(#f1cc4d,#c89320)!important;\\n  color:#261407!important;\\n  box-shadow:0 4px 9px rgba(0,0,0,.28),inset 0 0 0 1px rgba(255,244,180,.7)!important;\\n  font:900 15px/1.15 Georgia,\\"Times New Roman\\",serif!important;\\n  letter-spacing:.055em!important;\\n  text-transform:uppercase!important;\\n  cursor:pointer!important;\\n}',
        'gm-direct-instruction-btn{\\n  display:block!important;\\n  width:100%!important;\\n  min-height:58px!important;\\n  padding:14px 12px!important;\\n  border:3px solid #8a6030!important;\\n  border-radius:10px!important;\\n  background:linear-gradient(#f1cc4d,#c89320)!important;\\n  color:#261407!important;\\n  box-shadow:0 4px 9px rgba(0,0,0,.28),inset 0 0 0 1px rgba(255,244,180,.7)!important;\\n  font:900 15px/1.15 Georgia,\\"Times New Roman\\",serif!important;\\n  letter-spacing:.055em!important;\\n  text-transform:uppercase!important;\\n  cursor:pointer!important;\\n  -webkit-tap-highlight-color:transparent!important;\\n}',
    ),
]

for old, new in cupboard_fixes:
    if old not in src:
        raise SystemExit('cupboard tap-highlight anchor not found: ' + old[:60])
    count = src.count(old)
    if count != 1:
        raise SystemExit('cupboard tap-highlight anchor not unique (%d): %s' % (count, old[:60]))
    src = src.replace(old, new, 1)

# --- 2) Ink Pot: cancel button must not outrun the packaging/binding state -

old_cancel_css = ".gmBosBindChoices.v29 .gmBosCancelBind{display:block;margin:0;grid-column:1/-1}"
new_cancel_css = "#gmBosBindModal.packaging .gmBosBindChoices.v29 .gmBosCancelBind{display:block;margin:0;grid-column:1/-1}"
if src.count(old_cancel_css) != 1:
    raise SystemExit('Ink Pot cancel-button CSS anchor not found or not unique')
src = src.replace(old_cancel_css, new_cancel_css, 1)

# --- 3) Ink Pot: hide content-selection tick boxes on the captured clone --

old_strip = (
    "function gmBosStripPrintInteractivity(root){\\n"
    " qa('a[href]',root).forEach(a=>{a.removeAttribute('href');a.removeAttribute('target')});\\n"
    " qa('[onclick]',root).forEach(el=>el.removeAttribute('onclick'));\\n"
    " qa('button',root).forEach(b=>{b.disabled=true;b.setAttribute('aria-disabled','true')});\\n"
    " qa('textarea',root).forEach(t=>{t.setAttribute('readonly','readonly');t.textContent=t.value||t.textContent||''});\\n"
    " qa('input',root).forEach(i=>{i.setAttribute('readonly','readonly');if(i.type!=='checkbox'&&i.type!=='radio')i.setAttribute('value',i.value||'')});\\n"
    " qa('select',root).forEach(s=>s.disabled=true)\\n"
    "}"
)
new_strip = (
    "function gmBosStripPrintInteractivity(root){\\n"
    " qa('a[href]',root).forEach(a=>{a.removeAttribute('href');a.removeAttribute('target')});\\n"
    " qa('[onclick]',root).forEach(el=>el.removeAttribute('onclick'));\\n"
    " qa('button',root).forEach(b=>{b.disabled=true;b.setAttribute('aria-disabled','true')});\\n"
    " qa('textarea',root).forEach(t=>{t.setAttribute('readonly','readonly');t.textContent=t.value||t.textContent||''});\\n"
    " qa('input',root).forEach(i=>{i.setAttribute('readonly','readonly');if(i.type!=='checkbox'&&i.type!=='radio')i.setAttribute('value',i.value||'')});\\n"
    " qa('select',root).forEach(s=>s.disabled=true);\\n"
    " qa('.gmBosTocSelect,.gmBosTocItemSelect,.gmBosSpellSelect,.gmBosTocOpenBtn,.gmBosContentsActions',root).forEach(el=>el.style.setProperty('display','none','important'))\\n"
    "}"
)
if src.count(old_strip) != 1:
    raise SystemExit('gmBosStripPrintInteractivity anchor not found or not unique')
src = src.replace(old_strip, new_strip, 1)

marker = '<!-- FV 2.7.38 CUPBOARD/INKPOT UI FIX: consistent tap-highlight on Cupboard buttons; bind-modal Cancel now scoped to the active job state; content-selection tick boxes force-hidden before A4 capture. -->'
if marker not in src:
    src = src.replace('</head>', marker + '\n</head>', 1)

Path(sys.argv[2]).write_text(src, encoding='utf-8')
data = src.encode('utf-8')
print('bytes', len(data))
print('sha256', hashlib.sha256(data).hexdigest())
