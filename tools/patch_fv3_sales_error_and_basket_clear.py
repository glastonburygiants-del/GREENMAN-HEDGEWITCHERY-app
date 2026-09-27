#!/usr/bin/env python3
"""Fix two real sales bugs found from a real device diagnostics log.

1. "[object Object]" shown instead of the real error message.

   Confirmed by reading gmShopPost() and the Supabase shop-create-order
   function together: several of that function's error responses set
   `error` to a raw object (e.g. `error:pd`, PayPal's own JSON response
   body) rather than a string. The client's gmShopPost() does
   `throw new Error(d.error||'...')` - when d.error is an object,
   `new Error(anObject)` stringifies it via the object's default
   toString(), which is literally the text "[object Object]". This
   discarded the real underlying error (e.g. what PayPal actually
   rejected about a Wildwood Card order) both on-screen and in the
   diagnostics log added just before this patch. Fix: if d.error is an
   object, JSON.stringify() it instead, so the real error content
   survives.

2. The basket never clears after a successful checkout.

   Confirmed by reading gmCheckoutBasket() directly: after the order is
   created and window.top.location.href navigates to PayPal, the
   function never calls gmWriteBasket([]) or removes the 'gm-shop-busy'
   class it added at the start. If the navigation doesn't actually leave
   the app (or the user returns having cancelled/completed payment), the
   basket still shows the same item, stuck in the faded busy state -
   matching the real-device report "basket didn't clear when paid and
   just stuck faded out". Fix: clear the basket and remove the busy
   class right after the order is successfully created, before
   attempting to navigate away.

Applied last, after the sales diagnostics patch has already run.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_fv3_sales_error_and_basket_clear.py INPUT OUTPUT')

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
# (1) gmShopPost: preserve real error detail instead of "[object Object]".
# ---------------------------------------------------------------------
anchor = "async function gmShopPost(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','apikey':GM_SHOP_ANON,'Authorization':'Bearer '+GM_SHOP_ANON},body:JSON.stringify(body)});const d=await r.json().catch(()=>({}));if(!r.ok||!d.success)throw new Error(d.error||'Checkout could not be started');return d;}"
replacement = "async function gmShopPost(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','apikey':GM_SHOP_ANON,'Authorization':'Bearer '+GM_SHOP_ANON},body:JSON.stringify(body)});const d=await r.json().catch(()=>({}));if(!r.ok||!d.success){const em=d.error&&typeof d.error==='object'?JSON.stringify(d.error):(d.error||'Checkout could not be started');throw new Error(em);}return d;}"
text = apply_once(text, anchor, replacement, 'gmShopPost error stringification')

# ---------------------------------------------------------------------
# (2) gmCheckoutBasket: clear the basket and remove busy state on success.
# ---------------------------------------------------------------------
anchor = "gmCloseShop();try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}}catch(e){try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('CONSOLE ERROR','Journal Sales','Checkout failed'"
replacement = "gmWriteBasket([]);card&&card.classList.remove('gm-shop-busy');gmCloseShop();try{window.top.location.href=d.approval_url;}catch(_){window.location.href=d.approval_url;}}catch(e){try{parent.gmTabletDiagnosticsV1&&parent.gmTabletDiagnosticsV1.add('CONSOLE ERROR','Journal Sales','Checkout failed'"
text = apply_once(text, anchor, replacement, 'gmCheckoutBasket basket clear on success')

if text == original:
    raise SystemExit('no changes applied overall')

out.write_text(text, encoding='utf-8')
print(f'wrote {out} bytes={len(text)}')
print('gmShopPost now preserves real error detail (JSON.stringify) instead of "[object Object]"; '
      'gmCheckoutBasket now clears the basket and removes the busy state right after a successful order.')
