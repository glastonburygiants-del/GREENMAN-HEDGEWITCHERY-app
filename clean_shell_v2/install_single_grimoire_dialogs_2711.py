#!/usr/bin/env python3
from pathlib import Path
import json, re, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: install_single_grimoire_dialogs_2711.py INPUT OUTPUT')

src=Path(sys.argv[1]); out=Path(sys.argv[2])
s=src.read_text(encoding='utf-8')
marker='const PAGES = '
st=s.index(marker)+len(marker)
pages,end=json.JSONDecoder().raw_decode(s[st:])
if 'bos' not in pages:
    raise SystemExit('missing PAGES.bos')

# Grimoire: one A4 page for every entry. Fit text inside its own boxes and never
# split a Grimoire record or scale the whole sheet down.
bos=pages['bos']
bos=re.sub(r'\n?<style id="gm-grimoire-pagination-v1">.*?</style>\n?', '\n', bos, flags=re.S)
old_selector='.a4-page:not(.gm-flat):not(.gm-book-front):not(.gm-book-frontmatter)'
new_selector='.a4-page:not(.gm-flat):not(.gm-book-front):not(.gm-book-frontmatter):not(.grimoire-page):not(.summary-page)'
if new_selector not in bos:
    if old_selector not in bos:
        raise SystemExit('2.7.11: whole-book fitter selector anchor missing')
    bos=bos.replace(old_selector,new_selector,1)

builder_start=bos.index('function buildGrimoirePages(e){')
builder_stop=bos.index('\n\nfunction fitTextInsideBox',builder_start)
new_builder=r'''function buildGrimoirePages(e){
  const item=e.grimoireItem||e.item||{},title=item.Name||item.name||e.spellName||'Grimoire Entry';
  const magicalUses=item['Magical Uses']||item.magicalUses||'';
  const powers=item.Powers||item.powers||'';
  const green=item['Greenman Energy']||item.greenmanEnergy||item.green||'';
  const correspondences=[item.Element,item.Planet,item.Day,item.Number,item.Gender].filter(Boolean).join(' · ');
  const associated=associatedText(item);
  const description=item.Description||item.description||'';
  const folklore=item['Folk Lore']||item.folklore||'';
  const geology=item.Geology||item.Origin||'';
  const warning=item.Warning||item.warning||'';
  const identity=`<div class="parch-box"><div class="pp-section-title">Identity</div>${infoRow('Category',e.category)}${infoRow('Name',item.Name||item.name)}${infoRow('Ye Olde Name',item['Ye Olde Name']||item.old||item.yeOlde)}${infoRow('Latin',item.Latin||item['Latin Name']||item.latin)}</div>`;
  const magicalBox=`<div class="grimoire-info"><div class="grimoire-info-label">Magical Uses</div><div class="grimoire-info-text">${esc(magicalUses)}</div></div>`;
  const one=pageHead(title,'Grimoire Entry','1 of 1')+
  `<main class="grimoire-layout gm-grimoire-one-layout">
    <div class="grimoire-identity-notes">${identity}${hedgeNotesBox(e)}</div>
    <div class="grimoire-magical-full">${magicalBox}</div>
    <div class="grimoire-grid gm-grimoire-one-grid">
      ${gBlock('Powers',powers)}
      ${gBlock('Greenman Energy',green,'green')}
      ${gBlock('Correspondences',correspondences,'wide')}
      ${gBlock('Associated Items',associated,'wide')}
      ${gBlock('Description',description,'wide')}
      ${gBlock('Folk Lore',folklore,'wide')}
      ${gBlock('Geology / Origin',geology,'wide')}
      ${gBlock('Warning',warning,'wide')}
    </div>
  </main>`;
  return pageFrame(one,true,'grimoire-page gm-grimoire-native gm-grimoire-one');
}'''
bos=bos[:builder_start]+new_builder+bos[builder_stop:]
if 'const minimum=magical?6.8:7.6;' in bos:
    bos=bos.replace('const minimum=magical?6.8:7.6;','const minimum=magical?6.3:6.8;',1)
elif 'const minimum=magical?6.3:6.8;' not in bos:
    raise SystemExit('2.7.11: Grimoire text fitter minimum anchor missing')

fit_start=bos.index('function fitGrimoirePages(root=document){')
fit_stop=bos.index('\n\nfunction fitSummaryPages',fit_start)
new_fit=r'''function fitGrimoirePages(root=document){
  qsa('.grimoire-page',root).forEach(page=>{
    page.style.setProperty('--grimoire-fit-scale','1');
    fitAllGrimoireInfoBoxes(page);
    requestAnimationFrame(()=>fitAllGrimoireInfoBoxes(page));
    setTimeout(()=>fitAllGrimoireInfoBoxes(page),80);
  });
}'''
bos=bos[:fit_start]+new_fit+bos[fit_stop:]

single_css=r'''
<style id="gm-grimoire-single-page-v2">
.gm-grimoire-one .a4-content{transform:none!important;width:100%!important;height:100%!important;}
.gm-grimoire-one .gm-grimoire-one-layout{height:calc(100% - 72px)!important;display:grid!important;grid-template-rows:112px 230px minmax(0,1fr)!important;gap:6px!important;overflow:hidden!important;}
.gm-grimoire-one .grimoire-identity-notes{display:grid!important;grid-template-columns:1fr 1fr!important;gap:6px!important;height:112px!important;min-height:112px!important;overflow:hidden!important;}
.gm-grimoire-one .grimoire-identity-notes>.parch-box,.gm-grimoire-one .grimoire-identity-notes>.hedge-notes-box{height:112px!important;min-height:112px!important;max-height:112px!important;overflow:hidden!important;}
.gm-grimoire-one .grimoire-magical-full,.gm-grimoire-one .grimoire-magical-full>.grimoire-info{height:230px!important;min-height:230px!important;max-height:230px!important;}
.gm-grimoire-one .gm-grimoire-one-grid{display:grid!important;grid-template-columns:1fr 1fr!important;grid-template-rows:125px 95px 150px 150px minmax(100px,1fr)!important;gap:6px!important;min-height:0!important;overflow:hidden!important;}
.gm-grimoire-one .gm-grimoire-one-grid>.grimoire-info{height:auto!important;min-height:0!important;max-height:none!important;grid-column:auto!important;}
.gm-grimoire-one .gm-grimoire-one-grid>.grimoire-info:nth-child(1){grid-column:1!important;grid-row:1!important;}
.gm-grimoire-one .gm-grimoire-one-grid>.grimoire-info:nth-child(2){grid-column:2!important;grid-row:1!important;}
.gm-grimoire-one .gm-grimoire-one-grid>.grimoire-info:nth-child(3){grid-column:1!important;grid-row:2!important;}
.gm-grimoire-one .gm-grimoire-one-grid>.grimoire-info:nth-child(4){grid-column:2!important;grid-row:2!important;}
.gm-grimoire-one .gm-grimoire-one-grid>.grimoire-info:nth-child(5){grid-column:1 / -1!important;grid-row:3!important;}
.gm-grimoire-one .gm-grimoire-one-grid>.grimoire-info:nth-child(6){grid-column:1 / -1!important;grid-row:4!important;}
.gm-grimoire-one .gm-grimoire-one-grid>.grimoire-info:nth-child(7){grid-column:1!important;grid-row:5!important;}
.gm-grimoire-one .gm-grimoire-one-grid>.grimoire-info:nth-child(8){grid-column:2!important;grid-row:5!important;}
.gm-grimoire-one .grimoire-info{padding:6px!important;}
</style>
'''
if 'gm-grimoire-single-page-v2' not in bos:
    bos=bos.replace('</head>',single_css+'</head>',1)
pages['bos']=bos

# Greenman-styled replacement for browser-native alert/confirm UI. The visible card
# lives once in the outer shell, so it remains visible even if an embedded page
# navigates immediately after raising a notice.
DIALOG_CSS=r'''
<style id="gm-greenman-dialog-style">
#gm-greenman-dialog{position:fixed;inset:0;z-index:2147483000;display:none;align-items:center;justify-content:center;padding:20px;background:rgba(0,0,0,.76)}
#gm-greenman-dialog.gm-show{display:flex}
#gm-greenman-dialog-card{width:min(430px,100%);background:#f5ead0;color:#1a0e04;border:3px solid #c9a84c;border-radius:14px;padding:22px 20px;box-shadow:0 14px 38px rgba(0,0,0,.62);font-family:Georgia,serif}
#gm-greenman-dialog-title{font-family:Cinzel,Georgia,serif;font-size:18px;line-height:1.2;letter-spacing:.055em;text-align:center;color:#2d4a1e;margin:0 0 12px}
#gm-greenman-dialog-text{font-size:16px;line-height:1.48;color:#3a2010;margin:0 0 18px;white-space:pre-line;text-align:left}
#gm-greenman-dialog-actions{display:grid;grid-template-columns:1fr;gap:9px}
#gm-greenman-dialog-actions.gm-two{grid-template-columns:1fr 1fr}
#gm-greenman-dialog-actions button{min-height:48px;border-radius:8px;border:2px solid #8a6030;padding:9px 8px;font-family:Cinzel,Georgia,serif;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}
#gm-greenman-dialog-primary{background:#2d4a1e;color:#f5ead0;border-color:#c9a84c!important}
#gm-greenman-dialog-secondary{background:#e8c040;color:#1a0e04}
@media(max-width:420px){#gm-greenman-dialog-actions.gm-two{grid-template-columns:1fr}#gm-greenman-dialog-card{padding:19px 16px}}
@media print{#gm-greenman-dialog{display:none!important}}
</style>
'''
DIALOG_JS=r'''
(function(){
  if(window.__GM_GREENMAN_DIALOG_OWNER__)return;
  window.__GM_GREENMAN_DIALOG_OWNER__=true;
  function ensureGreenmanDialog(){
    var overlay=document.getElementById('gm-greenman-dialog');
    if(overlay)return overlay;
    overlay=document.createElement('div');
    overlay.id='gm-greenman-dialog';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');
    overlay.innerHTML='<div id="gm-greenman-dialog-card"><h2 id="gm-greenman-dialog-title">Greenman HedgeWitchery</h2><div id="gm-greenman-dialog-text"></div><div id="gm-greenman-dialog-actions"></div></div>';
    document.body.appendChild(overlay);return overlay;
  }
  function closeGreenmanDialog(){var o=document.getElementById('gm-greenman-dialog');if(o)o.classList.remove('gm-show');}
  window.gmGreenmanNotice=function(message,title){
    var o=ensureGreenmanDialog(),t=o.querySelector('#gm-greenman-dialog-title'),x=o.querySelector('#gm-greenman-dialog-text'),a=o.querySelector('#gm-greenman-dialog-actions');
    t.textContent=title||'Greenman HedgeWitchery';x.textContent=String(message==null?'':message);a.className='';a.innerHTML='<button id="gm-greenman-dialog-primary" type="button">Continue</button>';
    a.firstElementChild.onclick=function(){closeGreenmanDialog();};o.classList.add('gm-show');try{a.firstElementChild.focus();}catch(_e){}
  };
  window.gmGreenmanConfirm=function(message,onYes,yesLabel,noLabel,title){
    var o=ensureGreenmanDialog(),t=o.querySelector('#gm-greenman-dialog-title'),x=o.querySelector('#gm-greenman-dialog-text'),a=o.querySelector('#gm-greenman-dialog-actions');
    t.textContent=title||'Greenman HedgeWitchery';x.textContent=String(message==null?'':message);a.className='gm-two';
    a.innerHTML='<button id="gm-greenman-dialog-primary" type="button"></button><button id="gm-greenman-dialog-secondary" type="button"></button>';
    var yes=a.querySelector('#gm-greenman-dialog-primary'),no=a.querySelector('#gm-greenman-dialog-secondary');yes.textContent=yesLabel||'Yes';no.textContent=noLabel||'Cancel';
    yes.onclick=function(){closeGreenmanDialog();if(typeof onYes==='function')onYes();};no.onclick=function(){closeGreenmanDialog();};o.classList.add('gm-show');try{yes.focus();}catch(_e){}
  };
  window.alert=function(message){window.gmGreenmanNotice(message);};
})();
'''
DIALOG_SHIM=r'''
(function(){
  if(window.__GM_GREENMAN_DIALOG_SHIM__)return;window.__GM_GREENMAN_DIALOG_SHIM__=true;
  var nativeAlert=window.alert,nativeConfirm=window.confirm;
  window.alert=function(message){try{if(parent&&parent!==window&&typeof parent.gmGreenmanNotice==='function'){parent.gmGreenmanNotice(message);return;}}catch(_e){}nativeAlert(message);};
  window.gmGreenmanConfirm=function(message,onYes,yesLabel,noLabel,title){try{if(parent&&parent!==window&&typeof parent.gmGreenmanConfirm==='function'){parent.gmGreenmanConfirm(message,onYes,yesLabel,noLabel,title);return;}}catch(_e){}if(nativeConfirm(message)&&typeof onYes==='function')onYes();};
})();
'''

def replace_once(text,old,new,label):
    n=text.count(old)
    if n!=1:
        raise SystemExit(f'{label} anchor count {n}, expected 1')
    return text.replace(old,new,1)

admin=pages['admin']
admin=replace_once(admin,
"function resetCurrentGroup(){if(!confirm('Reset '+currentStockGroup+' to starting quantities?'))return;const s=stock();(STOCK_MASTER[currentStockGroup]||[]).forEach(n=>s[currentStockGroup][n]=startQty(currentStockGroup));saveStock(s);renderStock();renderLowStock();toast('Group reset')}",
"function resetCurrentGroup(){gmGreenmanConfirm('Reset '+currentStockGroup+' to starting quantities?',function(){const s=stock();(STOCK_MASTER[currentStockGroup]||[]).forEach(n=>s[currentStockGroup][n]=startQty(currentStockGroup));saveStock(s);renderStock();renderLowStock();toast('Group reset')},'Reset','Cancel')}",
'admin resetCurrentGroup')
admin=replace_once(admin,
"function resetAllStock(){if(!confirm('Reset ALL stock to starting quantities?'))return;setJSON(K_STOCK,defaultStock());renderAll();toast('All stock reset')}",
"function resetAllStock(){gmGreenmanConfirm('Reset ALL stock to starting quantities?',function(){setJSON(K_STOCK,defaultStock());renderAll();toast('All stock reset')},'Reset All','Cancel')}",
'admin resetAllStock')
admin=replace_once(admin,
"function resetSundriesGroup(){if(!confirm('Reset all sundries to 21?'))return;const s=stock();s.Sundries={};(STOCK_MASTER.Sundries||[]).forEach(n=>s.Sundries[n]=21);saveStock(s);renderSundries();renderStock();renderLowStock();renderDashboard();toast('Sundries reset')}",
"function resetSundriesGroup(){gmGreenmanConfirm('Reset all sundries to 21?',function(){const s=stock();s.Sundries={};(STOCK_MASTER.Sundries||[]).forEach(n=>s.Sundries[n]=21);saveStock(s);renderSundries();renderStock();renderLowStock();renderDashboard();toast('Sundries reset')},'Reset','Cancel')}",
'admin resetSundriesGroup')
old_clear="""window.gmClearAllStorage = function(){
  if(!confirm('Clear ALL app data? This cannot be undone.')) return;
  var keysToKeep = ['gm_app_mode','greenman_full_app_unlocked','greenman_full_app_unlocked','gm_admin_pin'];
  var keep = {};
  keysToKeep.forEach(function(k){ try{keep[k]=localStorage.getItem(k);}catch(e){} });
  try{ localStorage.clear(); }catch(e){}
  Object.keys(keep).forEach(function(k){ if(keep[k]!=null) try{localStorage.setItem(k,keep[k]);}catch(e){} });
  alert('App data cleared. Mode and unlock keys preserved.');
  try{parent.postMessage({source:'greenman-new-shell-v1',cmd:'nav',target:'admin'},'*');}catch(e){location.reload();}
};"""
new_clear="""window.gmClearAllStorage = function(){
  gmGreenmanConfirm('Clear ALL app data? This cannot be undone.',function(){
    var keysToKeep = ['gm_app_mode','greenman_full_app_unlocked','greenman_full_app_unlocked','gm_admin_pin'];
    var keep = {};
    keysToKeep.forEach(function(k){ try{keep[k]=localStorage.getItem(k);}catch(e){} });
    try{ localStorage.clear(); }catch(e){}
    Object.keys(keep).forEach(function(k){ if(keep[k]!=null) try{localStorage.setItem(k,keep[k]);}catch(e){} });
    alert('App data cleared. Mode and unlock keys preserved.');
    try{parent.postMessage({source:'greenman-new-shell-v1',cmd:'nav',target:'admin'},'*');}catch(e){location.reload();}
  },'Clear Data','Cancel');
};"""
admin=replace_once(admin,old_clear,new_clear,'admin clear all storage')
pages['admin']=admin

bos=pages['bos']
old_delete="function deleteActiveEntry(){if(!activeEntryId)return;if(!confirm('Delete this entry from your Book of Shadows?'))return;try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','BoS','Entry deleted',{entryId:activeEntryId},'',false);}catch(_gmDiagErr){}var all=readLS(LS_ENTRIES,[]).filter(Boolean);all=all.filter(function(e){return String(e.entryId||e.id||'')!==String(activeEntryId);});try{localStorage.setItem(LS_ENTRIES,JSON.stringify(all));}catch(ex){}showHome();}"
new_delete="function deleteActiveEntry(){if(!activeEntryId)return;gmGreenmanConfirm('Delete this entry from your Book of Shadows?',function(){try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','BoS','Entry deleted',{entryId:activeEntryId},'',false);}catch(_gmDiagErr){}var all=readLS(LS_ENTRIES,[]).filter(Boolean);all=all.filter(function(e){return String(e.entryId||e.id||'')!==String(activeEntryId);});try{localStorage.setItem(LS_ENTRIES,JSON.stringify(all));}catch(ex){}showHome();},'Delete','Keep Entry');}"
bos=replace_once(bos,old_delete,new_delete,'BoS delete confirmation')
pages['bos']=bos

# Tiny iframe shim on pages that use alert(). No duplicate dialog styling is added.
for key,html in list(pages.items()):
    if not re.search(r'\balert\s*\(',html):
        continue
    if '__GM_GREENMAN_DIALOG_SHIM__' not in html:
        pos=html.rfind('</script>')
        if pos<0:
            raise SystemExit('dialog page missing script: '+key)
        html=html[:pos]+'\n'+DIALOG_SHIM+'\n'+html[pos:]
    pages[key]=html

remaining=[key for key,html in pages.items() if re.search(r'\bconfirm\s*\(',html)]
if remaining:
    raise SystemExit('native confirm remains in: '+','.join(remaining))

new_json=json.dumps(pages,ensure_ascii=False,separators=(',',':'))
s=s[:st]+new_json+s[st+end:]

# Add the visible dialog owner to the outer shell exactly once.
head_pos=s.find('</head>',0,st)
if head_pos<0:
    raise SystemExit('outer shell missing </head>')
if 'gm-greenman-dialog-style' not in s[:st]:
    s=s[:head_pos]+DIALOG_CSS+s[head_pos:]
if 'gm-greenman-shell-dialog' not in s:
    shell_script='<script id="gm-greenman-shell-dialog">'+DIALOG_JS+'</script>\n'
    body_pos=s.rfind('</body>')
    if body_pos<0:
        raise SystemExit('outer shell missing </body>')
    s=s[:body_pos]+shell_script+s[body_pos:]

for term in ('gm-grimoire-single-page-v2','gm-grimoire-one','gm-greenman-dialog-style','__GM_GREENMAN_DIALOG_OWNER__','__GM_GREENMAN_DIALOG_SHIM__'):
    if term not in s:
        raise SystemExit('missing 2.7.11 guard: '+term)
for bad in ('gm-grimoire-split-1','gm-grimoire-split-2',"'1 of 2'","'2 of 2'"):
    if bad in pages['bos']:
        raise SystemExit('abandoned Grimoire split marker remains: '+bad)

out.write_text(s,encoding='utf-8')
print('Installed 2.7.11: every Grimoire entry remains one A4 page; native grey alert/confirm dialogs replaced with Greenman-styled cards')
