#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_stocktake_v10_10_manual_stock_sync.py input.html output.html")

src=Path(sys.argv[1]); dst=Path(sys.argv[2])
text=src.read_text(encoding="utf-8")
if "gm-stock-sync-v10-10" in text:
    raise SystemExit("manual Stock Sync patch already present")

# Hide the old connection strip. All stock movement now lives on Stock Sync.
head_anchor="</style></head><body>"
css=r'''
<style id="gm-stock-sync-v10-10">
.gm-connect{display:none!important}
#stocksync{display:none;overflow:auto;height:100%;padding:8px;max-width:1180px;margin:auto;width:100%}
#stocksync.on{display:block}
.sync-note{background:#f4ecd7;border:1px solid var(--line);border-radius:10px;padding:9px;font-size:11px;line-height:1.45;margin:7px 0}
.sync-connections{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:8px 0}
.sync-connection{background:var(--paper);border:1px solid var(--line);border-radius:11px;padding:10px}
.sync-connection h3{margin:0 0 4px;color:var(--green);font-size:15px}
.sync-state{font-size:11px;color:var(--muted);margin:4px 0 8px}
.sync-state.ok{color:var(--green);font-weight:700}
.sync-actions{display:flex;gap:6px;flex-wrap:wrap;margin:7px 0}
.sync-actions button,.sync-actions input{min-height:36px;border:1px solid var(--line);border-radius:8px;background:#fffaf0;padding:6px 8px;font:700 10px Georgia,serif}
.sync-actions button.primary{background:var(--green);color:#fff;border-color:var(--green)}
.sync-actions button:disabled{opacity:.42}
.sync-filters{display:flex;gap:5px;overflow:auto;margin:8px 0;padding-bottom:2px}
.sync-filters button{white-space:nowrap;min-height:34px;border:1px solid var(--line);border-radius:999px;background:var(--paper);padding:5px 9px;font:700 10px Georgia,serif}
.sync-filters button.on{background:var(--green);color:#fff}
.sync-list{display:grid;gap:8px}
.sync-item{background:var(--paper);border:1px solid var(--line);border-radius:11px;padding:10px}
.sync-item.diff{border-left:6px solid #b6782d}
.sync-item.same{border-left:6px solid #4c7756}
.sync-title{display:flex;justify-content:space-between;gap:8px;align-items:flex-start}
.sync-title strong{color:var(--green);font-size:15px}
.sync-title small{color:var(--muted)}
.sync-values{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin:8px 0}
.sync-value{background:#f8f0df;border:1px solid #e2d4b4;border-radius:8px;padding:6px}
.sync-value span{display:block;color:var(--muted);font-size:9px}
.sync-value b{display:block;color:var(--green);font-size:15px;margin-top:2px}
.sync-value.na b{color:#8a8378;font-size:11px}
.sync-sub{font-size:9px;color:var(--muted);margin-top:2px}
.sync-group{border-top:1px solid #e2d4b4;padding-top:7px;margin-top:7px}
.sync-group-label{font-size:9px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.sync-move{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:6px}
.sync-move input{width:68px;min-height:36px;border:1px solid var(--line);border-radius:8px;background:#fff;padding:6px;text-align:center}
.sync-empty{text-align:center;padding:20px;color:var(--muted);background:var(--paper);border:1px solid var(--line);border-radius:10px}
#gmSyncMsg{min-height:18px;font-size:11px;color:var(--green);font-weight:700;margin:6px 0}
#gmSyncMsg.bad{color:#8a3026}
@media(max-width:700px){
 .sync-connections{grid-template-columns:1fr}
 .sync-values{grid-template-columns:repeat(2,minmax(0,1fr))}
 .sync-actions button{flex:1 1 145px}
}
</style>
'''
if head_anchor not in text:
    raise SystemExit("head anchor missing")
text=text.replace(head_anchor,"</style>"+css+"</head><body>",1)

# Add Stock Sync tab.
tabs_anchor='''   <button data-page="summary">Stock Summary</button>
   <button data-page="sales">Sales</button>'''
tabs_new='''   <button data-page="summary">Stock Summary</button>
   <button data-page="stocksync">Stock Sync</button>
   <button data-page="sales">Sales</button>'''
if tabs_anchor not in text:
    raise SystemExit("Stock Sync tab anchor missing")
text=text.replace(tabs_anchor,tabs_new,1)

# Add Stock Sync page before Sales.
section_anchor='''  <section id="sales" class="backoffice">'''
section_markup=r'''  <section id="stocksync">
   <div class="bohead">
    <h2>Stock Sync</h2>
    <div class="sync-note"><b>Manual only.</b> Connecting reads and displays stock. It does not change Stocktake, Wildwood or Supabase. Stock only moves when you press an action and confirm it.</div>
    <div class="sync-connections">
     <div class="sync-connection">
      <h3>Wildwood App</h3>
      <div id="gmSyncWildState" class="sync-state">Not connected</div>
      <div class="sync-actions"><button class="primary" onclick="gmManualConnectWildwood()">CONNECT WILDWOOD APP</button><button onclick="gmOpenGreenmanApp()">OPEN GREENMAN APP</button></div>
     </div>
     <div class="sync-connection">
      <h3>Supabase Online Stock</h3>
      <div id="gmSyncOnlineState" class="sync-state">Not connected</div>
      <div class="sync-actions"><button class="primary" onclick="gmManualConnectSupabase()">CONNECT SUPABASE</button></div>
     </div>
    </div>
    <div id="gmSyncMsg"></div>
    <div class="sync-actions">
     <button id="gmBulkWildUp" onclick="gmBulkWildToApp()" disabled>SEND ALL STOCKTAKE STALL → APP</button>
     <button id="gmBulkWildDown" onclick="gmBulkAppToStocktake()" disabled>LOAD ALL APP WILDWOOD → STOCKTAKE</button>
     <button id="gmBulkOnlineUp" onclick="gmBulkOnlineToSupabase()" disabled>UPLOAD ALL ONLINE → SUPABASE</button>
     <button id="gmBulkOnlineDown" onclick="gmBulkSupabaseToStocktake()" disabled>DOWNLOAD ALL SUPABASE → STOCKTAKE</button>
    </div>
    <div id="gmSyncFilters" class="sync-filters"></div>
   </div>
   <div id="gmSyncList" class="sync-list"></div>
  </section>
'''
if section_anchor not in text:
    raise SystemExit("Sales section anchor missing")
text=text.replace(section_anchor,section_markup+section_anchor,1)

# Teach existing navigation about Stock Sync.
old_nav=""" document.querySelectorAll('#summary,.backoffice').forEach(x=>x.classList.remove('on'));
 if(p==='summary'){document.getElementById('summary').classList.add('on');renderSummary();return;}
 if(p==='sales'||p==='orders'||p==='subscribers'){document.getElementById(p).classList.add('on');setTimeout(()=>gmBackRefresh(false),0);return;}"""
new_nav=""" document.querySelectorAll('#summary,#stocksync,.backoffice').forEach(x=>x.classList.remove('on'));
 if(p==='summary'){document.getElementById('summary').classList.add('on');renderSummary();return;}
 if(p==='stocksync'){document.getElementById('stocksync').classList.add('on');gmRenderStockSync();return;}
 if(p==='sales'||p==='orders'||p==='subscribers'){document.getElementById(p).classList.add('on');setTimeout(()=>gmBackRefresh(false),0);return;}"""
if old_nav not in text:
    raise SystemExit("navigation anchor missing")
text=text.replace(old_nav,new_nav,1)

# Insert the manual sync logic before the final recurring summary refresh.
js_anchor="setInterval(()=>{if(current==='summary')renderSummary();else if(wildwoodMode()){processNewWildwoodLogs();collect();}},1400);"
if js_anchor not in text:
    raise SystemExit("final interval anchor missing")

js=r'''
// gm-stock-sync-v10-10
// All remote stock movement is explicit. Connections only read data.
let gmManualWildConnected=false;
let gmManualSupabaseConnected=false;
let gmManualWildData=null;
let gmManualOnlineItems=[];
let gmSyncCat='All';

function gmSyncMessage(s,bad){
 const e=document.getElementById('gmSyncMsg');if(!e)return;
 e.textContent=String(s||'');e.classList.toggle('bad',!!bad);
}
function gmPortionsFromUnits(units,row){
 const per=Number(row&&row.per);
 if(!Number.isFinite(per)||per<=0)return null;
 const n=Number(units);
 if(!Number.isFinite(n)||n<0)return null;
 return Math.max(0,Math.floor(n/per+1e-9));
}
function gmStocktakeTotalPortions(row){return gmPortionsFromUnits(row.total,row)}
function gmStocktakeStallPortions(row){
 const n=Number(row.stallSpells);return Number.isFinite(n)?Math.max(0,Math.floor(n+1e-9)):null;
}
function gmStocktakeOnlinePortions(row){
 const n=Number(row.onlineSpells);return Number.isFinite(n)?Math.max(0,Math.floor(n+1e-9)):null;
}
function gmWildValueForRow(stock,row){
 const g=stock&&stock[row.group];if(!g||typeof g!=='object')return null;
 const names=[row.name].concat(row.aliases||[]);
 for(const nm of names){
   const key=Object.keys(g).find(k=>norm(k)===norm(nm));
   if(key!=null&&Number.isFinite(Number(g[key])))return Math.max(0,Math.floor(Number(g[key])));
 }
 return 0;
}
function gmSetWildValueInSnapshot(stock,row,portions){
 const out=JSON.parse(JSON.stringify(stock&&typeof stock==='object'?stock:{}));
 out[row.group]=out[row.group]&&typeof out[row.group]==='object'?out[row.group]:{};
 const names=[row.name].concat(row.aliases||[]);
 let key=null;
 for(const nm of names){key=Object.keys(out[row.group]).find(k=>norm(k)===norm(nm));if(key)break}
 if(!key)key=row.aliases&&row.aliases.length?row.aliases[0]:row.name;
 out[row.group][key]=Math.max(0,Math.floor(Number(portions)||0));
 return out;
}
function gmRemoteOnlineForRow(row){
 return gmManualSupabaseConnected?gmFindRemote(row,gmManualOnlineItems):null;
}
function gmRemoteOnlinePortions(row){
 const remote=gmRemoteOnlineForRow(row);if(!remote)return {physical:null,reserved:null,available:null};
 const physical=gmPhysicalOnline(remote),available=Number(remote.stock_quantity);
 const physicalP=gmPortionsFromUnits(physical,row),availableP=gmPortionsFromUnits(available,row);
 const reservedP=(physicalP==null||availableP==null)?null:Math.max(0,physicalP-availableP);
 return {physical:physicalP,reserved:reservedP,available:availableP,physicalUnits:physical,availableUnits:available,reservedUnits:Math.max(0,Number(remote.reserved_quantity)||0),remote};
}
function gmFmtPortions(n){return n==null||!Number.isFinite(Number(n))?'—':String(Math.max(0,Math.floor(Number(n))))}
function gmSyncValue(label,val,sub,na){
 return '<div class="sync-value '+(na?'na':'')+'"><span>'+gmE(label)+'</span><b>'+gmE(val)+'</b>'+(sub?'<div class="sync-sub">'+gmE(sub)+'</div>':'')+'</div>';
}
function gmSyncConnectionUi(){
 const ws=document.getElementById('gmSyncWildState'),os=document.getElementById('gmSyncOnlineState');
 if(ws){ws.textContent=gmManualWildConnected?'Connected · figures loaded':'Not connected';ws.classList.toggle('ok',gmManualWildConnected)}
 if(os){os.textContent=gmManualSupabaseConnected?'Connected · figures loaded':'Not connected';os.classList.toggle('ok',gmManualSupabaseConnected)}
 for(const id of ['gmBulkWildUp','gmBulkWildDown']){const b=document.getElementById(id);if(b)b.disabled=!gmManualWildConnected}
 for(const id of ['gmBulkOnlineUp','gmBulkOnlineDown']){const b=document.getElementById(id);if(b)b.disabled=!gmManualSupabaseConnected}
}
function gmRenderSyncFilters(){
 const cats=['All','Herb','Crystal','Oil','Candle','Rune','Kit'];
 const e=document.getElementById('gmSyncFilters');if(!e)return;
 e.innerHTML=cats.map(c=>'<button class="'+(c===gmSyncCat?'on':'')+'" onclick="gmSyncCat=\''+c+'\';gmRenderStockSync()">'+(c==='All'?'All':c+(c==='Kit'?' / Consumables':'s'))+'</button>').join('');
}
function gmRenderStockSync(){
 gmSyncConnectionUi();gmRenderSyncFilters();
 const list=document.getElementById('gmSyncList');if(!list)return;
 let rows=collect();
 if(gmSyncCat!=='All')rows=rows.filter(r=>r.section===gmSyncCat);
 list.innerHTML=rows.map(function(row){
   const total=gmStocktakeTotalPortions(row),localStall=gmStocktakeStallPortions(row),localOnline=gmStocktakeOnlinePortions(row);
   const app=gmManualWildConnected&&gmManualWildData?gmWildValueForRow(gmManualWildData.stock,row):null;
   const sup=gmRemoteOnlinePortions(row);
   const wildSame=app!=null&&localStall!=null&&app===localStall;
   const onlineSame=sup.physical!=null&&localOnline!=null&&sup.physical===localOnline;
   const anyDiff=(gmManualWildConnected&&!wildSame)||(gmManualSupabaseConnected&&!onlineSame);
   const moveId='gmMove-'+String(row.id).replace(/[^a-z0-9]/gi,'_');
   let actions='<div class="sync-group"><div class="sync-group-label">Wildwood</div><div class="sync-actions">'+
     '<button '+(!gmManualWildConnected?'disabled ':'')+'onclick="gmPushRowToWild(\''+gmE(row.id)+'\')">STOCKTAKE STALL → APP</button>'+
     '<button '+(!gmManualWildConnected?'disabled ':'')+'onclick="gmPullRowFromWild(\''+gmE(row.id)+'\')">APP → STOCKTAKE STALL</button></div></div>'+
     '<div class="sync-group"><div class="sync-group-label">Supabase Online</div><div class="sync-actions">'+
     '<button '+(!gmManualSupabaseConnected?'disabled ':'')+'onclick="gmPushRowOnline(\''+gmE(row.id)+'\')">UPLOAD ONLINE</button>'+
     '<button '+(!gmManualSupabaseConnected?'disabled ':'')+'onclick="gmPullRowOnline(\''+gmE(row.id)+'\')">DOWNLOAD ONLINE</button></div></div>'+
     '<div class="sync-group"><div class="sync-group-label">Move allocation</div><div class="sync-move">'+
     '<input id="'+moveId+'" type="number" min="1" step="1" value="1" aria-label="Spell portions to move">'+
     '<button '+(!(gmManualWildConnected&&gmManualSupabaseConnected)?'disabled ':'')+'onclick="gmMoveOnlineWild(\''+gmE(row.id)+'\',1)">ONLINE → WILDWOOD</button>'+
     '<button '+(!(gmManualWildConnected&&gmManualSupabaseConnected)?'disabled ':'')+'onclick="gmMoveOnlineWild(\''+gmE(row.id)+'\',-1)">WILDWOOD → ONLINE</button></div></div>';
   return '<div class="sync-item '+(anyDiff?'diff':'same')+'"><div class="sync-title"><div><strong>'+gmE(row.name)+'</strong><div class="sync-sub">'+gmE(row.section)+'</div></div><small>'+gmE(row.unit||'')+'</small></div>'+
    '<div class="sync-values">'+
      gmSyncValue('Stocktake total',gmFmtPortions(total),'spell portions',false)+
      gmSyncValue('Stocktake stall',gmFmtPortions(localStall),'spell portions',false)+
      gmSyncValue('Stocktake online',gmFmtPortions(localOnline),'spell portions',false)+
      gmSyncValue('App Wildwood',gmManualWildConnected?gmFmtPortions(app):'Not connected','spell portions',!gmManualWildConnected)+
      gmSyncValue('Supabase online',gmManualSupabaseConnected?gmFmtPortions(sup.physical):'Not connected','spell portions',!gmManualSupabaseConnected)+
      gmSyncValue('Reserved',gmManualSupabaseConnected?gmFmtPortions(sup.reserved):'—','spell portions',!gmManualSupabaseConnected)+
      gmSyncValue('Available online',gmManualSupabaseConnected?gmFmtPortions(sup.available):'—','spell portions',!gmManualSupabaseConnected)+
    '</div>'+actions+'</div>';
 }).join('')||'<div class="sync-empty">No stock items in this section.</div>';
}
async function gmManualConnectWildwood(){
 gmSyncMessage('Reading Wildwood stock…',false);
 try{
   if(!gmMainBridge()||!gmMainInstalled())throw new Error('Greenman HedgeWitchery Apothecary is not installed on this device.');
   const d=gmReadMainWild();
   if(!d||!d.ready)throw new Error('Open the Greenman app once, then return here and connect again.');
   gmManualWildData={stock:gmGroups(d.stock),logs:Array.isArray(d.logs)?d.logs:[],revision:Number(d.revision||0)};
   gmManualWildConnected=true;
   gmSyncMessage('Wildwood connected. Nothing was changed.',false);
 }catch(e){gmManualWildConnected=false;gmManualWildData=null;gmSyncMessage(String(e.message||e),true)}
 gmRenderStockSync();
}
async function gmManualConnectSupabase(){
 gmSyncMessage('Connecting to Supabase…',false);
 try{
   const t=await gmToken(true);if(!t)throw new Error('Supabase connection cancelled.');
   const d=await gmRawApi('pull',{},t);
   gmManualOnlineItems=d.items||[];gmManualSupabaseConnected=true;
   gmSyncMessage('Supabase connected. Nothing was changed.',false);
 }catch(e){gmManualSupabaseConnected=false;gmManualOnlineItems=[];gmSyncMessage(String(e.message||e),true)}
 gmRenderStockSync();
}
function gmRowById(id){return collect().find(r=>String(r.id)===String(id))||null}
function gmSetLocalStall(row,portions){
 portions=Math.max(0,Math.floor(Number(portions)||0));
 const need=portions*Number(row.per||0);
 if(Number.isFinite(need)&&need>Number(row.total||0)+1e-9){
   syncBusy=true;try{row.setTotal(need)}finally{syncBusy=false}
   row.total=need;
 }
 if(row.kind==='ingredient'){
   setWild(row.group,row.aliases,portions);
   const rec=split[row.id]||{};rec.lastWild=portions;rec.lastTotal=row.total;rec.online=Math.max(0,row.total-portions*row.per);split[row.id]=rec;
 }else{
   const rec=split[row.id]||{};rec.stallSpells=portions;rec.lastTotal=row.total;rec.online=Math.max(0,row.total-portions*row.per);split[row.id]=rec;
 }
 saveSplit();
}
async function gmRefreshWildRead(){
 const d=gmReadMainWild();if(!d||!d.ready)throw new Error('Wildwood app link is not ready.');
 gmManualWildData={stock:gmGroups(d.stock),logs:Array.isArray(d.logs)?d.logs:[],revision:Number(d.revision||0)};
}
async function gmRefreshOnlineRead(){
 const t=await gmToken(false);if(!t)throw new Error('Supabase is not connected.');
 const d=await gmRawApi('pull',{},t);gmManualOnlineItems=d.items||[];
}
async function gmPushRowToWild(id){
 const row=gmRowById(id);if(!row||!gmManualWildConnected)return;
 const portions=gmStocktakeStallPortions(row);
 if(!confirm('Send '+row.name+' Stocktake stall quantity ('+gmFmtPortions(portions)+' spell portions) to the Wildwood app?'))return;
 try{
   const next=gmSetWildValueInSnapshot(gmManualWildData.stock,row,portions||0);
   const wr=gmWriteMainWild(next,gmManualWildData.logs||[]);
   if(!wr.ok)throw new Error('Wildwood update failed.');
   await gmRefreshWildRead();gmSyncMessage(row.name+' sent to Wildwood.',false);gmRenderStockSync();
 }catch(e){gmSyncMessage(String(e.message||e),true)}
}
async function gmPullRowFromWild(id){
 const row=gmRowById(id);if(!row||!gmManualWildConnected)return;
 const portions=gmWildValueForRow(gmManualWildData.stock,row);
 if(!confirm('Load '+row.name+' from Wildwood into Stocktake stall ('+gmFmtPortions(portions)+' spell portions)?'))return;
 gmSetLocalStall(row,portions||0);gmSyncMessage(row.name+' loaded from Wildwood into Stocktake.',false);gmRenderStockSync();
}
function gmOnlinePayloadForRow(row){
 return window.GM_STOCKTAKE_ONLINE_EXPORT().find(x=>String(x.stock_id)===String(row.id))||null;
}
async function gmPushRowOnline(id){
 const row=gmRowById(id);if(!row||!gmManualSupabaseConnected)return;
 const payload=gmOnlinePayloadForRow(row);if(!payload)return;
 if(!confirm('Upload '+row.name+' Stocktake Online quantity ('+gmFmtPortions(gmStocktakeOnlinePortions(row))+' spell portions) to Supabase?'))return;
 try{
   await gmApi('push',{items:[payload]},true);await gmRefreshOnlineRead();
   gmSyncMessage(row.name+' Online stock uploaded to Supabase.',false);gmRenderStockSync();
 }catch(e){gmSyncMessage(String(e.message||e),true)}
}
function gmApplyRemoteOnlineToLocalRow(row,remote){
 const physical=gmPhysicalOnline(remote);if(!Number.isFinite(physical)||physical<0)return false;
 const stallUnits=(gmStocktakeStallPortions(row)||0)*row.per;
 const wanted=stallUnits+physical;
 syncBusy=true;try{row.setTotal(wanted)}finally{syncBusy=false}
 const rec=split[row.id]||{};rec.online=physical;rec.lastTotal=wanted;
 if(row.kind==='ingredient')rec.lastWild=gmStocktakeStallPortions(row)||0;else rec.stallSpells=gmStocktakeStallPortions(row)||0;
 split[row.id]=rec;saveSplit();return true;
}
async function gmPullRowOnline(id){
 const row=gmRowById(id);if(!row||!gmManualSupabaseConnected)return;
 const remote=gmRemoteOnlineForRow(row);if(!remote){gmSyncMessage('No matching Supabase stock row for '+row.name+'.',true);return}
 const rp=gmRemoteOnlinePortions(row).physical;
 if(!confirm('Download '+row.name+' Supabase Online quantity ('+gmFmtPortions(rp)+' spell portions) into Stocktake Online?'))return;
 gmApplyRemoteOnlineToLocalRow(row,remote);gmSyncMessage(row.name+' loaded from Supabase into Stocktake.',false);gmRenderStockSync();
}
function gmChangedWildRows(){
 const out=[];for(const row of collect()){const a=gmStocktakeStallPortions(row),b=gmWildValueForRow(gmManualWildData.stock,row);if(a!=null&&b!=null&&a!==b)out.push(row)}return out;
}
function gmChangedOnlineRowsManual(){
 const out=[];for(const row of collect()){const a=gmStocktakeOnlinePortions(row),b=gmRemoteOnlinePortions(row).physical;if(a!=null&&b!=null&&a!==b)out.push(row)}return out;
}
async function gmBulkWildToApp(){
 if(!gmManualWildConnected)return;
 const changed=gmChangedWildRows();if(!changed.length){gmSyncMessage('Wildwood already matches Stocktake stall.',false);return}
 if(!confirm('Send '+changed.length+' changed item'+(changed.length===1?'':'s')+' from Stocktake stall to the Wildwood app?'))return;
 try{
   let next=JSON.parse(JSON.stringify(gmManualWildData.stock||{}));
   for(const row of changed)next=gmSetWildValueInSnapshot(next,row,gmStocktakeStallPortions(row)||0);
   const wr=gmWriteMainWild(next,gmManualWildData.logs||[]);if(!wr.ok)throw new Error('Wildwood bulk update failed.');
   await gmRefreshWildRead();gmSyncMessage(changed.length+' Wildwood item'+(changed.length===1?'':'s')+' updated.',false);gmRenderStockSync();
 }catch(e){gmSyncMessage(String(e.message||e),true)}
}
async function gmBulkAppToStocktake(){
 if(!gmManualWildConnected)return;
 const changed=gmChangedWildRows();if(!changed.length){gmSyncMessage('Stocktake stall already matches Wildwood.',false);return}
 if(!confirm('Load '+changed.length+' changed Wildwood item'+(changed.length===1?'':'s')+' into Stocktake stall?'))return;
 for(const row of changed)gmSetLocalStall(row,gmWildValueForRow(gmManualWildData.stock,row)||0);
 gmSyncMessage(changed.length+' Stocktake stall item'+(changed.length===1?'':'s')+' updated from Wildwood.',false);gmRenderStockSync();
}
async function gmBulkOnlineToSupabase(){
 if(!gmManualSupabaseConnected)return;
 const changed=gmChangedOnlineRowsManual();if(!changed.length){gmSyncMessage('Supabase Online already matches Stocktake Online.',false);return}
 if(!confirm('Upload '+changed.length+' changed Online item'+(changed.length===1?'':'s')+' from Stocktake to Supabase?'))return;
 try{
   const all=window.GM_STOCKTAKE_ONLINE_EXPORT(),ids=new Set(changed.map(r=>r.id)),payload=all.filter(x=>ids.has(x.stock_id));
   await gmApi('push',{items:payload},true);await gmRefreshOnlineRead();
   gmSyncMessage(gmUpdateCountText(payload),false);gmRenderStockSync();
 }catch(e){gmSyncMessage(String(e.message||e),true)}
}
async function gmBulkSupabaseToStocktake(){
 if(!gmManualSupabaseConnected)return;
 const changed=gmChangedOnlineRowsManual();if(!changed.length){gmSyncMessage('Stocktake Online already matches Supabase.',false);return}
 if(!confirm('Download '+changed.length+' changed Online item'+(changed.length===1?'':'s')+' from Supabase into Stocktake?'))return;
 let n=0;for(const row of changed){const remote=gmRemoteOnlineForRow(row);if(remote&&gmApplyRemoteOnlineToLocalRow(row,remote))n++}
 gmSyncMessage(n+' Stocktake Online item'+(n===1?'':'s')+' updated from Supabase.',false);gmRenderStockSync();
}
async function gmMoveOnlineWild(id,dir){
 const row=gmRowById(id);if(!row||!gmManualWildConnected||!gmManualSupabaseConnected)return;
 const input=document.getElementById('gmMove-'+String(row.id).replace(/[^a-z0-9]/gi,'_'));
 const qty=Math.max(1,Math.floor(Number(input&&input.value)||1));
 const sup=gmRemoteOnlinePortions(row),appNow=gmWildValueForRow(gmManualWildData.stock,row)||0;
 if(dir>0&&Number(sup.available||0)<qty){gmSyncMessage('Only '+gmFmtPortions(sup.available)+' '+row.name+' Online portions are available to move.',true);return}
 if(dir<0&&appNow<qty){gmSyncMessage('Only '+appNow+' '+row.name+' Wildwood portions are available to move.',true);return}
 const label=dir>0?'Online → Wildwood':'Wildwood → Online';
 if(!confirm('Move '+qty+' spell portion'+(qty===1?'':'s')+' of '+row.name+' '+label+'?'))return;
 const oldPhysical=Number(sup.physicalUnits),deltaUnits=qty*row.per,newPhysical=dir>0?oldPhysical-deltaUnits:oldPhysical+deltaUnits;
 if(dir>0&&newPhysical<Number(sup.reservedUnits||0)-1e-9){gmSyncMessage('Those portions are reserved for paid Online orders and cannot be moved.',true);return}
 const oldWild=appNow,newWild=dir>0?oldWild+qty:oldWild-qty;
 const remotePayload=Object.assign({},gmOnlinePayloadForRow(row),{online_amount:newPhysical});
 try{
   await gmApi('push',{items:[remotePayload]},true);
   const next=gmSetWildValueInSnapshot(gmManualWildData.stock,row,newWild);
   const wr=gmWriteMainWild(next,gmManualWildData.logs||[]);
   if(!wr.ok)throw new Error('Wildwood update failed after Online change.');
   gmSetLocalStall(row,newWild);
   const rec=split[row.id]||{};rec.online=newPhysical;rec.lastTotal=row.total;split[row.id]=rec;saveSplit();
   await gmRefreshWildRead();await gmRefreshOnlineRead();
   gmSyncMessage(qty+' '+row.name+' spell portion'+(qty===1?'':'s')+' moved '+label+'.',false);gmRenderStockSync();
 }catch(e){
   try{if(Number.isFinite(oldPhysical)){const rollback=Object.assign({},gmOnlinePayloadForRow(row),{online_amount:oldPhysical});await gmApi('push',{items:[rollback]},true)}}catch(_e){}
   gmSyncMessage(String(e.message||e),true)
 }
}

// Disable every old automatic Stall/Wildwood synchronization path.
// Existing intervals now call harmless no-op functions.
gmStallCloudSync=async function(){return false};
gmStallDeviceSync=async function(){return false};
window.GM_STOCKTAKE_STALL_SYNC=async function(){return false};
'''
text=text.replace(js_anchor,js+"\n"+js_anchor,1)

for marker in [
 "Stock Sync","CONNECT WILDWOOD APP","CONNECT SUPABASE",
 "Stocktake total","Stocktake stall","Stocktake online",
 "Supabase online","Reserved","Available online",
 "ONLINE → WILDWOOD","WILDWOOD → ONLINE",
 "gmStallCloudSync=async function(){return false}",
 "gmStallDeviceSync=async function(){return false}",
]:
    if marker not in text:
        raise SystemExit("missing manual sync marker: "+marker)

dst.write_text(text,encoding="utf-8")
print("patched Stocktake V10.10 manual Stock Sync page; remote stock movement is manual only")
