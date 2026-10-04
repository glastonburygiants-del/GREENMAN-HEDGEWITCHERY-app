#!/usr/bin/env python3
"""FV3.9 customer-facing spell-kit prices and Royal Mail delivery choice.

Runs after the existing Journal sales, country and customer-access patches.
Edits only the embedded PAGES.journal HTML.
"""
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_fv39_shop_prices_delivery.py INPUT OUTPUT")

src, out = map(Path, sys.argv[1:])
outer = src.read_text(encoding="utf-8")
pages_at = outer.index("const PAGES = ")
key_at = outer.index('"journal":', pages_at) + len('"journal":')
journal, used = json.JSONDecoder().raw_decode(outer[key_at:])
original = journal

anchor = "function gmWildwoodStart(id,kind){"
if journal.count(anchor) != 1:
    raise SystemExit(f"gmWildwoodStart anchor count {journal.count(anchor)}")

block = r"""
/* FV3.9 visible spell-kit pricing + customer-selected Royal Mail delivery. */
const GM_SHOP_PRICES_V39={Handful:2300,Weaving:2700,'Full Grove':3000};
const GM_SHOP_DELIVERY_V39={
 tracked48:{label:'Royal Mail Tracked 48 with Signature',pence:525},
 tracked24:{label:'Royal Mail Tracked 24 with Signature',pence:625}
};
const GM_SHOP_DELIVERY_KEY_V39='gm_greenman_delivery_v1';
function gmShopPricePenceV39(level){return Number(GM_SHOP_PRICES_V39[String(level||'')]||0);}
function gmShopMoneyV39(p){return(Number(p||0)/100).toFixed(2);}
function gmShopDeliveryV39(){try{const v=String(localStorage.getItem(GM_SHOP_DELIVERY_KEY_V39)||'');return GM_SHOP_DELIVERY_V39[v]?v:'';}catch(e){return'';}}
function gmSetDeliveryV39(v){try{if(GM_SHOP_DELIVERY_V39[v])localStorage.setItem(GM_SHOP_DELIVERY_KEY_V39,v);else localStorage.removeItem(GM_SHOP_DELIVERY_KEY_V39);}catch(e){}gmOpenBasket();}

entryCard=function(e){
 const preview=(e.entryType==='timing'?timingPreview(e):(e.entryType==='grimoire'?grimoirePreview(e):roleItems(e).slice(0,4).map(r=>cleanName(r.item)).join(' · ')));
 const level=gmSaleLevel(e);
 const canBuy=gmShopMode()==='full'&&gmShopCountryEligible()&&e.entryType!=='timing'&&e.entryType!=='grimoire'&&!!level;
 const bought=canBuy&&gmIsPurchased(e.entryId);
 const badge=bought?'<div style="position:absolute;top:8px;right:8px;background:#2d4a1e;color:#e8c040;font:bold 10px Georgia,serif;letter-spacing:.08em;padding:3px 8px;border:1px solid #c9a84c;border-radius:10px;z-index:2">PURCHASED</div>':'';
 const price=canBuy?'<div style="margin:0 12px 8px;color:#e8c040;font:bold 14px Georgia,serif">'+esc(level)+' Spell Kit · £'+gmShopMoneyV39(gmShopPricePenceV39(level))+'</div>':'';
 const add=canBuy?`<button class="gm-sale-btn gm-basket-add" onclick="gmAddSpellToBasket('${escAttr(e.entryId)}')">${bought?'BUY AGAIN':'ADD SPELL KIT TO BASKET'}</button>`:'';
 return `<article class="entry-card gm-entry-wrap" style="position:relative">${badge}<button class="gm-entry-open" onclick="openEntry('${escAttr(e.entryId)}')"><div class="entry-title">${esc(e.spellName||e.itemName||'Book of Shadows Entry')}</div><div class="entry-meta">${esc(e.method||e.category||'Greenman Entry')} · ${formatDate(e.savedAt)}</div><div class="entry-preview">${esc(preview||'Tap to open')}</div></button>${price}${add}</article>`;
};

gmOpenBasket=function(){
 if(!gmShopCountryEligible())return;
 const a=gmReadBasket(),ov=gmShopOverlay(),card=qs('#gmShopCard'),delivery=gmShopDeliveryV39();
 const itemTotal=a.reduce((s,x)=>s+gmShopPricePenceV39(x.spell_level)*Math.max(1,Number(x.quantity||1)),0);
 const deliveryPence=delivery?GM_SHOP_DELIVERY_V39[delivery].pence:0,total=itemTotal+deliveryPence;
 const lines=a.map((x,i)=>{
   const q=Math.max(1,Number(x.quantity||1)),unit=gmShopPricePenceV39(x.spell_level),line=unit*q;
   return '<div class="gm-shop-line"><strong>'+esc(x.spell_name)+'</strong><br>'+esc(x.spell_level)+' · '+esc(x.method)+
     '<br><span style="color:#e8c040;font-weight:700">£'+gmShopMoneyV39(unit)+' each</span>'+
     '<div class="gm-qty"><button onclick="gmSetQty('+i+',-1)">−</button><span>'+q+'</span><button onclick="gmSetQty('+i+',1)">+</button><span style="margin-left:auto;font-weight:700">£'+gmShopMoneyV39(line)+'</span></div></div>';
 }).join('');
 const deliveryHtml='<div style="margin:12px 0 8px"><div style="font-weight:700;color:#e8c040;margin-bottom:6px">DELIVERY</div>'+
   '<label style="display:flex;gap:8px;align-items:center;padding:7px 0"><input type="radio" name="gmDelivery" '+(delivery==='tracked48'?'checked ':'')+'onchange="gmSetDeliveryV39(\'tracked48\')"><span>Royal Mail Tracked 48 with Signature · <strong>£5.25</strong></span></label>'+
   '<label style="display:flex;gap:8px;align-items:center;padding:7px 0"><input type="radio" name="gmDelivery" '+(delivery==='tracked24'?'checked ':'')+'onchange="gmSetDeliveryV39(\'tracked24\')"><span>Royal Mail Tracked 24 with Signature · <strong>£6.25</strong></span></label></div>';
 const summary='<div style="border-top:1px solid rgba(201,168,76,.45);margin-top:8px;padding-top:9px;line-height:1.55">'+
   '<div style="display:flex;justify-content:space-between"><span>Spell kits</span><strong>£'+gmShopMoneyV39(itemTotal)+'</strong></div>'+
   '<div style="display:flex;justify-content:space-between"><span>Delivery</span><strong>'+(delivery?'£'+gmShopMoneyV39(deliveryPence):'Choose 24 or 48')+'</strong></div>'+
   '<div style="display:flex;justify-content:space-between;font-size:18px;color:#e8c040;margin-top:4px"><span>TOTAL</span><strong>'+(delivery?'£'+gmShopMoneyV39(total):'—')+'</strong></div></div>';
 card.innerHTML='<h2>Greenman Spell Kit Basket</h2>'+(a.length?lines:'<p>Your basket is empty.</p>')+
   (a.length?deliveryHtml+summary+'<div id="gmShopError" class="gm-shop-error"></div><div class="gm-shop-actions"><button class="btn btn-outline" onclick="gmCloseShop()">KEEP SHOPPING</button><button class="btn btn-gold" onclick="gmCheckoutBasket()">CHECKOUT</button></div>':'<div class="gm-shop-actions"><button class="btn btn-outline" onclick="gmCloseShop()">CLOSE</button></div>');
 ov.classList.add('show');
};

gmCheckoutBasket=async function(){
 if(!gmShopCountryEligible())return;
 const a=gmReadBasket();if(!a.length)return;
 const card=qs('#gmShopCard'),err=qs('#gmShopError'),delivery=gmShopDeliveryV39();
 if(err)err.textContent='';
 if(!delivery){if(err)err.textContent='Choose Tracked 24 or Tracked 48 delivery before checkout.';return;}
 card&&card.classList.add('gm-shop-busy');
 try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Checkout started',{kits:a.length,delivery_service:delivery},'',false);}catch(_gmDiagErr){}
 try{
   const checkoutBasket=a.map(x=>Object.assign({},x,{thermal_png_base64:gmThermalPngBase64(x)}));
   const d=await gmShopPost(GM_SHOP_CREATE,{sale_mode:'greenman',basket:checkoutBasket,delivery_service:delivery});
   if(!d.approval_url)throw new Error('PayPal approval link was not returned');
   try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('ACTION','Journal Sales','Checkout order created',{local_order_id:d.local_order_id,total:d.total,delivery_service:delivery},'',false);}catch(_gmDiagErr){}
   try{localStorage.setItem(GM_SHOP_PENDING,JSON.stringify({local_order_id:d.local_order_id||'',paypal_order_id:d.paypal_order_id||'',created_at:Date.now(),basket:a,delivery_service:delivery}));}catch(_gmPendingErr){}
   card&&card.classList.remove('gm-shop-busy');gmCloseShop();
   try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}
 }catch(e){
   try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('CONSOLE ERROR','Journal Sales','Checkout failed',{error:String(e&&e.message||e)},'',true);}catch(_gmDiagErr){}
   if(err)err.textContent=String(e.message||e);card&&card.classList.remove('gm-shop-busy');
 }
};
"""
journal = journal.replace(anchor, block + "\n" + anchor, 1)

for marker in (
    "Handful:2300",
    "Weaving:2700",
    "'Full Grove':3000",
    "Royal Mail Tracked 48 with Signature",
    "Royal Mail Tracked 24 with Signature",
    "Choose Tracked 24 or Tracked 48 delivery before checkout.",
    "delivery_service:delivery",
    "Spell Kit · £"
):
    if marker not in journal:
        raise SystemExit("missing marker: " + marker)

if journal == original:
    raise SystemExit("no changes applied")

encoded = json.dumps(journal, ensure_ascii=False).replace("</script>", "<\\/script>")
patched = outer[:key_at] + encoded + outer[key_at+used:]
out.write_text(patched, encoding="utf-8")
print(f"wrote {out} bytes={len(patched)}")
print("FV3.9: BoS kit prices + priced basket + Tracked 48/24 delivery choice.")
