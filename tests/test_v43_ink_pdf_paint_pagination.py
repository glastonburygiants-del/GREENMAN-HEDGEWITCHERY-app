#!/usr/bin/env python3
"""V43 Ink Pot SVG paint + ceremony pagination regression."""
import importlib.util
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v43',root/'tools/patch_v43_ink_pdf_paint_pagination.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
render="""async function gmBosRasterizeSvg(svg,token,scale,binding){
 const sourceKey=svg.getAttribute('data-gm-raster-key')||'',w=100,h=100,sc=1.45,cacheKey=sourceKey?(sourceKey+'|'+w+'x'+h+'|'+sc.toFixed(2)):'';
 const copy=svg.cloneNode(true);
  gmBosUniqueSvgDom(copy,'print_svg_'+token);
 const raw=new XMLSerializer().serializeToString(copy);
}"""
ceremony="""function heartCeremonyPages(e){
 function rangeStats(a,b,cap){const safeCap=Math.max(1,cap-6);return safeCap}
 let chosen=null,pageCount=1;
 function fullGroveSplit(start,count,cap){const safeCap=Math.max(1,cap-6);return safeCap}
}
function fitHeartText(root){}"""
page="""<!doctype html><html><head><style>.gmBosPrintSheet .gmStoryVine .vine-stem{fill:none}</style></head><body>
"""+render+ceremony+"</body></html>"
source="NO_ANDROID_CHANGE "+m.ANCHORS[0]+json.dumps(page)+";NO_DATA_CHANGE"
output=m.patch(source)
pos=output.index(m.ANCHORS[0])+len(m.ANCHORS[0])
result,_=json.JSONDecoder().raw_decode(output[pos:])
assert result.count(m.MARK)==1
assert 'gmBosV43InlinePrintSvgPaint(svg,copy)' in result
assert result.count('const safeCap=Math.max(1,cap-20);')==2
assert 'main.length>=13?3:1' in result
assert 'paint-v43' in result
assert "props=['fill','fill-opacity','stroke'" in result
assert output.startswith("NO_ANDROID_CHANGE ") and output.endswith(";NO_DATA_CHANGE")
for bad in (output,source.replace('function heartCeremonyPages(e){','function somethingElse(){')):
 try:m.patch(bad)
 except ValueError:pass
 else:raise AssertionError('V43 fail-closed guard did not reject bad source')
print("PASS V43: computed SVG paint included before raster and 13+ ceremony steps move to >=3 A4 pages")
