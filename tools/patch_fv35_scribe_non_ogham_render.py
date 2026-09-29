#!/usr/bin/env python3
from __future__ import annotations
import base64
import re
import sys
from pathlib import Path

DESK_RE = re.compile(r'const DESK_B64=\\\"([A-Za-z0-9+/=]+)\\\"')

OLD = '''  const canvas=updatePrintReserve.canvas||(updatePrintReserve.canvas=document.createElement("canvas"));
  const ctx=canvas.getContext("2d");
  ctx.font='17.333px Georgia, "Times New Roman", serif';'''

NEW = '''  const canvas=updatePrintReserve.canvas||(updatePrintReserve.canvas=document.createElement("canvas"));
  let ctx=null;try{ctx=canvas.getContext("2d")}catch(_){}
  if(!ctx||typeof ctx.measureText!=="function")return;
  ctx.font='17.333px Georgia, "Times New Roman", serif';'''


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {Path(sys.argv[0]).name} INPUT.html OUTPUT.html")
    src=Path(sys.argv[1]); dst=Path(sys.argv[2])
    app=src.read_text(encoding="utf-8")
    matches=list(DESK_RE.finditer(app))
    if len(matches)!=1:
        raise SystemExit(f"expected exactly one DESK_B64 payload, found {len(matches)}")
    m=matches[0]
    desk=base64.b64decode(m.group(1),validate=True).decode("utf-8")
    if desk.count(OLD)!=1:
        raise SystemExit(f"expected exactly one Scribe canvas block, found {desk.count(OLD)}")
    patched=desk.replace(OLD,NEW,1)
    b64=base64.b64encode(patched.encode("utf-8")).decode("ascii")
    out=app[:m.start(1)]+b64+app[m.end(1):]
    dst.write_text(out,encoding="utf-8")

    check=dst.read_text(encoding="utf-8")
    mm=DESK_RE.search(check)
    if not mm:
        raise SystemExit("DESK_B64 missing after write")
    d2=base64.b64decode(mm.group(1),validate=True).decode("utf-8")
    assert NEW in d2
    assert OLD not in d2
    print(f"Applied minimal Scribe non-Ogham canvas guard: {src.name} -> {dst.name}")


if __name__=="__main__":
    main()
