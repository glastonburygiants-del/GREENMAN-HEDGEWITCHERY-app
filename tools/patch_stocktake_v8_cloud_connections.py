#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit("usage: patch_stocktake_v8_cloud_connections.py input.html output.html")
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
text=src.read_text(encoding="utf-8")
if "gm-stocktake-v8-cloud-connections" in text:
    raise SystemExit("cloud connection patch already present")
if "GM_STOCKTAKE_ONLINE_EXPORT" not in text or "gm_admin_stock_v1" not in text:
    raise SystemExit("expected corrected V8 markers missing")

css=r'''
<style id="gm-stocktake-v8-cloud-connections">
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

tabs_anchor='''    <button data-page="subscribers">Subscribers</button>
   </div>
  </div>'''
connect_markup='''    <button data-page="subscribers">Subscribers</button>
   </div>
   <div class="gm-connect" aria-label="Stock connections">
    <span id="gmStallState" class="state">Stall stock not connected</span>
    <button id="gmStallSync" type="button">CONNECT / SYNC STALL</button>
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

old_mode="""function wildwoodMode(){try{const m=String(localStorage.getItem('gm_app_mode')||'').toLowerCase();return m==='master'||localStorage.getItem('gm_master_mode')==='1';}catch(e){return false}}"""
if text.count(old_mode)!=1:
    raise SystemExit(f"wildwoodMode anchor count: {text.count(old_mode)}")
text=text.replace(old_mode,"function wildwoodMode(){return true}",1)

sync_layer=r'''
const GM_STOCKTAKE_PROJECT='https://zzfgufuyetybxaeidcxu.supabase.co';
const GM_STOCKTAKE_KEY='sb_publishable_v5C9faTqdknJP9sdbgahCQ_MZVw_2gG';
const GM_STOCKTAKE_API=GM_STOCKTAKE_PROJECT+'/functions/v1/greenman-stocktake-private';
const GM_DEVICE_KEY='gm_stocktake_device_token_v2';
const GM_STALL_META='gm_stocktake_stall_cloud_meta_v1';
const GM_ONLINE_META='gm_stocktake_online_sync_v1';
let gmStallBusy=false,gmPairing=false;

function gmMsg(s,bad){
 const e=document.getElementById('gmConnectMsg');if(!e)return;
 e.textContent=String(s||'');e.classList.toggle('bad',!!bad);
}
function gmRead(k,fallback){try{return JSON.parse(localStorage.getItem(k)||JSON.stringify(fallback))}catch(e){return fallback}}
function gmCanon(v){try{return JSON.stringify(v==null?null:v)}catch(e){return String(v)}}
function gmGroups(v){return v&&typeof v==='object'&&!Array.isArray(v)?v:{}}
function gmMeta(k){try{const x=JSON.parse(localStorage.getItem(k)||'null');return x&&typeof x==='object'?x:null}catch(e){return null}}
function gmSaveMeta(k,v){localStorage.setItem(k,JSON.stringify(v))}
async function gmRawApi(action,payload,token){
 const headers={'Content-Type':'application/json','apikey':GM_STOCKTAKE_KEY};
 if(token)headers['x-stocktake-token']=token;
 const r=await fetch(GM_STOCKTAKE_API,{method:'POST',headers,body:JSON.stringify(Object.assign({action},payload||{}))});
 let d={};try{d=await r.json()}catch(e){}
 if(!r.ok){const err=new Error(d.error||('Stock request failed ('+r.status+')'));err.status=r.status;err.data=d;throw err}
 return d;
}
async function gmPair(){
 if(gmPairing)return null;
 gmPairing=true;
 try{
   const pass=window.prompt('Enter the Admin password once to connect this Stocktake.');
   if(pass==null)return null;
   const d=await gmRawApi('pair',{admin_passphrase:String(pass),label:'HedgeWitchery Stocktake V8'},null);
   if(!d.device_token)throw new Error('Stocktake pairing failed.');
   localStorage.setItem(GM_DEVICE_KEY,String(d.device_token));
   gmUpdateUi();
   return String(d.device_token);
 }finally{gmPairing=false}
}
async function gmToken(ask){
 let t=String(localStorage.getItem(GM_DEVICE_KEY)||'').trim();
 if(t)return t;
 if(!ask)return null;
 return await gmPair();
}
async function gmApi(action,payload,ask){
 let t=await gmToken(ask!==false);
 if(!t)throw new Error('Stock connection was cancelled.');
 try{return await gmRawApi(action,payload,t)}
 catch(e){
   if(e&&e.status===401){
     localStorage.removeItem(GM_DEVICE_KEY);
     if(ask===false)throw e;
     t=await gmPair();if(!t)throw e;
     return await gmRawApi(action,payload,t);
   }
   throw e;
 }
}
function gmMergeLogs(a,b){
 const out=[],seen=new Set();
 for(const x of ([]).concat(Array.isArray(a)?a:[],Array.isArray(b)?b:[])){
   const k=String((x&&x.id)||(x&&x.createdAt)||gmCanon(x));
   if(seen.has(k))continue;seen.add(k);out.push(x);
 }
 return out.slice(-1500);
}
function gmMergeStock(base,local,remote){
 const b=gmGroups(base),l=gmGroups(local),r=gmGroups(remote),out={};
 const gs=new Set([...Object.keys(b),...Object.keys(l),...Object.keys(r)]);
 for(const g of gs){
   const bg=gmGroups(b[g]),lg=gmGroups(l[g]),rg=gmGroups(r[g]),og={};
   const ks=new Set([...Object.keys(bg),...Object.keys(lg),...Object.keys(rg)]);
   for(const k of ks){
     const bv=Number(bg[k]),lv=Number(lg[k]),rv=Number(rg[k]);
     const bh=Number.isFinite(bv),lh=Number.isFinite(lv),rh=Number.isFinite(rv);
     if(lh&&rh){
       const lc=!bh||lv!==bv,rc=!bh||rv!==bv;
       if(lc&&!rc)og[k]=lv;
       else if(rc&&!lc)og[k]=rv;
       else if(lc&&rc&&lv!==rv)og[k]=Math.min(lv,rv);
       else og[k]=lv;
     }else if(lh)og[k]=lv;
     else if(rh)og[k]=rv;
     else if(k in lg)og[k]=lg[k];
     else if(k in rg)og[k]=rg[k];
   }
   out[g]=og;
 }
 return out;
}
function gmRefreshAfterStall(){
 try{collect()}catch(e){}
 try{if(current==='summary')renderSummary()}catch(e){}
}
async function gmStallCloudSync(ask){
 if(gmStallBusy||navigator.onLine===false)return false;
 gmStallBusy=true;
 try{
   const t=await gmToken(ask===true);if(!t)return false;
   const pulled=await gmRawApi('stall_pull',{},t);
   const st=pulled.state||{stock_json:{},log_json:[],revision:0};
   const remoteStock=gmGroups(st.stock_json),remoteLogs=Array.isArray(st.log_json)?st.log_json:[];
   const localStock=gmGroups(readWild()),localLogs=gmRead(WILD_LOG,[]);
   const meta=gmMeta(GM_STALL_META);

   if(!meta){
     const empty=Object.keys(remoteStock).length===0;
     if(Number(st.revision||0)===0&&empty){
       const p=await gmRawApi('stall_push',{base_revision:0,stock_json:localStock,log_json:Array.isArray(localLogs)?localLogs:[]},t);
       gmSaveMeta(GM_STALL_META,{revision:p.state.revision,stock:localStock,logs:Array.isArray(localLogs)?localLogs:[]});
     }else{
       localStorage.setItem(WILD_KEY,gmCanon(remoteStock));
       localStorage.setItem(WILD_LOG,gmCanon(remoteLogs));
       gmSaveMeta(GM_STALL_META,{revision:st.revision,stock:remoteStock,logs:remoteLogs});
       gmRefreshAfterStall();
     }
     gmUpdateUi();return true;
   }

   const localChanged=gmCanon(localStock)!==gmCanon(meta.stock)||gmCanon(localLogs)!==gmCanon(meta.logs);
   const remoteChanged=Number(st.revision||0)!==Number(meta.revision||0);

   if(localChanged&&!remoteChanged){
     const p=await gmRawApi('stall_push',{base_revision:st.revision,stock_json:localStock,log_json:Array.isArray(localLogs)?localLogs:[]},t);
     gmSaveMeta(GM_STALL_META,{revision:p.state.revision,stock:localStock,logs:Array.isArray(localLogs)?localLogs:[]});
   }else if(!localChanged&&remoteChanged){
     localStorage.setItem(WILD_KEY,gmCanon(remoteStock));
     localStorage.setItem(WILD_LOG,gmCanon(remoteLogs));
     gmSaveMeta(GM_STALL_META,{revision:st.revision,stock:remoteStock,logs:remoteLogs});
     gmRefreshAfterStall();
   }else if(localChanged&&remoteChanged){
     const mergedStock=gmMergeStock(meta.stock,localStock,remoteStock),mergedLogs=gmMergeLogs(localLogs,remoteLogs);
     const p=await gmRawApi('stall_push',{base_revision:st.revision,stock_json:mergedStock,log_json:mergedLogs},t);
     localStorage.setItem(WILD_KEY,gmCanon(mergedStock));
     localStorage.setItem(WILD_LOG,gmCanon(mergedLogs));
     gmSaveMeta(GM_STALL_META,{revision:p.state.revision,stock:mergedStock,logs:mergedLogs});
     gmRefreshAfterStall();
   }
   gmUpdateUi();return true;
 }catch(e){
   if(e&&e.status===401)localStorage.removeItem(GM_DEVICE_KEY);
   if(ask===true)gmMsg(String(e.message||e),true);
   gmUpdateUi();return false;
 }finally{gmStallBusy=false}
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
   'K:charcoal':['Charcoal Portion','Charcoal Disc','Charcoal discs'],
   'K:dish':['Incense Plate','Crystal Witch trinket dishes']
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
function gmOnlineSnapshot(){
 const snap={};
 for(const r of window.GM_STOCKTAKE_ONLINE_EXPORT()){
   if(r.online_amount!=null&&Number.isFinite(Number(r.online_amount)))snap[r.stock_id]=Number(r.online_amount);
 }
 return snap;
}
function gmApplyOnline(items){
 const rows=collect();let matched=0;
 for(const row of rows){
   const remote=gmFindRemote(row,items);if(!remote)continue;
   const available=Number(remote.stock_quantity);
   const reserved=Math.max(0,Number(remote.reserved_quantity)||0);
   const physical=Number.isFinite(Number(remote.physical_online_quantity))?Number(remote.physical_online_quantity):available+reserved;
   if(!Number.isFinite(physical)||physical<0)continue;
   const rec=split[row.id]||{},stall=Number.isFinite(row.stall)?row.stall:0,wanted=stall+physical;
   rec.online=physical;rec.onlineAvailable=Math.max(0,available);rec.onlineReserved=reserved;
   syncBusy=true;try{row.setTotal(wanted)}finally{syncBusy=false}
   rec.lastTotal=wanted;if(Number.isFinite(row.stallSpells))rec.lastWild=row.stallSpells;
   split[row.id]=rec;matched++;
 }
 saveSplit();
 for(const k of ['herbs','crystals','oils','candles','rest']){const a=frameApi(k);try{if(a&&a.refresh)a.refresh()}catch(e){}}
 if(current==='summary')renderSummary();
 return matched;
}
async function gmOnlineSend(){
 gmMsg('Sending corrected V8 Online stock…',false);
 try{
   const rows=window.GM_STOCKTAKE_ONLINE_EXPORT().filter(r=>r.online_amount!=null&&Number.isFinite(Number(r.online_amount)));
   const pushed=await gmApi('push',{items:rows},true);
   const pulled=await gmApi('pull',{},true);
   gmApplyOnline(pulled.items||[]);
   gmSaveMeta(GM_ONLINE_META,{snapshot:gmOnlineSnapshot(),server_time:pulled.server_time});
   const missed=(pushed.unmatched||[]).length+(pushed.ambiguous||[]).length+(pushed.invalid||[]).length;
   gmMsg('Online stock connected'+(missed?' · '+missed+' unmatched item'+(missed===1?'':'s')+' left unchanged':''),false);
   gmUpdateUi();
 }catch(e){gmMsg(String(e.message||e),true)}
}
async function gmOnlineLoad(){
 gmMsg('Loading Online stock…',false);
 try{
   const pulled=await gmApi('pull',{},true),matched=gmApplyOnline(pulled.items||[]);
   gmSaveMeta(GM_ONLINE_META,{snapshot:gmOnlineSnapshot(),server_time:pulled.server_time});
   gmMsg('Online stock loaded · '+matched+' matched item'+(matched===1?'':'s'),false);gmUpdateUi();
 }catch(e){gmMsg(String(e.message||e),true)}
}
async function gmOnlineSync(){
 const meta=gmMeta(GM_ONLINE_META);
 if(!meta){gmMsg('Choose SEND THIS STOCKTAKE ONLINE or LOAD ONLINE STOCK first.',true);return}
 gmMsg('Syncing Online stock…',false);
 try{
   const first=await gmApi('pull',{},true),rows=collect(),local=window.GM_STOCKTAKE_ONLINE_EXPORT();
   const last=meta.snapshot||{},push=[],conflicts=[];
   for(const l of local){
     if(l.online_amount==null||!Number.isFinite(Number(l.online_amount)))continue;
     const row=rows.find(x=>x.id===l.stock_id),remote=row&&gmFindRemote(row,first.items||[]);if(!remote)continue;
     const lv=Number(l.online_amount),rv=Number.isFinite(Number(remote.physical_online_quantity))?Number(remote.physical_online_quantity):(Number(remote.stock_quantity)||0)+(Number(remote.reserved_quantity)||0),old=Number(last[l.stock_id]);
     const haveOld=Number.isFinite(old),lc=!haveOld||Math.abs(lv-old)>1e-7,rc=!haveOld||Math.abs(rv-old)>1e-7;
     if(lc&&!rc)push.push(l);else if(lc&&rc&&Math.abs(lv-rv)>1e-7)conflicts.push(l.stock_id);
   }
   if(push.length)await gmApi('push',{items:push},true);
   const finalPull=await gmApi('pull',{},true);gmApplyOnline(finalPull.items||[]);
   gmSaveMeta(GM_ONLINE_META,{snapshot:gmOnlineSnapshot(),server_time:finalPull.server_time});
   gmMsg('Online stock synced'+(conflicts.length?' · '+conflicts.length+' simultaneous change'+(conflicts.length===1?'':'s')+' kept at the Online value':''),false);
 }catch(e){gmMsg(String(e.message||e),true)}
}
function gmUpdateUi(){
 const paired=!!String(localStorage.getItem(GM_DEVICE_KEY)||'').trim();
 const stall=document.getElementById('gmStallState'),online=document.getElementById('gmOnlineState');
 if(stall){stall.textContent=paired&&gmMeta(GM_STALL_META)?'Stall stock connected':paired?'Stall paired · sync once':'Stall stock not connected';stall.classList.toggle('ok',paired&&!!gmMeta(GM_STALL_META))}
 const ready=!!gmMeta(GM_ONLINE_META);
 if(online){online.textContent=ready?'Online stock connected':'Online stock not set up';online.classList.toggle('ok',ready)}
 const send=document.getElementById('gmOnlineSend'),load=document.getElementById('gmOnlineLoad'),sync=document.getElementById('gmOnlineSync');
 if(send)send.hidden=ready;if(load)load.hidden=ready;if(sync)sync.hidden=!ready;
}
document.getElementById('gmStallSync').onclick=async function(){gmMsg('Syncing Stall stock…',false);const ok=await gmStallCloudSync(true);if(ok)gmMsg('Stall stock synced.',false)};
document.getElementById('gmOnlineSend').onclick=gmOnlineSend;
document.getElementById('gmOnlineLoad').onclick=gmOnlineLoad;
document.getElementById('gmOnlineSync').onclick=gmOnlineSync;
window.GM_STOCKTAKE_STALL_SYNC=gmStallCloudSync;
window.GM_STOCKTAKE_SYNC_ONLINE=gmOnlineSync;
setInterval(function(){if(localStorage.getItem(GM_DEVICE_KEY))gmStallCloudSync(false)},2500);
window.addEventListener('online',function(){if(localStorage.getItem(GM_DEVICE_KEY))gmStallCloudSync(false)});
setTimeout(gmUpdateUi,100);
'''
end_anchor="setInterval(()=>{if(current==='summary')renderSummary();else if(wildwoodMode()){processNewWildwoodLogs();collect();}},1400);"
if text.count(end_anchor)!=1:
    raise SystemExit(f"V8 final interval anchor count: {text.count(end_anchor)}")
text=text.replace(end_anchor,sync_layer+"\n"+end_anchor,1)

for marker in (
    "gm-stocktake-v8-cloud-connections","stall_pull","stall_push",
    "CONNECT / SYNC STALL","SEND THIS STOCKTAKE ONLINE","SYNC ONLINE",
    "GM_STOCKTAKE_STALL_SYNC","GM_STOCKTAKE_SYNC_ONLINE"
):
    if marker not in text: raise SystemExit("missing cloud marker: "+marker)
for forbidden in ("WildwoodBridge","GMStockBridge","WILDWOOD_STOCK_BRIDGE"):
    if forbidden in text: raise SystemExit("native bridge marker must not be present: "+forbidden)

dst.write_text(text,encoding="utf-8")
print("patched corrected Stocktake V8 for Supabase Stall + Online sync without native bridge")
