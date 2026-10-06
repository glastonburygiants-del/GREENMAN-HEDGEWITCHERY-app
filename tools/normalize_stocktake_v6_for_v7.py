#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit("usage: normalize_stocktake_v6_for_v7.py input.html output.html")
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
s=src.read_text(encoding="utf-8")

# Older V8 source needed a one-space indentation normalization before the
# cloud-controls patch. V9 already has the expanded back-office tab bar, so
# preserve it exactly rather than trying to force the old Summary-only anchor.
old='''   <button data-page="summary">Summary</button>
  </div>
 </div>'''
new='''    <button data-page="summary">Summary</button>
   </div>
  </div>'''
if s.count(old)==1:
    s=s.replace(old,new,1)
elif 'data-page="subscribers"' not in s:
    raise SystemExit("Stocktake outer navigation is not a recognised V8/V9 source.")

dst.write_text(s,encoding="utf-8")
print("preserved Stocktake V9 navigation / normalized legacy V8 source")
