#!/usr/bin/env python3
"""Fix: Book of Shadows entry list doesn't refresh after checkout, so the
new "PURCHASED"/"BUY AGAIN" badge never actually appears until some other
action happens to redraw the list.

Real-device report: after a successful Greenman basket checkout, the
basket count correctly showed 0 kits (the previous basket-clear fix
working), but the entry card below it still showed the plain "ADD SPELL
KIT TO BASKET" button with no Purchased badge.

Root cause confirmed by reading renderEntries() directly: it's the only
function that redraws `#entryList` (via `.map(entryCard)`), and nothing
in gmCheckoutBasket() ever calls it after gmMarkPurchased() runs - the
list DOM the user is looking at was built before the purchase and is
never regenerated afterward, so it can't show the newly-set purchased
state even though the underlying data is correct.

Fix: call renderEntries() (wrapped in try/catch, since it may not always
be relevant depending on which Journal view is open) right after
gmMarkPurchased() in gmCheckoutBasket(), so the visible list redraws
immediately with the correct badge/button label.

Applied last, after the purchased-badge patch has already run.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_fv3_sales_rerender_entries.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
original = text

anchor = "gmMarkPurchased(a.map(x=>x.journal_entry_id));gmWriteBasket([]);"
replacement = "gmMarkPurchased(a.map(x=>x.journal_entry_id));try{renderEntries();}catch(_gmRenderErr){}gmWriteBasket([]);"

count = text.count(anchor)
if count != 1:
    raise SystemExit(f'gmCheckoutBasket mark-purchased anchor: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

if text == original:
    raise SystemExit('no change applied')

out.write_text(text, encoding='utf-8')
print(f'wrote {out} bytes={len(text)}')
print('gmCheckoutBasket now re-renders the Book of Shadows entry list immediately after a successful purchase, so the PURCHASED badge/BUY AGAIN label shows without needing another action first.')
