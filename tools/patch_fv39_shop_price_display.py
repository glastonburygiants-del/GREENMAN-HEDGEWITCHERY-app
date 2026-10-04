#!/usr/bin/env python3
"""EXP4R3: show agreed spell-kit selling prices in Book of Shadows and basket.

Runs after all existing Journal sales, country-gate and customer-access patches.
Edits only the embedded PAGES.journal HTML. No gate, signing, stock or payment
behaviour is changed.

Agreed prices:
  Handful (5 herbs)    GBP 23
  Weaving (7 herbs)    GBP 27
  Full Grove (11 herbs) GBP 30
"""
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_fv39_shop_price_display.py INPUT OUTPUT")

src, out = map(Path, sys.argv[1:])
outer = src.read_text(encoding="utf-8")
pages_at = outer.index("const PAGES = ")
key_at = outer.index('"journal":', pages_at) + len('"journal":')
journal, used = json.JSONDecoder().raw_decode(outer[key_at:])
original = journal

def once(anchor, replacement, label):
    global journal
    n = journal.count(anchor)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly 1 anchor, found {n}")
    journal = journal.replace(anchor, replacement, 1)

level_anchor = "function gmSaleLevel(e){const n=herbNames(e).length;if(n===5)return'Handful';if(n===7)return'Weaving';if(n===11)return'Full Grove';return null;}"
level_replacement = level_anchor + (
    "function gmSalePricePence(level){return level==='Handful'?2300:(level==='Weaving'?2700:(level==='Full Grove'?3000:0));}"
    "function gmSaleMoney(p){return'£'+((Number(p)||0)/100).toFixed(2);}"
    "function gmSalePriceLabel(level){const p=gmSalePricePence(level);return p?gmSaleMoney(p):'';}"
)
once(level_anchor, level_replacement, "price helpers")

entry_anchor = """function entryCard(e){const preview=(e.entryType==='timing'?timingPreview(e):(e.entryType==='grimoire'?grimoirePreview(e):roleItems(e).slice(0,4).map(r=>cleanName(r.item)).join(' · '))); const canBuy=gmShopMode()==='full'&&gmShopCountryEligible()&&e.entryType!=='timing'&&e.entryType!=='grimoire'&&!!gmSaleLevel(e); const bought=canBuy&&gmIsPurchased(e.entryId); const badge=bought?'<div style="position:absolute;top:8px;right:8px;background:#2d4a1e;color:#e8c040;font:bold 10px Georgia,serif;letter-spacing:.08em;padding:3px 8px;border:1px solid #c9a84c;border-radius:10px;z-index:2">PURCHASED</div>':''; const add=canBuy?`<button class="gm-sale-btn gm-basket-add" onclick="gmAddSpellToBasket('${escAttr(e.entryId)}')">${bought?'BUY AGAIN':'ADD SPELL KIT TO BASKET'}</button>`:''; return `<article class="entry-card gm-entry-wrap" style="position:relative">${badge}<button class="gm-entry-open" onclick="openEntry('${escAttr(e.entryId)}')"><div class="entry-title">${esc(e.spellName||e.itemName||'Book of Shadows Entry')}</div><div class="entry-meta">${esc(e.method||e.category||'Greenman Entry')} · ${formatDate(e.savedAt)}</div><div class="entry-preview">${esc(preview||'Tap to open')}</div></button>${add}</article>`;}"""
entry_replacement = """function entryCard(e){const preview=(e.entryType==='timing'?timingPreview(e):(e.entryType==='grimoire'?grimoirePreview(e):roleItems(e).slice(0,4).map(r=>cleanName(r.item)).join(' · '))); const canBuy=gmShopMode()==='full'&&gmShopCountryEligible()&&e.entryType!=='timing'&&e.entryType!=='grimoire'&&!!gmSaleLevel(e); const level=canBuy?gmSaleLevel(e):null; const bought=canBuy&&gmIsPurchased(e.entryId); const badge=bought?'<div style="position:absolute;top:8px;right:8px;background:#2d4a1e;color:#e8c040;font:bold 10px Georgia,serif;letter-spacing:.08em;padding:3px 8px;border:1px solid #c9a84c;border-radius:10px;z-index:2">PURCHASED</div>':''; const price=canBuy?`<div style="margin:8px 12px 4px;text-align:center;color:#2d4a1e;font:bold 15px Georgia,serif">${esc(level)} Spell Kit · ${esc(gmSalePriceLabel(level))}</div>`:''; const add=canBuy?`<button class="gm-sale-btn gm-basket-add" onclick="gmAddSpellToBasket('${escAttr(e.entryId)}')">${bought?'BUY AGAIN':'ADD SPELL KIT TO BASKET'}</button>`:''; return `<article class="entry-card gm-entry-wrap" style="position:relative">${badge}<button class="gm-entry-open" onclick="openEntry('${escAttr(e.entryId)}')"><div class="entry-title">${esc(e.spellName||e.itemName||'Book of Shadows Entry')}</div><div class="entry-meta">${esc(e.method||e.category||'Greenman Entry')} · ${formatDate(e.savedAt)}</div><div class="entry-preview">${esc(preview||'Tap to open')}</div></button>${price}${add}</article>`;}"""
once(entry_anchor, entry_replacement, "Book of Shadows price line")

basket_anchor = """function gmOpenBasket(){if(!gmShopCountryEligible())return;const a=gmReadBasket(),ov=gmShopOverlay(),card=qs('#gmShopCard');card.innerHTML='<h2>Greenman Spell Kit Basket</h2>'+(a.length?a.map((x,i)=>'<div class="gm-shop-line"><strong>'+esc(x.spell_name)+'</strong><br>'+esc(x.spell_level)+' · '+esc(x.method)+'<div class="gm-qty"><button onclick="gmSetQty('+i+',-1)">−</button><span>'+Number(x.quantity||1)+'</span><button onclick="gmSetQty('+i+',1)">+</button></div></div>').join(''):'<p>Your basket is empty.</p>')+(a.length?'<p class="gm-shop-note">Postage is calculated from the combined packed weight of the whole basket.</p><div id="gmShopError" class="gm-shop-error"></div><div class="gm-shop-actions"><button class="btn btn-outline" onclick="gmCloseShop()">KEEP SHOPPING</button><button class="btn btn-gold" onclick="gmCheckoutBasket()">CHECKOUT</button></div>':'<div class="gm-shop-actions"><button class="btn btn-outline" onclick="gmCloseShop()">CLOSE</button></div>');ov.classList.add('show');}"""
basket_replacement = """function gmOpenBasket(){if(!gmShopCountryEligible())return;const a=gmReadBasket(),ov=gmShopOverlay(),card=qs('#gmShopCard');const subtotal=a.reduce((sum,x)=>sum+gmSalePricePence(x.spell_level)*Math.max(1,Number(x.quantity||1)),0);card.innerHTML='<h2>Greenman Spell Kit Basket</h2>'+(a.length?a.map((x,i)=>{const q=Math.max(1,Number(x.quantity||1)),unit=gmSalePricePence(x.spell_level);return'<div class="gm-shop-line"><strong>'+esc(x.spell_name)+'</strong><br>'+esc(x.spell_level)+' · '+esc(x.method)+'<br><strong>'+esc(gmSaleMoney(unit))+' each</strong> · '+esc(gmSaleMoney(unit*q))+'<div class="gm-qty"><button onclick="gmSetQty('+i+',-1)">−</button><span>'+q+'</span><button onclick="gmSetQty('+i+',1)">+</button></div></div>';}).join(''):'<p>Your basket is empty.</p>')+(a.length?'<p style="font:bold 17px Georgia,serif;text-align:right;margin:12px 0 5px">Kit subtotal: '+esc(gmSaleMoney(subtotal))+'</p><p class="gm-shop-note">Delivery is added separately at checkout.</p><div id="gmShopError" class="gm-shop-error"></div><div class="gm-shop-actions"><button class="btn btn-outline" onclick="gmCloseShop()">KEEP SHOPPING</button><button class="btn btn-gold" onclick="gmCheckoutBasket()">CHECKOUT</button></div>':'<div class="gm-shop-actions"><button class="btn btn-outline" onclick="gmCloseShop()">CLOSE</button></div>');ov.classList.add('show');}"""
once(basket_anchor, basket_replacement, "basket price display")

if journal == original:
    raise SystemExit("no changes applied")

encoded = json.dumps(journal, ensure_ascii=False).replace("</script>", "<\\/script>")
patched = outer[:key_at] + encoded + outer[key_at+used:]

for required in ("Handful'?2300", "Weaving'?2700", "Full Grove'?3000", "Spell Kit ·", "Kit subtotal:"):
    if required not in patched:
        raise SystemExit("missing " + required)

out.write_text(patched, encoding="utf-8")
print(f"wrote {out} bytes={len(patched)}")
print("BOS cards and basket now display agreed £23/£27/£30 spell-kit prices.")
