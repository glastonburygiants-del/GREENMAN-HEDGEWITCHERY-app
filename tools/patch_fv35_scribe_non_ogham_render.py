#!/usr/bin/env python3
from __future__ import annotations
import base64
import re
import sys
from pathlib import Path

DESK_RE = re.compile(r'const DESK_B64=\\\"([A-Za-z0-9+/=]+)\\\"')

ANCHOR = '''function renderEnglishLine(text){
  const line=document.createElement("div");
  line.className="englishUnderLine";
  line.textContent=text;
  return line;
}
'''

APPEND_WORD_GAP = '''function appendWordGap(line){
  const sp=document.createElement("span");
  sp.className="space";
  const wordGap=Math.max(8,typingSizePt*1.34*.46);
  sp.style.width=wordGap+"px";sp.style.flexBasis=wordGap+"px";sp.style.height=Math.max(18,typingSizePt*1.34)+"px";
  line.appendChild(sp);
}
'''


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

    if desk.count("function appendWordGap(") != 0:
        raise SystemExit("appendWordGap is already present; refusing duplicate restore")
    if desk.count(ANCHOR) != 1:
        raise SystemExit(f"expected one renderEnglishLine anchor, found {desk.count(ANCHOR)}")

    patched=desk.replace(ANCHOR,ANCHOR+APPEND_WORD_GAP,1)
    if patched.count("function appendWordGap(line){") != 1:
        raise SystemExit("appendWordGap restore failed")

    b64=base64.b64encode(patched.encode("utf-8")).decode("ascii")
    out=app[:m.start(1)] + b64 + app[m.end(1):]
    dst.write_text(out,encoding="utf-8")

    check=dst.read_text(encoding="utf-8")
    mm=DESK_RE.search(check)
    if not mm:
        raise SystemExit("DESK_B64 missing after write")
    desk_check=base64.b64decode(mm.group(1),validate=True).decode("utf-8")
    assert desk_check.count("function appendWordGap(line){") == 1
    assert desk_check.count("appendWordGap(") == 2
    print(f"Restored exact Scribe appendWordGap helper: {src.name} -> {dst.name}")


if __name__=="__main__":
    main()
