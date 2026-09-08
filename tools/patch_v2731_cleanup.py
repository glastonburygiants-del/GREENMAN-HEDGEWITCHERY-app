#!/usr/bin/env python3
import re, sys, hashlib
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_v2731_cleanup.py INPUT.html OUTPUT.html')

src = Path(sys.argv[1]).read_text(encoding='utf-8')

# Remove the repeated editor/build instruction from both Admin and Spell Builder data.
internal_note = "App should pull this row's Greenman Energy Mode from the main item sheets. Use Secondary Energy Hint only if a serious/adult spell still needs a Draw/Hold/Release/Open/Transform flavour."
src = src.replace(internal_note, '')

# Remove the leaked Emerald build label from every duplicated data copy.
src = src.replace('EMERALD — SECOND CURRENT MASTER RECORD', 'EMERALD')
src = src.replace('EMERALD \\u2014 SECOND CURRENT MASTER RECORD', 'EMERALD')

# Remove research citation tags that were never intended as app prose.
src = re.sub(r'\s*\[cite\s*:[^\]]+\]', '', src, flags=re.I)

# Remove source-layer language from Fir Needle data copies.
src = src.replace(
    'Used in magic for: None supported by the source layer.',
    'Purification, protection, healing, new beginnings, strength and prosperity.'
)
src = re.sub(r'None supported by the source layer\.\s*,?\s*', '', src, flags=re.I)

# BoS must never use internal editor Instruction Notes as public wording.
old_wording = "function wording(e){const d=sd(e);return String(first(e&&e.WordingFocus,e&&e.wordingFocus,d['Wording Focus'],d['Instruction Notes'],e&&e.summary,''))}"
new_wording = "function wording(e){const d=sd(e);return String(first(e&&e.WordingFocus,e&&e.wordingFocus,d['Wording Focus'],e&&e.summary,''))}"
if old_wording not in src:
    raise SystemExit('BoS internal Instruction Notes fallback anchor not found')
src = src.replace(old_wording, new_wording, 1)

marker = '<!-- FV 2.7.31 USER-WORDING CLEANUP: leaked build labels/research tags removed; BoS cannot fall back to internal Instruction Notes. -->'
if marker not in src:
    src = src.replace('</head>', marker + '\n</head>', 1)

for bad in [
    'SECOND CURRENT MASTER RECORD',
    'CURRENT MASTER RECORD',
    'None supported by the source layer',
    '[cite:',
    'App should pull this row',
]:
    if bad.lower() in src.lower():
        raise SystemExit('User-facing build debris still present: ' + bad)

if "d['Instruction Notes']" in src[src.find('function wording(e){'):src.find('function energy(e){')]:
    raise SystemExit('BoS wording still falls back to Instruction Notes')

Path(sys.argv[2]).write_text(src, encoding='utf-8')
data = src.encode('utf-8')
print('bytes', len(data))
print('sha256', hashlib.sha256(data).hexdigest())
