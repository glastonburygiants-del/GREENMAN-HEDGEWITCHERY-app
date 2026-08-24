#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, zipfile
from pathlib import Path

ROOM_ASSET_BOWER = 'assets/greenman_bower.html'
ROOM_ASSET_SCRIBE = 'assets/greenman_scribe.html'

STYLE = r'''
<style id="greenman-bower-scribe-cupboard-v1">
/* Bower + Scribe are physical cupboard features, not generic menu buttons. */
.hedge-shelves .bower-scribe-row{position:relative!important;width:100%!important;min-height:118px!important;margin:0!important;padding:6px 4px 9px!important;display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;gap:6px!important;border-top:5px solid #180804!important;border-bottom:9px solid #170703!important;background:linear-gradient(90deg,#190904,#4a210d 9%,#261006 50%,#4a210d 91%,#190904)!important;box-shadow:inset 0 10px 18px rgba(0,0,0,.64),0 5px 9px rgba(0,0,0,.44)!important;overflow:hidden!important}
.bower-entry-front,.scribe-desk-front{position:relative!important;width:100%!important;height:94px!important;min-height:94px!important;margin:0!important;padding:0!important;overflow:hidden!important;border:5px solid #1a0803!important;border-radius:4px!important;cursor:pointer!important;color:#351407!important;box-shadow:inset 0 0 0 3px #8c5127,inset 0 0 0 7px #2a1006,inset 0 0 24px rgba(0,0,0,.7),0 5px 9px rgba(0,0,0,.5)!important}
.bower-entry-front{background:repeating-linear-gradient(88deg,rgba(255,255,255,.024) 0 2px,transparent 2px 24px),linear-gradient(90deg,#2a1006,#6d3417 10%,#47200d 50%,#6a3115 88%,#281006)!important}
.bower-entry-front::before{content:"";position:absolute;left:13%;right:13%;top:8px;bottom:8px;border:3px ridge rgba(153,91,43,.82);border-radius:50% 50% 12px 12px/32% 32% 10px 10px;background:radial-gradient(circle at 50% 36%,rgba(99,151,79,.33),transparent 38%),linear-gradient(180deg,#14200f 0,#0c150a 64%,#171008 100%);box-shadow:inset 0 0 18px rgba(0,0,0,.8),0 0 0 2px rgba(35,16,7,.72);pointer-events:none}
.bower-entry-front::after{content:"";position:absolute;z-index:3;left:17%;right:17%;top:13px;height:30px;background:radial-gradient(ellipse at 15% 45%,#476b35 0 13%,transparent 14%),radial-gradient(ellipse at 34% 22%,#35572c 0 12%,transparent 13%),radial-gradient(ellipse at 52% 40%,#52753b 0 13%,transparent 14%),radial-gradient(ellipse at 70% 23%,#35572c 0 12%,transparent 13%),radial-gradient(ellipse at 87% 48%,#476b35 0 13%,transparent 14%);filter:drop-shadow(0 2px 2px rgba(0,0,0,.55));pointer-events:none}
.scribe-desk-front{background:repeating-linear-gradient(88deg,rgba(255,255,255,.025) 0 2px,transparent 2px 25px),radial-gradient(ellipse at 30% 15%,rgba(201,126,55,.22),transparent 32%),linear-gradient(90deg,#2b1006,#733819 9%,#4c210d 48%,#6b3215 84%,#291006)!important}
.scribe-desk-front::before{content:"";position:absolute;inset:12px 12px 16px;border:3px ridge rgba(155,91,43,.82);border-radius:4px;background:linear-gradient(180deg,rgba(132,78,34,.42),rgba(56,24,10,.52));box-shadow:inset 0 0 14px rgba(0,0,0,.5);pointer-events:none}
.scribe-desk-front::after{content:"";position:absolute;z-index:3;left:23%;right:23%;bottom:10px;height:9px;border:2px solid #3b1b09;border-radius:999px;background:linear-gradient(#d3a656,#86501f 62%,#351608);box-shadow:0 2px 4px rgba(0,0,0,.5);pointer-events:none}
.bower-scribe-label{position:absolute;z-index:5;left:8px;right:8px;top:39px;display:flex;align-items:center;justify-content:center;text-align:center;color:#ead59f;font:900 clamp(12px,2.8vw,20px)/1.02 Georgia,"Times New Roman",serif;letter-spacing:.065em;text-transform:uppercase;text-shadow:0 2px 0 #120602,0 0 8px rgba(0,0,0,.8);pointer-events:none}
.bower-entry-front .bower-scribe-label{top:47px;color:#e6d9a9;text-shadow:0 2px 0 #071004,0 0 8px #000}
.scribe-desk-hinge{position:absolute;z-index:4;top:9px;width:28px;height:8px;border:2px solid #40200c;border-radius:3px;background:linear-gradient(#e0b462,#8a551f 58%,#3a1908);box-shadow:0 2px 3px rgba(0,0,0,.55)}
.scribe-desk-hinge.left{left:18%}.scribe-desk-hinge.right{right:18%}
.bower-entry-front:active,.scribe-desk-front:active{transform:translateY(2px)}
@media(max-width:640px){.hedge-shelves .bower-scribe-row{min-height:94px!important;padding:4px 3px 7px!important;gap:3px!important;border-top-width:4px!important;border-bottom-width:7px!important}.bower-entry-front,.scribe-desk-front{height:73px!important;min-height:73px!important;border-width:4px!important}.bower-entry-front::before{left:11%;right:11%;top:6px;bottom:6px;border-width:2px!important}.scribe-desk-front::before{inset:9px 8px 12px;border-width:2px!important}.bower-scribe-label{top:29px;font-size:clamp(10px,3.2vw,14px);letter-spacing:.035em}.bower-entry-front .bower-scribe-label{top:36px}.scribe-desk-hinge{top:7px;width:22px;height:6px}.scribe-desk-front::after{bottom:7px;height:7px}}
</style>
'''

ROOM_VIEWS = r'''
<div class="screen daily-room-view" id="bowerView" hidden><div class="daily-room-app"><iframe class="daily-room-frame" id="bowerFrame" title="Greenman Bower"></iframe><button type="button" class="daily-room-return" id="backFromBower" aria-label="Back to Hedgewitch Cupboard" title="Back to Hedgewitch Cupboard">←</button></div></div>
<div class="screen daily-room-view" id="scribeView" hidden><div class="daily-room-app"><iframe class="daily-room-frame" id="scribeFrame" title="Greenman Scribe Desk"></iframe><button type="button" class="daily-room-return" id="backFromScribe" aria-label="Back to Hedgewitch Cupboard" title="Back to Hedgewitch Cupboard">←</button></div></div>
'''

APPEND_FN = r'''
function appendBowerScribeFronts(){
  const row=document.createElement('section');row.className='bower-scribe-row';
  const bower=document.createElement('button');bower.type='button';bower.className='bower-entry-front';bower.setAttribute('aria-label','Open the Bower');bower.innerHTML='<span class="bower-scribe-label">The Bower</span>';bower.addEventListener('click',openBower);
  const scribe=document.createElement('button');scribe.type='button';scribe.className='scribe-desk-front';scribe.setAttribute('aria-label','Open the Scribe Desk');scribe.innerHTML='<span class="scribe-desk-hinge left"></span><span class="scribe-desk-hinge right"></span><span class="bower-scribe-label">Scribe Desk</span>';scribe.addEventListener('click',openScribe);
  row.appendChild(bower);row.appendChild(scribe);hedgeShelvesEl.appendChild(row);
}
'''

def replace_once(text, old, new, label):
    count=text.count(old)
    if count!=1: raise SystemExit(f'{label}: expected 1 match, found {count}')
    return text.replace(old,new,1)

def patch_cupboard(cupboard):
    if 'greenman-bower-scribe-cupboard-v1' in cupboard: raise SystemExit('Cupboard already contains Bower/Scribe patch')
    cupboard=replace_once(cupboard,'</head><body>',STYLE+'\n</head><body>','insert Bower/Scribe CSS')
    anchor='''<div class="screen daily-room-view" id="crystalTumblerView" hidden>\n  <div class="daily-room-app">\n    <iframe class="daily-room-frame" id="crystalTumblerFrame" title="Greenman Crystal Tumbler"></iframe>\n    <button type="button" class="daily-room-return" id="backFromCrystalTumbler" aria-label="Back to Hedgewitch Cupboard" title="Back to Hedgewitch Cupboard">←</button>\n  </div>\n</div>\n'''
    cupboard=replace_once(cupboard,anchor,anchor+ROOM_VIEWS,'insert room views')
    old='''const runeHallView=document.getElementById('runeHallView');\nconst crystalTumblerView=document.getElementById('crystalTumblerView');\nconst runeHallFrame=document.getElementById('runeHallFrame');\nconst crystalTumblerFrame=document.getElementById('crystalTumblerFrame');'''
    cupboard=replace_once(cupboard,old,old+'''\nconst bowerView=document.getElementById('bowerView');\nconst scribeView=document.getElementById('scribeView');\nconst bowerFrame=document.getElementById('bowerFrame');\nconst scribeFrame=document.getElementById('scribeFrame');''','add DOM refs')
    old="function loadDailyRoom(frame,base64Text){\n  if(!frame||frame.dataset.loaded==='1')return;\n  frame.srcdoc=decodeRoomHtml(base64Text);\n  frame.dataset.loaded='1';\n}\n"
    cupboard=replace_once(cupboard,old,old+"function loadAssetRoom(frame,path){\n  if(!frame||frame.dataset.loaded==='1')return;\n  frame.src=path;\n  frame.dataset.loaded='1';\n}\n",'add asset loader')
    cupboard=replace_once(cupboard,"const next=view==='supply'?'supply':view==='spell'?'spell':view==='incense'?'incense':view==='runeHall'?'runeHall':view==='crystalTumbler'?'crystalTumbler':'hedge';","const next=view==='supply'?'supply':view==='spell'?'spell':view==='incense'?'incense':view==='runeHall'?'runeHall':view==='crystalTumbler'?'crystalTumbler':view==='bower'?'bower':view==='scribe'?'scribe':'hedge';",'extend selector')
    old="  const gmWasRuneHall=!runeHallView.hidden;\n  const gmWasCrystalTumbler=!crystalTumblerView.hidden;\n  hedgeView.hidden=next!=='hedge';incenseView.hidden=next!=='incense';supplyView.hidden=next!=='supply';spellView.hidden=next!=='spell';\n  runeHallView.hidden=next!=='runeHall';crystalTumblerView.hidden=next!=='crystalTumbler';"
    new="  const gmWasRuneHall=!runeHallView.hidden;\n  const gmWasCrystalTumbler=!crystalTumblerView.hidden;\n  const gmWasBower=!bowerView.hidden;\n  const gmWasScribe=!scribeView.hidden;\n  hedgeView.hidden=next!=='hedge';incenseView.hidden=next!=='incense';supplyView.hidden=next!=='supply';spellView.hidden=next!=='spell';\n  runeHallView.hidden=next!=='runeHall';crystalTumblerView.hidden=next!=='crystalTumbler';bowerView.hidden=next!=='bower';scribeView.hidden=next!=='scribe';"
    cupboard=replace_once(cupboard,old,new,'show/hide rooms')
    old="  if(gmWasCrystalTumbler&&next!=='crystalTumbler'&&crystalTumblerFrame){\n    try{crystalTumblerFrame.removeAttribute('srcdoc');delete crystalTumblerFrame.dataset.loaded;}catch(_gmUnloadErr){}\n  }\n"
    new=old+"  if(gmWasBower&&next!=='bower'&&bowerFrame){try{bowerFrame.removeAttribute('src');delete bowerFrame.dataset.loaded;}catch(_gmUnloadErr){}}\n  if(gmWasScribe&&next!=='scribe'&&scribeFrame){try{scribeFrame.removeAttribute('src');delete scribeFrame.dataset.loaded;}catch(_gmUnloadErr){}}\n"
    cupboard=replace_once(cupboard,old,new,'unload rooms')
    old="  if(next==='runeHall')loadDailyRoom(runeHallFrame,RUNE_HALL_ROOM_B64);\n  if(next==='crystalTumbler')loadDailyRoom(crystalTumblerFrame,CRYSTAL_TUMBLER_ROOM_B64);"
    cupboard=replace_once(cupboard,old,old+"\n  if(next==='bower')loadAssetRoom(bowerFrame,'file:///android_asset/greenman_bower.html');\n  if(next==='scribe')loadAssetRoom(scribeFrame,'file:///android_asset/greenman_scribe.html');",'load rooms')
    old="function openRuneHall(){setCupboardView('runeHall')}\nfunction openCrystalTumbler(){setCupboardView('crystalTumbler')}\nfunction returnToHedgewitch(){setCupboardView('hedge')}"
    new="function openRuneHall(){setCupboardView('runeHall')}\nfunction openCrystalTumbler(){setCupboardView('crystalTumbler')}\nfunction openBower(){setCupboardView('bower')}\nfunction openScribe(){setCupboardView('scribe')}\nfunction returnToHedgewitch(){setCupboardView('hedge')}"
    cupboard=replace_once(cupboard,old,new,'open functions')
    marker='function appendDailyDrawers(){'
    cupboard=replace_once(cupboard,marker,APPEND_FN+marker,'append function')
    cupboard=replace_once(cupboard,"  appendIncenseDrawerFront();\n  appendDailyDrawers();\n  appendIncenseBlendShelf();","  appendIncenseDrawerFront();\n  appendDailyDrawers();\n  appendBowerScribeFronts();\n  appendIncenseBlendShelf();",'place row')
    cupboard=replace_once(cupboard,"['backToHedge','backFromSpellCupboard','backFromIncenseDrawer','backFromRuneHall','backFromCrystalTumbler'].forEach(function(id){","['backToHedge','backFromSpellCupboard','backFromIncenseDrawer','backFromRuneHall','backFromCrystalTumbler','backFromBower','backFromScribe'].forEach(function(id){",'wire backs')
    old="window.addEventListener('message',event=>{\n  const message=event.data||{};\n  if(message.source!=='greenman-rune-hall-v1'||message.cmd!=='addHedgewitchRune')return;"
    new="window.addEventListener('message',event=>{\n  const message=event.data||{};\n  if(bowerFrame&&bowerFrame.contentWindow&&event.source===bowerFrame.contentWindow&&(message.type==='greenman:prepareTreehouse'||message.type==='greenman:goTreehouse')){try{bowerFrame.contentWindow.postMessage(message,'*')}catch(_gmBowerRelayErr){}return;}\n  if(message.source!=='greenman-rune-hall-v1'||message.cmd!=='addHedgewitchRune')return;"
    cupboard=replace_once(cupboard,old,new,'relay Bower Treehouse messages')
    for token in ['id="bowerView"','id="scribeView"','function openBower()','function openScribe()','appendBowerScribeFronts();','file:///android_asset/greenman_bower.html','file:///android_asset/greenman_scribe.html','greenman-bower-scribe-cupboard-v1']:
        if token not in cupboard: raise SystemExit(f'missing patched token: {token}')
    return cupboard

def patch_index(index_text):
    assignment='PAGES.cupboard = '
    pos=index_text.find(assignment)
    if pos<0: raise SystemExit('PAGES.cupboard assignment not found')
    value_start=pos+len(assignment)
    cupboard,rel_end=json.JSONDecoder().raw_decode(index_text[value_start:])
    patched=patch_cupboard(cupboard)
    token=json.dumps(patched,ensure_ascii=False).replace('</script>','<\\/script>')
    value_end=value_start+rel_end
    return index_text[:value_start]+token+index_text[value_end:]

def rebuild_apk(base_apk,output_apk,patched_index,bower,scribe):
    with zipfile.ZipFile(base_apk,'r') as zin, zipfile.ZipFile(output_apk,'w') as zout:
        for info in zin.infolist():
            if info.filename.upper().startswith('META-INF/'): continue
            data=patched_index.encode('utf-8') if info.filename=='assets/index.html' else zin.read(info.filename)
            ni=zipfile.ZipInfo(filename=info.filename,date_time=info.date_time);ni.compress_type=info.compress_type;ni.comment=info.comment;ni.extra=info.extra;ni.internal_attr=info.internal_attr;ni.external_attr=info.external_attr;ni.create_system=info.create_system
            zout.writestr(ni,data)
        for arcname,src in [(ROOM_ASSET_BOWER,bower),(ROOM_ASSET_SCRIBE,scribe)]:
            zi=zipfile.ZipInfo(arcname);zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o644<<16;zout.writestr(zi,src.read_bytes())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('base_apk',type=Path);ap.add_argument('bower_html',type=Path);ap.add_argument('scribe_html',type=Path);ap.add_argument('output_apk',type=Path);args=ap.parse_args()
    with zipfile.ZipFile(args.base_apk,'r') as z:index=z.read('assets/index.html').decode('utf-8')
    patched=patch_index(index);rebuild_apk(args.base_apk,args.output_apk,patched,args.bower_html,args.scribe_html)
    print(args.output_apk)
if __name__=='__main__':main()
