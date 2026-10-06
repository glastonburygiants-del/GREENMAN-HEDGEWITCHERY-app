#!/usr/bin/env python3
"""FV4.0 Android spell-shop flow.

Runs after FV3.9. Keeps the existing spell pricing and Royal Mail delivery maths,
but moves the persistent basket to the Book of Shadows front page and routes
Greenman online spell checkout to the website. Android shows a clear handoff
message first; the Web App has its own direct website flow.
"""
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_fv40_shop_website_checkout.py INPUT OUTPUT")

src, out = map(Path, sys.argv[1:])
outer = src.read_text(encoding="utf-8")
pages_at = outer.index("const PAGES = ")
key_at = outer.index('"journal":', pages_at) + len('"journal":')
journal, used = json.JSONDecoder().raw_decode(outer[key_at:])
original = journal

basket = '<div class="gm-basket-bar" id="gmBasketBar"><div class="gm-basket-count" id="gmBasketCount">Basket · 0 kits</div><button class="btn btn-gold" onclick="gmOpenBasket()">OPEN BASKET</button></div>\n'
if journal.count(basket) != 1:
    raise SystemExit(f"basket bar anchor count {journal.count(basket)}")
journal = journal.replace(basket, "", 1)
front = '<button class="btn btn-outline" onclick="printWholeBos()">Print Book of Shadows</button>\n<div class="gold-rule" id="catStart"><span>Categories</span></div>'
front_new = '<button class="btn btn-outline" onclick="printWholeBos()">Print Book of Shadows</button>\n' + basket + '<div class="gold-rule" id="catStart"><span>Categories</span></div>'
if journal.count(front) != 1:
    raise SystemExit(f"BoS front print anchor count {journal.count(front)}")
journal = journal.replace(front, front_new, 1)

render_old = 'function renderBosFront(){renderCategories(); updateBosCount();}'
render_new = 'function renderBosFront(){renderCategories(); updateBosCount(); try{gmUpdateBasketBar();}catch(e){}}'
if journal.count(render_old) != 1:
    raise SystemExit(f"renderBosFront anchor count {journal.count(render_old)}")
journal = journal.replace(render_old, render_new, 1)

payload_old = "function gmSalePayload(e){const i=(e&&e.items)||{};const items=[];function add(type,name,role){name=cleanName(name);if(name)items.push({item_type:type,item_name:name,item_role:role});}add('Candle',i.candle,'Candle');add('Herb',i.earth,'Earth Herb');add('Herb',i.air,'Air Herb');add('Herb',i.fire,'Fire Herb');add('Herb',i.water,'Water Herb');(i.spellHerbs||[]).forEach((h,n)=>add('Herb',h,'Spell Herb '+(n+1)));add('Crystal',i.crystal,'Crystal');add('Rune',i.rune,'Rune');add('Oil',i.oil,'Oil');return{journal_entry_id:e.entryId||'',spell_level:gmSaleLevel(e),spell_name:e.spellName||'Greenman Spell Kit',method:gmSaleMethodLabel(e.method),items:items};}"
payload_new = "function gmSalePayload(e){const i=(e&&e.items)||{};const items=[];function add(type,name,role){name=cleanName(name);if(name)items.push({item_type:type,item_name:name,item_role:role});}add('Candle',i.candle,'Candle');add('Herb',i.earth,'Earth Herb');add('Herb',i.air,'Air Herb');add('Herb',i.fire,'Fire Herb');add('Herb',i.water,'Water Herb');(i.spellHerbs||[]).forEach((h,n)=>add('Herb',h,'Spell Herb '+(n+1)));add('Crystal',i.crystal,'Crystal');add('Rune',i.rune,'Rune');add('Oil',i.oil,'Oil');return{journal_entry_id:e.entryId||'',spell_level:gmSaleLevel(e),spell_name:e.spellName||'Greenman Spell Kit',spell_category:e.category||'',method:gmSaleMethodLabel(e.method),items:items};}"
if journal.count(payload_old) != 1:
    raise SystemExit(f"gmSalePayload anchor count {journal.count(payload_old)}")
journal = journal.replace(payload_old, payload_new, 1)


add_old = "function gmAddSpellToBasket(id){if(!gmShopCountryEligible())return;const e=readLS(LS_ENTRIES,[]).find(x=>x.entryId===id);if(!e)return;const a=gmReadBasket(),p=gmSalePayload(e),found=a.find(x=>x.journal_entry_id===p.journal_entry_id);if(found)found.quantity=Number(found.quantity||1)+1;else a.push(Object.assign({quantity:1},p));gmWriteBasket(a);try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Spell kit added to basket',{spell_level:p.spell_level,method:p.method},'',false);}catch(_gmDiagErr){}toast('Added to basket');}"
add_new = r'''const GM_SHOP_STOCK_STATUS='https://zzfgufuyetybxaeidcxu.supabase.co/functions/v1/shop-stock-status';
function gmAddSpellToBasketNow(e,p){
 const a=gmReadBasket(),found=a.find(x=>x.journal_entry_id===p.journal_entry_id);
 if(found)found.quantity=Number(found.quantity||1)+1;else a.push(Object.assign({quantity:1},p));
 gmWriteBasket(a);
 try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Spell kit added to basket',{spell_level:p.spell_level,method:p.method},'',false);}catch(_gmDiagErr){}
 toast('Added to basket');
}
gmAddSpellToBasket=async function(id){
 if(!gmShopCountryEligible())return;
 const e=readLS(LS_ENTRIES,[]).find(x=>x.entryId===id);if(!e)return;
 const p=gmSalePayload(e);
 try{
   const d=await gmShopPost(GM_SHOP_STOCK_STATUS,{spell:Object.assign({quantity:1},p)});
   if(d.stock_delay){
     const ov=gmShopOverlay(),card=qs('#gmShopCard');
     const missing=(d.shortages||[]).map(x=>esc(x.item_name||'')).filter(Boolean);
     card.innerHTML='<h2>A longer walk through the Wildwood</h2><p style="line-height:1.55">Greenman must venture deeper into the darkest reaches of the Wildwood to gather part of your spell. Your spell can still be ordered, but it may take a little longer to prepare while the missing ingredients are gathered.</p>'+(missing.length?'<p class="gm-shop-note">Waiting to be gathered: '+missing.join(', ')+'</p>':'')+'<div class="gm-shop-actions"><button class="btn btn-outline" onclick="gmCloseShop()">WAIT FOR RESTOCK</button><button class="btn btn-gold" onclick="gmConfirmDelayedSpell()">BUY IT NOW</button></div>';
     window.gmConfirmDelayedSpell=function(){gmAddSpellToBasketNow(e,p);gmCloseShop();};
     ov.classList.add('show');return;
   }
 }catch(err){
   try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('CONSOLE ERROR','Journal Sales','Stock delay check unavailable',{error:String(err&&err.message||err)},'',false);}catch(_gmDiagErr){}
 }
 gmAddSpellToBasketNow(e,p);
};'''
if journal.count(add_old) != 1:
    raise SystemExit(f"gmAddSpellToBasket anchor count {journal.count(add_old)}")
journal = journal.replace(add_old, add_new, 1)

start = journal.index('gmCheckoutBasket=async function(){')
end = journal.index('\n\nfunction gmWildwoodStart(id,kind){', start)
replacement = r'''gmCheckoutBasket=async function(){
 if(!gmShopCountryEligible())return;
 const a=gmReadBasket();if(!a.length)return;
 const card=qs('#gmShopCard'),err=qs('#gmShopError'),delivery=gmShopDeliveryV39();
 if(err)err.textContent='';
 if(!delivery){if(err)err.textContent='Choose Tracked 24 or Tracked 48 delivery before checkout.';return;}
 card.innerHTML='<h2>Complete your spell order</h2><p style="line-height:1.55">You’ll now be taken to the Greenman HedgeWitchery Apothecary website to complete your secure payment.</p><div class="gm-shop-actions"><button class="btn btn-outline" onclick="gmOpenBasket()">BACK</button><button class="btn btn-gold" onclick="gmContinueWebsiteCheckoutV40()">CONTINUE TO PAYMENT</button></div>';
};

async function gmContinueWebsiteCheckoutV40(){
 if(!gmShopCountryEligible())return;
 const a=gmReadBasket();if(!a.length)return;
 const card=qs('#gmShopCard'),delivery=gmShopDeliveryV39();
 card&&card.classList.add('gm-shop-busy');
 try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Website checkout started',{kits:a.length,delivery_service:delivery},'',false);}catch(_gmDiagErr){}
 try{
   const checkoutBasket=a.map(x=>Object.assign({},x,{thermal_png_base64:gmThermalPngBase64(x)}));
   const d=await gmShopPost(GM_SHOP_CREATE,{sale_mode:'greenman',basket:checkoutBasket,delivery_service:delivery,checkout_source:'android'});
   if(!d.approval_url)throw new Error('The secure checkout page was not returned.');
   try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Website checkout order created',{local_order_id:d.local_order_id,total:d.total,delivery_service:delivery},'',false);}catch(_gmDiagErr){}
   try{localStorage.setItem(GM_SHOP_PENDING,JSON.stringify({local_order_id:d.local_order_id||'',paypal_order_id:d.paypal_order_id||'',created_at:Date.now(),basket:a,delivery_service:delivery}));}catch(_gmPendingErr){}
   card&&card.classList.remove('gm-shop-busy');gmCloseShop();
   try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}
 }catch(e){
   try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('CONSOLE ERROR','Journal Sales','Website checkout failed',{error:String(e&&e.message||e)},'',true);}catch(_gmDiagErr){}
   if(card){card.classList.remove('gm-shop-busy');card.innerHTML='<h2>Checkout could not start</h2><div class="gm-shop-error">'+esc(String(e&&e.message||e))+'</div><div class="gm-shop-actions"><button class="btn btn-outline" onclick="gmOpenBasket()">BACK TO BASKET</button></div>';}
 }
};'''
journal = journal[:start] + replacement + journal[end:]

journal = journal.replace('<br><em>Woods Witch &amp; RuneSmith</em>', '')

for marker in (
    "checkout_source:'android'",
    "spell_category:e.category",
    "CONTINUE TO PAYMENT",
    "You’ll now be taken to the Greenman HedgeWitchery Apothecary website",
    "gmContinueWebsiteCheckoutV40",
    "GM_SHOP_STOCK_STATUS",
    "WAIT FOR RESTOCK",
    "BUY IT NOW",
    "darkest reaches of the Wildwood",
    "gm_greenman_pending_order_v1",
):
    if marker not in journal:
        raise SystemExit("missing marker: " + marker)
if journal.count('id="gmBasketBar"') != 1:
    raise SystemExit("basket bar must exist exactly once")
if journal.find('id="gmBasketBar"') > journal.find('id="catStart"'):
    raise SystemExit("basket bar is not on the BoS front page above Categories")
if journal == original:
    raise SystemExit("no changes applied")

encoded = json.dumps(journal, ensure_ascii=False).replace("</script>", "<\\/script>")
patched = outer[:key_at] + encoded + outer[key_at+used:]

# Wildwood stock remains a separate, manually controlled pool.
# Zero stays zero until the user changes it or explicitly presses RESTOCK ALL TO 7.
admin_at = patched.index('"admin":', pages_at) + len('"admin":')
admin, admin_used = json.JSONDecoder().raw_decode(patched[admin_at:])
admin_start = "function startQty(group){return (group==='Herbs'||group==='Crystals'||group==='Oils'||group==='Runes')?7:21}"
if admin.count(admin_start) != 1:
    raise SystemExit(f"Wildwood startQty anchor count {admin.count(admin_start)}")
admin = admin.replace(admin_start, "function startQty(group){return 7}", 1)
stock_buttons = '<div class="button-row"><button class="btn" onclick="resetCurrentGroup()">Reset Group to Start Qty</button><button class="btn green" onclick="saveStockNow()">Save Stock List</button></div>'
stock_buttons_new = '<div class="button-row"><button class="btn" onclick="resetCurrentGroup()">Reset Group to 7</button><button class="btn green" onclick="restockAllWildwoodTo7()">RESTOCK ALL TO 7</button><button class="btn green" onclick="saveStockNow()">Save Stock List</button></div>'
if admin.count(stock_buttons) != 1:
    raise SystemExit(f"Wildwood stock button anchor count {admin.count(stock_buttons)}")
admin = admin.replace(stock_buttons, stock_buttons_new, 1)
reset_anchor = "function resetCurrentGroup(){gmGreenmanConfirm('Reset '+currentStockGroup+' to starting quantities?',function(){const s=stock();(STOCK_MASTER[currentStockGroup]||[]).forEach(n=>s[currentStockGroup][n]=startQty(currentStockGroup));saveStock(s);renderStock();renderLowStock();toast('Group reset')},'Reset','Cancel')}"
restock_fn = reset_anchor + "\nfunction restockAllWildwoodTo7(){gmGreenmanConfirm('Restock every Wildwood item to 7? This is a manual Stall restock and does not take stock automatically from Online.',function(){const s=stock();Object.keys(STOCK_MASTER).forEach(g=>{s[g]=s[g]||{};(STOCK_MASTER[g]||[]).forEach(n=>s[g][n]=7)});saveStock(s);renderAll();toast('Wildwood stock restocked to 7')},'Restock all to 7','Cancel')}"
if admin.count(reset_anchor) != 1:
    raise SystemExit(f"Wildwood reset function anchor count {admin.count(reset_anchor)}")
admin = admin.replace(reset_anchor, restock_fn, 1)
for marker in ("RESTOCK ALL TO 7","function restockAllWildwoodTo7","function startQty(group){return 7}"):
    if marker not in admin:
        raise SystemExit("missing Admin marker: " + marker)
admin_encoded = json.dumps(admin, ensure_ascii=False).replace("</script>", "<\\/script>")
patched = patched[:admin_at] + admin_encoded + patched[admin_at+admin_used:]

out.write_text(patched, encoding="utf-8")
print(f"wrote {out} bytes={len(patched)}")
print("FV4.1: BoS-front checkout + Online stock delay warning + manual Wildwood restock-to-7.")
