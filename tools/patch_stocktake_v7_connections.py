#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit("usage: patch_stocktake_v7_connections.py input.html output.html")
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
text=src.read_text(encoding="utf-8")
if "gm-stocktake-v7-connections" in text:
    raise SystemExit("Stocktake V7 connection patch already present")
if "GM_STOCKTAKE_ONLINE_EXPORT" not in text or "gm_admin_stock_v1" not in text:
    raise SystemExit("expected Stocktake V6 markers missing")

css=r'''
<style id="gm-stocktake-v7-connections">
.gm-connect{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:6px;font-size:10px}
.gm-connect .state{padding:5px 7px;border:1px solid var(--line);border-radius:7px;background:var(--paper);color:var(--muted);font-weight:700}
.gm-connect .state.ok{color:var(--green);border-color:#8fa27c}
.gm-connect button{min-height:31px;border:1px solid var(--line);border-radius:7px;background:var(--paper);color:var(--green);font:700 10px Georgia,serif;padding:5px 8px}
.gm-connect button.primary{background:var(--green);color:#fff;border-color:var(--green)}
.gm-connect button[hidden]{display:none!important}
#gmConnectMsg{flex-basis:100%;min-height:12px;color:var(--muted)}
#gmConnectMsg.bad{color:#8a3026}
@media(max-width:700px){.gm-connect button{flex:1 1 auto}.gm-connect .state{flex:1 1 auto;text-align:center}}
</style>
'''
head_anchor="</style></head><body>"
if text.count(head_anchor)!=1:
    raise SystemExit(f"outer style/head anchor count: {text.count(head_anchor)}")
text=text.replace(head_anchor,"</style>"+css+"</head><body>",1)

tabs_anchor='''    <button data-page="summary">Summary</button>
   </div>
  </div>'''
connect_markup='''    <button data-page="summary">Summary</button>
   </div>
   <div class="gm-connect" aria-label="Stock connections">
    <span id="gmStallState" class="state">Stall bridge checking…</span>
    <span id="gmOnlineState" class="state">Online stock not set up</span>
    <button id="gmOnlineSend" type="button">SEND THIS STOCKTAKE ONLINE</button>
    <button id="gmOnlineLoad" type="button">LOAD ONLINE STOCK</button>
    <button id="gmOnlineSync" class="primary" type="button" hidden>SYNC ONLINE</button>
    <span id="gmConnectMsg" aria-live="polite"></span>
   </div>
  </div>'''
if text.count(tabs_anchor)!=1:
    raise SystemExit(f"outer tabs anchor count: {text.count(tabs_anchor)}")
text=text.replace(tabs_anchor,connect_markup,1)

old_helpers='''function wildwoodMode(){try{const m=String(localStorage.getItem('gm_app_mode')||'').toLowerCase();return m==='master'||localStorage.getItem('gm_master_mode')==='1';}catch(e){return false}}
function frameApi(k){try{return document.getElementById('f-'+k).contentWindow.__stockAPI||null}catch(e){return null}}
function readWild(){try{const x=JSON.parse(localStorage.getItem(WILD_KEY)||'{}');return x&&typeof x==='object'?x:{}}catch(e){return {}}}
function writeWild(w){try{localStorage.setItem(WILD_KEY,JSON.stringify(w))}catch(e){}}'''
new_helpers='''function bridgeState(){
 try{
   if(window.WildwoodBridge&&typeof window.WildwoodBridge.readState==='function'){
     const s=JSON.parse(String(window.WildwoodBridge.readState()||'{}'));
     return s&&typeof s==='object'?s:null;
   }
 }catch(e){}
 return null;
}
function wildwoodMode(){
 try{
   const s=bridgeState();
   const m=String(s&&s.app_mode!=null?s.app_mode:localStorage.getItem('gm_app_mode')||'').toLowerCase();
   const master=String(s&&s.master_mode!=null?s.master_mode:localStorage.getItem('gm_master_mode')||'0');
   return m==='master'||master==='1';
 }catch(e){return false}
}
function frameApi(k){try{return document.getElementById('f-'+k).contentWindow.__stockAPI||null}catch(e){return null}}
function readWild(){
 try{
   const s=bridgeState();
   if(s&&s.stock_json){
     const x=JSON.parse(String(s.stock_json));if(x&&typeof x==='object'&&!Array.isArray(x))return x;
   }
   const x=JSON.parse(localStorage.getItem(WILD_KEY)||'{}');return x&&typeof x==='object'?x:{};
 }catch(e){return {}}
}
function writeWild(w){
 const raw=JSON.stringify(w&&typeof w==='object'?w:{});
 try{localStorage.setItem(WILD_KEY,raw)}catch(e){}
 try{
   if(window.WildwoodBridge&&typeof window.WildwoodBridge.writeStock==='function')window.WildwoodBridge.writeStock(raw);
 }catch(e){}
}
function readWildLogs(){
 try{
   const s=bridgeState();
   const raw=s&&s.log_json!=null?String(s.log_json):String(localStorage.getItem(WILD_LOG)||'[]');
   const x=JSON.parse(raw);return Array.isArray(x)?x:[];
 }catch(e){return []}
}'''
if text.count(old_helpers)!=1:
    raise SystemExit(f"Wildwood helper anchor count: {text.count(old_helpers)}")
text=text.replace(old_helpers,new_helpers,1)

old_logs=""" let logs=[];try{logs=JSON.parse(localStorage.getItem(WILD_LOG)||'[]');if(!Array.isArray(logs))logs=[]}catch(e){logs=[]}"""
if text.count(old_logs)!=1:
    raise SystemExit(f"Wildwood log read anchor count: {text.count(old_logs)}")
text=text.replace(old_logs," let logs=readWildLogs();",1)

sync_layer=r'''
const GM_STOCKTAKE_PROJECT='https://zzfgufuyetybxaeidcxu.supabase.co';
const GM_STOCKTAKE_KEY='sb_publishable_v5C9faTqdknJP9sdbgahCQ_MZVw_2gG';
const GM_STOCKTAKE_API=GM_STOCKTAKE_PROJECT+'/functions/v1/greenman-stocktake-private';
const GM_STOCKTAKE_DEVICE_KEY='gm_stocktake_device_token_v1';
const GM_ONLINE_SYNC_KEY='gm_stocktake_online_sync_v1';

function gmConnectMsg(s,bad){
 const e=document.getElementById('gmConnectMsg');if(!e)return;e.textContent=String(s||'');e.classList.toggle('bad',!!bad);
}
function gmOnlineMeta(){
 try{const x=JSON.parse(localStorage.getItem(GM_ONLINE_SYNC_KEY)||'null');return x&&typeof x==='object'?x:null}catch(e){return null}
}
function gmSaveOnlineMeta(snapshot,serverTime){
 localStorage.setItem(GM_ONLINE_SYNC_KEY,JSON.stringify({version:1,snapshot:snapshot||{},server_time:serverTime||new Date().toISOString()}));
 gmUpdateConnectUi();
}
async function gmPairStocktake(){
 const pass=window.prompt('Enter the Admin password once to connect this Stocktake to Online stock.');
 if(pass==null)return null;
 const r=await fetch(GM_STOCKTAKE_API,{
   method:'POST',
   headers:{'Content-Type':'application/json','apikey':GM_STOCKTAKE_KEY},
   body:JSON.stringify({action:'pair',admin_passphrase:String(pass),label:'HedgeWitchery Stocktake'})
 });
 let d={};try{d=await r.json()}catch(e){}
 if(!r.ok||!d.device_token)throw new Error(d.error||'Stocktake pairing failed.');
 localStorage.setItem(GM_STOCKTAKE_DEVICE_KEY,String(d.device_token));
 return String(d.device_token);
}
async function gmDeviceToken(force){
 if(force)localStorage.removeItem(GM_STOCKTAKE_DEVICE_KEY);
 let t=String(localStorage.getItem(GM_STOCKTAKE_DEVICE_KEY)||'').trim();
 if(t)return t;
 return await gmPairStocktake();
}
async function gmStockApi(action,payload,retry){
 let token=await gmDeviceToken(false);
 if(!token)throw new Error('Online stock connection was cancelled.');
 const r=await fetch(GM_STOCKTAKE_API,{
   method:'POST',
   headers:{'Content-Type':'application/json','apikey':GM_STOCKTAKE_KEY,'x-stocktake-token':token},
   body:JSON.stringify(Object.assign({action},payload||{}))
 });
 let d={};try{d=await r.json()}catch(e){}
 if(r.status===401&&retry!==false){
   token=await gmDeviceToken(true);
   if(!token)throw new Error('Online stock connection was cancelled.');
   return gmStockApi(action,payload,false);
 }
 if(!r.ok)throw new Error(d.error||('Online stock request failed ('+r.status+')'));
 return d;
}
function gmCoreType(section,itemType){
 if(section==='Kit')return itemType==='Packaging'||itemType==='Spell Extra';
 return section===itemType;
}
function gmLocalAliases(row){
 const a=[row.name].concat(row.aliases||[]);
 const extra={
   'K:small':['60 x 60 mm Envelope','65 x 65 mm Envelope','Small glassine bags 65×65 mm'],
   'K:large':['98 x 76 mm Envelope','92 x 68 mm Envelope','Large glassine bags 92×68 mm'],
   'K:mailer':['Outer Mailer / Parcel Pack'],
   'K:jar':['Spell Jar'],
   'K:bag':['Charm Bag'],
   'K:charcoal':['Charcoal Portion']
 };
 return a.concat(extra[row.id]||[]);
}
function gmUnitCompatible(a,b){
 const x=norm(a),y=norm(b);if(!x||!y)return true;
 const each=new Set(['each','disc','discs','piece','pieces','item','items']);
 return (each.has(x)&&each.has(y))||x===y;
}
function gmFindRemote(row,items){
 const names=gmLocalAliases(row).map(norm).filter(Boolean);
 const m=(items||[]).filter(x=>gmCoreType(row.section,String(x.item_type||''))&&names.includes(norm(x.item_name))&&gmUnitCompatible(row.unit,x.stock_unit));
 return m.length===1?m[0]:null;
}
function gmSnapshotFromLocal(){
 const snap={};for(const r of window.GM_STOCKTAKE_ONLINE_EXPORT()){
   if(r.online_amount!=null&&Number.isFinite(Number(r.online_amount)))snap[r.stock_id]=Number(r.online_amount);
 }return snap;
}
function gmApplyRemote(items){
 const rows=collect();let matched=0,unmatched=0;
 for(const row of rows){
   const remote=gmFindRemote(row,items);
   if(!remote){if(row.online!=null)unmatched++;continue}
   const q=Number(remote.stock_quantity);if(!Number.isFinite(q)||q<0)continue;
   const rec=split[row.id]||{};
   rec.online=q;
   const stall=Number.isFinite(row.stall)?row.stall:0;
   const wanted=Number.isFinite(row.stall)?stall+q:q;
   syncBusy=true;
   try{row.setTotal(wanted)}finally{syncBusy=false}
   rec.lastTotal=wanted;
   if(Number.isFinite(row.stallSpells))rec.lastWild=row.stallSpells;
   split[row.id]=rec;matched++;
 }
 saveSplit();
 for(const k of ['herbs','crystals','oils','candles','rest']){const a=frameApi(k);try{if(a&&a.refresh)a.refresh()}catch(e){}}
 if(current==='summary')renderSummary();
 return{matched,unmatched};
}
async function gmInitialSend(){
 gmConnectMsg('Sending the Stocktake Online figures…',false);
 try{
   const rows=window.GM_STOCKTAKE_ONLINE_EXPORT().filter(r=>r.online_amount!=null&&Number.isFinite(Number(r.online_amount)));
   const pushed=await gmStockApi('push',{items:rows});
   const pulled=await gmStockApi('pull');
   gmApplyRemote(pulled.items||[]);
   gmSaveOnlineMeta(gmSnapshotFromLocal(),pulled.server_time);
   const missed=(pushed.unmatched||[]).length+(pushed.ambiguous||[]).length+(pushed.invalid||[]).length;
   gmConnectMsg('Online stock connected'+(missed?' · '+missed+' local item'+(missed===1?'':'s')+' kept local only':''),false);
 }catch(e){gmConnectMsg(String(e.message||e),true)}
}
async function gmInitialLoad(){
 gmConnectMsg('Loading Online stock…',false);
 try{
   const pulled=await gmStockApi('pull');
   const result=gmApplyRemote(pulled.items||[]);
   gmSaveOnlineMeta(gmSnapshotFromLocal(),pulled.server_time);
   gmConnectMsg('Online stock loaded · '+result.matched+' matched item'+(result.matched===1?'':'s'),false);
 }catch(e){gmConnectMsg(String(e.message||e),true)}
}
async function gmSyncOnline(){
 const meta=gmOnlineMeta();if(!meta){gmConnectMsg('Choose SEND THIS STOCKTAKE ONLINE or LOAD ONLINE STOCK first.',true);return}
 const btn=document.getElementById('gmOnlineSync');if(btn)btn.disabled=true;
 gmConnectMsg('Syncing Online stock…',false);
 try{
   const first=await gmStockApi('pull');
   const rows=collect(),local=window.GM_STOCKTAKE_ONLINE_EXPORT();
   const last=meta.snapshot||{},push=[],conflicts=[];
   for(const l of local){
     if(l.online_amount==null||!Number.isFinite(Number(l.online_amount)))continue;
     const row=rows.find(x=>x.id===l.stock_id);if(!row)continue;
     const remote=gmFindRemote(row,first.items||[]);if(!remote)continue;
     const lv=Number(l.online_amount),rv=Number(remote.stock_quantity),old=Number(last[l.stock_id]);
     const haveOld=Number.isFinite(old),localChanged=!haveOld||Math.abs(lv-old)>1e-7,remoteChanged=!haveOld||Math.abs(rv-old)>1e-7;
     if(localChanged&&!remoteChanged)push.push(l);
     else if(localChanged&&remoteChanged&&Math.abs(lv-rv)>1e-7)conflicts.push(l.stock_id);
   }
   if(push.length)await gmStockApi('push',{items:push});
   const finalPull=await gmStockApi('pull');
   gmApplyRemote(finalPull.items||[]);
   gmSaveOnlineMeta(gmSnapshotFromLocal(),finalPull.server_time);
   gmConnectMsg('Online stock synced'+(conflicts.length?' · '+conflicts.length+' simultaneous change'+(conflicts.length===1?'':'s')+' kept at the Online value':''),false);
 }catch(e){gmConnectMsg(String(e.message||e),true)}
 finally{if(btn)btn.disabled=false}
}
function gmUpdateConnectUi(){
 const stall=document.getElementById('gmStallState'),online=document.getElementById('gmOnlineState');
 let linked=false;
 try{linked=!!(window.WildwoodBridge&&typeof window.WildwoodBridge.available==='function'&&window.WildwoodBridge.available())}catch(e){}
 if(stall){stall.textContent=linked?'HedgeWitchery Android App linked':'Stall bridge waiting';stall.classList.toggle('ok',linked)}
 const ready=!!gmOnlineMeta();
 if(online){online.textContent=ready?'Online stock connected':'Online stock not set up';online.classList.toggle('ok',ready)}
 const send=document.getElementById('gmOnlineSend'),load=document.getElementById('gmOnlineLoad'),sync=document.getElementById('gmOnlineSync');
 if(send)send.hidden=ready;if(load)load.hidden=ready;if(sync)sync.hidden=!ready;
}
document.getElementById('gmOnlineSend').onclick=gmInitialSend;
document.getElementById('gmOnlineLoad').onclick=gmInitialLoad;
document.getElementById('gmOnlineSync').onclick=gmSyncOnline;
window.GM_STOCKTAKE_SYNC_ONLINE=gmSyncOnline;
window.GM_STOCKTAKE_LOAD_ONLINE=gmInitialLoad;
window.GM_STOCKTAKE_SEND_ONLINE=gmInitialSend;
setInterval(gmUpdateConnectUi,1600);
setTimeout(gmUpdateConnectUi,100);
'''
end_anchor="setInterval(()=>{if(current==='summary')renderSummary();else if(wildwoodMode()){processNewWildwoodLogs();collect();}},1400);"
if text.count(end_anchor)!=1:
    raise SystemExit(f"V6 final interval anchor count: {text.count(end_anchor)}")
text=text.replace(end_anchor,sync_layer+"\n"+end_anchor,1)

for marker in (
    "gm-stocktake-v7-connections","WildwoodBridge","greenman-stocktake-private",
    "SEND THIS STOCKTAKE ONLINE","LOAD ONLINE STOCK","SYNC ONLINE",
    "GM_STOCKTAKE_SYNC_ONLINE","gm_admin_stock_v1","gm_stock_deduction_log",
    "gm_stocktake_device_token_v1"
):
    if marker not in text: raise SystemExit("missing V7 marker: "+marker)

if "x-stocktake-token':GM_STOCKTAKE_PRIVATE" in text or "GM_STOCKTAKE_PRIVATE=" in text:
    raise SystemExit("embedded static Stocktake token must not be present")

dst.write_text(text,encoding="utf-8")
print("patched Stocktake V7 with Wildwood bridge and paired Supabase Online stock connection")
