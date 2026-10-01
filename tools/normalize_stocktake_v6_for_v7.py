#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=3:
    raise SystemExit("usage: normalize_stocktake_v6_for_v7.py input.html output.html")
src=Path(sys.argv[1]); dst=Path(sys.argv[2])
s=src.read_text(encoding="utf-8")
old='''   <button data-page="summary">Summary</button>
  </div>
 </div>'''
new='''    <button data-page="summary">Summary</button>
   </div>
  </div>'''
if s.count(old)!=1:
    raise SystemExit(f"stocktake outer tabs source anchor count: {s.count(old)}")
s=s.replace(old,new,1)
dst.write_text(s,encoding="utf-8")
print("normalized Stocktake V6 outer indentation for V7 patcher")
