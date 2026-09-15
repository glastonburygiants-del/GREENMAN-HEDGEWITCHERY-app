#!/usr/bin/env python3
"""Revert all of v33's tap-highlight-transparent changes.

User feedback after v33 shipped: the blue tap-highlight box should be left
alone everywhere, including the Cupboard's supply/incense drawers - those
already show their own distinct highlight effect (not the browser's blue
box) and should not have been touched at all. This reverts every
tap-highlight-transparent addition from v33 (BoS entry-card, Cupboard
incense/daily drawer fronts, Bower back/close/modalBackPrimary, and the
nested Ogham Treehouse reading controls). The other three v33 fixes
(:active press-feedback, instant Incense Blend click, dead Scribe lookups)
are untouched.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_v34_revert_taphighlight_except_drawers.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
original = text


def revert_once(text, anchor, label):
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 occurrence of anchor, found {count}')
    reverted = text.replace(anchor, "", 1)
    if reverted == text:
        raise SystemExit(f'{label}: no change applied')
    return reverted


# BoS .entry-card - revert.
anchor = ".entry-card{background:#3a2a10;border:1px solid rgba(201,168,76,.65);border-radius:10px;padding:13px 14px;text-align:left;color:var(--cream);-webkit-tap-highlight-color:transparent;}"
replacement = ".entry-card{background:#3a2a10;border:1px solid rgba(201,168,76,.65);border-radius:10px;padding:13px 14px;text-align:left;color:var(--cream);}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bos .entry-card revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Cupboard .incense-drawer-front - revert.
anchor = ".incense-drawer-front{position:relative;display:flex;width:100%;height:94px;align-items:center;justify-content:center;overflow:hidden;border:6px solid #1a0803;border-radius:4px;background:repeating-linear-gradient(88deg,rgba(255,255,255,.026) 0 2px,transparent 2px 25px),radial-gradient(ellipse at 30% 15%,rgba(201,126,55,.22),transparent 32%),linear-gradient(90deg,#2b1006,#733819 9%,#4c210d 48%,#6b3215 84%,#291006);box-shadow:inset 0 0 0 3px #8c5127,inset 0 0 0 8px #2a1006,inset 0 0 28px rgba(0,0,0,.68),0 7px 12px rgba(0,0,0,.55);cursor:pointer;-webkit-tap-highlight-color:transparent}"
replacement = ".incense-drawer-front{position:relative;display:flex;width:100%;height:94px;align-items:center;justify-content:center;overflow:hidden;border:6px solid #1a0803;border-radius:4px;background:repeating-linear-gradient(88deg,rgba(255,255,255,.026) 0 2px,transparent 2px 25px),radial-gradient(ellipse at 30% 15%,rgba(201,126,55,.22),transparent 32%),linear-gradient(90deg,#2b1006,#733819 9%,#4c210d 48%,#6b3215 84%,#291006);box-shadow:inset 0 0 0 3px #8c5127,inset 0 0 0 8px #2a1006,inset 0 0 28px rgba(0,0,0,.68),0 7px 12px rgba(0,0,0,.55);cursor:pointer}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'cupboard .incense-drawer-front revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Cupboard combined .incense-drawer-front/.daily-drawer-front rule - revert.
anchor = ".hedge-shelves .incense-drawer-front,\\n.hedge-shelves .daily-drawer-front{-webkit-tap-highlight-color:transparent;"
replacement = ".hedge-shelves .incense-drawer-front,\\n.hedge-shelves .daily-drawer-front{"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'cupboard combined drawer-front rule revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Bower #backBtn (base) - revert.
anchor = "#backBtn{position:absolute;left:2.4%;top:2.4%;z-index:40;width:58px;height:58px;border-radius:50%;border:3px solid #2b1408;background:radial-gradient(circle at 36% 30%,#9d6b36,#633a1b 60%,#35190c);color:#f1d997;font-size:38px;line-height:45px;box-shadow:0 5px 10px #000b,inset 0 0 0 2px #c38a49;cursor:pointer;-webkit-tap-highlight-color:transparent}"
replacement = "#backBtn{position:absolute;left:2.4%;top:2.4%;z-index:40;width:58px;height:58px;border-radius:50%;border:3px solid #2b1408;background:radial-gradient(circle at 36% 30%,#9d6b36,#633a1b 60%,#35190c);color:#f1d997;font-size:38px;line-height:45px;box-shadow:0 5px 10px #000b,inset 0 0 0 2px #c38a49;cursor:pointer}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bower #backBtn (base) revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Bower #backBtn (430px breakpoint) - revert.
anchor = "@media(max-width:430px){#backBtn{width:50px;height:50px;font-size:32px;-webkit-tap-highlight-color:transparent}"
replacement = "@media(max-width:430px){#backBtn{width:50px;height:50px;font-size:32px}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bower #backBtn (430px) revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Bower #backBtn (2nd breakpoint) - revert.
anchor = "#backBtn{width:52px!important;height:52px!important;top:2.0%!important;left:2.2%!important;font-size:34px!important;-webkit-tap-highlight-color:transparent!important}"
replacement = "#backBtn{width:52px!important;height:52px!important;top:2.0%!important;left:2.2%!important;font-size:34px!important}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bower #backBtn (2nd breakpoint) revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Bower .close - revert.
anchor = ".close{position:sticky;float:right;top:0;z-index:5;width:42px;height:42px;border:0;border-radius:50%;background:#5b2e18;color:#f2d89a;font-size:28px;box-shadow:0 4px 9px #0007;cursor:pointer;-webkit-tap-highlight-color:transparent}"
replacement = ".close{position:sticky;float:right;top:0;z-index:5;width:42px;height:42px;border:0;border-radius:50%;background:#5b2e18;color:#f2d89a;font-size:28px;box-shadow:0 4px 9px #0007;cursor:pointer}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bower .close revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Bower .modalBackPrimary - revert.
anchor = ".modalBackPrimary{\\n  position:sticky;top:0;z-index:8;float:left;\\n  min-width:96px;height:44px;padding:0 14px;margin:0 8px 10px 0;\\n  border:2px solid #4d2914;border-radius:15px;\\n  background:linear-gradient(#956536,#542d17);color:#f8e2a7;\\n  font:bold 12px Georgia,\\\"Times New Roman\\\",serif;letter-spacing:.07em;\\n  box-shadow:0 4px 9px #0007,inset 0 0 0 1px rgba(239,194,116,.25);cursor:pointer;\\n  -webkit-tap-highlight-color:transparent;\\n}"
replacement = ".modalBackPrimary{\\n  position:sticky;top:0;z-index:8;float:left;\\n  min-width:96px;height:44px;padding:0 14px;margin:0 8px 10px 0;\\n  border:2px solid #4d2914;border-radius:15px;\\n  background:linear-gradient(#956536,#542d17);color:#f8e2a7;\\n  font:bold 12px Georgia,\\\"Times New Roman\\\",serif;letter-spacing:.07em;\\n  box-shadow:0 4px 9px #0007,inset 0 0 0 1px rgba(239,194,116,.25);cursor:pointer;\\n}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bower .modalBackPrimary revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Bower nested Ogham Treehouse #risen - revert.
anchor = "#risen{height:100%;max-width:105px;filter:drop-shadow(0 13px 10px #000c) drop-shadow(0 0 11px rgba(235,194,93,.34));transform:translateY(46%);opacity:0;transition:transform .55s cubic-bezier(.16,.77,.17,1.15),opacity .3s;pointer-events:auto;cursor:pointer;-webkit-tap-highlight-color:transparent}"
replacement = "#risen{height:100%;max-width:105px;filter:drop-shadow(0 13px 10px #000c) drop-shadow(0 0 11px rgba(235,194,93,.34));transform:translateY(46%);opacity:0;transition:transform .55s cubic-bezier(.16,.77,.17,1.15),opacity .3s;pointer-events:auto;cursor:pointer}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bower ogham #risen revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Bower nested Ogham Treehouse .socket img - revert.
anchor = ".socket img{height:132%;max-width:68px;object-fit:contain;filter:drop-shadow(0 7px 6px #000c);transform:translateY(82%);opacity:0;transition:transform .55s cubic-bezier(.18,.8,.2,1.14),opacity .25s;cursor:pointer;-webkit-tap-highlight-color:transparent}"
replacement = ".socket img{height:132%;max-width:68px;object-fit:contain;filter:drop-shadow(0 7px 6px #000c);transform:translateY(82%);opacity:0;transition:transform .55s cubic-bezier(.18,.8,.2,1.14),opacity .25s;cursor:pointer}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bower ogham .socket img revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Bower nested Ogham Treehouse .castStick - revert.
anchor = ".castStick{position:absolute;width:12%;height:48%;filter:drop-shadow(0 7px 5px #000d);cursor:pointer;transform-origin:50% 50%;opacity:0;transition:opacity .18s,transform .58s cubic-bezier(.18,.82,.19,1.18);-webkit-tap-highlight-color:transparent}"
replacement = ".castStick{position:absolute;width:12%;height:48%;filter:drop-shadow(0 7px 5px #000d);cursor:pointer;transform-origin:50% 50%;opacity:0;transition:opacity .18s,transform .58s cubic-bezier(.18,.82,.19,1.18)}"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bower ogham .castStick revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

# Bower nested Ogham Treehouse .readingBack - revert.
anchor = '.readingBack{\\\\n  position:sticky;top:0;z-index:8;float:left;\\\\n  min-width:92px;height:42px;padding:0 13px;margin:0 8px 8px 0;\\\\n  border:2px solid #4a2814;border-radius:15px;\\\\n  background:linear-gradient(#936335,#542d17);color:#f8e2a7;\\\\n  font:bold 12px Georgia,\\\\\\"Times New Roman\\\\\\",serif;letter-spacing:.07em;\\\\n  box-shadow:0 4px 9px #0007,inset 0 0 0 1px rgba(239,194,116,.25);cursor:pointer;\\\\n  -webkit-tap-highlight-color:transparent;\\\\n}'
replacement = '.readingBack{\\\\n  position:sticky;top:0;z-index:8;float:left;\\\\n  min-width:92px;height:42px;padding:0 13px;margin:0 8px 8px 0;\\\\n  border:2px solid #4a2814;border-radius:15px;\\\\n  background:linear-gradient(#936335,#542d17);color:#f8e2a7;\\\\n  font:bold 12px Georgia,\\\\\\"Times New Roman\\\\\\",serif;letter-spacing:.07em;\\\\n  box-shadow:0 4px 9px #0007,inset 0 0 0 1px rgba(239,194,116,.25);cursor:pointer;\\\\n}'
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'bower ogham .readingBack revert: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

if text == original:
    raise SystemExit('no changes applied overall')

out.write_text(text, encoding='utf-8')
print(f'wrote {out} bytes={len(text)}')
print('Reverted all v33 tap-highlight-transparent additions: BoS entry-card, '
      'Cupboard incense/daily drawer fronts, Bower back/close/modalBackPrimary, '
      'and nested Ogham Treehouse controls all restored to their pre-v33 state.')
