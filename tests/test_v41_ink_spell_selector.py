#!/usr/bin/env python3
"""Print Spell tab regression: later Scribe function must keep symbol tab refresh."""
import importlib.util
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gmv41',root/'tools/patch_v41_ink_spell_selector.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

early="""function gmInkSetTab(name){const key=String(name||'print').toLowerCase();if(key==='symbols'&&typeof renderInkSpellPrint==='function')renderInkSpellPrint()}"""
late=("function gmInkSetTab(name){const key=String(name||'print').toLowerCase();"
      "$$('[data-inktab]').forEach(x=>x.classList.toggle('active',x.dataset.inktab===key));"
      "$$('.inkTabPanel').forEach(p=>p.classList.toggle('active',p.id==='ink'+key[0].toUpperCase()+key.slice(1)));"+mod.LATE)
page=("<!doctype html><html><head></head><body><div id='gmInkSpellList'></div>"
      + "<script>"+early+";function renderInkSpellPrint(){return GM_BOS.spellCatalog()}"+late+"</script></body></html>")
source="ORIGINAL_APP_PREFIX:"+mod.ANCHORS[0]+json.dumps(page)+";ORIGINAL_APP_SUFFIX"
fixed=mod.patch(source)
pos,tail=fixed.split(mod.ANCHORS[0],1)
assert pos=="ORIGINAL_APP_PREFIX:"
output,_n=json.JSONDecoder().raw_decode(tail)
assert output.count(mod.MARKER)==1
assert output.count(mod.FIXED)==1
assert output.count("function gmInkSetTab(")==2
assert "GM_BOS.spellCatalog()" in output
assert "gmInkSpellList" in output
assert output.replace(mod.FIXED+"/* "+mod.MARKER+" */",mod.LATE,1)==page
assert fixed.endswith(";ORIGINAL_APP_SUFFIX")
for bad in [fixed,source.replace(mod.LATE,"broken"),source.replace("function renderInkSpellPrint(){","function missing(){")]:
    try:
        mod.patch(bad)
        raise AssertionError("Fail-closed patch accepted incompatible source")
    except ValueError:
        pass
print("PASS: late handler now refreshes Print Spell, preserves original app and all other routes")
