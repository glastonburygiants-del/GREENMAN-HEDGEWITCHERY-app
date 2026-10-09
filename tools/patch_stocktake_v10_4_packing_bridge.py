#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_stocktake_v10_4_packing_bridge.py input.html output.html")

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding="utf-8")

css_anchor = "#gmPrintFrame{display:block!important;position:fixed;left:-10000px;top:0;width:57mm;height:90mm;border:0}"
packing_css = r"""
.packfilters{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px}
.packfilters button{min-height:38px;border:1px solid var(--line);border-radius:999px;background:#fffaf0;padding:7px 11px;font:700 11px Georgia,serif}
.packfilters button.on{background:var(--green);color:#fff;border-color:var(--green)}
.packcards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-bottom:10px}
.packcard{background:var(--paper);border:1px solid var(--line);border-radius:9px;padding:9px}
.packcard span{display:block;font-size:10px;color:var(--muted)}
.packcard strong{display:block;color:var(--green);font-size:18px;margin-top:2px}
.packorder{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:11px;margin:10px 0;box-shadow:0 1px 0 rgba(0,0,0,.03)}
.packorder.waiting{border-left:7px solid #a56b28}
.packorder.ready{border-left:7px solid #3d6b4d}
.packorder.posted{opacity:.78;border-left:7px solid #6b6b6b}
.packtop{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;flex-wrap:wrap}
.packtitle{font-size:18px;color:var(--green);font-weight:700}
.packmeta{font-size:11px;color:var(--muted);line-height:1.45;margin-top:3px}
.packstatus{border-radius:999px;padding:6px 9px;background:#eee2c8;border:1px solid var(--line);font-size:10px;font-weight:700;white-space:nowrap}
.packstatus.waiting{background:#fff0d8;border-color:#cfaa62}
.packstatus.ready{background:#e4f0e5;border-color:#8fb091}
.packsection{margin-top:10px}
.packsection h3{font-size:13px;color:var(--green);margin:0 0 6px;border-bottom:1px solid #dfd1b1;padding-bottom:4px}
.packgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px}
.packitem{display:grid;grid-template-columns:30px minmax(0,1fr) auto;gap:7px;align-items:center;background:#fffaf0;border:1px solid #e3d7ba;border-radius:8px;padding:7px}
.packitem input{width:22px;height:22px;accent-color:var(--green)}
.packitem.done .packname{text-decoration:line-through;opacity:.55}
.packitem.missing{border-color:#b6712d;background:#fff1df}
.packname{font-size:12px;font-weight:700}
.packrole{font-size:9px;color:var(--muted);margin-top:1px}
.packqty{font-size:11px;font-weight:700;white-space:nowrap}
.packcustomer{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px;margin-top:10px}
.packbox{background:#f7efdc;border:1px solid #dfd1b1;border-radius:9px;padding:8px;font-size:12px;line-height:1.45}
.packprogress{font-size:11px;font-weight:700;color:var(--green)}
.packdanger{background:#fff0ee!important;border-color:#b45b50!important;color:#7a241d!important}
.packempty{padding:20px;text-align:center;color:var(--muted);background:var(--paper);border:1px solid var(--line);border-radius:10px}
@media(max-width:700px){.packcards{grid-template-columns:repeat(2,minmax(0,1fr))}.packgrid,.packcustomer{grid-template-columns:1fr}.packtop{display:block}.packstatus{display:inline-block;margin-top:6px}}
"""
if css_anchor not in text:
    raise SystemExit("packing CSS anchor missing")
text = text.replace(css_anchor, packing_css + "\n" + css_anchor, 1)

old_orders = """  <section id="orders" class="backoffice">
   <div class="bohead"><h2>Orders</h2><div class="borow"><button class="primary" onclick="gmBackRefresh(true)">REFRESH ORDERS</button></div></div>
   <div id="gmOrdersBody"></div>
  </section>"""
new_orders = """  <section id="orders" class="backoffice">
   <div class="bohead">
    <h2>Packing Desk</h2>
    <div class="borow"><button class="primary" onclick="gmBackRefresh(true)">REFRESH ORDERS</button><button onclick="gmOpenGreenmanApp()">OPEN GREENMAN APP</button></div>
    <div class="packfilters" id="gmOrderFilters">
     <button class="on" data-view="live" onclick="gmSetOrderView('live')">TO PACK</button>
     <button data-view="waiting" onclick="gmSetOrderView('waiting')">WAITING FOR STOCK</button>
     <button data-view="posted" onclick="gmSetOrderView('posted')">POSTED</button>
     <button data-view="unpaid" onclick="gmSetOrderView('unpaid')">TEST / UNPAID</button>
    </div>
   </div>
   <div id="gmOrderCards" class="packcards"></div>
   <div id="gmOrdersBody"></div>
  </section>"""
if old_orders not in text:
    raise SystemExit("orders section anchor missing")
text = text.replace(old_orders, new_orders, 1)

start = text.find("function gmBackorderText(o){")
end = text.find("function gmPrintAddressLabel(id){", start)
if start < 0 or end < 0:
    raise SystemExit("orders code boundaries missing")

orders_js = r"""
let gmOrderView='live';
const GM_PACK_PROGRESS='gm_stocktake_pack_progress_v1';
function gmPackStore(){try{const x=JSON.parse(localStorage.getItem(GM_PACK_PROGRESS)||'{}');return x&&typeof x==='object'?x:{}}catch(e){return {}}}
function gmPackSave(x){localStorage.setItem(GM_PACK_PROGRESS,JSON.stringify(x||{}))}
function gmPackItemKey(it,i){return String(it.id||((it.item_role||'item')+'|'+(it.item_name||'')+'|'+i))}
function gmPackDone(orderId,key){const s=gmPackStore();return !!(s[String(orderId)]&&s[String(orderId)][String(key)])}
function gmTogglePackItem(orderId,key,checked){
 const s=gmPackStore(),id=String(orderId),k=String(key);s[id]=s[id]||{};if(checked)s[id][k]=1;else delete s[id][k];gmPackSave(s);gmRenderOrders();
}
function gmOrderSpell(o){
 const sd=o&&o.spell_data||{},sp=Array.isArray(sd.spells)&&sd.spells.length?sd.spells[0]:{};
 return {
  name:o.spell_name||sp.spell_name||'Spell order',
  level:sp.spell_level||sd.spell_level||'',
  category:sp.spell_category||sd.spell_category||'',
  method:sp.method||sd.method||sd.finish_type||'',
  quantity:Number(sp.quantity||1)||1,
  postage:sd.postage_band||o.tracking_service||''
 };
}
function gmPackingItems(o){
 let rows=gmOrderItems(o.id).slice();
 if(!rows.length){
   const sd=o&&o.spell_data||{},sp=Array.isArray(sd.spells)&&sd.spells.length?sd.spells[0]:{};
   rows=(sp.items||[]).map(function(x,i){return {id:'fallback-'+i,item_name:x.item_name,item_role:x.item_role,quantity:1,unit:'each',stock_item_id:null,backordered_quantity:0}});
 }
 const order={Candle:10,'Earth Herb':20,'Air Herb':21,'Fire Herb':22,'Water Herb':23,Crystal:40,Rune:50,Oil:60,Finish:70,'Method Supply':70};
 rows.sort(function(a,b){
   const ar=String(a.item_role||''),br=String(b.item_role||'');
   const av=order[ar]||(ar.indexOf('Herb')>=0?30:80),bv=order[br]||(br.indexOf('Herb')>=0?30:80);
   return av-bv||ar.localeCompare(br)||String(a.item_name||'').localeCompare(String(b.item_name||''));
 });
 return rows;
}
function gmMissingItem(o,it){
 const backs=gmOrderBacks(o.id);
 if(Number(it.backordered_quantity||0)>0)return true;
 return backs.some(function(b){return Number(b.stock_item_id)===Number(it.stock_item_id)&&Number(b.quantity_needed||0)>0});
}
function gmPackProgress(o){
 const rows=gmPackingItems(o),done=rows.filter(function(it,i){return gmPackDone(o.id,gmPackItemKey(it,i))}).length;
 return {done:done,total:rows.length};
}
function gmStatusLabel(st){
 st=String(st||'new');
 return ({new:'TO GATHER',gathering:'GATHERING',waiting_for_stock:'WAITING FOR STOCK',packed:'PACKED',ready_to_post:'READY TO POST',dispatched:'POSTED',complete:'POSTED'})[st]||st.replaceAll('_',' ').toUpperCase();
}
function gmBackorderText(o){
 const backs=gmOrderBacks(o.id);if(!backs.length)return '';
 const items=gmOrderItems(o.id);
 const names=backs.map(function(b){const it=items.find(x=>Number(x.stock_item_id)===Number(b.stock_item_id));return gmE((it&&it.item_name)||'Stock item')+' · '+Number(b.quantity_needed||0)+' '+gmE(b.unit||'')}).join('<br>');
 return '<div class="bowarn"><b>Waiting for stock</b><br>'+names+'</div>';
}
function gmOrderViewMatch(o){
 const paid=o.payment_status==='paid',st=String(o.fulfilment_status||'new');
 if(gmOrderView==='unpaid')return !paid;
 if(gmOrderView==='posted')return paid&&(st==='dispatched'||st==='complete');
 if(gmOrderView==='waiting')return paid&&st==='waiting_for_stock';
 return paid&&st!=='dispatched'&&st!=='complete'&&st!=='waiting_for_stock';
}
function gmSetOrderView(v){
 gmOrderView=v;
 document.querySelectorAll('#gmOrderFilters button').forEach(function(b){b.classList.toggle('on',b.dataset.view===v)});
 gmRenderOrders();
}
function gmPackingHtml(o){
 const rows=gmPackingItems(o);
 if(!rows.length)return '<div class="packempty">No packing items were recorded for this order.</div>';
 return '<div class="packgrid">'+rows.map(function(it,i){
   const key=gmPackItemKey(it,i),done=gmPackDone(o.id,key),missing=gmMissingItem(o,it);
   const qty=Number(it.quantity||1),unit=String(it.unit||'each');
   return '<label class="packitem '+(done?'done ':'')+(missing?'missing':'')+'"><input type="checkbox" '+(done?'checked ':'')+'onchange="gmTogglePackItem(\''+gmE(o.id)+'\',\''+gmE(key).replaceAll("'","&#39;")+'\',this.checked)"><div><div class="packname">'+gmE(it.item_name||'Item')+'</div><div class="packrole">'+gmE(it.item_role||'Pack item')+(missing?' · WAITING FOR STOCK':'')+'</div></div><div class="packqty">'+qty+' '+gmE(unit)+'</div></label>';
 }).join('')+'</div>';
}
function gmRenderOrders(){
 if(!gmBackData)return;
 const all=gmBackData.orders||[],body=document.getElementById('gmOrdersBody');
 const counts={
   live:all.filter(function(o){const s=String(o.fulfilment_status||'new');return o.payment_status==='paid'&&s!=='dispatched'&&s!=='complete'&&s!=='waiting_for_stock'}).length,
   waiting:all.filter(function(o){return o.payment_status==='paid'&&String(o.fulfilment_status||'new')==='waiting_for_stock'}).length,
   ready:all.filter(function(o){const s=String(o.fulfilment_status||'new');return o.payment_status==='paid'&&(s==='packed'||s==='ready_to_post')}).length,
   posted:all.filter(function(o){const s=String(o.fulfilment_status||'new');return o.payment_status==='paid'&&(s==='dispatched'||s==='complete')}).length
 };
 const cards=document.getElementById('gmOrderCards');
 if(cards)cards.innerHTML=
   '<div class="packcard"><span>To pack</span><strong>'+counts.live+'</strong></div>'+
   '<div class="packcard"><span>Waiting for stock</span><strong>'+counts.waiting+'</strong></div>'+
   '<div class="packcard"><span>Packed / ready</span><strong>'+counts.ready+'</strong></div>'+
   '<div class="packcard"><span>Posted</span><strong>'+counts.posted+'</strong></div>';
 const orders=all.filter(gmOrderViewMatch);
 if(!orders.length){body.innerHTML='<div class="packempty">Nothing in this section.</div>';return}
 body.innerHTML=orders.map(function(o){
   const st=String(o.fulfilment_status||'new'),paid=o.payment_status==='paid',sp=gmOrderSpell(o),prog=gmPackProgress(o);
   const statusClass=st==='waiting_for_stock'?'waiting':(st==='packed'||st==='ready_to_post'?'ready':(st==='dispatched'||st==='complete'?'ready':''));
   const addr='<div class="packbox"><b>Send to</b><br><b>'+gmE(o.shipping_name||'Name not entered')+'</b><br>'+gmAddr(o)+(o.customer_email?'<br>'+gmE(o.customer_email):'')+'</div>';
   const spell='<div class="packbox"><b>Spell</b><br>'+gmE(sp.name)+(sp.category?'<br>'+gmE(sp.category):'')+(sp.level?'<br><b>Level:</b> '+gmE(sp.level):'')+(sp.method?'<br><b>Finish:</b> '+gmE(sp.method):'')+(sp.quantity>1?'<br><b>Quantity:</b> '+sp.quantity:'')+(sp.postage?'<br><b>Delivery:</b> '+gmE(sp.postage):'')+'</div>';
   const tracking=o.tracking_number?'<div class="bonote"><b>'+gmE(o.tracking_service||'Royal Mail')+'</b> · '+gmE(o.tracking_number)+'</div>':'';
   let controls='';
   if(paid&&st!=='dispatched'&&st!=='complete'){
     controls='<div class="borow"><button onclick="gmSetOrderStatus(\''+o.id+'\',\'new\')">TO GATHER</button><button onclick="gmSetOrderStatus(\''+o.id+'\',\'gathering\')">GATHERING</button><button onclick="gmSetOrderStatus(\''+o.id+'\',\'packed\')">PACKED</button><button onclick="gmSetOrderStatus(\''+o.id+'\',\'ready_to_post\')">READY TO POST</button></div>'+
      '<div class="borow"><button onclick="gmPrintPackingList(\''+o.id+'\')">PRINT PACKING LIST</button><button onclick="gmPrintAddressLabel(\''+o.id+'\')">PRINT ADDRESS LABEL</button></div>'+
      '<div class="borow"><select id="svc-'+o.id+'"><option>Royal Mail Tracked 48 with Signature</option><option>Royal Mail Tracked 24 with Signature</option></select><input id="trk-'+o.id+'" placeholder="Tracking number"><button class="primary" onclick="gmDispatchOrder(\''+o.id+'\')">MARK AS POSTED + SEND EMAIL</button></div>';
   }else{
     controls='<div class="borow">'+(paid?'<button onclick="gmPrintPackingList(\''+o.id+'\')">PRINT PACKING LIST</button><button onclick="gmPrintAddressLabel(\''+o.id+'\')">PRINT ADDRESS LABEL</button>':'')+'</div>';
   }
   controls+='<div class="borow"><button class="packdanger" onclick="gmDeleteOrder(\''+o.id+'\')">DELETE ORDER</button></div>';
   return '<div class="packorder '+statusClass+'"><div class="packtop"><div><div class="packtitle">'+gmE(sp.name)+'</div><div class="packmeta">'+gmDate(o.created_at)+' · Order '+gmE(String(o.id).slice(0,8).toUpperCase())+' · '+gmP(o.total_pence)+' · '+gmE(o.payment_status||'')+'</div></div><div class="packstatus '+statusClass+'">'+gmStatusLabel(st)+'</div></div>'+
    '<div class="packcustomer">'+spell+addr+'</div>'+gmBackorderText(o)+
    '<div class="packsection"><h3>PACKING LIST <span class="packprogress">· '+prog.done+' / '+prog.total+' packed</span></h3>'+gmPackingHtml(o)+'</div>'+
    tracking+controls+'</div>';
 }).join('');
}
async function gmSetOrderStatus(id,status){
 try{await gmApi('set_order_status',{order_id:id,status:status},true);await gmBackRefresh(true)}
 catch(e){gmMsg(String(e.message||e),true)}
}
async function gmDeleteOrder(id){
 const o=gmBackData&&(gmBackData.orders||[]).find(function(x){return String(x.id)===String(id)});
 const title=o?(o.spell_name||'this order'):'this order';
 if(!confirm('DELETE '+title+'?\n\nThis removes the order, its packing items and its backorder records. Stock quantities are NOT put back automatically.'))return;
 try{
   await gmApi('delete_order',{order_id:id},true);

   // Remove it from the visible back-office data immediately.
   // The following dashboard refresh then verifies Supabase agrees.
   if(gmBackData){
     gmBackData.orders=(gmBackData.orders||[]).filter(function(x){return String(x.id)!==String(id)});
     gmBackData.order_items=(gmBackData.order_items||[]).filter(function(x){return String(x.order_id)!==String(id)});
     gmBackData.backorders=(gmBackData.backorders||[]).filter(function(x){return String(x.order_id)!==String(id)});
   }
   const ps=gmPackStore();delete ps[String(id)];gmPackSave(ps);
   gmRenderBack();
   gmMsg('Order deleted. Stock quantities were left unchanged.',false);

   try{await gmBackRefresh(true)}catch(_refreshError){}
 }catch(e){gmMsg(String(e.message||e),true)}
}
function gmPrintPackingList(id){
 if(!gmBackData)return;
 const o=(gmBackData.orders||[]).find(function(x){return String(x.id)===String(id)});if(!o)return;
 const sp=gmOrderSpell(o),items=gmPackingItems(o),addr=gmAddr(o);
 const rows=items.map(function(it){return '<tr><td>'+gmE(it.item_role||'Item')+'</td><td><b>'+gmE(it.item_name||'')+'</b></td><td>'+Number(it.quantity||1)+' '+gmE(it.unit||'each')+'</td></tr>'}).join('');
 const html='<!doctype html><html><head><meta charset="utf-8"><style>@page{size:A4;margin:12mm}body{font-family:Arial,sans-serif;color:#111}h1{font-size:20pt;margin:0 0 3mm}h2{font-size:13pt;margin:6mm 0 2mm}.meta{font-size:10pt;line-height:1.5}.grid{display:grid;grid-template-columns:1fr 1fr;gap:8mm}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #bbb;padding:2.5mm;text-align:left;font-size:10pt}.check{width:8mm}.footer{font-size:8pt;margin-top:8mm}</style></head><body><h1>Greenman HedgeWitchery Apothecary · Packing List</h1><div class="meta"><b>'+gmE(sp.name)+'</b> · '+gmE(sp.level)+' · '+gmE(sp.method)+'<br>Order '+gmE(String(o.id).toUpperCase())+' · '+gmDate(o.created_at)+'</div><div class="grid"><div><h2>Pack</h2><table><tr><th class="check">✓</th><th>Item</th><th>Qty</th></tr>'+items.map(function(it){return '<tr><td>□</td><td><small>'+gmE(it.item_role||'')+'</small><br><b>'+gmE(it.item_name||'')+'</b></td><td>'+Number(it.quantity||1)+' '+gmE(it.unit||'each')+'</td></tr>'}).join('')+'</table></div><div><h2>Send to</h2><div class="meta"><b>'+gmE(o.shipping_name||'')+'</b><br>'+addr+'<br><br>'+gmE(o.customer_email||'')+'</div><h2>Delivery</h2><div class="meta">'+gmE(sp.postage||'')+'</div></div></div><div class="footer">Greenman HedgeWitchery Apothecary · '+gmE(String(o.id).slice(0,8).toUpperCase())+'</div></body></html>';
 try{if(window.GreenmanStocktake&&window.GreenmanStocktake.printHtml){window.GreenmanStocktake.printHtml(html,'Greenman packing list');return}}catch(e){}
 const doc=document.getElementById('gmPrintFrame').contentDocument;doc.open();doc.write(html);doc.close();setTimeout(function(){document.getElementById('gmPrintFrame').contentWindow.print()},120);
}
async function gmDispatchOrder(id){
 const service=document.getElementById('svc-'+id).value,tracking=document.getElementById('trk-'+id).value.trim();
 if(!tracking){gmMsg('Enter the Royal Mail tracking number first.',true);return}
 try{
   const d=await gmApi('dispatch_order',{order_id:id,tracking_service:service,tracking_number:tracking},true);
   gmMsg(d.email&&d.email.sent?'Order marked posted and dispatch email sent.':'Order marked posted. The customer email needs checking.',!(d.email&&d.email.sent));
   try{const cloud=await gmApi('pull',{},true);gmApplyOnline(cloud.items||[])}catch(_e){}
   await gmBackRefresh(true);
 }catch(e){gmMsg(String(e.message||e),true)}
}
"""
text = text[:start] + orders_js + "\n" + text[end:]

bridge_anchor = "setInterval(()=>{if(current==='summary')renderSummary();else if(wildwoodMode()){processNewWildwoodLogs();collect();}},1400);"
if bridge_anchor not in text:
    raise SystemExit("same-device bridge insertion anchor missing")
bridge_js = r"""
// V10.4 same-device Wildwood bridge. Main app owns Wildwood; Online remains Supabase.
const GM_MAIN_WILD_META='gm_stocktake_mainapp_wildwood_meta_v1';
function gmMainBridge(){return !!(window.GreenmanStocktake&&typeof window.GreenmanStocktake.readMainWildwood==='function')}
function gmMainInstalled(){try{return gmMainBridge()&&!!window.GreenmanStocktake.mainAppInstalled()}catch(e){return false}}
function gmParseBridge(raw){try{return JSON.parse(String(raw||'{}'))||{}}catch(e){return {}}}
function gmWildCanon(stock,logs){return gmCanon({stock:gmGroups(stock),logs:Array.isArray(logs)?logs:[]})}
function gmReadMainWild(){
 if(!gmMainBridge())return {installed:false,ready:false};
 const d=gmParseBridge(window.GreenmanStocktake.readMainWildwood());
 if(d.stock_json!==undefined){try{d.stock=JSON.parse(d.stock_json||'{}')}catch(e){d.stock={}}}
 if(d.log_json!==undefined){try{d.logs=JSON.parse(d.log_json||'[]')}catch(e){d.logs=[]}}
 return d;
}
function gmWriteMainWild(stock,logs){
 if(!gmMainBridge())return {ok:false};
 return gmParseBridge(window.GreenmanStocktake.writeMainWildwood(JSON.stringify(gmGroups(stock)),JSON.stringify(Array.isArray(logs)?logs:[])));
}
async function gmStallDeviceSync(showMessage){
 try{
   if(!gmMainBridge()||!gmMainInstalled()){
     const st=document.getElementById('gmStallState');if(st){st.textContent='Greenman app not linked on this device';st.classList.remove('ok')}
     if(showMessage)gmMsg('The Greenman HedgeWitchery Apothecary app is not installed on this device.',true);
     return false;
   }
   const remote=gmReadMainWild(),localStock=gmGroups(readWild()),localLogs=gmRead(WILD_LOG,[]),meta=gmMeta(GM_MAIN_WILD_META);
   if(!remote.ready){
     const wr=gmWriteMainWild(localStock,localLogs);
     if(!wr.ok)throw new Error('Wildwood could not be linked to the main app.');
     gmSaveMeta(GM_MAIN_WILD_META,{revision:Number(wr.revision||0),canon:gmWildCanon(localStock,localLogs)});
   }else{
     const remoteStock=gmGroups(remote.stock),remoteLogs=Array.isArray(remote.logs)?remote.logs:[],rev=Number(remote.revision||0);
     const localCanon=gmWildCanon(localStock,localLogs),remoteCanon=gmWildCanon(remoteStock,remoteLogs);
     if(!meta||rev>Number(meta.revision||0)){
       localStorage.setItem(WILD_KEY,JSON.stringify(remoteStock));
       localStorage.setItem(WILD_LOG,JSON.stringify(remoteLogs));
       gmSaveMeta(GM_MAIN_WILD_META,{revision:rev,canon:remoteCanon});
       gmRefreshAfterStall();
     }else if(localCanon!==String(meta.canon||'')){
       const wr=gmWriteMainWild(localStock,localLogs);
       if(!wr.ok)throw new Error('Wildwood changes could not be sent to the main app.');
       gmSaveMeta(GM_MAIN_WILD_META,{revision:Number(wr.revision||rev),canon:localCanon});
     }
   }
   const st=document.getElementById('gmStallState');if(st){st.textContent='Wildwood linked to Greenman app';st.classList.add('ok')}
   if(showMessage)gmMsg('Wildwood stock synced with the Greenman app on this device.',false);
   return true;
 }catch(e){
   const st=document.getElementById('gmStallState');if(st){st.textContent='Wildwood app link needs attention';st.classList.remove('ok')}
   if(showMessage)gmMsg(String(e.message||e),true);
   return false;
 }
}
function gmOpenGreenmanApp(){
 try{if(window.GreenmanStocktake&&window.GreenmanStocktake.openMainApp&&window.GreenmanStocktake.openMainApp())return}catch(e){}
 gmMsg('The Greenman HedgeWitchery Apothecary app is not installed on this device.',true);
}
try{
 const stallBtn=document.getElementById('gmStallSync');
 if(stallBtn){stallBtn.textContent='SYNC WILDWOOD WITH APP';stallBtn.onclick=function(){gmStallDeviceSync(true)}}
 const connect=stallBtn&&stallBtn.parentElement;
 if(connect&&!document.getElementById('gmOpenGreenman')){
   const b=document.createElement('button');b.id='gmOpenGreenman';b.type='button';b.textContent='OPEN GREENMAN APP';b.onclick=gmOpenGreenmanApp;
   connect.insertBefore(b,document.getElementById('gmOnlineState'));
 }
 const oldUi=gmUpdateUi;
 gmUpdateUi=function(){oldUi();const st=document.getElementById('gmStallState');if(st){const linked=gmMainInstalled()&&!!gmMeta(GM_MAIN_WILD_META);st.textContent=linked?'Wildwood linked to Greenman app':gmMainInstalled()?'Greenman app found · sync Wildwood':'Greenman app not linked on this device';st.classList.toggle('ok',linked)}};
 gmStallCloudSync=gmStallDeviceSync;
 window.GM_STOCKTAKE_STALL_SYNC=gmStallDeviceSync;
 setInterval(function(){gmStallDeviceSync(false)},2500);
 setTimeout(function(){gmStallDeviceSync(false);gmUpdateUi()},350);
}catch(e){}
"""
text = text.replace(bridge_anchor, bridge_js + "\n" + bridge_anchor, 1)

for marker in [
    "Packing Desk",
    "DELETE ORDER",
    "gmDeleteOrder",
    "gmPrintPackingList",
    "SYNC WILDWOOD WITH APP",
    "gmStallDeviceSync",
    "OPEN GREENMAN APP",
]:
    if marker not in text:
        raise SystemExit("missing V10.4 marker: " + marker)

dst.write_text(text, encoding="utf-8")
print("patched Stocktake V10.4 packing desk + delete orders + same-device Wildwood bridge")
