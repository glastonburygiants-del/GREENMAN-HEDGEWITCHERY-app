#!/usr/bin/env python3
"""Fix: sale checkout can build a kit the backend always rejects.

Confirmed by reading the live Supabase shop-create-order edge function
directly (not secondhand): it requires an EXACT herb count per level -
Handful=5, Weaving=7, Full Grove=11 - and rejects anything else with
"<Level> must contain <N> herbs." It also requires the client to send
one of exactly "Handful"/"Weaving"/"Full Grove" as spell_level.

The client's gmSaleLevel() (added by the FV3.1 Journal sales patch)
picks a level from a saved spell's freeform `depth` text first, and
otherwise falls back to range checks (11+ herbs -> Full Grove, 7+ ->
Weaving, else Handful). Both paths can pick a level whose herb count
doesn't actually match the spell's real herb count - e.g. a spell with
6, 8, 9, 10 or 12+ herbs, or a `depth` string that says "full" but
doesn't actually have 11 herbs. The customer can add such a spell to
the basket, but checkout will always fail there with the backend's
herb-count error - a confusing, avoidable dead end after they've
already tried to buy.

Fix: gmSaleLevel() now only returns a level when the spell's real herb
count is exactly 5, 7 or 11 (ignoring the unreliable `depth` text
entirely, since nothing confirms it agrees with the actual herbs);
otherwise it returns null. The two sale-entry points (the Journal's
"ADD SPELL KIT TO BASKET" button and the Quick List's Wildwood
CARD/CASH buttons) now both require a non-null gmSaleLevel(e) before
showing themselves, so an unsellable spell simply isn't offered for
sale rather than failing after the fact.

Applied last, after the FV3.1 Journal sales patch has already run.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_fv3_sales_herbcount_gate.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')
original = text


def apply_once(text, anchor, replacement, label):
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 occurrence of anchor, found {count}')
    return text.replace(anchor, replacement, 1)


# (1) gmSaleLevel: only trust the spell's real herb count, exact match only.
anchor = (
    "function gmSaleLevel(e){const d=String((e&&e.depth)||'').toLowerCase();"
    "if(d.includes('full')||d.includes('grove'))return'Full Grove';"
    "if(d.includes('weav'))return'Weaving';"
    "if(d.includes('hand'))return'Handful';"
    "const n=herbNames(e).length;"
    "return n>=11?'Full Grove':(n>=7?'Weaving':'Handful');}"
)
replacement = (
    "function gmSaleLevel(e){const n=herbNames(e).length;"
    "if(n===5)return'Handful';if(n===7)return'Weaving';if(n===11)return'Full Grove';"
    "return null;}"
)
text = apply_once(text, anchor, replacement, 'gmSaleLevel exact-match rewrite')

# (2) Journal entry card: only offer ADD SPELL KIT TO BASKET when sellable.
anchor = "const canBuy=gmShopMode()==='full'&&e.entryType!=='timing'&&e.entryType!=='grimoire';"
replacement = "const canBuy=gmShopMode()==='full'&&e.entryType!=='timing'&&e.entryType!=='grimoire'&&!!gmSaleLevel(e);"
text = apply_once(text, anchor, replacement, 'Journal canBuy herb-count gate')

# (3) Quick List card: only offer Wildwood CARD/CASH when sellable.
anchor = "const sale=gmShopMode()==='master'?`<div class=\\\"gm-sale-row\\\">"
replacement = "const sale=(gmShopMode()==='master'&&!!gmSaleLevel(e))?`<div class=\\\"gm-sale-row\\\">"
text = apply_once(text, anchor, replacement, 'Quick List Wildwood sale-row herb-count gate')

if text == original:
    raise SystemExit('no changes applied overall')

out.write_text(text, encoding='utf-8')
print(f'wrote {out} bytes={len(text)}')
print('Sale checkout now only offered for spells with exactly 5, 7, or 11 herbs '
      '(matching the live backend\'s exact requirement, confirmed via Supabase MCP) - '
      'depth-text guessing removed, both sale entry points gated the same way.')
