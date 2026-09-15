#!/usr/bin/env python3
"""Fix: merged button/UX consistency audit findings.

User complaints (in plain terms): "some buttons show a blue box on tap and
some don't, some need a double-tap and some a single tap, some feel slow,
some instant, and Cupboard specifically feels clunky/slow to navigate."

Confirmed by reading the actual shipped code (PAGES.home, PAGES.admin,
PAGES.bos, PAGES.cupboard, PAGES.bower, PAGES.scribe) that four narrow,
independent inconsistencies exist:

1. Two buttons are missing the `:active` press-feedback rule every sibling
   button in their room already has: `.gm-home-full-unlock-btn` (Home) and
   `.pin-key` (Admin PIN keypad).

2. Several "door/tile" style controls are missing
   `-webkit-tap-highlight-color:transparent`, while visually/functionally
   identical sibling controls in the same room already have it:
   `.entry-card` (BoS, sibling of `.category-square`), `.incense-drawer-front`
   / `.daily-drawer-front` (Cupboard, siblings of `.cupboard-door` /
   `.feature-room-entry`), `#backBtn` / `.close` / `.modalBackPrimary`
   (Bower, siblings of `#treehouseAccess` / `#objSmelting` / `.object`), and
   `#risen` / `.castStick` / `.socket img` / `.readingBack` (the nested
   Ogham Treehouse iframe inside Bower, siblings of `.methodPlaque` /
   `#bowerReturn`).

3. A later "V32" hotfix silently reassigns the global
   `buildIncenseBlendCard` (no var/let/const, so it overwrites the original
   top-level function) to a version gated behind a 400ms setTimeout +
   dblclick shortcut, while the visually identical `buildSpellVesselCard`
   (Spell Cupboard cards on the same shelves) opens its popup instantly on
   click. This is the confirmed cause of "Cupboard specifically feels
   clunky/slow" for Incense Blend cards. Fix: delete the V32 override so the
   original instant-click function (already defined earlier in the same
   file) is what executes - lower-diff than rewriting the override in
   place, and behaviourally identical to before the V32 hotfix existed.

4. Two dead JS lookups in PAGES.scribe reference ids removed from markup in
   earlier cleanups: `#gmInkReturnLiveBtn` (removed with the V29 INK
   markup simplification) and `#gmScribeJobTitle` (removed with the old BoS
   Text Conversion panel). Both are harmless (`if(back)`/`if(title)`
   guarded) but are dead code doing nothing on every call; since no HTML
   restores either id, the safe fix is removing the dead lookups.

Applied last (via the workflow step ordering), after every content check
above has verified the eager/lazy PAGES forms, so this only makes the four
changes described - no deity/herb code, no broad refactor, matching the
in-scope fix plan exactly.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_v33_button_ux_fixes.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
original = text


def apply_once(text, anchor, replacement, label):
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 occurrence of anchor, found {count}')
    patched = text.replace(anchor, replacement, 1)
    if patched == text:
        raise SystemExit(f'{label}: no change applied')
    return patched


# ---------------------------------------------------------------------
# (1a) Home: .gm-home-full-unlock-btn missing :active press feedback.
# ---------------------------------------------------------------------
anchor = ".begin-btn:active {\\n  transform: scale(0.95);\\n  box-shadow: 0 2px 14px rgba(122,26,26,0.6);\\n}\\n"
replacement = anchor + ".gm-home-full-unlock-btn:active{transform:scale(0.95);}\\n"
text = apply_once(text, anchor, replacement, 'home unlock-btn :active')

# ---------------------------------------------------------------------
# (1b) Admin: .pin-key missing :active press feedback.
# ---------------------------------------------------------------------
anchor = ".btn:active{transform:scale(.98)}"
replacement = anchor + ".pin-key:active{transform:scale(.98)}"
text = apply_once(text, anchor, replacement, 'admin pin-key :active')

# ---------------------------------------------------------------------
# (2a) BoS: .entry-card missing tap-highlight-transparent.
# ---------------------------------------------------------------------
anchor = ".entry-card{background:#3a2a10;border:1px solid rgba(201,168,76,.65);border-radius:10px;padding:13px 14px;text-align:left;color:var(--cream);}"
replacement = ".entry-card{background:#3a2a10;border:1px solid rgba(201,168,76,.65);border-radius:10px;padding:13px 14px;text-align:left;color:var(--cream);-webkit-tap-highlight-color:transparent;}"
text = apply_once(text, anchor, replacement, 'bos .entry-card tap-highlight')

# ---------------------------------------------------------------------
# (2b) Cupboard: .incense-drawer-front missing tap-highlight-transparent.
# ---------------------------------------------------------------------
anchor = ".incense-drawer-front{position:relative;display:flex;width:100%;height:94px;align-items:center;justify-content:center;overflow:hidden;border:6px solid #1a0803;border-radius:4px;background:repeating-linear-gradient(88deg,rgba(255,255,255,.026) 0 2px,transparent 2px 25px),radial-gradient(ellipse at 30% 15%,rgba(201,126,55,.22),transparent 32%),linear-gradient(90deg,#2b1006,#733819 9%,#4c210d 48%,#6b3215 84%,#291006);box-shadow:inset 0 0 0 3px #8c5127,inset 0 0 0 8px #2a1006,inset 0 0 28px rgba(0,0,0,.68),0 7px 12px rgba(0,0,0,.55);cursor:pointer}"
replacement = anchor[:-1] + ";-webkit-tap-highlight-color:transparent}"
text = apply_once(text, anchor, replacement, 'cupboard .incense-drawer-front tap-highlight')

# ---------------------------------------------------------------------
# (2c) Cupboard: combined .incense-drawer-front/.daily-drawer-front rule.
# ---------------------------------------------------------------------
anchor = ".hedge-shelves .incense-drawer-front,\\n.hedge-shelves .daily-drawer-front{"
replacement = anchor + "-webkit-tap-highlight-color:transparent;"
text = apply_once(text, anchor, replacement, 'cupboard combined drawer-front rule tap-highlight')

# ---------------------------------------------------------------------
# (2d) Bower: #backBtn (all 3 responsive redeclarations) + .close +
#      .modalBackPrimary missing tap-highlight-transparent.
# ---------------------------------------------------------------------
anchor = "#backBtn{position:absolute;left:2.4%;top:2.4%;z-index:40;width:58px;height:58px;border-radius:50%;border:3px solid #2b1408;background:radial-gradient(circle at 36% 30%,#9d6b36,#633a1b 60%,#35190c);color:#f1d997;font-size:38px;line-height:45px;box-shadow:0 5px 10px #000b,inset 0 0 0 2px #c38a49;cursor:pointer}"
replacement = anchor[:-1] + ";-webkit-tap-highlight-color:transparent}"
text = apply_once(text, anchor, replacement, 'bower #backBtn (base) tap-highlight')

anchor = "@media(max-width:430px){#backBtn{width:50px;height:50px;font-size:32px}"
replacement = "@media(max-width:430px){#backBtn{width:50px;height:50px;font-size:32px;-webkit-tap-highlight-color:transparent}"
text = apply_once(text, anchor, replacement, 'bower #backBtn (430px breakpoint) tap-highlight')

anchor = "#backBtn{width:52px!important;height:52px!important;top:2.0%!important;left:2.2%!important;font-size:34px!important}"
replacement = anchor[:-1] + ";-webkit-tap-highlight-color:transparent!important}"
text = apply_once(text, anchor, replacement, 'bower #backBtn (2nd breakpoint) tap-highlight')

anchor = ".close{position:sticky;float:right;top:0;z-index:5;width:42px;height:42px;border:0;border-radius:50%;background:#5b2e18;color:#f2d89a;font-size:28px;box-shadow:0 4px 9px #0007;cursor:pointer}"
replacement = anchor[:-1] + ";-webkit-tap-highlight-color:transparent}"
text = apply_once(text, anchor, replacement, 'bower .close tap-highlight')

anchor = ".modalBackPrimary{\\n  position:sticky;top:0;z-index:8;float:left;\\n  min-width:96px;height:44px;padding:0 14px;margin:0 8px 10px 0;\\n  border:2px solid #4d2914;border-radius:15px;\\n  background:linear-gradient(#956536,#542d17);color:#f8e2a7;\\n  font:bold 12px Georgia,\\\"Times New Roman\\\",serif;letter-spacing:.07em;\\n  box-shadow:0 4px 9px #0007,inset 0 0 0 1px rgba(239,194,116,.25);cursor:pointer;\\n}"
replacement = anchor[:-1] + "  -webkit-tap-highlight-color:transparent;\\n}"
text = apply_once(text, anchor, replacement, 'bower .modalBackPrimary tap-highlight')

# ---------------------------------------------------------------------
# (2e) Bower's nested Ogham Treehouse iframe markup (a JS string embedded
#      inside PAGES.bower, hence the doubled backslash-escapes below):
#      #risen, .castStick, .socket img, .readingBack missing
#      tap-highlight-transparent.
# ---------------------------------------------------------------------
anchor = "#risen{height:100%;max-width:105px;filter:drop-shadow(0 13px 10px #000c) drop-shadow(0 0 11px rgba(235,194,93,.34));transform:translateY(46%);opacity:0;transition:transform .55s cubic-bezier(.16,.77,.17,1.15),opacity .3s;pointer-events:auto;cursor:pointer}"
replacement = anchor[:-1] + ";-webkit-tap-highlight-color:transparent}"
text = apply_once(text, anchor, replacement, 'bower ogham #risen tap-highlight')

anchor = ".socket img{height:132%;max-width:68px;object-fit:contain;filter:drop-shadow(0 7px 6px #000c);transform:translateY(82%);opacity:0;transition:transform .55s cubic-bezier(.18,.8,.2,1.14),opacity .25s;cursor:pointer}"
replacement = anchor[:-1] + ";-webkit-tap-highlight-color:transparent}"
text = apply_once(text, anchor, replacement, 'bower ogham .socket img tap-highlight')

anchor = ".castStick{position:absolute;width:12%;height:48%;filter:drop-shadow(0 7px 5px #000d);cursor:pointer;transform-origin:50% 50%;opacity:0;transition:opacity .18s,transform .58s cubic-bezier(.18,.82,.19,1.18)}"
replacement = anchor[:-1] + ";-webkit-tap-highlight-color:transparent}"
text = apply_once(text, anchor, replacement, 'bower ogham .castStick tap-highlight')

anchor = '.readingBack{\\\\n  position:sticky;top:0;z-index:8;float:left;\\\\n  min-width:92px;height:42px;padding:0 13px;margin:0 8px 8px 0;\\\\n  border:2px solid #4a2814;border-radius:15px;\\\\n  background:linear-gradient(#936335,#542d17);color:#f8e2a7;\\\\n  font:bold 12px Georgia,\\\\\\"Times New Roman\\\\\\",serif;letter-spacing:.07em;\\\\n  box-shadow:0 4px 9px #0007,inset 0 0 0 1px rgba(239,194,116,.25);cursor:pointer;\\\\n}'
replacement = anchor[:-1] + "  -webkit-tap-highlight-color:transparent;\\\\n}"
text = apply_once(text, anchor, replacement, 'bower ogham .readingBack tap-highlight')

# ---------------------------------------------------------------------
# (3) Cupboard: remove the V32 buildIncenseBlendCard override (setTimeout
#     400ms + dblclick shortcut) so the original instant-click top-level
#     function (defined earlier in the same file) executes instead.
# ---------------------------------------------------------------------
anchor = (
    "buildIncenseBlendCard=function(blend){\\n"
    "    const card=document.createElement('button');card.type='button';card.className='spell-vessel-card incense-blend-card kind-bowl';card.setAttribute('aria-label',flatName(blend&&blend.name||'Incense Blend'));\\n"
    "    const crystal=companionItemById(blend&&blend.crystalId,'Crystal');const rune=companionItemById(blend&&blend.runeId,'Rune');\\n"
    "    card.innerHTML='<div class=\\\"spell-vessel-art\\\">'+incenseBlendArtwork(blend)+'</div><div class=\\\"incense-companion-icons\\\">'+companionBadge(crystal,'crystal')+companionBadge(rune,'rune')+'</div>';\\n"
    "    let timer=0,lastTap=0;\\n"
    "    card.addEventListener('click',event=>{\\n"
    "      event.preventDefault();const now=Date.now();\\n"
    "      if(now-lastTap<390){lastTap=0;if(timer)clearTimeout(timer);timer=0;openFinishedBlendCupboard(blend);return}\\n"
    "      lastTap=now;timer=window.setTimeout(()=>{timer=0;lastTap=0;openIncenseBlendPopup(blend)},400);\\n"
    "    });\\n"
    "    card.addEventListener('dblclick',event=>{event.preventDefault();event.stopPropagation();if(timer)clearTimeout(timer);timer=0;lastTap=0;openFinishedBlendCupboard(blend)});\\n"
    "    return card;\\n"
    "  };\\n\\n"
)
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'V32 buildIncenseBlendCard override: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, "", 1)

if "buildIncenseBlendCard=function(blend)" in text:
    raise SystemExit('V32 buildIncenseBlendCard override still present after removal attempt')

# ---------------------------------------------------------------------
# (4) Scribe: remove dead #gmInkReturnLiveBtn / #gmScribeJobTitle lookups.
#     Two independent renderInkPrintRoom() definitions exist in the
#     shipped PAGES.scribe payload (separate embedded documents); both are
#     patched identically.
# ---------------------------------------------------------------------
anchor = "stored=$('#gmInkExportLastBoundBtn'),back=$('#gmInkReturnLiveBtn');"
replacement = "stored=$('#gmInkExportLastBoundBtn');"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'scribe renderInkPrintRoom (variant A) destructure: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

anchor = "btn=$('#gmInkPrintBoundBtn'),back=$('#gmInkReturnLiveBtn'),find=$('#gmInkFindBoundPdfBtn')"
replacement = "btn=$('#gmInkPrintBoundBtn'),find=$('#gmInkFindBoundPdfBtn')"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'scribe renderInkPrintRoom (variant B) destructure: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

anchor = "btn.onclick=gmInkPrintBound;if(back)back.onclick=openBos;"
count = text.count(anchor)
if count != 2:
    raise SystemExit(f'scribe "if(back)back.onclick=openBos;" statements: expected exactly 2 occurrences, found {count}')
replacement = "btn.onclick=gmInkPrintBound;"
text = text.replace(anchor, replacement)

if "gmInkReturnLiveBtn" in text:
    # The diagnostic-only id list at 'INK STATE' still legitimately
    # references the removed control's former id string for logging
    # purposes elsewhere; only fail if it's still in a live lookup form.
    if "back=$('#gmInkReturnLiveBtn')" in text:
        raise SystemExit('gmInkReturnLiveBtn lookup still present after removal attempt')

if "const title=$('#gmScribeJobTitle');if(title)title.textContent='Cancelling safely…';" in text:
    pass  # will be removed below; this branch only documents intent

anchor = "const title=$('#gmScribeJobTitle');if(title)title.textContent='Cancelling safely…';"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'scribe gmScribeJobTitle lookup: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, "", 1)

if "gmScribeJobTitle" in text:
    raise SystemExit('gmScribeJobTitle reference still present after removal attempt')

if text == original:
    raise SystemExit('no changes applied overall')

out.write_text(text, encoding='utf-8')
print(f'wrote {out} bytes={len(text)}')
print('Button/UX fixes applied: home unlock-btn + admin pin-key :active rules; '
      'tap-highlight-transparent added to BoS entry-card, Cupboard incense/daily '
      'drawer fronts, Bower back/close/modalBackPrimary and nested Ogham '
      'Treehouse controls; V32 Incense Blend card double-tap/delay override '
      'removed (instant click restored); dead Scribe gmInkReturnLiveBtn/'
      'gmScribeJobTitle lookups removed.')
