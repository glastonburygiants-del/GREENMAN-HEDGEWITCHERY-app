#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit("usage: patch_main_stall_cloud_sync.py input.html output.html")
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
text=src.read_text(encoding="utf-8")
if "gm-stall-cloud-sync-v1" in text:
    raise SystemExit("stall cloud sync already present")
if "gm_admin_stock_v1" not in text or "gm_stock_deduction_log" not in text:
    raise SystemExit("expected Wildwood stock keys missing from main app")

script=r'''
<script id="gm-stall-cloud-sync-v1">
(function(){
'use strict';
const API='https://zzfgufuyetybxaeidcxu.supabase.co/functions/v1/greenman-stocktake-private';
const APIKEY='sb_publishable_v5C9faTqdknJP9sdbgahCQ_MZVw_2gG';
const TOKEN='gm_stall_cloud_device_token_v1';
const META='gm_stall_cloud_sync_meta_v1';
const STOCK='gm_admin_stock_v1';
const LOG='gm_stock_deduction_log';
let busy=false,timer=null,pairing=false;

function ownerMode(){
 try{
   const m=String(localStorage.getItem('gm_app_mode')||'').toLowerCase();
   return m==='master'||m==='wildwood'||localStorage.getItem('gm_master_mode')==='1';
 }catch(_e){return false}
}
function readObj(k,fallback){
 try{const v=JSON.parse(localStorage.getItem(k)||JSON.stringify(fallback));return v}catch(_e){return fallback}
}
function canon(v){try{return JSON.stringify(v==null?null:v)}catch(_e){return String(v)}}
function readMeta(){try{return JSON.parse(localStorage.getItem(META)||'null')}catch(_e){return null}}
function saveMeta(revision,stock,logs){
 localStorage.setItem(META,JSON.stringify({revision:Number(revision||0),stock:stock||{},logs:Array.isArray(logs)?logs:[],saved_at:new Date().toISOString()}));
}
async function api(action,body,token){
 const h={'Content-Type':'application/json','apikey':APIKEY};
 if(token)h['x-stocktake-token']=token;
 const r=await fetch(API,{method:'POST',headers:h,body:JSON.stringify(Object.assign({action},body||{}))});
 let d={};try{d=await r.json()}catch(_e){}
 if(!r.ok){const e=new Error(d.error||('Stall sync failed ('+r.status+')'));e.status=r.status;e.data=d;throw e}
 return d;
}
async function pair(){
 if(pairing)return null;
 pairing=true;
 try{
   const pass=window.prompt('Enter the Admin password once to connect Wildwood Stall stock.');
   if(pass==null)return null;
   const d=await api('pair',{admin_passphrase:String(pass),label:'HedgeWitchery Android Stall Sync'},null);
   if(!d.device_token)throw new Error('Stall sync pairing failed.');
   localStorage.setItem(TOKEN,String(d.device_token));
   return String(d.device_token);
 }finally{pairing=false}
}
async function token(){
 let t=String(localStorage.getItem(TOKEN)||'').trim();
 if(t)return t;
 return await pair();
}
function stockEmpty(o){return !o||typeof o!=='object'||Array.isArray(o)||Object.keys(o).length===0}
function mergeLogs(a,b){
 const out=[],seen=new Set();
 for(const x of ([]).concat(Array.isArray(a)?a:[],Array.isArray(b)?b:[])){
   const k=String((x&&x.id)||(x&&x.createdAt)||canon(x));
   if(seen.has(k))continue;seen.add(k);out.push(x);
 }
 return out.slice(-1500);
}
function groups(o){return o&&typeof o==='object'&&!Array.isArray(o)?o:{}}
function mergeStock(base,local,remote){
 const b=groups(base),l=groups(local),r=groups(remote),out={};
 const gs=new Set([...Object.keys(b),...Object.keys(l),...Object.keys(r)]);
 for(const g of gs){
   const bg=groups(b[g]),lg=groups(l[g]),rg=groups(r[g]),og={};
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
async function pushState(t,revision,stock,logs){
 try{
   return await api('stall_push',{base_revision:Number(revision||0),stock_json:stock,log_json:logs},t);
 }catch(e){
   if(e&&e.status===401){localStorage.removeItem(TOKEN);throw e}
   throw e;
 }
}
async function sync(){
 if(busy||!ownerMode()||navigator.onLine===false)return;
 busy=true;
 try{
   const t=await token();if(!t)return;
   const pulled=await api('stall_pull',{},t);
   const state=pulled.state||{stock_json:{},log_json:[],revision:0};
   const remoteStock=groups(state.stock_json),remoteLogs=Array.isArray(state.log_json)?state.log_json:[];
   const localStock=groups(readObj(STOCK,{})),localLogs=readObj(LOG,[]);
   const meta=readMeta();

   if(!meta){
     if(Number(state.revision||0)===0&&stockEmpty(remoteStock)){
       const p=await pushState(t,0,localStock,Array.isArray(localLogs)?localLogs:[]);
       saveMeta(p.state.revision,localStock,Array.isArray(localLogs)?localLogs:[]);
     }else{
       localStorage.setItem(STOCK,canon(remoteStock));
       localStorage.setItem(LOG,canon(remoteLogs));
       saveMeta(state.revision,remoteStock,remoteLogs);
     }
     return;
   }

   const localChanged=canon(localStock)!==canon(meta.stock)||canon(localLogs)!==canon(meta.logs);
   const remoteChanged=Number(state.revision||0)!==Number(meta.revision||0);

   if(localChanged&&!remoteChanged){
     const p=await pushState(t,state.revision,localStock,Array.isArray(localLogs)?localLogs:[]);
     saveMeta(p.state.revision,localStock,Array.isArray(localLogs)?localLogs:[]);
     return;
   }
   if(!localChanged&&remoteChanged){
     localStorage.setItem(STOCK,canon(remoteStock));
     localStorage.setItem(LOG,canon(remoteLogs));
     saveMeta(state.revision,remoteStock,remoteLogs);
     try{window.dispatchEvent(new CustomEvent('gm-wildwood-stock-cloud-update'))}catch(_e){}
     return;
   }
   if(localChanged&&remoteChanged){
     const mergedStock=mergeStock(meta.stock,localStock,remoteStock);
     const mergedLogs=mergeLogs(localLogs,remoteLogs);
     const p=await pushState(t,state.revision,mergedStock,mergedLogs);
     localStorage.setItem(STOCK,canon(mergedStock));
     localStorage.setItem(LOG,canon(mergedLogs));
     saveMeta(p.state.revision,mergedStock,mergedLogs);
     try{window.dispatchEvent(new CustomEvent('gm-wildwood-stock-cloud-update'))}catch(_e){}
   }
 }catch(e){
   if(e&&e.status===401)localStorage.removeItem(TOKEN);
 }finally{busy=false}
}
function start(){
 if(timer)clearInterval(timer);
 timer=setInterval(sync,2500);
 setTimeout(sync,300);
}
window.GM_WILDWOOD_STALL_CLOUD_SYNC=sync;
window.addEventListener('online',sync);
window.addEventListener('focus',sync);
document.addEventListener('visibilitychange',function(){if(!document.hidden)sync()});
start();
})();
</script>
'''
pos=text.rfind("</body>")
if pos<0: raise SystemExit("outer body close missing")
text=text[:pos]+script+"\n"+text[pos:]
for m in ("gm-stall-cloud-sync-v1","stall_pull","stall_push","gm_admin_stock_v1","gm_stock_deduction_log"):
    if m not in text: raise SystemExit("missing marker "+m)
dst.write_text(text,encoding="utf-8")
print("added pure-Web Wildwood Stall cloud sync; no native Android bridge")
