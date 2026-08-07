#!/usr/bin/env python3
from pathlib import Path
import sys, json

if len(sys.argv)!=3:
    raise SystemExit('usage: install_ui_feedback.py INPUT OUTPUT')
src=Path(sys.argv[1]); out=Path(sys.argv[2]); s=src.read_text(encoding='utf-8')

def esc(text):
    return json.dumps(text, ensure_ascii=False)[1:-1]

def replace_once(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label} anchor count was {n}, expected 1')
    s=s.replace(old,new,1)

# Outer mode owner: full/master explicitly asks native Android to re-enter immersive mode.
outer_old="""function mode(){ return (localStorage.getItem('gm_app_mode') || 'lite').toLowerCase(); }
function setMode(m){
  m=(m||'lite').toLowerCase();
  localStorage.setItem('gm_app_mode', m);
  if(m==='lite'){
    localStorage.setItem('gm_lite_mode','1');
  }else{
    localStorage.removeItem('gm_lite_mode');
    localStorage.setItem('greenman_full_app_unlocked','1');
  }
  syncModeClass();
  refreshCurrent();
}"""
outer_new="""function mode(){ return (localStorage.getItem('gm_app_mode') || 'lite').toLowerCase(); }
function requestNativeImmersive(){
  try{
    if(window.GreenmanAndroid&&typeof window.GreenmanAndroid.refreshImmersive==='function'){
      window.GreenmanAndroid.refreshImmersive();
    }
  }catch(e){}
}
function setMode(m){
  m=(m||'lite').toLowerCase();
  localStorage.setItem('gm_app_mode', m);
  if(m==='lite'){
    localStorage.setItem('gm_lite_mode','1');
  }else{
    localStorage.removeItem('gm_lite_mode');
    localStorage.setItem('greenman_full_app_unlocked','1');
  }
  syncModeClass();
  refreshCurrent();
  if(m!=='lite'){
    requestNativeImmersive();
    setTimeout(requestNativeImmersive,120);
    setTimeout(requestNativeImmersive,480);
  }
}"""
replace_once(outer_old,outer_new,'outer setMode')

# Full-room message also reasserts immersive mode after entering Rune Hall / Crystal Tumbler.
view_old="""  if(m.type==='greenman-cupboard-view-changed'){
    const fullRoom=m.view==='runeHall'||m.view==='crystalTumbler';
    document.body.classList.toggle('gm-full-room',fullRoom);
    gmResetAppViewport(m.view==='hedge');
    setTimeout(function(){gmResetAppViewport(false)},80);
    setTimeout(function(){gmResetAppViewport(false)},280);
    return;
  }"""
view_new="""  if(m.type==='greenman-cupboard-view-changed'){
    const fullRoom=m.view==='runeHall'||m.view==='crystalTumbler';
    document.body.classList.toggle('gm-full-room',fullRoom);
    gmResetAppViewport(m.view==='hedge');
    setTimeout(function(){gmResetAppViewport(false)},80);
    setTimeout(function(){gmResetAppViewport(false)},280);
    if(fullRoom&&mode()!=='lite'){
      requestNativeImmersive();
      setTimeout(requestNativeImmersive,120);
    }
    return;
  }"""
replace_once(view_old,view_new,'full-room immersive handoff')

# Inside spellBuilder: restore the exact earlier Greenman Gather completion dialog and add print feedback.
status_old="""  function setGatherStatus(show,message){
    var st=ensureGatherStatus();
    st.textContent=message||'Gathering your spell…';
    st.classList.toggle('show',!!show);
  }
  function setGatherButtonsDisabled(flag){"""
status_new="""  function setGatherStatus(show,message){
    var st=ensureGatherStatus();
    st.textContent=message||'Gathering your spell…';
    st.classList.toggle('show',!!show);
  }
  function ensureGatherCompleteDialog(){
    var overlay=document.getElementById('gm-gather-complete-overlay');
    if(overlay)return overlay;
    var css=document.createElement('style');
    css.id='gm-gather-complete-style';
    css.textContent='#gm-gather-complete-overlay{position:fixed;inset:0;z-index:950000;display:none;align-items:center;justify-content:center;padding:20px;background:rgba(0,0,0,.76)}#gm-gather-complete-overlay.show{display:flex}#gm-gather-complete-card{width:min(430px,100%);background:#f5ead0;color:#1a0e04;border:3px solid #c9a84c;border-radius:14px;padding:22px 20px;box-shadow:0 14px 38px rgba(0,0,0,.62);font-family:Georgia,serif}#gm-gather-complete-title{font-family:Cinzel,Georgia,serif;font-size:18px;line-height:1.2;letter-spacing:.06em;text-align:center;color:#2d4a1e;margin:0 0 12px}#gm-gather-complete-text{font-size:16px;line-height:1.48;color:#3a2010;margin:0 0 18px;text-align:left}#gm-gather-complete-actions{display:grid;grid-template-columns:1fr 1fr;gap:9px}#gm-gather-complete-actions button{min-height:48px;border-radius:8px;border:2px solid #8a6030;padding:9px 8px;font-family:Cinzel,Georgia,serif;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}#gm-gather-open-journal{background:#2d4a1e;color:#f5ead0;border-color:#c9a84c!important}#gm-gather-stay{background:#e8c040;color:#1a0e04}@media(max-width:420px){#gm-gather-complete-actions{grid-template-columns:1fr}#gm-gather-complete-card{padding:19px 16px}}@media print{#gm-gather-complete-overlay{display:none!important}}';
    document.head.appendChild(css);
    overlay=document.createElement('div');
    overlay.id='gm-gather-complete-overlay';
    overlay.setAttribute('role','dialog');
    overlay.setAttribute('aria-modal','true');
    overlay.innerHTML='<div id="gm-gather-complete-card"><h2 id="gm-gather-complete-title">✦ Your Spell Is Gathered ✦</h2><p id="gm-gather-complete-text">Your spell is gathered. The Greenman has laid a Quick List of every chosen item in your Journal, ready for the cupboard or a shopping trip. When you wish to keep the full spell, open the Journal and choose <strong>Save &amp; Add to BoS</strong> to place it in your personal Book of Shadows on this device.</p><div id="gm-gather-complete-actions"><button id="gm-gather-open-journal" type="button">Open Journal</button><button id="gm-gather-stay" type="button">Begin Another Spell</button></div></div>';
    document.body.appendChild(overlay);
    overlay.querySelector('#gm-gather-open-journal').addEventListener('click',function(){
      overlay.classList.remove('show');
      try{parent.postMessage({source:'greenman-new-shell-v1',cmd:'nav',target:'journal'},'*');}catch(_e){}
    });
    overlay.querySelector('#gm-gather-stay').addEventListener('click',function(){overlay.classList.remove('show');});
    return overlay;
  }
  function showGatherCompleteDialog(){
    var overlay=ensureGatherCompleteDialog();
    overlay.classList.add('show');
    try{overlay.querySelector('#gm-gather-open-journal').focus();}catch(_e){}
  }
  function ensurePrintStatus(){
    var st=document.getElementById('gm-print-preparing-message');
    if(st)return st;
    var css=document.getElementById('gm-print-preparing-style');
    if(!css){
      css=document.createElement('style');
      css.id='gm-print-preparing-style';
      css.textContent='#gm-print-preparing-message{position:fixed;left:50%;bottom:82px;transform:translateX(-50%);z-index:940000;display:none;width:min(430px,calc(100% - 28px));padding:13px 15px;border:3px solid #c9a84c;border-radius:11px;background:#1a3010;color:#fff6d8;box-shadow:0 8px 24px rgba(0,0,0,.55);font-family:Georgia,serif;font-size:15px;font-weight:700;line-height:1.25;text-align:center}#gm-print-preparing-message.show{display:block}@media print{#gm-print-preparing-message{display:none!important}}';
      document.head.appendChild(css);
    }
    st=document.createElement('div');
    st.id='gm-print-preparing-message';
    st.setAttribute('role','status');
    st.setAttribute('aria-live','polite');
    document.body.appendChild(st);
    return st;
  }
  function setPrintStatus(show,message){
    var st=ensurePrintStatus();
    st.textContent=message||'The Greenman is getting your pages ready to print…';
    st.classList.toggle('show',!!show);
  }
  function setGatherButtonsDisabled(flag){"""
replace_once(esc(status_old),esc(status_new),'Gather dialog / print status')

# Replace the browser alert with the restored Greenman dialog.
alert_old="""      setTimeout(function(){setGatherStatus(false);},350);
      alert('Spell gathered. Journal, shopping list, Admin capture and stock have been updated.');"""
alert_new="""      setTimeout(function(){setGatherStatus(false);},350);
      showGatherCompleteDialog();"""
replace_once(esc(alert_old),esc(alert_new),'Gather completion alert')

# Print page/pack feedback. These replacements do not change what is printed.
render_old="""function renderPrint(pages,kind){
 if(!pages.length){busy=false;alert('No completed print pages were ready.');return}"""
render_new="""function renderPrint(pages,kind){
 if(!pages.length){busy=false;setPrintStatus(false);alert('No completed print pages were ready.');return}"""
replace_once(esc(render_old),esc(render_new),'renderPrint empty')

print_call_old=""" setTimeout(function(){try{if(typeof window.gmNumerologyLines==='function')window.gmNumerologyLines(root,sp)}catch(e){}qa('.true-page',d).forEach(fitPage);busy=false;try{printFrame.contentWindow.document.title=title;printFrame.contentWindow.focus();printFrame.contentWindow.print()}catch(e){console.error(e)}},900);"""
print_call_new=""" setTimeout(function(){try{if(typeof window.gmNumerologyLines==='function')window.gmNumerologyLines(root,sp)}catch(e){}qa('.true-page',d).forEach(fitPage);busy=false;setPrintStatus(false);try{printFrame.contentWindow.document.title=title;printFrame.contentWindow.focus();printFrame.contentWindow.print()}catch(e){console.error(e)}},900);"""
replace_once(esc(print_call_old),esc(print_call_new),'full print handoff status')

pack_old="""function buildPack(){
 if(busy)return;busy=true;var native=window.print;window.print=function(){};
 try{var old=q('#gm-v40-print-stack');if(old)old.remove();window.gmV40Print()}catch(e){window.print=native;busy=false;console.error(e);return}"""
pack_new="""function buildPack(){
 if(busy)return;busy=true;setPrintStatus(true,'The Greenman is getting your A4 pack ready to print…');var native=window.print;window.print=function(){};
 try{var old=q('#gm-v40-print-stack');if(old)old.remove();window.gmV40Print()}catch(e){window.print=native;busy=false;setPrintStatus(false);console.error(e);return}"""
replace_once(esc(pack_old),esc(pack_new),'A4 pack status')

page_old="""function buildPage(){if(busy)return;busy=true;var f=window.GM_CURRENT_FILE||'Page';"""
page_new="""function buildPage(){if(busy)return;busy=true;setPrintStatus(true,'The Greenman is getting your A4 page ready to print…');var f=window.GM_CURRENT_FILE||'Page';"""
replace_once(esc(page_old),esc(page_new),'A4 page status')

lite_old="""function printLiteThree(){
 var sp=state(),label=activeMethod(sp)||'Spell Jar',spell=txt(sp.spell||sp.category||'This Spell');
 var p1=document.getElementById('print-pack-summary-page-1'),p2=document.getElementById('print-pack-summary-page-2');
 if(!p1||!p2){alert('Open both Summary pages before printing the Lite Pack.');return;}"""
lite_new="""function printLiteThree(){
 var sp=state(),label=activeMethod(sp)||'Spell Jar',spell=txt(sp.spell||sp.category||'This Spell');
 var p1=document.getElementById('print-pack-summary-page-1'),p2=document.getElementById('print-pack-summary-page-2');
 if(!p1||!p2){alert('Open both Summary pages before printing the Lite Pack.');return;}
 setPrintStatus(true,'The Greenman is getting your Lite pack ready to print…');"""
replace_once(esc(lite_old),esc(lite_new),'Lite print status start')

lite_call_old="""  try{f.contentWindow.focus();f.contentWindow.print();}finally{setTimeout(function(){f.remove();},1800);} """
# Existing source has no trailing space after }. Use exact fallback.
if esc(lite_call_old) not in s:
    lite_call_old="""  try{f.contentWindow.focus();f.contentWindow.print();}finally{setTimeout(function(){f.remove();},1800);}"""
lite_call_new="""  setPrintStatus(false);
  try{f.contentWindow.focus();f.contentWindow.print();}finally{setTimeout(function(){f.remove();},1800);}"""
replace_once(esc(lite_call_old),esc(lite_call_new),'Lite print handoff status')

# Guards
if "alert('Spell gathered. Journal, shopping list, Admin capture and stock have been updated.')" in s:
    raise SystemExit('old browser Gather alert still present')
for required in ('✦ Your Spell Is Gathered ✦','The Greenman is getting your A4 page ready to print…','requestNativeImmersive','refreshImmersive'):
    if required not in s:
        raise SystemExit(f'missing required UI repair: {required}')

out.write_text(s,encoding='utf-8')
print('Installed Greenman Gather dialog, print feedback and full-mode immersive handoff')
