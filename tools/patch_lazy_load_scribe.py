#!/usr/bin/env python3
"""Defer Scribe's ~15MB page payload (code + 217 embedded images) so it is
only fully parsed the first time the user navigates to Scribe, instead of
on every app cold start regardless of use.

Confirmed via real device logs (Choreographer frame-skip warnings, ART GC
pressure, a low-memory-killer cascade that killed the print spooler) and
static analysis (AUDIT_REPORT.md) that Scribe's payload is the dominant
cost in both app startup lag and memory pressure during use. Confirmed via
direct inspection of showPage() that `PAGES[page]` is only ever *read* at
actual navigation time - nothing eagerly iterates or serializes PAGES - so
deferring construction of the string itself is safe and sufficient.

Technique: wrap the giant string literal in a function. JS engines
pre-parse function bodies lazily - doing a cheap brace-matching scan at
load time, and only fully parsing (tokenizing escapes, allocating the
string) the first time the function is actually called. Expose PAGES.scribe
as a getter that calls the function once, then replaces itself with a plain
cached value so every later read is instant. Byte-identical string content;
zero behavioural change once Scribe has been opened once per session.
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_lazy_load_scribe.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text(encoding='utf-8')

marker = 'PAGES.scribe = "'
start = text.find(marker)
if start < 0:
    raise SystemExit('PAGES.scribe = "..." assignment not found')
if text.find(marker, start + 1) != -1:
    raise SystemExit('PAGES.scribe = "..." assignment anchor is not unique')

quote_start = start + len(marker) - 1  # index of the opening "
i = quote_start + 1
n = len(text)
while i < n:
    c = text[i]
    if c == '\\':
        i += 2
        continue
    if c == '"':
        break
    i += 1
if i >= n:
    raise SystemExit('unterminated PAGES.scribe string literal')
quote_end = i + 1  # one past the closing "

if text[quote_end] != ';':
    raise SystemExit('PAGES.scribe string literal not followed by ";" as expected')

literal = text[quote_start:quote_end]  # includes both quotes, byte-identical
statement_end = quote_end + 1  # one past the ";"

replacement = (
    'function __gmLazyScribeSrc(){return ' + literal + ';}\n'
    'Object.defineProperty(PAGES,"scribe",{configurable:true,enumerable:true,'
    'get:function(){var v=__gmLazyScribeSrc();'
    'Object.defineProperty(PAGES,"scribe",{value:v,configurable:true,writable:true,enumerable:true});'
    'return v;}});'
)

patched = text[:start] + replacement + text[statement_end:]

if patched == text:
    raise SystemExit('no change applied')
if 'PAGES.scribe = "' in patched:
    raise SystemExit('direct PAGES.scribe assignment survived')
if patched.count('__gmLazyScribeSrc') != 2:
    raise SystemExit('expected exactly 2 occurrences of __gmLazyScribeSrc (definition + call)')
if literal not in patched:
    raise SystemExit('original scribe string literal missing from patched output')

# The rest of the file (everything before the anchor, and everything after
# the original statement) must be completely untouched.
if patched[:start] != text[:start]:
    raise SystemExit('content before the anchor changed unexpectedly')
if patched[start + len(replacement):] != text[statement_end:]:
    raise SystemExit('content after the anchor changed unexpectedly')

out.write_text(patched, encoding='utf-8')
print('PAGES.scribe deferred: parsed/constructed on first navigation to Scribe, not at app startup')
