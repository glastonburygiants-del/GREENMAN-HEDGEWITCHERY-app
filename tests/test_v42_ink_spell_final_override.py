#!/usr/bin/env python3
import importlib.util,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('v42',root/'tools/patch_v42_ink_spell_final_override.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
begin='function gmInkSetTab(name){'+'gmInkSetTab=function(name){\n'
source_page=("<html><head></head><body><div id='gmInkSpellList'></div><script>"+
             begin+m.OLD+'function renderInkSpellPrint(){return GM_BOS.spellCatalog()}</script></body></html>')
input_source='PRODUCTION_SHELL_UNCHANGED '+m.ANCHORS[0]+json.dumps(source_page)+';END_SHELL'
out=m.patch(input_source)
pos=out.index(m.ANCHORS[0])+len(m.ANCHORS[0])
doc,n=json.JSONDecoder().raw_decode(out[pos:])
assert m.MARK in doc
assert m.NEW in doc
assert 'gmInkSpellList' in doc and 'GM_BOS.spellCatalog()' in doc
assert doc.replace(m.NEW+'/* '+m.MARK+' */',m.OLD,1)==source_page
assert out.startswith('PRODUCTION_SHELL_UNCHANGED ') and out.endswith(';END_SHELL')
for candidate in (out,input_source.replace(m.OLD,'unrelated function')):
    try:m.patch(candidate)
    except ValueError:pass
    else:raise AssertionError('fail-closed source guard not enforced')
print('PASS V42: final tab override restores Print Spell, no changes outside Scribe')
