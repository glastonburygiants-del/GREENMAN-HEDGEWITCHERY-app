#!/usr/bin/env python3
"""Fix: real-device diagnostic log captured

    GM V36 protected render error on 14_goddess_herb.html
    ReferenceError: deities is not defined
        at init (<anonymous>:732:91)
        at window.GM_SINGLE_LOAD (<anonymous>:25:38)

    GM V36 protected render error on 15_god_herb.html
    ReferenceError: deities is not defined
        at init (<anonymous>:733:84)

twice, both on Spell Builder step files loaded via window.GM_SINGLE_LOAD
inside PAGES.spellBuilder's single-page-app engine.

Root cause, confirmed by reading the actual shipped Spell Builder engine
script: its init() dispatches each step file to renderSelectPage(kind,
filterFn, dataSet, matchField, next), where dataSet is called as a
zero-arg function (`dataSet()`), exactly like every other step -
crystal/rune/oil pages pass the local `crystals` / `runes` / `oils`
helpers. The goddess/god steps pass `deities` the same way:

    else if(file.includes('goddess')) renderSelectPage('goddess', deityFilter('goddess'), deities, 'Matching Deities', 'god');
    else if(file.includes('god_herb')) renderSelectPage('god', deityFilter('god'), deities, 'Matching Deities', 'oil');

`deityFilter()` (the live, current deity system) is defined in this exact
same closure and works correctly. But unlike `herbs`/`crystals`/`oils`/
`runes`, which each have a matching:

    const herbs = () => arr('Herbs');
    const crystals = () => arr('Crystals');
    const oils = () => arr('Oils');
    const runes = () => arr('Runes');

...there is no `const deities = () => arr('Deities');` anywhere in this
closure, even though the live current data source (window.GM_DATA) does
carry a top-level `Deities` array (confirmed: 100 entries) exactly
parallel to Herbs/Crystals/Oils/Runes. So `deities` is simply never
declared - not a different scope, not a renamed live variable, just this
one accessor missing from the same list its four siblings are on. This is
a straightforward naming/definition gap, not the old parallel
"herbs for desires" deity system the app has had scoping tangles with
elsewhere; nothing about that legacy system is touched here.

Fix: add the single missing accessor, immediately after `runes`, matching
the existing pattern byte-for-byte. This does not remove or rename
anything, and does not touch the old/legacy deity data path at all.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_spellbuilder_deities_undefined.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')


# PAGES.spellBuilder is embedded as a JSON string literal inside this
# file (const PAGES = {...}), so its source lives here with JS newlines
# stored as the two literal characters backslash-n, not real newlines.
anchor = "  const herbs = () => arr('Herbs');\\n  const crystals = () => arr('Crystals');\\n  const oils = () => arr('Oils');\\n  const runes = () => arr('Runes');\\n"
count = text.count(anchor)
if count != 1:
    raise SystemExit(f'expected exactly 1 occurrence of the herbs/crystals/oils/runes accessor block, found {count}')

replacement = anchor + "  const deities = () => arr('Deities');\\n"

if "const deities = () => arr('Deities');\\n" in text:
    raise SystemExit('deities accessor already present - refusing to double-patch')

patched = text.replace(anchor, replacement, 1)

if patched == text:
    raise SystemExit('no change applied')
if patched.count("const deities = () => arr('Deities');\\n") != 1:
    raise SystemExit('expected exactly 1 occurrence of the new deities accessor after patching')

start = text.index(anchor)
if patched[:start] != text[:start]:
    raise SystemExit('content before the anchor changed unexpectedly')
if patched[start + len(replacement):] != text[start + len(anchor):]:
    raise SystemExit('content after the anchor changed unexpectedly')

out.write_text(patched, encoding='utf-8')
print("Spell Builder: added missing 'deities' accessor (parallel to herbs/crystals/oils/runes) fixing ReferenceError on 14_goddess_herb.html / 15_god_herb.html")
