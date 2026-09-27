#!/usr/bin/env python3
"""Feature: show a "Purchased" badge and "Buy Again" once a Journal entry
has been bought through the Greenman basket checkout.

User request: the Book of Shadows entry card should show it's already
been bought, and offer "Buy Again" instead of the plain "Add Spell Kit
to Basket" label, once a spell has gone through checkout.

Adds a small localStorage-backed record (gm_greenman_purchased_entries_v1,
a plain array of journal_entry_id strings) with two helpers:
gmIsPurchased(id) / gmMarkPurchased(ids). gmCheckoutBasket() marks every
basket item's journal_entry_id purchased at the same point it now clears
the basket (right after the order is successfully created with Supabase/
PayPal) - this is the same "the sale was initiated" moment the app
already treats as final elsewhere (e.g. Wildwood Cash marks a sale
complete immediately), since there is no payment-capture callback that
ever reaches this app instance to confirm PayPal payment completed.

entryCard() then shows a "PURCHASED" badge and relabels the button
"BUY AGAIN" (same gmAddSpellToBasket handler - still fully functional,
this is a label/badge change only) when the entry has been purchased.

Applied last, after the sales error/basket-clear patch has already run.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_fv3_sales_purchased_badge.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
original = text


def apply_once(text, anchor, replacement, label):
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 occurrence of anchor, found {count}')
    return text.replace(anchor, replacement, 1)


# ---------------------------------------------------------------------
# (1) Add gmIsPurchased/gmMarkPurchased helpers, right before gmSaleLevel.
# ---------------------------------------------------------------------
anchor = "function gmSaleLevel(e){const n=herbNames(e).length;if(n===5)return'Handful';if(n===7)return'Weaving';if(n===11)return'Full Grove';return null;}"
replacement = (
    "const GM_SHOP_PURCHASED='gm_greenman_purchased_entries_v1';"
    "function gmIsPurchased(id){if(!id)return false;try{const a=JSON.parse(localStorage.getItem(GM_SHOP_PURCHASED)||'[]');return Array.isArray(a)&&a.includes(id);}catch(e){return false;}}"
    "function gmMarkPurchased(ids){try{const a=JSON.parse(localStorage.getItem(GM_SHOP_PURCHASED)||'[]');const set=new Set(Array.isArray(a)?a:[]);(ids||[]).forEach(id=>{if(id)set.add(id);});localStorage.setItem(GM_SHOP_PURCHASED,JSON.stringify(Array.from(set)));}catch(e){}}"
    + anchor
)
text = apply_once(text, anchor, replacement, 'gmIsPurchased/gmMarkPurchased helpers')

# ---------------------------------------------------------------------
# (2) gmCheckoutBasket: mark every basket item's entry purchased right
#     alongside clearing the basket, on successful order creation.
# ---------------------------------------------------------------------
anchor = "gmWriteBasket([]);card&&card.classList.remove('gm-shop-busy');gmCloseShop();"
replacement = "gmMarkPurchased(a.map(x=>x.journal_entry_id));gmWriteBasket([]);card&&card.classList.remove('gm-shop-busy');gmCloseShop();"
text = apply_once(text, anchor, replacement, 'gmCheckoutBasket mark-purchased on success')

# ---------------------------------------------------------------------
# (3) entryCard: show a Purchased badge and relabel the button Buy Again.
# ---------------------------------------------------------------------
anchor = "function entryCard(e){const preview=(e.entryType==='timing'?timingPreview(e):(e.entryType==='grimoire'?grimoirePreview(e):roleItems(e).slice(0,4).map(r=>cleanName(r.item)).join(' · '))); const canBuy=gmShopMode()==='full'&&e.entryType!=='timing'&&e.entryType!=='grimoire'&&!!gmSaleLevel(e); const add=canBuy?`<button class=\\\"gm-sale-btn gm-basket-add\\\" onclick=\\\"gmAddSpellToBasket('${escAttr(e.entryId)}')\\\">ADD SPELL KIT TO BASKET</button>`:''; return `<article class=\\\"entry-card gm-entry-wrap\\\"><button class=\\\"gm-entry-open\\\" onclick=\\\"openEntry('${escAttr(e.entryId)}')\\\"><div class=\\\"entry-title\\\">${esc(e.spellName||e.itemName||'Book of Shadows Entry')}</div><div class=\\\"entry-meta\\\">${esc(e.method||e.category||'Greenman Entry')} · ${formatDate(e.savedAt)}</div><div class=\\\"entry-preview\\\">${esc(preview||'Tap to open')}</div></button>${add}</article>`;}"
replacement = (
    "function entryCard(e){const preview=(e.entryType==='timing'?timingPreview(e):(e.entryType==='grimoire'?grimoirePreview(e):roleItems(e).slice(0,4).map(r=>cleanName(r.item)).join(' · '))); const canBuy=gmShopMode()==='full'&&e.entryType!=='timing'&&e.entryType!=='grimoire'&&!!gmSaleLevel(e); const bought=canBuy&&gmIsPurchased(e.entryId); const badge=bought?'<div style=\\\"position:absolute;top:8px;right:8px;background:#2d4a1e;color:#e8c040;font:bold 10px Georgia,serif;letter-spacing:.08em;padding:3px 8px;border:1px solid #c9a84c;border-radius:10px;z-index:2\\\">PURCHASED</div>':''; const add=canBuy?`<button class=\\\"gm-sale-btn gm-basket-add\\\" onclick=\\\"gmAddSpellToBasket('${escAttr(e.entryId)}')\\\">${bought?'BUY AGAIN':'ADD SPELL KIT TO BASKET'}</button>`:''; return `<article class=\\\"entry-card gm-entry-wrap\\\" style=\\\"position:relative\\\">${badge}<button class=\\\"gm-entry-open\\\" onclick=\\\"openEntry('${escAttr(e.entryId)}')\\\"><div class=\\\"entry-title\\\">${esc(e.spellName||e.itemName||'Book of Shadows Entry')}</div><div class=\\\"entry-meta\\\">${esc(e.method||e.category||'Greenman Entry')} · ${formatDate(e.savedAt)}</div><div class=\\\"entry-preview\\\">${esc(preview||'Tap to open')}</div></button>${add}</article>`;}"
)
text = apply_once(text, anchor, replacement, 'entryCard purchased badge/buy-again label')

if text == original:
    raise SystemExit('no changes applied overall')

out.write_text(text, encoding='utf-8')
print(f'wrote {out} bytes={len(text)}')
print('Journal entries now show a PURCHASED badge and BUY AGAIN label once bought through the Greenman basket checkout.')
