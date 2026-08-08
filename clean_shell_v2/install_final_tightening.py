#!/usr/bin/env python3
from pathlib import Path
import json,re,sys

if len(sys.argv)!=3:
    raise SystemExit('usage: install_final_tightening.py INPUT OUTPUT')

src=Path(sys.argv[1]); out=Path(sys.argv[2])
s=src.read_text(encoding='utf-8')

# ---------- helpers ----------
def replace_once(text, old, new, label):
    n=text.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 anchor, found {n}')
    return text.replace(old,new,1)

def inject_before(text, marker, addition, label):
    i=text.rfind(marker)
    if i<0: raise SystemExit(f'{label}: marker not found')
    return text[:i]+addition+text[i:]

# ---------- parse embedded pages ----------
marker='const PAGES = '
start=s.index(marker)+len(marker)
obj,end=json.JSONDecoder().raw_decode(s[start:])
required={'admin','bos','spellBuilder','grimoire'}
if not required.issubset(obj):
    raise SystemExit('required embedded pages missing')
admin=obj['admin']; bos=obj['bos']; spell=obj['spellBuilder']; grimoire=obj['grimoire']

# ---------- extract canonical Grimoire item names only ----------
mi=grimoire.index('const ITEMS =')+len('const ITEMS =')
items,_=json.JSONDecoder().raw_decode(grimoire[mi:].lstrip())
families=['Herb','Crystal','Rune','Oil','Deity']
name_lib={fam:[str(x.get('_name') or x.get('Name') or '').strip() for x in items if x.get('_category')==fam and str(x.get('_name') or x.get('Name') or '').strip()] for fam in families}
for fam in families:
    name_lib[fam]=sorted(dict.fromkeys(name_lib[fam]),key=lambda x:x.casefold())

# ---------- ADMIN: Sundries refresh ----------
admin=replace_once(admin,
"function changeStock(g,n,delta){const s=stock();s[g][n]=Math.max(0,Number(s[g][n]||0)+delta);saveStock(s);renderStock();renderLowStock()}",
"function changeStock(g,n,delta){const s=stock();s[g][n]=Math.max(0,Number(s[g][n]||0)+delta);saveStock(s);renderStock();if(g==='Sundries')renderSundries();renderLowStock();renderDashboard()}",
'Sundries plus/minus refresh')
admin=replace_once(admin,
"function setStockQty(g,n){const el=document.getElementById('set_'+safeId(g,n));const s=stock();s[g][n]=Math.max(0,Number(el.value||0));saveStock(s);renderStock();renderLowStock();toast('Stock updated')}",
"function setStockQty(g,n){const el=document.getElementById('set_'+safeId(g,n));const s=stock();s[g][n]=Math.max(0,Number(el.value||0));saveStock(s);renderStock();if(g==='Sundries')renderSundries();renderLowStock();renderDashboard();toast('Stock updated')}",
'Sundries Set refresh')
admin=replace_once(admin,
"function replenishCheckedStock(){const checked=[...document.querySelectorAll('.low-check:checked')];if(!checked.length)return toast('No low stock ticked');const mode=document.getElementById('replenishMode').value;const s=stock();checked.forEach(c=>{const [g,n]=c.value.split('||');if(!s[g])s[g]={};if(mode==='plus7')s[g][n]=Number(s[g][n]||0)+7;else if(mode==='plus21')s[g][n]=Number(s[g][n]||0)+21;else s[g][n]=startQty(g)});saveStock(s);renderLowStock();renderStock();toast('Checked stock replenished')}",
"function replenishCheckedStock(){const checked=[...document.querySelectorAll('.low-check:checked')];if(!checked.length)return toast('No low stock ticked');const mode=document.getElementById('replenishMode').value;const s=stock();checked.forEach(c=>{const [g,n]=c.value.split('||');if(!s[g])s[g]={};if(mode==='plus7')s[g][n]=Number(s[g][n]||0)+7;else if(mode==='plus21')s[g][n]=Number(s[g][n]||0)+21;else s[g][n]=startQty(g)});saveStock(s);renderLowStock();renderStock();renderSundries();renderDashboard();toast('Checked stock replenished')}",
'Sundries low-stock replenish refresh')

# ---------- ADMIN: Greenman Book Printer ----------
admin=replace_once(admin,
'''<section class="panel" id="masterTools"><div class="card"><h2 style="color:#e8c040;">✦ Master Tools ✦</h2><div class="button-row"><button class="btn red" onclick="gmClearAllStorage()">⚠ Clear All App Data (Keep Mode)</button><button class="btn green" onclick="gmClearSpellState()">✦ Clear Stuck Test Data Only</button></div><p style="font-size:12px;color:#a08040;margin-top:8px;font-style:italic;">Clear All keeps mode &amp; PIN. Clear Test Data removes only current spell state.</p></div></section>''',
'''<section class="panel" id="masterTools"><div class="card"><h2 style="color:#e8c040;">✦ Master Tools ✦</h2><div class="button-row"><button class="btn red" onclick="gmClearAllStorage()">⚠ Clear All App Data (Keep Mode)</button><button class="btn green" onclick="gmClearSpellState()">✦ Clear Stuck Test Data Only</button><button class="btn green" onclick="gmOpenBookPrinter()">📖 Greenman Book Printer</button></div><p style="font-size:12px;color:#a08040;margin-top:8px;font-style:italic;">Clear All keeps mode &amp; PIN. Clear Test Data removes only current spell state.</p></div></section>
<div id="gmBookPrinterOverlay" class="gm-book-printer-overlay" aria-hidden="true"><section class="gm-book-printer-card" role="dialog" aria-modal="true" aria-labelledby="gmBookPrinterTitle"><header><h2 id="gmBookPrinterTitle">✦ Greenman Book Printer ✦</h2><p>Choose the Grimoire sections for this book. Tick a section, give it an order number, then choose all items or individual entries.</p></header><div class="gm-book-printer-fields"><label>Book title<input id="gmBookTitle" value="Greenman HedgeWitchery Grimoire"/></label><label>Subtitle<input id="gmBookSubtitle" value="A Greenman reference book"/></label></div><div id="gmBookPrinterRows"></div><div class="gm-book-printer-actions"><button class="btn ghost" type="button" onclick="gmCloseBookPrinter()">Close</button><button class="btn green" type="button" onclick="gmStartBookPrinter()">Build &amp; Print Book</button></div></section></div>''',
'Admin Master Tools Book Printer button')

admin_css=r'''
<style id="gm-admin-book-printer-style">
.gm-book-printer-overlay{position:fixed;inset:0;z-index:999999;background:rgba(0,0,0,.78);display:none;align-items:center;justify-content:center;padding:12px}.gm-book-printer-overlay.open{display:flex}.gm-book-printer-card{width:min(760px,98vw);max-height:92vh;overflow:auto;background:#f6ead0;color:#271505;border:4px solid #c9a84c;border-radius:14px;padding:16px;box-shadow:0 18px 50px rgba(0,0,0,.7)}.gm-book-printer-card h2{margin:0;text-align:center;color:#2d4a1e;font-family:Georgia,serif;font-size:23px}.gm-book-printer-card header p{margin:6px 0 12px;text-align:center;font-size:13px;color:#65451b}.gm-book-printer-fields{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px}.gm-book-printer-fields label{font-size:11px;font-weight:700;color:#5a3a08}.gm-book-printer-fields input{width:100%;margin-top:3px}.gm-book-row{border:1px solid rgba(138,96,48,.45);border-radius:9px;background:#fff8df;margin:7px 0;padding:8px}.gm-book-row-main{display:grid;grid-template-columns:auto minmax(120px,1fr) 74px minmax(145px,.8fr);align-items:center;gap:7px}.gm-book-row-main .gm-book-name{font-family:Georgia,serif;font-size:15px;font-weight:700;color:#2d4a1e}.gm-book-order{width:70px!important}.gm-book-choose{margin-top:8px;display:none;max-height:190px;overflow:auto;border-top:1px solid rgba(138,96,48,.35);padding-top:7px;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px}.gm-book-choose.open{display:grid}.gm-book-item-check{display:flex;align-items:flex-start;gap:5px;background:#f3e4bd;border-radius:5px;padding:5px;font-size:11px;line-height:1.15}.gm-book-printer-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;position:sticky;bottom:-16px;background:#f6ead0;padding:10px 0 0;margin-top:10px}@media(max-width:560px){.gm-book-printer-fields{grid-template-columns:1fr}.gm-book-row-main{grid-template-columns:auto 1fr 62px}.gm-book-row-main select{grid-column:2/4}.gm-book-choose{grid-template-columns:1fr}.gm-book-printer-card{padding:12px}}
</style>
'''
admin=admin.replace('</head>',admin_css+'</head>',1)

admin_js='''
<script id="gm-admin-book-printer-v1">
(function(){
'use strict';
const LIBRARY=__LIBRARY__;
const SECTIONS=[['Herb','Herbs'],['Crystal','Crystals'],['Oil','Oils'],['Rune','Runes'],['Deity','Deities']];
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
window.gmRenderBookPrinter=function(){
 var host=document.getElementById('gmBookPrinterRows');if(!host)return;
 host.innerHTML=SECTIONS.map(function(row,i){var key=row[0],label=row[1],names=LIBRARY[key]||[];return '<div class="gm-book-row" data-book-section="'+key+'"><div class="gm-book-row-main"><input type="checkbox" class="gm-book-on" '+(i===0?'checked':'')+'><span class="gm-book-name">'+esc(label)+'</span><input class="gm-book-order" type="number" min="1" max="99" value="'+(i+1)+'" title="Book order"><select class="gm-book-mode" onchange="gmBookModeChanged(this)"><option value="all">All '+esc(label)+'</option><option value="choose">Choose individual items</option></select></div><div class="gm-book-choose">'+names.map(function(name){return '<label class="gm-book-item-check"><input type="checkbox" value="'+esc(name)+'"><span>'+esc(name)+'</span></label>';}).join('')+'</div></div>';}).join('');
};
window.gmBookModeChanged=function(sel){var row=sel.closest('.gm-book-row'),box=row&&row.querySelector('.gm-book-choose');if(box)box.classList.toggle('open',sel.value==='choose');};
window.gmOpenBookPrinter=function(){gmRenderBookPrinter();var o=document.getElementById('gmBookPrinterOverlay');o.classList.add('open');o.setAttribute('aria-hidden','false');};
window.gmCloseBookPrinter=function(){var o=document.getElementById('gmBookPrinterOverlay');o.classList.remove('open');o.setAttribute('aria-hidden','true');};
window.gmStartBookPrinter=function(){
 var rows=Array.from(document.querySelectorAll('#gmBookPrinterRows .gm-book-row')),sections=[];
 rows.forEach(function(row){if(!row.querySelector('.gm-book-on').checked)return;var key=row.getAttribute('data-book-section'),mode=row.querySelector('.gm-book-mode').value,order=Math.max(1,Number(row.querySelector('.gm-book-order').value||99)),names=[];if(mode==='choose')names=Array.from(row.querySelectorAll('.gm-book-choose input:checked')).map(function(x){return x.value;});sections.push({key:key,mode:mode,order:order,names:names});});
 if(!sections.length){toast('Tick at least one book section');return;}
 sections.sort(function(a,b){return a.order-b.order;});
 var req={version:1,title:String(document.getElementById('gmBookTitle').value||'Greenman HedgeWitchery Grimoire').trim(),subtitle:String(document.getElementById('gmBookSubtitle').value||'').trim(),sections:sections,createdAt:new Date().toISOString()};
 try{localStorage.setItem('gm_admin_book_print_request',JSON.stringify(req));}catch(e){toast('Could not prepare book request');return;}
 gmCloseBookPrinter();toast('Book choices saved. Opening the Grimoire printer…');
 setTimeout(function(){try{parent.postMessage({source:'greenman-new-shell-v1',cmd:'nav',target:'grimoire'},'*');}catch(e){}},180);
};
})();
</script>
'''.replace('__LIBRARY__',json.dumps(name_lib,ensure_ascii=False,separators=(',',':')))
admin=inject_before(admin,'</body>',admin_js,'Admin Book Printer JS')

# ---------- SPELL BUILDER: one current spell/method title owner ----------
old_title='''  window.GM_PRINT_HEADER_TITLE=function(sp){
    if(window.GM_INSTRUCTION_RENDER_CONTEXT){
      var live=window.GM_INSTRUCTION_RENDER_CONTEXT;
      return text(live.spell)+(text(live.method)?' · '+text(live.method):'');
    }
    sp=sp||state();
    var spell=text((sp.sd||{}).Spell||sp.selectedSpell||sp.spell||sp.category||'Spell');
    var type=method(sp);
    return type ? spell+' · '+type : spell;
  };'''
new_title='''  window.GM_PRINT_HEADER_TITLE=function(sp){
    sp=sp||state();
    /* Final identity owner: always derive the title from the current spell state.
       Do not reuse an older instruction render context or the broad category title. */
    var spell=text(sp.spell||sp.selectedSpell||(sp.sd||{}).Spell||sp.category||'Spell');
    var type=method(sp);
    return type ? spell+' · '+type : spell;
  };'''
spell=replace_once(spell,old_title,new_title,'Spell/Method print identity owner')

# ---------- BoS: robust flat fit ----------
fit_start=bos.index('function fitFlatPages(root){')
fit_end=bos.index('\nfunction gmFlatPrint(area){',fit_start)
new_fit=r'''function fitFlatPages(root){
  qsa('.gm-flat .true-page',root).forEach(function(pg){
    var c=pg.querySelector('.true-content')||pg.firstElementChild;if(!c)return;
    var cs=c.style,availH=pg.clientHeight||1058,availW=pg.clientWidth||756;
    function reset(){cs.setProperty('transform','none','important');cs.setProperty('transform-origin','top left','important');cs.setProperty('height','auto','important');cs.setProperty('min-height','0','important');cs.setProperty('max-height','none','important');}
    function measure(){
      var base=c.getBoundingClientRect(),needH=Math.max(c.scrollHeight||0,c.offsetHeight||0,availH),needW=Math.max(c.scrollWidth||0,c.offsetWidth||0,availW);
      var nodes=c.querySelectorAll('*');
      for(var i=0;i<nodes.length;i++){var r=nodes[i].getBoundingClientRect();if(!r.width&&!r.height)continue;needH=Math.max(needH,r.bottom-base.top);needW=Math.max(needW,r.right-base.left);}
      return {h:needH,w:needW};
    }
    reset();pg.style.setProperty('--summary-fit-scale','1','important');
    var lo=.25,hi=1,best=.25;
    for(var n=0;n<12;n++){
      var mid=(lo+hi)/2;reset();cs.setProperty('width',(100/mid).toFixed(3)+'%','important');void c.offsetHeight;var m=measure();
      if(m.h*mid<=availH-8 && m.w*mid<=availW-8){best=mid;lo=mid;}else hi=mid;
    }
    var safe=Math.max(.25,Math.min(1,best-.006));reset();cs.setProperty('width',(100/safe).toFixed(3)+'%','important');cs.setProperty('transform','scale('+safe.toFixed(4)+')','important');
    pg.setAttribute('data-gm-print-fit',safe.toFixed(4));
  });
}
'''
bos=bos[:fit_start]+new_fit+bos[fit_end:]

# ---------- BoS: front cover, contents, real item index, continuous page numbers ----------
icon_file=Path(__file__).with_name('greenman_custom_app_icon_192_webp.b64')
icon_b64=''
if icon_file.exists(): icon_b64=''.join(icon_file.read_text().split())

bos_css=r'''
<style id="gm-final-book-style-v1">
.gm-book-front{background:radial-gradient(circle at 50% 34%,rgba(232,192,64,.14),transparent 34%),linear-gradient(180deg,#241608,#3a2a10 46%,#211306)!important;color:#faf6ec!important;border:4px double #c9a84c!important}.gm-book-cover-inner{height:100%;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:70px 55px}.gm-book-cover-mark{width:172px;height:172px;object-fit:cover;border-radius:34px;border:3px solid #c9a84c;box-shadow:0 0 34px rgba(232,192,64,.24);margin:20px 0}.gm-book-cover-title{font-family:Georgia,serif;color:#e8c040;font-size:42px;line-height:1.08;letter-spacing:.04em}.gm-book-cover-sub{font-family:Georgia,serif;font-style:italic;color:#f6ead0;font-size:20px;line-height:1.35;margin-top:14px}.gm-book-cover-symbol{position:absolute;top:50%;transform:translateY(-50%);font-size:118px;color:#e8c040;opacity:.10}.gm-book-cover-symbol.left{left:26px}.gm-book-cover-symbol.right{right:26px}.gm-book-frontmatter .a4-content{padding:54px 58px!important}.gm-book-front-title{font-family:Georgia,serif;color:#3a2109;font-size:32px;text-align:center;border-bottom:2px solid #8a6030;padding-bottom:12px;margin-bottom:22px}.gm-book-content-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;border-bottom:1px dotted rgba(90,58,8,.45);padding:6px 2px;font-family:Georgia,serif;font-size:14px;line-height:1.2}.gm-book-content-row small{display:block;color:#7a5a30;font-style:italic;margin-top:2px}.gm-book-index-family{font-family:Georgia,serif;color:#2d4a1e;font-size:20px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin:13px 0 5px;border-bottom:1px solid #c9a84c;padding-bottom:4px}.gm-book-index-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;padding:3px 2px;border-bottom:1px dotted rgba(90,58,8,.3);font-family:Georgia,serif;font-size:12.5px}.gm-book-page-number{position:absolute!important;left:50%!important;bottom:7mm!important;transform:translateX(-50%)!important;z-index:999!important;font-family:Georgia,serif!important;font-size:10px!important;color:#6c512b!important;background:rgba(255,250,236,.78)!important;border-radius:999px!important;padding:2px 7px!important;pointer-events:none!important}.gm-book-front .gm-book-page-number{display:none!important}.gm-book-preparing{position:fixed;inset:0;z-index:999999;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.72)}.gm-book-preparing.show{display:flex}.gm-book-preparing-card{width:min(430px,90vw);background:#1a3010;color:#fff3cf;border:3px solid #c9a84c;border-radius:14px;padding:22px;text-align:center;font-family:Georgia,serif;font-size:18px;font-weight:700;box-shadow:0 12px 35px rgba(0,0,0,.55)}@media print{.gm-book-preparing{display:none!important}.gm-book-page-number{display:block!important}}
</style>
'''
bos=bos.replace('</head>',bos_css+'</head>',1)

bos_js=r'''
<script id="gm-final-book-owner-v1">
(function(){
'use strict';
const INDEX_LIBRARY=__INDEX_LIBRARY__;
const FAMILY_LABELS={Herb:'Herbs',Crystal:'Crystals',Rune:'Runes',Oil:'Oils',Deity:'Deities'};
const FAMILY_ORDER=['Herb','Crystal','Rune','Oil','Deity'];
const COVER_ICON='__ICON_DATA__';
function h(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function exactHas(text,name){var e=String(name).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');try{return new RegExp('(^|[^A-Za-z0-9])'+e+'(?=$|[^A-Za-z0-9])','i').test(text);}catch(_e){return false;}}
function entryTitle(e){if(!e)return'Book of Shadows Entry';if(e.entryType==='grimoire')return String(e.spellName||((e.grimoireItem||e.item||{})._name)||((e.grimoireItem||e.item||{}).Name)||'Grimoire Entry');if(e.entryType==='incenseBlend')return String(e.spellName||e.name||'Incense Blend');if(e.entryType==='timing')return String(e.spellName||e.name||e.category||'Timing');return String(e.spellName||e.name||'Spell');}
function entryMeta(e){if(!e)return'';if(e.entryType==='grimoire')return String(e.category||'Grimoire');if(e.entryType==='incenseBlend')return'Incense Blend';if(e.entryType==='timing')return String(e.category||'Timing');return [e.method,e.category].filter(Boolean).join(' · ');}
function preparing(on){var o=document.getElementById('gmBookPreparing');if(!o){o=document.createElement('div');o.id='gmBookPreparing';o.className='gm-book-preparing';o.innerHTML='<div class="gm-book-preparing-card">The Greenman is binding your Book of Shadows…</div>';document.body.appendChild(o);}o.classList.toggle('show',!!on);}
function coverPage(){var icon=COVER_ICON?'<img class="gm-book-cover-mark" alt="Greenman" src="'+COVER_ICON+'">':'<div class="gm-book-cover-mark" style="display:flex;align-items:center;justify-content:center;font-size:72px;background:#2d4a1e">✦</div>';return '<section class="a4-page gm-book-front"><div class="a4-content"><div class="gm-book-cover-inner"><span class="gm-book-cover-symbol left">☽</span><span class="gm-book-cover-symbol right">☀</span><div class="gm-book-cover-title">Greenman<br>Book of Shadows</div>'+icon+'<div class="gm-book-cover-sub">Your record of spells cast and magic worked.</div></div></div></section>';}
function frontPage(title,body,extra){return '<section class="a4-page gm-book-frontmatter '+(extra||'')+'"><div class="a4-content"><div class="gm-book-front-title">'+h(title)+'</div>'+body+'</div></section>';}
function chunk(list,size){var out=[];for(var i=0;i<list.length;i+=size)out.push(list.slice(i,i+size));return out.length?out:[[]];}
function makeContents(rows,contentStart){var pages=chunk(rows,28),out=[];pages.forEach(function(pg,pi){var body=pg.map(function(r){return '<div class="gm-book-content-row"><div>'+h(r.title)+(r.meta?'<small>'+h(r.meta)+'</small>':'')+'</div><strong>'+String(contentStart+r.offset)+'</strong></div>';}).join('');out.push(frontPage('Contents'+(pages.length>1?' · '+(pi+1)+' of '+pages.length:''),body,'gm-book-contents'));});return out;}
function scanIndex(contentPages,firstContentPage){var map={};FAMILY_ORDER.forEach(function(f){map[f]={};});contentPages.forEach(function(page,i){var txt=' '+String(page.textContent||'').replace(/\s+/g,' ').trim()+' ',num=firstContentPage+i;FAMILY_ORDER.forEach(function(f){(INDEX_LIBRARY[f]||[]).forEach(function(name){if(exactHas(txt,name)){(map[f][name]||(map[f][name]=[])).push(num);}});});});return map;}
function compress(nums){nums=Array.from(new Set(nums)).sort(function(a,b){return a-b;});var out=[];for(var i=0;i<nums.length;){var a=nums[i],b=a;while(i+1<nums.length&&nums[i+1]===b+1){i++;b=nums[i];}out.push(a===b?String(a):a+'–'+b);i++;}return out.join(', ');}
function indexRows(map){var rows=[];FAMILY_ORDER.forEach(function(f){var names=Object.keys(map[f]||{}).filter(function(n){return map[f][n]&&map[f][n].length;}).sort(function(a,b){return a.localeCompare(b,undefined,{sensitivity:'base'});});if(!names.length)return;rows.push({family:f,label:FAMILY_LABELS[f],heading:true});names.forEach(function(n){rows.push({family:f,name:n,pages:compress(map[f][n])});});});return rows;}
function makeIndex(map){var rows=indexRows(map),pages=[],current=[],count=0;rows.forEach(function(r){var cost=r.heading?2:1;if(count+cost>34&&current.length){pages.push(current);current=[];count=0;}current.push(r);count+=cost;});if(current.length)pages.push(current);if(!pages.length)pages=[[]];return pages.map(function(pg,pi){var body=pg.map(function(r){return r.heading?'<div class="gm-book-index-family">'+h(r.label)+'</div>':'<div class="gm-book-index-row"><span>'+h(r.name)+'</span><strong>'+h(r.pages)+'</strong></div>';}).join('');return frontPage('Item Index'+(pages.length>1?' · '+(pi+1)+' of '+pages.length:''),body,'gm-book-index');});}
function fitGenerated(root){qsa('.a4-page:not(.gm-flat):not(.gm-book-front):not(.gm-book-frontmatter)',root).forEach(function(pg){var c=pg.querySelector('.a4-content');if(!c)return;var cs=c.style,ah=pg.clientHeight||1123,aw=pg.clientWidth||794;function reset(){cs.setProperty('transform','none','important');cs.setProperty('transform-origin','top left','important');cs.setProperty('height','auto','important');cs.setProperty('min-height','0','important');cs.setProperty('max-height','none','important');}function measure(){var base=c.getBoundingClientRect(),needH=Math.max(c.scrollHeight||0,c.offsetHeight||0,ah),needW=Math.max(c.scrollWidth||0,c.offsetWidth||0,aw),nodes=c.querySelectorAll('*');for(var j=0;j<nodes.length;j++){var r=nodes[j].getBoundingClientRect();if(!r.width&&!r.height)continue;needH=Math.max(needH,r.bottom-base.top);needW=Math.max(needW,r.right-base.left);}return{h:needH,w:needW};}reset();var lo=.30,hi=1,best=.30;for(var i=0;i<12;i++){var mid=(lo+hi)/2;reset();cs.setProperty('width',(100/mid).toFixed(3)+'%','important');void c.offsetHeight;var m=measure();if(m.h*mid<=ah-12&&m.w*mid<=aw-12){best=mid;lo=mid;}else hi=mid;}var sc=Math.max(.30,Math.min(1,best-.008));reset();cs.setProperty('width',(100/sc).toFixed(3)+'%','important');cs.setProperty('transform','scale('+sc.toFixed(4)+')','important');pg.setAttribute('data-gm-book-fit',sc.toFixed(4));});}
function numberPages(area){var pages=qsa('.a4-page',area),num=0;pages.forEach(function(pg){if(pg.classList.contains('gm-book-front'))return;num++;var foot=document.createElement('div');foot.className='gm-book-page-number';foot.textContent=String(num);pg.appendChild(foot);});return num;}
window.gmPrintBookOfShadows=function(){
 if(bosIsLiteMode())return;preparing(true);setTimeout(function(){
  try{
   var list=entries(),area=qs('#printArea');area.innerHTML='';var scratch=document.createElement('div'),rows=[],offset=0;
   list.forEach(function(e){var before=qsa('.a4-page',scratch).length;if(hasBosSnapshot(e))appendFlatSnapshot(scratch,e,null);else scratch.insertAdjacentHTML('beforeend',buildEntryPages(e));var after=qsa('.a4-page',scratch).length;rows.push({title:entryTitle(e),meta:entryMeta(e),offset:offset});offset+=Math.max(0,after-before);});
   var contentPages=qsa('.a4-page',scratch);var contentsCount=Math.max(1,Math.ceil(rows.length/28)),firstContent=contentsCount+1;
   area.insertAdjacentHTML('beforeend',coverPage());makeContents(rows,firstContent).forEach(function(x){area.insertAdjacentHTML('beforeend',x);});
   while(scratch.firstChild)area.appendChild(scratch.firstChild);
   var realContent=qsa('.a4-page',area).filter(function(pg){return !pg.classList.contains('gm-book-front')&&!pg.classList.contains('gm-book-frontmatter');});
   var map=scanIndex(realContent,firstContent);makeIndex(map).forEach(function(x){area.insertAdjacentHTML('beforeend',x);});
   document.body.classList.add('gm-bos-fitting');void document.body.offsetHeight;try{fitSummaryPages(area);}catch(e){}try{fitGrimoirePages(area);}catch(e){}try{fitFlatPages(area);}catch(e){}try{fitGenerated(area);}catch(e){}numberPages(area);document.body.classList.remove('gm-bos-fitting');preparing(false);setTimeout(function(){window.print();},160);
  }catch(err){preparing(false);console.error('Greenman BoS book build failed',err);alert('The Book of Shadows could not be prepared.');}
 },70);
};
window.printAll=window.gmPrintBookOfShadows;
})();
</script>
'''
icon_data=('data:image/webp;base64,'+icon_b64) if icon_b64 else ''
bos_js=bos_js.replace('__INDEX_LIBRARY__',json.dumps(name_lib,ensure_ascii=False,separators=(',',':'))).replace('__ICON_DATA__',icon_data)
bos=inject_before(bos,'</body>',bos_js,'BoS final book owner')

# ---------- GRIMOIRE: Admin/Master custom book printer ----------
grimoire_css=r'''
<style id="gm-admin-book-print-style-v1">
#gmAdminBookPrintArea{display:none}.gm-admin-book-status{position:fixed;inset:0;z-index:999999;background:rgba(0,0,0,.78);display:none;align-items:center;justify-content:center}.gm-admin-book-status.show{display:flex}.gm-admin-book-status>div{width:min(430px,90vw);background:#1a3010;color:#fff3cf;border:3px solid #c9a84c;border-radius:14px;padding:22px;text-align:center;font-family:Georgia,serif;font-size:18px;font-weight:700}.gm-admin-book-page{position:relative!important}.gm-admin-book-page-number{position:absolute;left:50%;bottom:6mm;transform:translateX(-50%);font-family:Georgia,serif;font-size:10px;color:#68451d;background:rgba(255,250,236,.82);padding:2px 7px;border-radius:999px;z-index:20}.gm-admin-book-cover{background:radial-gradient(circle at 50% 32%,rgba(232,192,64,.17),transparent 34%),linear-gradient(180deg,#241608,#3a2a10 46%,#211306)!important;color:#faf6ec!important;border:4px double #c9a84c!important}.gm-admin-book-cover-inner{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:70px 55px}.gm-admin-book-cover-title{font-family:Georgia,serif;color:#e8c040;font-size:40px;line-height:1.1}.gm-admin-book-cover-sub{font-family:Georgia,serif;color:#f6ead0;font-size:20px;line-height:1.35;font-style:italic;margin-top:16px}.gm-admin-book-front{background:linear-gradient(180deg,#fff7df,#f3e5bd)!important;color:#201105!important;padding:48px 54px!important}.gm-admin-book-front h2{font-family:Georgia,serif;text-align:center;font-size:30px;color:#3a2109;border-bottom:2px solid #8a6030;padding-bottom:12px;margin:0 0 20px}.gm-admin-book-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;border-bottom:1px dotted rgba(90,58,8,.38);padding:5px 0;font-family:Georgia,serif;font-size:13px}.gm-admin-book-section{font-family:Georgia,serif;color:#2d4a1e;font-size:18px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin:11px 0 4px;border-bottom:1px solid #c9a84c;padding-bottom:3px}@media print{body.gm-admin-book-print #gmAdminBookPrintArea{display:block!important}body.gm-admin-book-print .app-header,body.gm-admin-book-print .scroll,body.gm-admin-book-print .bottom-tabbar,body.gm-admin-book-print .sheet-actions,body.gm-admin-book-print .ref-popup,body.gm-admin-book-print .kb,body.gm-admin-book-print .gm-admin-book-status{display:none!important}body.gm-admin-book-print #a4Page{display:none!important}body.gm-admin-book-print #gmAdminBookPrintArea .a4-shell{display:block!important;width:210mm!important;height:297mm!important;min-height:297mm!important;max-height:297mm!important;margin:0!important;border:0!important;border-radius:0!important;box-shadow:none!important;overflow:hidden!important;page-break-after:always!important;break-after:page!important}body.gm-admin-book-print #gmAdminBookPrintArea .a4-shell:last-child{page-break-after:auto!important;break-after:auto!important}.gm-admin-book-cover .gm-admin-book-page-number{display:none!important}}
</style>
'''
grimoire=grimoire.replace('</head>',grimoire_css+'</head>',1)
grimoire=replace_once(grimoire,'<div class="sheet-actions" id="sheetActions">','<div id="gmAdminBookPrintArea"></div><div id="gmAdminBookStatus" class="gm-admin-book-status"><div>The Greenman is preparing your master book…</div></div><div class="sheet-actions" id="sheetActions">','Grimoire master print hosts')

grimoire_js=r'''
<script id="gm-admin-master-book-owner-v1">
(function(){
'use strict';
const KEY='gm_admin_book_print_request';
const FAMILY_LABELS={Herb:'Herbs',Crystal:'Crystals',Rune:'Runes',Oil:'Oils',Deity:'Deities'};
const FAMILY_ORDER=['Herb','Crystal','Rune','Oil','Deity'];
function esc2(v){return String(v==null?'':v).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function status(on){var el=document.getElementById('gmAdminBookStatus');if(el)el.classList.toggle('show',!!on);}
function stripIds(root){root.removeAttribute&&root.removeAttribute('id');Array.from(root.querySelectorAll('[id]')).forEach(function(x){x.removeAttribute('id');});Array.from(root.querySelectorAll('button')).forEach(function(x){x.remove();});return root;}
function cloneSheet(item){var prev=selected;selected=item;renderSheet();var src=document.getElementById('gmGrimoirePrintSheet'),cl=stripIds(src.cloneNode(true));cl.classList.add('gm-admin-book-page','gm-admin-book-item');cl.setAttribute('data-book-item',String(item._name||item.Name||''));cl.setAttribute('data-book-family',String(item._category||''));selected=prev;renderSheet();return cl;}
function exactHas2(text,name){var e=String(name).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');try{return new RegExp('(^|[^A-Za-z0-9])'+e+'(?=$|[^A-Za-z0-9])','i').test(text);}catch(_e){return false;}}
function compress2(nums){nums=Array.from(new Set(nums)).sort(function(a,b){return a-b;});var out=[];for(var i=0;i<nums.length;){var a=nums[i],b=a;while(i+1<nums.length&&nums[i+1]===b+1){i++;b=nums[i];}out.push(a===b?String(a):a+'–'+b);i++;}return out.join(', ');}
function front(title,body,cls){var p=document.createElement('article');p.className='a4-shell gm-admin-book-page gm-admin-book-front '+(cls||'');p.innerHTML='<h2>'+esc2(title)+'</h2>'+body;return p;}
function cover(req){var p=document.createElement('article');p.className='a4-shell gm-admin-book-page gm-admin-book-cover';p.innerHTML='<div class="gm-admin-book-cover-inner"><div class="gm-admin-book-cover-title">'+esc2(req.title||'Greenman HedgeWitchery Grimoire')+'</div><div class="gm-admin-book-cover-sub">'+esc2(req.subtitle||'A Greenman reference book')+'</div></div>';return p;}
function chunk2(list,size){var out=[];for(var i=0;i<list.length;i+=size)out.push(list.slice(i,i+size));return out.length?out:[[]];}
function selectItems(req){var ordered=[],sections=(req.sections||[]).slice().sort(function(a,b){return (a.order||99)-(b.order||99);});sections.forEach(function(sec){var names=new Set((sec.names||[]).map(function(n){return String(n).toLowerCase();}));var list=ITEMS.filter(function(it){if(it._category!==sec.key)return false;if(sec.mode==='choose')return names.has(String(it._name||it.Name||'').toLowerCase());return true;});ordered.push({key:sec.key,label:FAMILY_LABELS[sec.key]||sec.key,items:list});});return ordered;}
function fitClone(page){var c=page.querySelector('.a4-fit-content');if(!c)return;c.style.transform='none';c.style.width='794px';void c.offsetHeight;var need=Math.max(c.scrollHeight,c.offsetHeight),scale=need>1102?Math.max(.42,1102/need):1;c.style.width=(100/scale).toFixed(3)+'%';c.style.transformOrigin='top left';c.style.transform='scale('+scale.toFixed(4)+')';page.setAttribute('data-gm-admin-fit',scale.toFixed(4));}
function addFoot(page,n){var f=document.createElement('div');f.className='gm-admin-book-page-number';f.textContent=String(n);page.appendChild(f);}
function buildIndex(itemPages,firstPage){var map={};FAMILY_ORDER.forEach(function(f){map[f]={};});var lib={};FAMILY_ORDER.forEach(function(f){lib[f]=ITEMS.filter(function(x){return x._category===f;}).map(function(x){return String(x._name||x.Name||'');}).filter(Boolean);});itemPages.forEach(function(pg,i){var txt=' '+String(pg.textContent||'').replace(/\s+/g,' ').trim()+' ',n=firstPage+i;FAMILY_ORDER.forEach(function(f){lib[f].forEach(function(name){if(exactHas2(txt,name))(map[f][name]||(map[f][name]=[])).push(n);});});});return map;}
function indexPages(map){var rows=[];FAMILY_ORDER.forEach(function(f){var names=Object.keys(map[f]).filter(function(n){return map[f][n].length;}).sort(function(a,b){return a.localeCompare(b,undefined,{sensitivity:'base'});});if(!names.length)return;rows.push({h:true,label:FAMILY_LABELS[f]});names.forEach(function(n){rows.push({name:n,pages:compress2(map[f][n])});});});var pages=[],cur=[],cost=0;rows.forEach(function(r){var c=r.h?2:1;if(cost+c>34&&cur.length){pages.push(cur);cur=[];cost=0;}cur.push(r);cost+=c;});if(cur.length)pages.push(cur);if(!pages.length)pages=[[]];return pages.map(function(pg,i){return front('Item Index'+(pages.length>1?' · '+(i+1)+' of '+pages.length:''),pg.map(function(r){return r.h?'<div class="gm-admin-book-section">'+esc2(r.label)+'</div>':'<div class="gm-admin-book-row"><span>'+esc2(r.name)+'</span><strong>'+esc2(r.pages)+'</strong></div>';}).join(''),'gm-admin-book-index');});}
function build(req){var area=document.getElementById('gmAdminBookPrintArea');area.innerHTML='';var groups=selectItems(req),contents=[];groups.forEach(function(g){contents.push({section:true,label:g.label});g.items.forEach(function(it){contents.push({label:String(it._name||it.Name||''),family:g.label,item:it});});});var contentChunks=chunk2(contents,30),contentsCount=contentChunks.length,firstItem=contentsCount+1,itemOffset=0;area.appendChild(cover(req));contentChunks.forEach(function(ch,i){var body=ch.map(function(r){if(r.section)return '<div class="gm-admin-book-section">'+esc2(r.label)+'</div>';var page=firstItem+(itemOffset++);return '<div class="gm-admin-book-row"><span>'+esc2(r.label)+'</span><strong>'+page+'</strong></div>';}).join('');area.appendChild(front('Contents'+(contentChunks.length>1?' · '+(i+1)+' of '+contentChunks.length:''),body,'gm-admin-book-contents'));});var itemPages=[];groups.forEach(function(g){g.items.forEach(function(it){var p=cloneSheet(it);area.appendChild(p);itemPages.push(p);});});itemPages.forEach(fitClone);var map=buildIndex(itemPages,firstItem);indexPages(map).forEach(function(p){area.appendChild(p);});var n=0;Array.from(area.querySelectorAll('.a4-shell')).forEach(function(p){if(p.classList.contains('gm-admin-book-cover'))return;n++;addFoot(p,n);});}
function run(){var raw='';try{raw=localStorage.getItem(KEY)||'';}catch(e){}if(!raw)return;var req;try{req=JSON.parse(raw);}catch(e){try{localStorage.removeItem(KEY);}catch(_e){}return;}try{localStorage.removeItem(KEY);}catch(_e){}status(true);setTimeout(function(){try{build(req);status(false);document.body.classList.add('gm-admin-book-print');setTimeout(function(){window.print();},150);}catch(err){status(false);console.error('Admin book build failed',err);alert('The master book could not be prepared.');}},100);}
window.addEventListener('afterprint',function(){document.body.classList.remove('gm-admin-book-print');});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(run,180);});else setTimeout(run,180);
})();
</script>
'''
grimoire=inject_before(grimoire,'</body>',grimoire_js,'Grimoire Admin Book Printer JS')

# ---------- put pages back ----------
obj['admin']=admin;obj['bos']=bos;obj['spellBuilder']=spell;obj['grimoire']=grimoire
new_json=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
s=s[:start]+new_json+s[start+end:]

# ---------- remove obsolete outer Journal/BoS print override ----------
pat=re.compile(r'\n?<script id="gm-journal-bos-print-wait-patch-v4">.*?</script>\s*',re.S)
s,n=pat.subn('\n',s,count=1)
if n!=1: raise SystemExit(f'obsolete outer print override removal count {n}')

# ---------- guards ----------
guards=[
 ('book printer button','Greenman Book Printer'),
 ('Sundries live refresh',"if(g==='Sundries')renderSundries()"),
 ('BoS book owner','gm-final-book-owner-v1'),
 ('BoS contents','Item Index'),
 ('Admin master book request','gm_admin_book_print_request'),
 ('Grimoire master book owner','gm-admin-master-book-owner-v1'),
 ('current title owner','Final identity owner'),
]
for label,term in guards:
    if term not in s: raise SystemExit(f'missing {label}')
if 'gm-journal-bos-print-wait-patch-v4' in s: raise SystemExit('obsolete BoS print override still present')

out.write_text(s,encoding='utf-8')
print('Installed final tightening: Sundries refresh, spell identity, BoS book, master book printer, robust page fitting')
print('Grimoire master item counts:',{k:len(v) for k,v in name_lib.items()})
