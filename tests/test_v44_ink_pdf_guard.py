#!/usr/bin/env python3
"""Fail-closed V44 contract test; final application is also checked by V28 workflow."""
import importlib.util,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v44',root/'tools/patch_v44_ink_pdf_guard.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
page="""<!doctype html><html><head></head><body>
<!-- GM_INK_A4_SVG_PAINT_PAGINATION_V43 -->
<script>
async function gmBosRasterizeSvg(svg,token,scale,binding){
const cacheKey=svg.matches('.gmStoryVine,.gmTagBranch')?'|paint-v43':'';
}
async function gmBosPreparePrintPage(page,idx,total,binding,printMap){
  const fitMs=Date.now()-phase;[...stage.querySelectorAll('svg:not(.gmInkScriptWordSvg)')].forEach(svg=>{});
for(let j=0;j<svgs.length;j++){await gmBosRasterizeSvg(svgs[j],idx+'_'+j,total>100?1.12:(total>40?1.25:1.45),binding);if(j%8===7)await new Promise(r=>setTimeout(r,0))}
}
async function printSpell(options){
 options=options||{};if(!pages.length)build();const ix=Number(options.spellIndex)
}
function gmBosBuildFlatPdf(){
push('%PDF-1.4\\n%Greenman Flat A4\\n');
}
</script></body></html>"""
src="OUTER_PREFIX "+m.ANCHORS[0]+json.dumps(page)+";OUTER_SUFFIX"
out=m.patch(src)
start=out.index(m.ANCHORS[0])+len(m.ANCHORS[0])
inner,_=json.JSONDecoder().raw_decode(out[start:])
assert inner.count(m.MARK)==1
for expected in ("gmBosV44PrepareVineForPdf","No incomplete PDF was saved.","Greenman Flat A4 V44","|paint-v44","options=options||{};build();"):
 assert expected in inner,expected
assert "options=options||{};if(!pages.length)build();" not in inner
assert out.startswith("OUTER_PREFIX ") and out.endswith(";OUTER_SUFFIX")
for candidate in (out,src.replace("OUTER_PREFIX ","OUTER_PREFIX ").replace(m.ANCHORS[0], "BAD ",1)):
 try:m.patch(candidate)
 except ValueError:pass
 else:raise AssertionError("expected fail-closed")
print("PASS: V44 identifies and rejects unconverted PDF vine, forces fresh pages, tags PDF, preserves outer app")
