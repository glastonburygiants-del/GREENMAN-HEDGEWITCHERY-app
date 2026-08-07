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

def replace_raw_once(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label} raw anchor count was {n}, expected 1')
    s = s.replace(old, new, 1)

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

# Keep the Greenman Gate entirely inside the visible area above the software keyboard.
# The gate uses VisualViewport when Android exposes it, so it follows the real keyboard
# height instead of using a device-specific hard-coded lift.
gate_css_old = '''#gmGate{position:fixed;inset:0;z-index:100;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.75);padding:18px}#gmGate.open{display:flex}.gate-card{width:min(420px,100%);background:#f5ead0;color:#1a0e04;border:3px solid #c9a84c;border-radius:12px;padding:18px;box-shadow:0 12px 35px rgba(0,0,0,.55)}.gate-title{font-size:18px;font-weight:700;color:#2d4a1e;margin:0 0 8px;text-align:center}.gate-text{font-size:14px;line-height:1.35;margin:0 0 12px;color:#3a2010}.gate-card input{width:100%;font-size:18px;padding:12px;border:2px solid #8a6030;border-radius:8px;text-align:center;background:#fffaf0;color:#1a0e04}.gate-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.gate-btn{background:#e8c040;color:#1a0e04;border:2px solid #8a6030;border-radius:7px;padding:10px;font-weight:700;font-family:Georgia,serif}.gate-btn.green{background:#2d4a1e;color:#f5ead0;border-color:#c9a84c}.gate-msg{font-size:13px;text-align:center;min-height:18px;color:#8a1a1a;margin-top:8px;font-style:italic}'''
gate_css_new = gate_css_old + '''
#gmGate.gm-keyboard-open{align-items:flex-start!important;justify-content:center!important;padding-top:10px!important;padding-bottom:10px!important;overflow-y:auto!important;overscroll-behavior:contain}
#gmGate.gm-keyboard-open .gate-card{margin-top:0!important;max-height:calc(var(--gm-gate-visible-height,100vh) - 20px)!important;overflow-y:auto!important;overscroll-behavior:contain}
#gmGate.gm-keyboard-open .gate-row{position:relative;z-index:2}'''
replace_raw_once(gate_css_old, gate_css_new, 'Greenman Gate keyboard CSS')

gate_js_old = '''function openGate(admin){
  const g=document.getElementById('gmGate'); g.classList.add('open');
  document.getElementById('gateMsg').textContent = admin ? 'Master access opens the Admin ledger.' : '';
  setTimeout(()=>document.getElementById('gateInput').focus(),50);
}
function closeGate(){document.getElementById('gmGate').classList.remove('open'); document.getElementById('gateInput').value=''; document.getElementById('gateMsg').textContent='';}'''
gate_js_new = '''function gmSyncGateKeyboard(){
  const g=document.getElementById('gmGate');
  const input=document.getElementById('gateInput');
  if(!g||!input)return;
  if(!g.classList.contains('open')){
    g.classList.remove('gm-keyboard-open');
    g.style.removeProperty('top');
    g.style.removeProperty('bottom');
    g.style.removeProperty('height');
    g.style.removeProperty('--gm-gate-visible-height');
    return;
  }
  const vv=window.visualViewport;
  const base=parseFloat(g.dataset.gmGateBaseHeight||'0')||Math.max(window.innerHeight||0,document.documentElement.clientHeight||0);
  const visible=vv?vv.height:(window.innerHeight||base);
  const keyboardVisible=(base-visible)>110;
  const inputActive=document.activeElement===input;
  const lift=inputActive||keyboardVisible;
  g.classList.toggle('gm-keyboard-open',lift);
  if(lift&&vv){
    const h=Math.max(260,Math.floor(vv.height));
    g.style.setProperty('--gm-gate-visible-height',h+'px');
    g.style.top=Math.max(0,Math.floor(vv.offsetTop||0))+'px';
    g.style.bottom='auto';
    g.style.height=h+'px';
    g.scrollTop=0;
  }else if(!lift){
    g.style.removeProperty('top');
    g.style.removeProperty('bottom');
    g.style.removeProperty('height');
    g.style.removeProperty('--gm-gate-visible-height');
  }
}
function openGate(admin){
  const g=document.getElementById('gmGate');
  const vv=window.visualViewport;
  g.dataset.gmGateBaseHeight=String(Math.max(window.innerHeight||0,document.documentElement.clientHeight||0,vv?vv.height:0));
  g.classList.add('open');
  document.getElementById('gateMsg').textContent = admin ? 'Master access opens the Admin ledger.' : '';
  setTimeout(function(){
    document.getElementById('gateInput').focus();
    gmSyncGateKeyboard();
  },50);
  setTimeout(gmSyncGateKeyboard,180);
  setTimeout(gmSyncGateKeyboard,420);
}
function closeGate(){
  const g=document.getElementById('gmGate');
  g.classList.remove('open','gm-keyboard-open');
  g.style.removeProperty('top');
  g.style.removeProperty('bottom');
  g.style.removeProperty('height');
  g.style.removeProperty('--gm-gate-visible-height');
  delete g.dataset.gmGateBaseHeight;
  document.getElementById('gateInput').value='';
  document.getElementById('gateMsg').textContent='';
}'''
replace_raw_once(gate_js_old, gate_js_new, 'Greenman Gate keyboard JS')

gate_listener_old = '''document.getElementById('gateInput').addEventListener('keydown', e=>{if(e.key==='Enter') submitGate();});
document.getElementById('gmOpenFullFloat').addEventListener('click', ()=>openGate(false));'''
gate_listener_new = '''document.getElementById('gateInput').addEventListener('keydown', e=>{if(e.key==='Enter') submitGate();});
document.getElementById('gateInput').addEventListener('focus',function(){setTimeout(gmSyncGateKeyboard,40);setTimeout(gmSyncGateKeyboard,180);});
document.getElementById('gateInput').addEventListener('blur',function(){setTimeout(gmSyncGateKeyboard,260);});
if(window.visualViewport){
  window.visualViewport.addEventListener('resize',gmSyncGateKeyboard);
  window.visualViewport.addEventListener('scroll',gmSyncGateKeyboard);
}
window.addEventListener('resize',function(){if(document.getElementById('gmGate').classList.contains('open'))setTimeout(gmSyncGateKeyboard,60);});
document.getElementById('gmOpenFullFloat').addEventListener('click', ()=>openGate(false));'''
replace_raw_once(gate_listener_old, gate_listener_new, 'Greenman Gate keyboard listeners')

# Build guards: embedded page HTML is stored in a JavaScript string, so quoted
# welcome-mat markers may appear escaped. Accept the exact raw or escaped representation.
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

for required in (
    '#gmGate.gm-keyboard-open',
    'function gmSyncGateKeyboard()',
    'window.visualViewport.addEventListener(\'resize\',gmSyncGateKeyboard)',
    "g.style.setProperty('--gm-gate-visible-height',h+'px')"
):
    if required not in s:
        raise SystemExit(f'missing Greenman Gate keyboard change: {required}')

out.write_text(s, encoding='utf-8')
print('Installed welcoming mat plus keyboard-safe Greenman Gate positioning')
