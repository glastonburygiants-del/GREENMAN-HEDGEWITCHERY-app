from pathlib import Path
import json
import hashlib
import sys

src_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
outer = src_path.read_text(encoding="utf-8")
marker = "PAGES.cupboard = "
idx = outer.index(marker) + len(marker)
while outer[idx].isspace():
    idx += 1
cup, consumed = json.JSONDecoder().raw_decode(outer[idx:])

start = cup.index("function renderNav(){")
end = cup.index("function approvedEmptyJarSymbol", start)
nav = cup[start:end]
if nav.count("    render();") != 3:
    raise RuntimeError("Supply navigation render calls did not match the protected baseline")
nav = nav.replace("    render();", "    queueSupplyRender();")
cup = cup[:start] + nav + cup[end:]

rs_start = cup.index("function renderShelves(){")
rs_end = cup.index("let artworkUseCounter=0;", rs_start)
new_render = r'''let gmSupplyRenderGeneration=0;
let gmSupplyRenderFrame=0;
let gmSupplyRendering=false;
let gmSupplyNeedsRender=true;

function gmSupplyNextFrame(callback){
  const raf=window.requestAnimationFrame||function(fn){return window.setTimeout(fn,16)};
  return raf.call(window,callback);
}
function gmSupplyCancelFrame(handle){
  if(!handle)return;
  try{
    const cancel=window.cancelAnimationFrame||window.clearTimeout;
    cancel.call(window,handle);
  }catch(_e){}
}
function queueSupplyRender(){
  renderNav();
  gmSupplyNeedsRender=true;
  if(supplyView.hidden)return;
  if(gmSupplyRenderFrame)gmSupplyCancelFrame(gmSupplyRenderFrame);
  gmSupplyRenderFrame=gmSupplyNextFrame(function(){
    gmSupplyRenderFrame=0;
    renderShelves();
  });
}
function cancelSupplyRenderForRoomChange(){
  if(!gmSupplyRendering&&!gmSupplyRenderFrame)return;
  gmSupplyRenderGeneration++;
  gmSupplyRendering=false;
  gmSupplyNeedsRender=true;
  if(gmSupplyRenderFrame){
    gmSupplyCancelFrame(gmSupplyRenderFrame);
    gmSupplyRenderFrame=0;
  }
  shelvesEl.removeAttribute('aria-busy');
}
function renderShelves(){
  const generation=++gmSupplyRenderGeneration;
  const groups=currentGroups();
  const pendingCardWork=[];
  const totalItems=groups.reduce((groupTotal,group)=>groupTotal+group.shelves.reduce((shelfTotal,shelf)=>shelfTotal+shelf.items.length,0),0);
  let renderedItems=0;
  gmSupplyRendering=true;
  gmSupplyNeedsRender=false;
  shelvesEl.setAttribute('aria-busy','true');
  shelvesEl.innerHTML='';
  try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Supply Cupboard','Item render started',{generation,totalItems,filter:state.filter,mode:state.mode},'',false);}catch(_gmDiagErr){}
  groups.forEach(group=>{
    const wrapper=document.createElement('section');wrapper.className='association-group';
    const groupTitle=document.createElement('div');groupTitle.className='group-title';groupTitle.textContent=group.title;
    wrapper.appendChild(groupTitle);
    const emptyCount=group.shelves.filter(shelf=>!shelf.items.length).length;
    const useDecorativeFill=state.mode==='All Items'&&(state.filter==='Element'||state.filter==='Planet')&&emptyCount===2;
    let decorativeIndex=0;
    group.shelves.forEach(shelf=>{
      const section=document.createElement('section');section.className='shelf';
      const title=document.createElement('div');title.className='shelf-title';title.textContent=shelf.title;
      const track=document.createElement('div');track.className='item-track';track.dataset.shelfKey=shelf.key;track.addEventListener('scroll',onTrackScroll,{passive:true});
      if(shelf.items.length){
        section.appendChild(title);
        section.appendChild(track);
        pendingCardWork.push({track:track,items:shelf.items.slice()});
      }else if(useDecorativeFill){
        section.classList.add('decorative-shelf');
        section.innerHTML=decorativeShelfScene(decorativeIndex===0?'vessels':'bags-cauldron');
        decorativeIndex++;
      }else{
        section.appendChild(title);
        section.appendChild(track);
      }
      wrapper.appendChild(section);
    });
    shelvesEl.appendChild(wrapper);
  });

  function finishSupplyRender(){
    if(generation!==gmSupplyRenderGeneration)return;
    gmSupplyRenderFrame=0;
    gmSupplyRendering=false;
    gmSupplyNeedsRender=false;
    shelvesEl.removeAttribute('aria-busy');
    gmSupplyNextFrame(restoreTrackScrolls);
    try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Supply Cupboard','All items rendered',{generation,renderedItems,totalItems,filter:state.filter,mode:state.mode},'',false);}catch(_gmDiagErr){}
  }
  function gmProcessNextCardBatch(){
    gmSupplyRenderFrame=0;
    if(generation!==gmSupplyRenderGeneration)return;
    if(supplyView.hidden){
      gmSupplyRendering=false;
      gmSupplyNeedsRender=true;
      shelvesEl.removeAttribute('aria-busy');
      return;
    }
    const batchStart=(window.performance&&performance.now)?performance.now():Date.now();
    let cardsThisFrame=0;
    while(pendingCardWork.length){
      const job=pendingCardWork[0];
      const item=job.items.shift();
      if(item){
        job.track.appendChild(buildCard(item));
        renderedItems++;
        cardsThisFrame++;
      }
      if(!job.items.length)pendingCardWork.shift();
      const now=(window.performance&&performance.now)?performance.now():Date.now();
      if(cardsThisFrame>=2||now-batchStart>=6)break;
    }
    if(pendingCardWork.length){
      gmSupplyRenderFrame=gmSupplyNextFrame(gmProcessNextCardBatch);
    }else{
      finishSupplyRender();
    }
  }
  if(pendingCardWork.length){
    gmSupplyRenderFrame=gmSupplyNextFrame(gmProcessNextCardBatch);
  }else{
    finishSupplyRender();
  }
}
'''
cup = cup[:rs_start] + new_render + cup[rs_end:]

old_header = """function setCupboardView(view){
  const next=view==='supply'?'supply':view==='spell'?'spell':view==='incense'?'incense':view==='runeHall'?'runeHall':view==='crystalTumbler'?'crystalTumbler':'hedge';
  gmCurrentCupboardView=next;"""
new_header = """function setCupboardView(view){
  const next=view==='supply'?'supply':view==='spell'?'spell':view==='incense'?'incense':view==='runeHall'?'runeHall':view==='crystalTumbler'?'crystalTumbler':'hedge';
  const previous=gmCurrentCupboardView;
  if(previous==='supply'&&next!=='supply')cancelSupplyRenderForRoomChange();
  gmCurrentCupboardView=next;"""
if old_header not in cup:
    raise RuntimeError("Cupboard view owner did not match the protected baseline")
cup = cup.replace(old_header, new_header, 1)

old_special = """  if(next==='spell'){showSpellCategories();renderSpellCupboard()}
  if(next==='incense')renderIncenseDrawer();
  if(next==='runeHall')loadDailyRoom(runeHallFrame,RUNE_HALL_ROOM_B64);
  if(next==='crystalTumbler')loadDailyRoom(crystalTumblerFrame,CRYSTAL_TUMBLER_ROOM_B64);"""
new_special = """  if(next==='spell'){showSpellCategories();renderSpellCupboard()}
  if(next==='incense')renderIncenseDrawer();
  if(next==='supply'){
    if(gmSupplyNeedsRender||!shelvesEl.children.length)queueSupplyRender();
    else gmSupplyNextFrame(restoreTrackScrolls);
  }
  if(next==='runeHall')loadDailyRoom(runeHallFrame,RUNE_HALL_ROOM_B64);
  if(next==='crystalTumbler')loadDailyRoom(crystalTumblerFrame,CRYSTAL_TUMBLER_ROOM_B64);"""
if old_special not in cup:
    raise RuntimeError("Cupboard room activation block did not match the protected baseline")
cup = cup.replace(old_special, new_special, 1)

old_render = "function render(){renderNav();renderShelves();renderHedgewitch();renderSpellCupboard();}"
new_render_fn = "function render(){renderNav();renderHedgewitch();renderSpellCupboard();gmSupplyNeedsRender=true;}"
if old_render not in cup:
    raise RuntimeError("Cupboard initial render did not match the protected baseline")
cup = cup.replace(old_render, new_render_fn, 1)

encoded = json.dumps(cup, ensure_ascii=False).replace("</script>", "<\\/script>")
new_outer = outer[:idx] + encoded + outer[idx + consumed:]

check_idx = new_outer.index(marker) + len(marker)
while new_outer[check_idx].isspace():
    check_idx += 1
check_cup, check_consumed = json.JSONDecoder().raw_decode(new_outer[check_idx:])
for required in ("Item render started", "All items rendered", "cancelSupplyRenderForRoomChange", "cardsThisFrame>=2"):
    if required not in check_cup:
        raise RuntimeError("Supply repair verification failed: " + required)
if "(window.requestIdleCallback||window.requestAnimationFrame).call(window,gmProcessNextCardBatch)" in check_cup:
    raise RuntimeError("Old Supply Cupboard idle scheduler remains")
if "</script>" in new_outer[check_idx:check_idx + check_consumed]:
    raise RuntimeError("An inner script closer was not escaped")

out_path.write_text(new_outer, encoding="utf-8")
print("Supply Cupboard room repair applied")
print("HTML SHA-256:", hashlib.sha256(new_outer.encode()).hexdigest())
