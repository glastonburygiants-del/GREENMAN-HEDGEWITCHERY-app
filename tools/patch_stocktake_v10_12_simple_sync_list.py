#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv)!=3:
    raise SystemExit("usage: patch_stocktake_v10_12_simple_sync_list.py input.html output.html")

src=Path(sys.argv[1]); dst=Path(sys.argv[2])
text=src.read_text(encoding="utf-8")
if "gm-simple-sync-v10-12" in text:
    raise SystemExit("simple sync patch already present")

# Replace only the Stock Sync section.
pattern=r'<section id="stocksync">.*?</section>\s*<section id="sales"'
m=re.search(pattern,text,re.S)
if not m:
    raise SystemExit("Stock Sync section not found")
simple=r'''<section id="stocksync">
   <div class="simple-sync-head">
    <div class="simple-sync-title">Stock Sync</div>
    <div class="simple-sync-connect">
     <button id="gmSimpleWildBtn" onclick="gmManualConnectWildwood()">CONNECT WILDWOOD</button>
     <span id="gmSyncWildState" class="simple-sync-state">Not connected</span>
     <button id="gmSimpleSupBtn" onclick="gmManualConnectSupabase()">CONNECT SUPABASE</button>
     <span id="gmSyncOnlineState" class="simple-sync-state">Not connected</span>
    </div>
    <div id="gmSyncMsg" class="simple-sync-msg"></div>
    <div class="simple-sync-bulk">
     <button id="gmBulkWildUp" onclick="gmBulkWildToApp()" disabled>STOCKTAKE → WW</button>
     <button id="gmBulkWildDown" onclick="gmBulkAppToStocktake()" disabled>WW → STOCKTAKE</button>
     <button id="gmBulkOnlineUp" onclick="gmBulkOnlineToSupabase()" disabled>UPLOAD → SUPABASE</button>
     <button id="gmBulkOnlineDown" onclick="gmBulkSupabaseToStocktake()" disabled>SUPABASE → STOCKTAKE</button>
    </div>
    <div id="gmSyncFilters" class="simple-sync-filters"></div>
   </div>
   <div class="simple-sync-table">
    <div class="simple-sync-row simple-sync-header">
     <div>Item</div><div>Stocktake</div><div>WW</div><div>Supabase</div>
    </div>
    <div id="gmSyncList"></div>
   </div>
  </section>
  <section id="sales"'''
text=text[:m.start()]+simple+text[m.end():]

# Add compact styling to the real outer head.
head=text.find("</head>")
if head<0:
    raise SystemExit("outer head close not found")
css=r'''
<style id="gm-simple-sync-v10-12">
#stocksync{display:none;overflow:auto;height:100%;padding:8px;max-width:1180px;margin:auto;width:100%}
#stocksync.on{display:block}
.simple-sync-head{position:sticky;top:0;z-index:8;background:var(--bg);padding:3px 0 7px}
.simple-sync-title{font-size:19px;font-weight:700;color:var(--green);margin-bottom:7px}
.simple-sync-connect{display:grid;grid-template-columns:auto 1fr auto 1fr;gap:5px;align-items:center}
.simple-sync-connect button{min-height:38px;border:1px solid var(--line);border-radius:8px;background:var(--green);color:white;padding:6px 9px;font:700 10px Georgia,serif}
.simple-sync-state{min-height:38px;display:flex;align-items:center;padding:5px 7px;border:1px solid var(--line);border-radius:8px;background:var(--paper);font-size:10px;color:var(--muted)}
.simple-sync-state.ok{color:var(--green);font-weight:700;border-color:#8fa27c}
.simple-sync-msg{font-size:10px;min-height:16px;margin-top:5px;color:var(--green);font-weight:700}
.simple-sync-msg.bad{color:#8a3026}
.simple-sync-bulk{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin:5px 0}
.simple-sync-bulk button{min-height:34px;border:1px solid var(--line);border-radius:7px;background:#fffaf0;padding:5px 6px;font:700 9px Georgia,serif}
.simple-sync-bulk button:disabled{opacity:.38}
.simple-sync-filters{display:flex;gap:4px;overflow-x:auto;padding:4px 0}
.simple-sync-filters button{white-space:nowrap;min-height:32px;border:1px solid var(--line);border-radius:999px;background:var(--paper);padding:4px 8px;font:700 10px Georgia,serif}
.simple-sync-filters button.on{background:var(--green);color:white}
.simple-sync-table{background:var(--paper);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.simple-sync-row{display:grid;grid-template-columns:minmax(140px,1.7fr) repeat(3,minmax(72px,.8fr));align-items:center;border-bottom:1px solid #e1d5b8;min-height:46px}
.simple-sync-row:last-child{border-bottom:0}
.simple-sync-row>div{padding:7px 6px;min-width:0}
.simple-sync-header{background:#e7ddc4;color:var(--green);font-weight:700;font-size:11px;min-height:38px}
.simple-sync-item{font-size:12px}
.simple-sync-name{font-weight:700;color:var(--green);line-height:1.15}
.simple-sync-section{font-size:9px;color:var(--muted);margin-top:2px}
.simple-sync-num{text-align:center;font-size:16px;font-weight:700;color:#2b261e}
.simple-sync-num.na{font-size:10px;color:#928a7e;font-weight:400}
.simple-sync-sub{font-size:8px;color:var(--muted);font-weight:400;line-height:1.2;margin-top:1px}
.simple-sync-item.diff{background:#fff8ea}
.simple-sync-item.same{background:#fbf7eb}
.simple-sync-detail{display:none;grid-column:1/-1!important;background:#f4ecd7;border-top:1px dashed #cdbd98;padding:7px!important}
.simple-sync-item.open .simple-sync-detail{display:block}
.simple-sync-actions{display:flex;gap:5px;flex-wrap:wrap}
.simple-sync-actions button,.simple-sync-actions input{min-height:34px;border:1px solid var(--line);border-radius:7px;background:#fffaf0;padding:5px 7px;font:700 9px Georgia,serif}
.simple-sync-actions button:disabled{opacity:.4}
.simple-sync-actions input{width:62px;text-align:center}
.simple-sync-hint{font-size:9px;color:var(--muted);margin-top:5px}
@media(max-width:650px){
 .simple-sync-connect{grid-template-columns:1fr 1fr}
 .simple-sync-connect button{font-size:9px}
 .simple-sync-row{grid-template-columns:minmax(110px,1.5fr) repeat(3,minmax(58px,.7fr))}
 .simple-sync-row>div{padding:6px 4px}
 .simple-sync-name{font-size:11px}
 .simple-sync-num{font-size:14px}
 .simple-sync-header{font-size:10px}
 .simple-sync-bulk{grid-template-columns:repeat(2,minmax(0,1fr))}
}
</style>
'''
text=text[:head]+css+text[head:]

# Override only the Stock Sync rendering/interaction. Existing connection and transfer
# functions stay intact.
anchor="setInterval(()=>{if(current==='summary')renderSummary();else if(wildwoodMode()){processNewWildwoodLogs();collect();}},1400);"
if anchor not in text:
    raise SystemExit("final interval anchor missing")
js=r'''
// gm-simple-sync-v10-12
async function gmManualConnectWildwood(){
 gmSyncMessage('Reading Wildwood stock…',false);
 try{
   if(!gmMainBridge())throw new Error('This Stocktake build cannot see the phone link.');
   const d=gmReadMainWild();
   if(!d.installed)throw new Error('Greenman HedgeWitchery Apothecary is not installed on this device.');
   if(d.error)throw new Error('Greenman app found, but that installed version does not yet contain the Stocktake link.');
   if(!d.ready)throw new Error('Greenman app found. Open it once, then return here and press CONNECT WILDWOOD again.');
   gmManualWildData={stock:gmGroups(d.stock),logs:Array.isArray(d.logs)?d.logs:[],revision:Number(d.revision||0)};
   gmManualWildConnected=true;
   gmSyncMessage('Wildwood connected. Nothing was changed.',false);
 }catch(e){
   gmManualWildConnected=false;gmManualWildData=null;gmSyncMessage(String(e.message||e),true);
 }
 gmRenderStockSync();
}
function gmSimpleNum(n,sub,na){
 const v=na?'—':gmFmtPortions(n);
 return '<div class="simple-sync-num '+(na?'na':'')+'">'+v+(sub?'<div class="simple-sync-sub">'+gmE(sub)+'</div>':'')+'</div>';
}
function gmSimpleToggle(id){
 const e=document.getElementById('syncrow-'+String(id).replace(/[^a-z0-9]/gi,'_'));
 if(e)e.classList.toggle('open');
}
function gmRenderStockSync(){
 gmSyncConnectionUi();gmRenderSyncFilters();
 const list=document.getElementById('gmSyncList');if(!list)return;
 let rows=collect();
 if(gmSyncCat!=='All')rows=rows.filter(r=>r.section===gmSyncCat);
 list.innerHTML=rows.map(function(row){
   const total=gmStocktakeTotalPortions(row);
   const ww=gmManualWildConnected&&gmManualWildData?gmWildValueForRow(gmManualWildData.stock,row):null;
   const sup=gmRemoteOnlinePortions(row);
   const supMain=gmManualSupabaseConnected?sup.physical:null;
   const localStall=gmStocktakeStallPortions(row),localOnline=gmStocktakeOnlinePortions(row);
   const wildDiff=gmManualWildConnected&&ww!=null&&localStall!=null&&ww!==localStall;
   const onlineDiff=gmManualSupabaseConnected&&supMain!=null&&localOnline!=null&&supMain!==localOnline;
   const cls=(wildDiff||onlineDiff)?'diff':'same';
   const rid='syncrow-'+String(row.id).replace(/[^a-z0-9]/gi,'_');
   const moveId='gmMove-'+String(row.id).replace(/[^a-z0-9]/gi,'_');
   const supSub=gmManualSupabaseConnected&&sup.physical!=null?('avail '+gmFmtPortions(sup.available)+(Number(sup.reserved||0)>0?' · res '+gmFmtPortions(sup.reserved):'')):'';
   return '<div id="'+rid+'" class="simple-sync-row simple-sync-item '+cls+'" onclick="if(event.target.tagName!==\'BUTTON\'&&event.target.tagName!==\'INPUT\')gmSimpleToggle(\''+gmE(row.id)+'\')">'+
    '<div><div class="simple-sync-name">'+gmE(row.name)+'</div><div class="simple-sync-section">'+gmE(row.section)+'</div></div>'+
    gmSimpleNum(total,'portions',false)+
    gmSimpleNum(ww,'portions',!gmManualWildConnected)+
    gmSimpleNum(supMain,supSub,!gmManualSupabaseConnected)+
    '<div class="simple-sync-detail"><div class="simple-sync-actions">'+
      '<button '+(!gmManualWildConnected?'disabled ':'')+'onclick="gmPushRowToWild(\''+gmE(row.id)+'\')">STOCKTAKE → WW</button>'+
      '<button '+(!gmManualWildConnected?'disabled ':'')+'onclick="gmPullRowFromWild(\''+gmE(row.id)+'\')">WW → STOCKTAKE</button>'+
      '<button '+(!gmManualSupabaseConnected?'disabled ':'')+'onclick="gmPushRowOnline(\''+gmE(row.id)+'\')">STOCKTAKE ONLINE → SUPABASE</button>'+
      '<button '+(!gmManualSupabaseConnected?'disabled ':'')+'onclick="gmPullRowOnline(\''+gmE(row.id)+'\')">SUPABASE → STOCKTAKE</button>'+
      '<input id="'+moveId+'" type="number" min="1" step="1" value="1">'+
      '<button '+(!(gmManualWildConnected&&gmManualSupabaseConnected)?'disabled ':'')+'onclick="gmMoveOnlineWild(\''+gmE(row.id)+'\',1)">ONLINE → WW</button>'+
      '<button '+(!(gmManualWildConnected&&gmManualSupabaseConnected)?'disabled ':'')+'onclick="gmMoveOnlineWild(\''+gmE(row.id)+'\',-1)">WW → ONLINE</button>'+
    '</div><div class="simple-sync-hint">Tap the item again to close these controls.</div></div>'+
   '</div>';
 }).join('');
 if(!rows.length)list.innerHTML='<div class="sync-empty">No stock items in this section.</div>';
}
function gmSyncConnectionUi(){
 const ws=document.getElementById('gmSyncWildState'),os=document.getElementById('gmSyncOnlineState');
 if(ws){ws.textContent=gmManualWildConnected?'Connected':'Not connected';ws.classList.toggle('ok',gmManualWildConnected)}
 if(os){os.textContent=gmManualSupabaseConnected?'Connected':'Not connected';os.classList.toggle('ok',gmManualSupabaseConnected)}
 for(const id of ['gmBulkWildUp','gmBulkWildDown']){const b=document.getElementById(id);if(b)b.disabled=!gmManualWildConnected}
 for(const id of ['gmBulkOnlineUp','gmBulkOnlineDown']){const b=document.getElementById(id);if(b)b.disabled=!gmManualSupabaseConnected}
}
'''
text=text.replace(anchor,js+"\n"+anchor,1)

for marker in ["Item</div><div>Stocktake</div><div>WW</div><div>Supabase","gm-simple-sync-v10-12","STOCKTAKE → WW","avail "]:
    if marker not in text:
        raise SystemExit("missing simple sync marker: "+marker)

dst.write_text(text,encoding="utf-8")
print("patched compact Item | Stocktake | WW | Supabase sync list")
