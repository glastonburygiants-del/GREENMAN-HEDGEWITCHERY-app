#!/usr/bin/env python3
"""Wire the Journal sales feature into the app's own diagnostics logger.

Real-device debugging showed the checkout "Failed to fetch" error never
appeared in a GREENMAN TABLET DIAGNOSTICS log at all - the sales code
catches its own errors and shows them only in the on-screen shop card,
with nothing sent to parent.gmTabletDiagnosticsV1 the way every other
area of the app (Journal, Spell Builder, Cupboard, Scribe, etc.) already
does. That made this bug much harder to diagnose than it needed to be.

Adds the same `parent.gmTabletDiagnosticsV1 && parent.gmTabletDiagnosticsV1
.add(...)` calls already used throughout the rest of the app to the four
sales entry points, so future sales issues show up directly in a
diagnostics log instead of only as an on-screen message:
  - gmAddSpellToBasket(): logs when a spell kit is added to the basket.
  - gmCheckoutBasket(): logs when checkout starts, when the order is
    created successfully (with the local order id/total), and - marked
    serious - when it fails, with the actual error message.
  - gmFinishWildwood(): logs when a Wildwood card/cash sale starts, when
    it succeeds, and - marked serious - when it fails, with the actual
    error message.

Applied last, after the FV3 Journal sales patch and the herb-count gate
have already run.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_fv3_sales_diagnostics.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
original = text


def apply_once(text, anchor, replacement, label):
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 occurrence of anchor, found {count}')
    return text.replace(anchor, replacement, 1)


def diag(kind, area, message, detail_js, serious):
    serious_js = 'true' if serious else 'false'
    return (
        "try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add("
        f"'{kind}','{area}','{message}',{detail_js},'',{serious_js});"
        "}catch(_gmDiagErr){}"
    )


# ---------------------------------------------------------------------
# (1) gmAddSpellToBasket: log when a spell kit is added to the basket.
# ---------------------------------------------------------------------
anchor = "function gmAddSpellToBasket(id){const e=readLS(LS_ENTRIES,[]).find(x=>x.entryId===id);if(!e)return;const a=gmReadBasket(),p=gmSalePayload(e),found=a.find(x=>x.journal_entry_id===p.journal_entry_id);if(found)found.quantity=Number(found.quantity||1)+1;else a.push(Object.assign({quantity:1},p));gmWriteBasket(a);toast('Added to basket');}"
replacement = (
    "function gmAddSpellToBasket(id){const e=readLS(LS_ENTRIES,[]).find(x=>x.entryId===id);if(!e)return;const a=gmReadBasket(),p=gmSalePayload(e),found=a.find(x=>x.journal_entry_id===p.journal_entry_id);if(found)found.quantity=Number(found.quantity||1)+1;else a.push(Object.assign({quantity:1},p));gmWriteBasket(a);"
    + diag('ACTION', 'Journal Sales', 'Spell kit added to basket', "{spell_level:p.spell_level,method:p.method}", False)
    + "toast('Added to basket');}"
)
text = apply_once(text, anchor, replacement, 'gmAddSpellToBasket diagnostics')

# ---------------------------------------------------------------------
# (2) gmCheckoutBasket: log start, success, and failure (serious).
# ---------------------------------------------------------------------
anchor = "function gmCheckoutBasket(){const a=gmReadBasket();if(!a.length)return;const card=qs('#gmShopCard'),err=qs('#gmShopError');if(err)err.textContent='';card&&card.classList.add('gm-shop-busy');try{const d=await gmShopPost(GM_SHOP_CREATE,{sale_mode:'greenman',basket:a});if(!d.approval_url)throw new Error('PayPal approval link was not returned');gmCloseShop();try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}}catch(e){if(err)err.textContent=String(e.message||e);card&&card.classList.remove('gm-shop-busy');}}"
replacement = (
    "function gmCheckoutBasket(){const a=gmReadBasket();if(!a.length)return;const card=qs('#gmShopCard'),err=qs('#gmShopError');if(err)err.textContent='';card&&card.classList.add('gm-shop-busy');"
    + diag('ACTION', 'Journal Sales', 'Checkout started', "{kits:a.length}", False)
    + "try{const d=await gmShopPost(GM_SHOP_CREATE,{sale_mode:'greenman',basket:a});if(!d.approval_url)throw new Error('PayPal approval link was not returned');"
    + diag('ACTION', 'Journal Sales', 'Checkout order created', "{local_order_id:d.local_order_id,total:d.total}", False)
    + "gmCloseShop();try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}}catch(e){"
    + diag('CONSOLE ERROR', 'Journal Sales', 'Checkout failed', "{error:String(e&&e.message||e)}", True)
    + "if(err)err.textContent=String(e.message||e);card&&card.classList.remove('gm-shop-busy');}}"
)
text = apply_once(text, anchor, replacement, 'gmCheckoutBasket diagnostics')

# ---------------------------------------------------------------------
# (3) gmFinishWildwood: log start, success (cash/card), and failure (serious).
# ---------------------------------------------------------------------
anchor = "async function gmFinishWildwood(id,kind){const e=readLS(LS_QUICK,[]).find(x=>x.entryId===id);if(!e)return;const email=(qs('#gmSaleEmail')&&qs('#gmSaleEmail').value||'').trim(),receipt=!!(qs('#gmReceiptWanted')&&qs('#gmReceiptWanted').checked),marketing=!!(qs('#gmMarketingWanted')&&qs('#gmMarketingWanted').checked),err=qs('#gmShopError'),card=qs('#gmShopCard');if((receipt||marketing)&&!email){if(err)err.textContent='Enter an email address for the selected email option.';return;}card&&card.classList.add('gm-shop-busy');try{const p=gmSalePayload(e),body={sale_mode:'wildwood',payment_method:kind,customer_email:email,receipt_requested:receipt,marketing_opt_in:marketing,spell:p};const d=await gmShopPost(kind==='cash'?GM_WILDWOOD_CASH:GM_SHOP_CREATE,body);if(kind==='cash'){gmCloseShop();toast('Cash sale recorded'+(d.receipt_sent?' · receipt sent':''));}else{if(!d.approval_url)throw new Error('PayPal approval link was not returned');gmCloseShop();try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}}}catch(e){if(err)err.textContent=String(e.message||e);card&&card.classList.remove('gm-shop-busy');}}"
replacement = (
    "async function gmFinishWildwood(id,kind){const e=readLS(LS_QUICK,[]).find(x=>x.entryId===id);if(!e)return;const email=(qs('#gmSaleEmail')&&qs('#gmSaleEmail').value||'').trim(),receipt=!!(qs('#gmReceiptWanted')&&qs('#gmReceiptWanted').checked),marketing=!!(qs('#gmMarketingWanted')&&qs('#gmMarketingWanted').checked),err=qs('#gmShopError'),card=qs('#gmShopCard');if((receipt||marketing)&&!email){if(err)err.textContent='Enter an email address for the selected email option.';return;}card&&card.classList.add('gm-shop-busy');"
    + diag('ACTION', 'Journal Sales', 'Wildwood sale started', "{kind:kind}", False)
    + "try{const p=gmSalePayload(e),body={sale_mode:'wildwood',payment_method:kind,customer_email:email,receipt_requested:receipt,marketing_opt_in:marketing,spell:p};const d=await gmShopPost(kind==='cash'?GM_WILDWOOD_CASH:GM_SHOP_CREATE,body);if(kind==='cash'){"
    + diag('ACTION', 'Journal Sales', 'Wildwood cash sale recorded', "{receipt_sent:!!d.receipt_sent}", False)
    + "gmCloseShop();toast('Cash sale recorded'+(d.receipt_sent?' · receipt sent':''));}else{if(!d.approval_url)throw new Error('PayPal approval link was not returned');"
    + diag('ACTION', 'Journal Sales', 'Wildwood card order created', "{local_order_id:d.local_order_id,total:d.total}", False)
    + "gmCloseShop();try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}}}catch(e){"
    + diag('CONSOLE ERROR', 'Journal Sales', 'Wildwood sale failed', "{kind:kind,error:String(e&&e.message||e)}", True)
    + "if(err)err.textContent=String(e.message||e);card&&card.classList.remove('gm-shop-busy');}}"
)
text = apply_once(text, anchor, replacement, 'gmFinishWildwood diagnostics')

if text == original:
    raise SystemExit('no changes applied overall')

out.write_text(text, encoding='utf-8')
print(f'wrote {out} bytes={len(text)}')
print('Journal sales feature (add to basket, checkout, Wildwood card/cash) now reports '
      'to the same GREENMAN TABLET DIAGNOSTICS logger as the rest of the app, with '
      'checkout/sale failures marked serious and including the real error message.')
