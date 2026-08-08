#!/usr/bin/env python3
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: repair_embedded_script_boundaries.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')
marker = 'const PAGES = '
start = s.index(marker) + len(marker)
obj, end = json.JSONDecoder().raw_decode(s[start:])
raw = s[start:start+end]

unsafe = raw.lower().count('</script>')
if unsafe == 0:
    raise SystemExit('boundary repair expected unsafe inner </script> tags but found 0')

# Preserve the decoded embedded pages exactly. Only protect the outer HTML parser
# by escaping the slash in inner closing script tags inside the PAGES source.
fixed = raw.replace('</script>', '<\\/script>').replace('</SCRIPT>', '<\\/SCRIPT>')

if fixed.lower().count('</script>') != 0:
    raise SystemExit('unsafe inner </script> remains after repair')

# The decoded PAGES object must remain identical after boundary escaping.
obj2, end2 = json.JSONDecoder().raw_decode(fixed)
if obj2 != obj or end2 != len(fixed):
    raise SystemExit('decoded embedded pages changed during boundary repair')

s2 = s[:start] + fixed + s[start+end:]
out.write_text(s2, encoding='utf-8')
print(f'Repaired embedded script boundaries: {unsafe} unsafe closers -> 0')
print(f'Protected inner closers now present: {fixed.lower().count("<\\/script>")}')
