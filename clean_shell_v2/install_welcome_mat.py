#!/usr/bin/env python3
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: install_welcome_mat.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')

def esc(text):
    return json.dumps(text, ensure_ascii=False)[1:-1]

def replace_once(old, new, label):
    global s
    old_e, new_e = esc(old), esc(new)
    n = s.count(old_e)
    if n != 1:
        raise SystemExit(f'{label} anchor count was {n}, expected 1')
    s = s.replace(old_e, new_e, 1)

# Brighten the existing invitation glow instead of adding another visual system.
glow_old = '''    <filter id="matGlow" x="-35%" y="-65%" width="170%" height="230%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="4.5" result="blur"/>
      <feFlood flood-color="#d8b567" flood-opacity="0.68" result="gold"/>
      <feComposite in="gold" in2="blur" operator="in" result="bloom"/>
      <feMerge><feMergeNode in="bloom"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>'''
glow_new = '''    <filter id="matGlow" x="-45%" y="-85%" width="190%" height="270%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="6.2" result="blur"/>
      <feFlood flood-color="#f1cd72" flood-opacity="0.88" result="gold"/>
      <feComposite in="gold" in2="blur" operator="in" result="bloom"/>
      <feMerge><feMergeNode in="bloom"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>'''
replace_once(glow_old, glow_new, 'mat glow')

# The mat remains its original size while the doors are shut. Once the doors open,
# it grows upward from the threshold so it feels like the entrance is welcoming the user.
mat_old = '''    #WELCOME_MAT{pointer-events:none;cursor:default;}
    #WELCOME_MAT .mat-hit{pointer-events:none;}
    #MAT_HEDGEWITCH_TEXT{
      fill:#c3ab7b;
      opacity:.88;
      transition:fill .45s ease,filter .45s ease,opacity .45s ease;
    }
    .opened:not(.lite-mode) #WELCOME_MAT{pointer-events:all;cursor:pointer;}
    .opened:not(.lite-mode) #WELCOME_MAT .mat-hit{pointer-events:all;}
    .opened:not(.lite-mode) #MAT_HEDGEWITCH_TEXT{
      fill:#f0cf85;
      filter:url(#matGlow);
      animation:matInvitation 2.15s ease-in-out infinite;
    }
    @keyframes matInvitation{
      0%,100%{opacity:.76}
      50%{opacity:1}
    }'''
mat_new = '''    #WELCOME_MAT{
      pointer-events:none;cursor:default;
      transform-origin:600px 1428px;
      transform:translateY(0) scale(1,1);
      transition:transform .72s cubic-bezier(.2,.72,.18,1),filter .58s ease;
      will-change:transform,filter;
    }
    #WELCOME_MAT .mat-hit{pointer-events:none;}
    #MAT_HEDGEWITCH_TEXT{
      fill:#c3ab7b;
      opacity:.88;
      font-size:34px;
      transition:fill .45s ease,filter .45s ease,opacity .45s ease,font-size .62s cubic-bezier(.2,.72,.18,1);
    }
    .opened:not(.lite-mode) #WELCOME_MAT{
      pointer-events:all;cursor:pointer;
      transform:translateY(-3px) scale(1.015,1.18);
      filter:drop-shadow(0 -8px 16px rgba(241,205,114,.42)) drop-shadow(0 0 12px rgba(216,181,103,.42));
    }
    .opened:not(.lite-mode) #WELCOME_MAT .mat-hit{pointer-events:all;}
    .opened:not(.lite-mode) #MAT_HEDGEWITCH_TEXT{
      fill:#ffe3a2;
      font-size:37px;
      filter:url(#matGlow);
      animation:matInvitation 2.15s ease-in-out infinite;
    }
    @keyframes matInvitation{
      0%,100%{opacity:.88}
      50%{opacity:1}
    }'''
replace_once(mat_old, mat_new, 'welcome mat opening animation')

# Build guards: embedded page HTML is stored in a JavaScript string, so quoted
# markers may appear escaped. Accept the exact raw or escaped representation.
for required in (
    'transform:translateY(-3px) scale(1.015,1.18)',
    'font-size:37px',
    'flood-opacity="0.88"',
    'drop-shadow(0 -8px 16px rgba(241,205,114,.42))',
    'id="WELCOME_MAT"'
):
    if required not in s and esc(required) not in s:
        raise SystemExit(f'missing welcome-mat change: {required}')

if s.count(esc('id="WELCOME_MAT"')) != 1:
    raise SystemExit('WELCOME_MAT owner count changed')

out.write_text(s, encoding='utf-8')
print('Installed taller welcome mat, taller lettering and brighter golden invitation glow')
