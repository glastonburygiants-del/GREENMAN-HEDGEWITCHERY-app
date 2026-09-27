#!/usr/bin/env python3
"""FV3.3 paid checkout completion + thermal instruction slip patch.

Runs after the existing Journal sales patches. It edits only the embedded
PAGES.journal HTML string and leaves every other embedded room byte-for-byte
untouched.
"""
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_fv3_sales_paid_confirmation.py INPUT OUTPUT')

src, out = map(Path, sys.argv[1:])
outer = src.read_text(encoding='utf-8')
pages_at = outer.index('const PAGES = ')
key_at = outer.index('"journal":', pages_at) + len('"journal":')
journal, used = json.JSONDecoder().raw_decode(outer[key_at:])
original = journal

def once(anchor, replacement, label):
    global journal
    n = journal.count(anchor)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly 1 anchor, found {n}')
    journal = journal.replace(anchor, replacement, 1)

old_payload = "function gmSalePayload(e){const i=(e&&e.items)||{};const items=[];function add(type,name,role){name=cleanName(name);if(name)items.push({item_type:type,item_name:name,item_role:role});}add('Candle',i.candle,'Candle');add('Herb',i.earth,'Earth Herb');add('Herb',i.air,'Air Herb');add('Herb',i.fire,'Fire Herb');add('Herb',i.water,'Water Herb');(i.spellHerbs||[]).forEach((h,n)=>add('Herb',h,'Spell Herb '+(n+1)));add('Crystal',i.crystal,'Crystal');add('Rune',i.rune,'Rune');add('Oil',i.oil,'Oil');return{journal_entry_id:e.entryId||'',spell_level:gmSaleLevel(e),spell_name:e.spellName||'Greenman Spell Kit',method:e.method||'Spell Jar',items:items};}"
new_payload = r"""const GM_SHOP_PENDING='gm_greenman_pending_order_v1';
const GM_SHOP_STATUS='https://zzfgufuyetybxaeidcxu.supabase.co/functions/v1/shop-order-status';
function gmSaleMethodLabel(v){v=String(v||'').toLowerCase();if(v.includes('smoke')||v.includes('flame')||v.includes('burn'))return'Smoke and Flame';if(v.includes('charm')||v.includes('bag'))return'Charm Bag';return'Spell Jar';}
function gmThermalSteps(v){
 const m=gmSaleMethodLabel(v),f='Complete the spell using the finishing guidance in the app.';
 if(m==='Smoke and Flame')return[
  'Hold the crystal until warm.','Anoint the candle with oil and light it.','Place the rune beside the candle.','Light three charcoal discs and place them in a heatproof dish.','Place the crystal in the middle of the charcoal discs. If it cracks or changes, that becomes part of the magic.','Add the Earth herb to a grinder or bowl.','Add the Air herb.','Add the Fire herb.','Add the Water herb, then grind and mix all four herbs together.','Add five drops of oil to bind the base mixture.','Add the base mixture to the charcoal.','Call the Goddess.','Call the God.','Add each extra spell herb to the charcoal.','When everything has finished burning and the ash is cool, rub the ash onto the rune.','Take the crystal once it is cool enough. '+f,'Hold the wooden rune until you feel the spell is done, then burn it.'
 ];
 if(m==='Charm Bag')return[
  'Warm the crystal in your hand, then place it at the bottom of the charm bag.','Anoint the candle with oil and light it.','Add the Earth herb to the charm bag.','Add the Air herb to the charm bag.','Add the Fire herb to the charm bag.','Add the Water herb to the charm bag.','Call the Goddess.','Call the God.','Add each extra spell herb while holding the spell’s intention.','Pass the wooden rune through the candle flame and allow it to burn a little.','Anoint the rune with oil to bind the magic.','Place the rune in the charm bag to seal the magic.',f
 ];
 return[
  'Hold the crystal until warm, then place it at the bottom of the jar.','Anoint the top half of the candle with one drop of oil.','Add the Earth herb as the first layer.','Add the Air herb as the next layer.','Add the Fire herb as the next layer.','Add the Water herb as the next layer.','Call the Goddess.','Call the God.','Add each extra spell herb while holding the spell’s intention.','Add five drops of oil to bind the herbs.','Place the rune in the jar to seal the magic.','Close the jar, light the candle, and use the candle wax to seal the jar.',f
 ];
}
function gmThermalPngBase64(sp){
 try{
  const W=456,M=22,MW=W-M*2,tmp=document.createElement('canvas');tmp.width=W;tmp.height=10;let c=tmp.getContext('2d');if(!c)return'';
  const rows=[];
  function add(text,font,lh,center){text=String(text||'').trim();if(!text)return;c.font=font;const words=text.split(/\s+/);let line='';for(const w of words){const test=line?line+' '+w:w;if(c.measureText(test).width>MW&&line){rows.push({text:line,font,lh,center:!!center});line=w;}else line=test;}if(line)rows.push({text:line,font,lh,center:!!center});}
  function gap(n){rows.push({gap:n});}
  add('GREENMAN HEDGEWITCHERY APOTHECARY','700 17px Arial',22,true);gap(6);
  add(sp.spell_name||'Your Spell','700 22px Arial',28,true);add(gmSaleMethodLabel(sp.method),'700 17px Arial',23,true);gap(10);
  add('SIMPLE INSTRUCTIONS','700 17px Arial',24,true);gap(4);
  gmThermalSteps(sp.method).forEach((x,i)=>{add((i+1)+'. '+x,'15px Arial',20,false);gap(3);});
  gap(7);add('SEE APP FOR FULL INSTRUCTIONS.','700 16px Arial',22,true);
  let h=24;for(const r of rows)h+=r.gap||r.lh;h+=24;tmp.height=Math.max(180,h);
  c=tmp.getContext('2d');c.fillStyle='#fff';c.fillRect(0,0,W,tmp.height);c.fillStyle='#000';c.textBaseline='top';let y=24;
  for(const r of rows){if(r.gap){y+=r.gap;continue;}c.font=r.font;c.textAlign=r.center?'center':'left';c.fillText(r.text,r.center?W/2:M,y);y+=r.lh;}
  return(tmp.toDataURL('image/png').split(',')[1]||'');
 }catch(e){return'';}
}
function gmSalePayload(e){const i=(e&&e.items)||{};const items=[];function add(type,name,role){name=cleanName(name);if(name)items.push({item_type:type,item_name:name,item_role:role});}add('Candle',i.candle,'Candle');add('Herb',i.earth,'Earth Herb');add('Herb',i.air,'Air Herb');add('Herb',i.fire,'Fire Herb');add('Herb',i.water,'Water Herb');(i.spellHerbs||[]).forEach((h,n)=>add('Herb',h,'Spell Herb '+(n+1)));add('Crystal',i.crystal,'Crystal');add('Rune',i.rune,'Rune');add('Oil',i.oil,'Oil');return{journal_entry_id:e.entryId||'',spell_level:gmSaleLevel(e),spell_name:e.spellName||'Greenman Spell Kit',method:gmSaleMethodLabel(e.method),items:items};}"""
once(old_payload, new_payload, 'sale payload / thermal helpers')

old_checkout = "async function gmCheckoutBasket(){const a=gmReadBasket();if(!a.length)return;const card=qs('#gmShopCard'),err=qs('#gmShopError');if(err)err.textContent='';card&&card.classList.add('gm-shop-busy');try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Checkout started',{kits:a.length},'',false);}catch(_gmDiagErr){}try{const d=await gmShopPost(GM_SHOP_CREATE,{sale_mode:'greenman',basket:a});if(!d.approval_url)throw new Error('PayPal approval link was not returned');try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Checkout order created',{local_order_id:d.local_order_id,total:d.total},'',false);}catch(_gmDiagErr){}gmMarkPurchased(a.map(x=>x.journal_entry_id));try{renderEntries();}catch(_gmRenderErr){}gmWriteBasket([]);card&&card.classList.remove('gm-shop-busy');gmCloseShop();try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}}catch(e){try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('CONSOLE ERROR','Journal Sales','Checkout failed',{error:String(e&&e.message||e)},'',true);}catch(_gmDiagErr){}if(err)err.textContent=String(e.message||e);card&&card.classList.remove('gm-shop-busy');}}"
new_checkout = "async function gmCheckoutBasket(){const a=gmReadBasket();if(!a.length)return;const card=qs('#gmShopCard'),err=qs('#gmShopError');if(err)err.textContent='';card&&card.classList.add('gm-shop-busy');try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Checkout started',{kits:a.length},'',false);}catch(_gmDiagErr){}try{const checkoutBasket=a.map(x=>Object.assign({},x,{thermal_png_base64:gmThermalPngBase64(x)}));const d=await gmShopPost(GM_SHOP_CREATE,{sale_mode:'greenman',basket:checkoutBasket});if(!d.approval_url)throw new Error('PayPal approval link was not returned');try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Checkout order created',{local_order_id:d.local_order_id,total:d.total},'',false);}catch(_gmDiagErr){}try{localStorage.setItem(GM_SHOP_PENDING,JSON.stringify({local_order_id:d.local_order_id||'',paypal_order_id:d.paypal_order_id||'',created_at:Date.now(),basket:a}));}catch(_gmPendingErr){}card&&card.classList.remove('gm-shop-busy');gmCloseShop();try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}}catch(e){try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('CONSOLE ERROR','Journal Sales','Checkout failed',{error:String(e&&e.message||e)},'',true);}catch(_gmDiagErr){}if(err)err.textContent=String(e.message||e);card&&card.classList.remove('gm-shop-busy');}}"
once(old_checkout, new_checkout, 'paid-only checkout completion')

anchor = "function gmWildwoodStart(id,kind){"
insert = r"""
function gmReadPendingOrder(){try{const p=JSON.parse(localStorage.getItem(GM_SHOP_PENDING)||'null');return p&&typeof p==='object'?p:null;}catch(e){return null;}}
function gmPaidSpellList(basket){return(Array.isArray(basket)?basket:[]).map(x=>({spell_name:String(x&&x.spell_name||'Your Spell'),method:gmSaleMethodLabel(x&&x.method),journal_entry_id:String(x&&x.journal_entry_id||''),quantity:Math.max(1,Number(x&&x.quantity)||1)}));}
function gmPaidConfirmationHtml(p){const spells=gmPaidSpellList(p&&p.basket),total=spells.reduce((n,x)=>n+x.quantity,0),many=total!==1;const list=spells.map(x=>'<div class="gm-shop-line"><strong>'+esc(x.spell_name)+'</strong><br><em>'+esc(x.method)+'</em>'+(x.quantity>1?'<br>Qty '+esc(x.quantity):'')+'</div>').join('');let conjure='';if(spells.length===1){const x=spells[0];conjure='Your <strong>'+esc(x.spell_name)+' '+esc(x.method)+'</strong> is now being conjured and prepared by hand. Once it is ready, it will begin its magical journey to your doorstep.';}else{conjure='Your spells are now being conjured and prepared by hand. Once they are ready, they will begin their magical journey to your doorstep.';}return '<h2>'+(many?'YOUR SPELLS ARE BEING PREPARED':'YOUR SPELL IS BEING PREPARED')+'</h2><p><strong>Your payment has been confirmed.</strong></p>'+list+'<p>'+conjure+'</p><p>Your complete '+(many?'spells and instructions remain':'spell and instructions remain')+' safely in your Book of Shadows inside the app, where you can return '+(many?'to them':'to it')+' whenever you wish. A simple printed guide will also travel with '+(many?'each spell':'your spell')+', so you have the essential instructions to hand when '+(many?'they arrive':'it arrives')+'.</p><p>May '+(many?'your spells carry the intentions with which you created them':'your spell carry the intention with which you created it')+'.</p><p style="text-align:center"><strong>Greenman HedgeWitchery Apothecary</strong><br><em>Woods Witch &amp; RuneSmith</em></p><div class="gm-shop-actions"><button class="btn btn-green" onclick="gmCarryOnAfterPurchase()">CARRY ON</button></div>';}
function gmShowPaidConfirmation(p){const ov=gmShopOverlay(),card=qs('#gmShopCard');if(!card)return;card.innerHTML=gmPaidConfirmationHtml(p);ov.classList.add('show');}
function gmCarryOnAfterPurchase(){gmCloseShop();try{renderEntries();}catch(_gmRenderErr){}}
let gmPendingCheckBusy=false;
async function gmCheckPendingPayment(){if(gmPendingCheckBusy)return;const p=gmReadPendingOrder();if(!p||!p.local_order_id||!p.paypal_order_id)return;gmPendingCheckBusy=true;try{const d=await gmShopPost(GM_SHOP_STATUS,{local_order_id:p.local_order_id,paypal_order_id:p.paypal_order_id});if(d.payment_status==='paid'){const ids=gmPaidSpellList(p.basket).map(x=>x.journal_entry_id).filter(Boolean);gmMarkPurchased(ids);gmWriteBasket([]);try{localStorage.removeItem(GM_SHOP_PENDING);}catch(_gmRemoveErr){}try{renderEntries();}catch(_gmRenderErr){}try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Paid order confirmed in app',{local_order_id:p.local_order_id},'',false);}catch(_gmDiagErr){}gmShowPaidConfirmation(p);}}catch(e){try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('CONSOLE ERROR','Journal Sales','Pending payment status check failed',{error:String(e&&e.message||e)},'',false);}catch(_gmDiagErr){}}finally{gmPendingCheckBusy=false;}}
window.addEventListener('focus',()=>setTimeout(gmCheckPendingPayment,150));
window.addEventListener('pageshow',()=>setTimeout(gmCheckPendingPayment,150));
document.addEventListener('visibilitychange',()=>{if(!document.hidden)setTimeout(gmCheckPendingPayment,150);});
setTimeout(gmCheckPendingPayment,600);
"""
once(anchor, insert + anchor, 'paid status confirmation')

if journal == original:
    raise SystemExit('no changes applied')
encoded = json.dumps(journal, ensure_ascii=False)
patched = outer[:key_at] + encoded + outer[key_at+used:]
out.write_text(patched, encoding='utf-8')
print(f'wrote {out} bytes={len(patched)}')
print('FV3.3 sales: paid-only PURCHASED/basket clear, 57mm PNG slip, canonical methods, CARRY ON confirmation.')
