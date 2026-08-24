#!/usr/bin/env python3
from pathlib import Path
import argparse, json, sys


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_cupboard(cup):
    anchor = '''<div class="screen daily-room-view" id="runeHallView" hidden>\n  <div class="daily-room-app">\n    <iframe class="daily-room-frame" id="runeHallFrame" title="Greenman Rune Hall"></iframe>\n    <button type="button" class="daily-room-return" id="backFromRuneHall" aria-label="Back to Hedgewitch Cupboard" title="Back to Hedgewitch Cupboard">←</button>\n  </div>\n</div>'''
    insert = '''<div class="screen daily-room-view" id="bowerRoomView" hidden>\n  <div class="daily-room-app">\n    <iframe class="daily-room-frame" id="bowerRoomFrame" title="Greenman Practical Woodcraft Bower"></iframe>\n    <button type="button" class="daily-room-return" id="backFromBowerRoom" aria-label="Back to Hedgewitch Cupboard" title="Back to Hedgewitch Cupboard">←</button>\n  </div>\n</div>\n<div class="screen daily-room-view" id="scribeRoomView" hidden>\n  <div class="daily-room-app">\n    <iframe class="daily-room-frame" id="scribeRoomFrame" title="Greenman Scribe"></iframe>\n    <button type="button" class="daily-room-return" id="backFromScribeRoom" aria-label="Back to Hedgewitch Cupboard" title="Back to Hedgewitch Cupboard">←</button>\n  </div>\n</div>\n''' + anchor
    cup = replace_once(cup, anchor, insert, 'room containers')

    anchor = """const spellView=document.getElementById('spellView');\nconst runeHallView=document.getElementById('runeHallView');\nconst crystalTumblerView=document.getElementById('crystalTumblerView');\nconst runeHallFrame=document.getElementById('runeHallFrame');\nconst crystalTumblerFrame=document.getElementById('crystalTumblerFrame');"""
    insert = """const spellView=document.getElementById('spellView');\nconst bowerRoomView=document.getElementById('bowerRoomView');\nconst scribeRoomView=document.getElementById('scribeRoomView');\nconst runeHallView=document.getElementById('runeHallView');\nconst crystalTumblerView=document.getElementById('crystalTumblerView');\nconst bowerRoomFrame=document.getElementById('bowerRoomFrame');\nconst scribeRoomFrame=document.getElementById('scribeRoomFrame');\nconst runeHallFrame=document.getElementById('runeHallFrame');\nconst crystalTumblerFrame=document.getElementById('crystalTumblerFrame');"""
    cup = replace_once(cup, anchor, insert, 'DOM refs')

    anchor = """function appendDailyDrawers(){\n  const row=document.createElement('section');row.className='daily-drawer-row';"""
    feature_fn = """function appendBowerScribeRooms(){\n  const row=document.createElement('section');row.className='feature-room-row';\n\n  const bower=document.createElement('button');\n  bower.type='button';bower.className='feature-room-entry bower-entry';bower.setAttribute('aria-label','Enter the Bower');\n  bower.innerHTML='<span class="bower-vines vine-left"></span><span class="bower-vines vine-right"></span><span class="bower-arch"><span class="bower-depth"></span></span><span class="feature-room-plaque">THE BOWER</span>';\n  bower.addEventListener('click',openBowerRoom);\n\n  const scribe=document.createElement('button');\n  scribe.type='button';scribe.className='feature-room-entry scribe-entry';scribe.setAttribute('aria-label',\"Open the Scribe's Desk\");\n  scribe.innerHTML='<span class="scribe-desk-lid"><span class="scribe-keyhole"></span><span class="scribe-quill">✒</span></span><span class="feature-room-plaque">THE SCRIBE</span>';\n  scribe.addEventListener('click',openScribeRoom);\n\n  row.appendChild(bower);row.appendChild(scribe);hedgeShelvesEl.appendChild(row);\n}\n\n""" + anchor
    cup = replace_once(cup, anchor, feature_fn, 'feature function')

    anchor = """  appendOwnedShelf('Crystals','Crystal','Crystal');\n  appendOwnedShelf('Herbs','Herb','Herb');\n  appendIncenseDrawerFront();"""
    insert = """  appendOwnedShelf('Crystals','Crystal','Crystal');\n  appendOwnedShelf('Herbs','Herb','Herb');\n  appendBowerScribeRooms();\n  appendIncenseDrawerFront();"""
    cup = replace_once(cup, anchor, insert, 'render placement')

    anchor = """function setCupboardView(view){\n  const next=view==='supply'?'supply':view==='spell'?'spell':view==='incense'?'incense':view==='runeHall'?'runeHall':view==='crystalTumbler'?'crystalTumbler':'hedge';"""
    insert = """function setCupboardView(view){\n  const next=view==='supply'?'supply':view==='spell'?'spell':view==='incense'?'incense':view==='bowerRoom'?'bowerRoom':view==='scribeRoom'?'scribeRoom':view==='runeHall'?'runeHall':view==='crystalTumbler'?'crystalTumbler':'hedge';"""
    cup = replace_once(cup, anchor, insert, 'view enum')

    anchor = """  const gmWasRuneHall=!runeHallView.hidden;\n  const gmWasCrystalTumbler=!crystalTumblerView.hidden;\n  hedgeView.hidden=next!=='hedge';incenseView.hidden=next!=='incense';supplyView.hidden=next!=='supply';spellView.hidden=next!=='spell';\n  runeHallView.hidden=next!=='runeHall';crystalTumblerView.hidden=next!=='crystalTumbler';"""
    insert = """  const gmWasBowerRoom=!bowerRoomView.hidden;\n  const gmWasScribeRoom=!scribeRoomView.hidden;\n  const gmWasRuneHall=!runeHallView.hidden;\n  const gmWasCrystalTumbler=!crystalTumblerView.hidden;\n  hedgeView.hidden=next!=='hedge';incenseView.hidden=next!=='incense';supplyView.hidden=next!=='supply';spellView.hidden=next!=='spell';\n  bowerRoomView.hidden=next!=='bowerRoom';scribeRoomView.hidden=next!=='scribeRoom';\n  runeHallView.hidden=next!=='runeHall';crystalTumblerView.hidden=next!=='crystalTumbler';"""
    cup = replace_once(cup, anchor, insert, 'view hidden')

    anchor = """  if(gmWasRuneHall&&next!=='runeHall'&&runeHallFrame){\n    try{runeHallFrame.removeAttribute('srcdoc');delete runeHallFrame.dataset.loaded;}catch(_gmUnloadErr){}\n  }"""
    insert = """  if(gmWasBowerRoom&&next!=='bowerRoom'&&bowerRoomFrame){\n    try{bowerRoomFrame.removeAttribute('src');delete bowerRoomFrame.dataset.loaded;}catch(_gmUnloadErr){}\n  }\n  if(gmWasScribeRoom&&next!=='scribeRoom'&&scribeRoomFrame){\n    try{scribeRoomFrame.removeAttribute('src');delete scribeRoomFrame.dataset.loaded;}catch(_gmUnloadErr){}\n  }\n""" + anchor
    cup = replace_once(cup, anchor, insert, 'room unload')

    anchor = """  if(next==='runeHall')loadDailyRoom(runeHallFrame,RUNE_HALL_ROOM_B64);\n  if(next==='crystalTumbler')loadDailyRoom(crystalTumblerFrame,CRYSTAL_TUMBLER_ROOM_B64);"""
    insert = """  if(next==='bowerRoom'&&bowerRoomFrame&&bowerRoomFrame.dataset.loaded!=='1'){bowerRoomFrame.src='bower.html';bowerRoomFrame.dataset.loaded='1';}\n  if(next==='scribeRoom'&&scribeRoomFrame&&scribeRoomFrame.dataset.loaded!=='1'){scribeRoomFrame.src='scribe.html';scribeRoomFrame.dataset.loaded='1';}\n  if(next==='runeHall')loadDailyRoom(runeHallFrame,RUNE_HALL_ROOM_B64);\n  if(next==='crystalTumbler')loadDailyRoom(crystalTumblerFrame,CRYSTAL_TUMBLER_ROOM_B64);"""
    cup = replace_once(cup, anchor, insert, 'room loaders')

    anchor = """function openIncenseDrawer(){setCupboardView('incense')}\nfunction openRuneHall(){setCupboardView('runeHall')}"""
    insert = """function openIncenseDrawer(){setCupboardView('incense')}\nfunction openBowerRoom(){setCupboardView('bowerRoom')}\nfunction openScribeRoom(){setCupboardView('scribeRoom')}\nfunction openRuneHall(){setCupboardView('runeHall')}"""
    cup = replace_once(cup, anchor, insert, 'open functions')

    anchor = """['backToHedge','backFromSpellCupboard','backFromIncenseDrawer','backFromRuneHall','backFromCrystalTumbler'].forEach(function(id){"""
    insert = """['backToHedge','backFromSpellCupboard','backFromIncenseDrawer','backFromBowerRoom','backFromScribeRoom','backFromRuneHall','backFromCrystalTumbler'].forEach(function(id){"""
    cup = replace_once(cup, anchor, insert, 'back buttons')

    css = r'''
<style id="greenman-bower-scribe-cupboard-v1">
/* Bower + Scribe are furniture/architecture, not menu tiles. */
.feature-room-row{position:relative;display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0 0 12px;padding:8px 7px 11px;border-top:8px solid #180804;border-bottom:12px solid #170703;background:linear-gradient(90deg,#190904,#4a210d 9%,#261006 50%,#4a210d 91%,#190904);box-shadow:inset 0 10px 20px rgba(0,0,0,.62),0 6px 10px rgba(0,0,0,.46)}
.feature-room-entry{position:relative;height:112px;min-height:112px;border:4px solid #1f0d05;border-radius:7px;background:#241006;padding:0;overflow:hidden;cursor:pointer;box-shadow:inset 0 0 0 2px rgba(190,137,68,.15),inset 0 0 24px #0009,0 4px 7px #0008;-webkit-tap-highlight-color:transparent}
.feature-room-entry:active{transform:translateY(2px)}
.feature-room-plaque{position:absolute;z-index:8;left:50%;bottom:6px;transform:translateX(-50%);min-width:76%;padding:4px 7px;border:2px solid #271208;border-radius:4px;background:linear-gradient(#865528,#4a2813);color:#f0d59a;text-align:center;font:700 clamp(10px,2.8vw,15px)/1.1 Georgia,serif;letter-spacing:.08em;text-shadow:0 1px 2px #000;box-shadow:0 3px 6px #0009}
.bower-entry{background:radial-gradient(ellipse at 50% 42%,#31533a 0,#183122 42%,#09140e 77%)}
.bower-arch{position:absolute;left:18%;right:18%;top:8%;bottom:18%;border:8px solid #4a2d17;border-radius:48% 48% 11% 11% / 38% 38% 10% 10%;background:radial-gradient(ellipse at 50% 55%,rgba(118,171,91,.30),transparent 40%),linear-gradient(#0b1810,#1a3524 55%,#07110b);box-shadow:inset 0 0 22px #000,0 4px 8px #0008}
.bower-depth{position:absolute;inset:10% 13% 8%;border-radius:48% 48% 8% 8% / 37% 37% 8% 8%;background:repeating-linear-gradient(105deg,transparent 0 12px,rgba(60,101,61,.45) 13px 17px,transparent 18px 30px),radial-gradient(ellipse at 50% 78%,#536e3c 0 10%,transparent 11%),linear-gradient(#0e2116,#2b5736 47%,#102218);box-shadow:inset 0 0 15px #000b}
.bower-vines{position:absolute;z-index:4;top:3%;bottom:17%;width:26%;background:radial-gradient(ellipse at 28% 12%,#7fa65a 0 10%,transparent 11%),radial-gradient(ellipse at 72% 27%,#477535 0 11%,transparent 12%),radial-gradient(ellipse at 32% 45%,#6e9b4e 0 10%,transparent 11%),radial-gradient(ellipse at 68% 65%,#365e2d 0 10%,transparent 11%),radial-gradient(ellipse at 35% 83%,#719d4d 0 10%,transparent 11%)}
.bower-vines.vine-left{left:2%}.bower-vines.vine-right{right:2%;transform:scaleX(-1)}
.scribe-entry{background:linear-gradient(90deg,#2d1509,#70401c 20%,#4a250f 51%,#774720 80%,#291207)}
.scribe-desk-lid{position:absolute;left:6%;right:6%;top:8%;bottom:19%;border:5px solid #2a1207;border-radius:6px;background:repeating-linear-gradient(0deg,rgba(255,235,184,.025) 0 2px,transparent 2px 12px),linear-gradient(90deg,#4a220d,#8a5225 25%,#603316 52%,#91592a 77%,#3d1b0b);box-shadow:inset 0 0 0 3px rgba(213,162,84,.12),inset 0 0 17px #0007,0 5px 8px #0008}
.scribe-desk-lid:before{content:"";position:absolute;left:7%;right:7%;top:14%;bottom:15%;border:2px solid rgba(202,151,76,.28);border-radius:4px}
.scribe-keyhole{position:absolute;left:50%;bottom:13%;width:13px;height:18px;transform:translateX(-50%);background:radial-gradient(circle at 50% 28%,#170905 0 31%,transparent 34%),linear-gradient(90deg,transparent 36%,#170905 37% 63%,transparent 64%);filter:drop-shadow(0 1px 1px rgba(220,172,91,.3))}
.scribe-quill{position:absolute;left:50%;top:43%;transform:translate(-50%,-50%) rotate(-16deg);color:#e4c98b;font-size:43px;line-height:1;text-shadow:0 2px 2px #000,0 0 5px rgba(230,194,121,.15)}
@media(max-width:640px){.feature-room-row{gap:5px;padding:6px 4px 9px;border-top-width:6px;border-bottom-width:10px}.feature-room-entry{height:96px;min-height:96px}.bower-arch{left:17%;right:17%;border-width:6px}.scribe-quill{font-size:37px}.feature-room-plaque{bottom:5px;font-size:clamp(9px,3.1vw,13px)}}
</style>
'''
    css_anchor = '<style id="greenman-v36-correct-daily-drawers-and-half-incense-shelf">'
    cup = replace_once(cup, css_anchor, css + css_anchor, 'CSS anchor')

    for required in (
        'bowerRoomView', 'scribeRoomView', 'openBowerRoom', 'openScribeRoom',
        "bowerRoomFrame.src='bower.html'", "scribeRoomFrame.src='scribe.html'",
        'feature-room-row', 'RUNE_HALL_ROOM_B64', 'CRYSTAL_TUMBLER_ROOM_B64'
    ):
        if required not in cup:
            raise RuntimeError(f'missing required marker after patch: {required}')
    return cup


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('index_html')
    ap.add_argument('--report', default='')
    args = ap.parse_args()
    path = Path(args.index_html)
    text = path.read_text(encoding='utf-8')

    assign = 'PAGES.cupboard = '
    pos = text.find(assign)
    if pos < 0:
        raise RuntimeError('authoritative PAGES.cupboard assignment missing')
    start = pos + len(assign)
    old_cup, rel_end = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(old_cup, str) or 'Hedgewitch Cupboard' not in old_cup:
        raise RuntimeError('authoritative cupboard page could not be decoded')

    new_cup = patch_cupboard(old_cup)
    end = start + rel_end
    new_text = text[:start] + json.dumps(new_cup, ensure_ascii=False, separators=(',', ':')) + text[end:]
    path.write_text(new_text, encoding='utf-8')

    check = path.read_text(encoding='utf-8')
    check_start = check.find(assign) + len(assign)
    check_cup, _ = json.JSONDecoder().raw_decode(check[check_start:])
    if check_cup != new_cup:
        raise RuntimeError('cupboard serialization verification failed')

    report = {
        'baseline_index_bytes': len(text.encode('utf-8')),
        'patched_index_bytes': len(new_text.encode('utf-8')),
        'baseline_cupboard_chars': len(old_cup),
        'patched_cupboard_chars': len(new_cup),
        'markers': {
            'bower': 'bowerRoomView' in new_cup,
            'scribe': 'scribeRoomView' in new_cup,
            'rune_hall_preserved': 'RUNE_HALL_ROOM_B64' in new_cup,
            'crystal_tumbler_preserved': 'CRYSTAL_TUMBLER_ROOM_B64' in new_cup,
        }
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'PATCH_FAILED: {exc}', file=sys.stderr)
        raise
