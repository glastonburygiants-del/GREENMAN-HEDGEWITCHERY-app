#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: install_proven_summary_print.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')

# 1) Restore the proven whole-page fit principle from the locked A4 print pack,
# but only for Summary page 2 and only inside the existing canonical print/page owner.
anchor = """ if(!isInfo&&!isInstructions){\\n  var content=q('.true-content',page)||page,pass=0;\\n  while(content.scrollHeight>1058&&pass++<10){\\n   textLeaves(content).forEach(function(el){var fs=parseFloat(getComputedStyle(el).fontSize)||12;if(fs>5.2){el.style.setProperty('font-size',Math.max(5.2,fs*.95).toFixed(2)+'px','important');el.style.setProperty('line-height','1.05','important')}});\\n   qa('.true-box,.item-row',content).forEach(function(el){var cs=getComputedStyle(el),pt=parseFloat(cs.paddingTop)||0,pr=parseFloat(cs.paddingRight)||0,pb=parseFloat(cs.paddingBottom)||0,pl=parseFloat(cs.paddingLeft)||0;el.style.setProperty('padding',Math.max(1,pt*.9)+'px '+Math.max(1,pr*.9)+'px '+Math.max(1,pb*.9)+'px '+Math.max(1,pl*.9)+'px','important')});\\n  }\\n }\\n}"""

replacement = """ if(!isInfo&&!isInstructions){\\n  var content=q('.true-content',page)||page,pass=0;\\n  while(content.scrollHeight>1058&&pass++<10){\\n   textLeaves(content).forEach(function(el){var fs=parseFloat(getComputedStyle(el).fontSize)||12;if(fs>5.2){el.style.setProperty('font-size',Math.max(5.2,fs*.95).toFixed(2)+'px','important');el.style.setProperty('line-height','1.05','important')}});\\n   qa('.true-box,.item-row',content).forEach(function(el){var cs=getComputedStyle(el),pt=parseFloat(cs.paddingTop)||0,pr=parseFloat(cs.paddingRight)||0,pb=parseFloat(cs.paddingBottom)||0,pl=parseFloat(cs.paddingLeft)||0;el.style.setProperty('padding',Math.max(1,pt*.9)+'px '+Math.max(1,pr*.9)+'px '+Math.max(1,pb*.9)+'px '+Math.max(1,pl*.9)+'px','important')});\\n  }\\n }\\n // Proven locked-pack final containment: keep the A4 frame fixed and fit only\\n // Summary page 2 content to the real 756 x 1058 canvas after all text is populated.\\n if(p2){\\n  var fitContent=q(':scope > .true-content',page)||q('.true-content',page);\\n  if(fitContent){\\n   fitContent.style.removeProperty('transform');\\n   fitContent.style.setProperty('transform-origin','top left','important');\\n   fitContent.style.removeProperty('width');\\n   void page.offsetHeight;\\n   var neededH=(fitContent.scrollHeight||0)/Math.max(1,page.clientHeight||1058);\\n   var neededW=(fitContent.scrollWidth||0)/Math.max(1,page.clientWidth||756);\\n   var needed=Math.max(neededH,neededW);\\n   if(needed>1.002){\\n    var p2scale=Math.max(.50,Math.min(1,1/needed)*.985);\\n    fitContent.style.setProperty('width',(100/p2scale).toFixed(4)+'%','important');\\n    fitContent.style.setProperty('transform','scale('+p2scale.toFixed(5)+')','important');\\n    page.setAttribute('data-gm-summary2-fit',p2scale.toFixed(5));\\n   }else{\\n    fitContent.style.removeProperty('width');\\n    fitContent.style.removeProperty('transform');\\n    page.setAttribute('data-gm-summary2-fit','1.00000');\\n   }\\n  }\\n }\\n}"""

if s.count(anchor) != 1:
    raise SystemExit(f'canonical fitPage anchor count was {s.count(anchor)}, expected 1')
s = s.replace(anchor, replacement, 1)

# 2) Restore the locked print pack's dedicated black-and-white print behaviour.
# It is inserted only into the generated print documents, never into the screen UI.
bw = (
"@media print{"
"*{color:#000!important;background:transparent!important;background-color:transparent!important;background-image:none!important;-webkit-print-color-adjust:economy!important;print-color-adjust:economy!important;color-adjust:economy!important;}"
".border-outer,.border-inner{border-color:#000!important;}"
".corner svg{stroke:#000!important;}"
".pack-page,.pp-page,.page,.true-page{border-color:#000!important;box-shadow:none!important;}"
".altar-slot,.altar-slot.filled,.ac,.ac.centre{border-color:#000!important;}"
".altar-label,.al,.altar-val{color:#000!important;}"
".rec-badge{background:#000!important;color:#fff!important;}"
".spell-btn,.spell-btn.recommended,.spell-btn.selected{border-color:#000!important;}"
".pp-tag{background:transparent!important;border-color:#999!important;}"
".time-row.best{background:transparent!important;border-color:#000!important;}"
".corr-table th{background:transparent!important;border-color:#000!important;}"
".corr-table td{border-color:#ccc!important;}"
".item-row.header{background:transparent!important;border-color:#000!important;}"
".element-circle svg path,.element-circle svg circle{stroke:#999!important;}"
".gm-ritual-head .gm-col-title{background:transparent!important;border-color:#000!important;color:#000!important;}"
".gm-step.gm-making-cell,.gm-step.gm-voice-cell{border-color:#ccc!important;}"
".pp-entry-card,.deity-half{border-color:#ccc!important;background:transparent!important;}"
".pp-info-box{border-color:#ccc!important;background:transparent!important;}"
".pp-info-text.green,.item-green,.deity-info-grid .pp-info-text{color:#000!important;}"
"svg path,svg circle,svg line{stroke:#000!important;fill:none!important;}"
"}"
)

# Full A4 page / pack document. Put monochrome rules after all scoped page CSS.
full_anchor = "'+scoped+'</style></head><body><main id=\\\"root\\\"></main></body></html>'"
full_repl = "'+scoped+'" + bw + "</style></head><body><main id=\\\"root\\\"></main></body></html>'"
if s.count(full_anchor) != 1:
    raise SystemExit(f'full print style anchor count was {s.count(full_anchor)}, expected 1')
s = s.replace(full_anchor, full_repl, 1)

# Lite/Simple Summary print document. Append the same locked B&W block at the end
# of its print-only CSS so the live Summary screen remains full colour.
lite_anchor = ".gm-v79-paper li{font-size:14px!important;line-height:1.18!important;padding:0 0 5px 4px!important;break-inside:avoid!important}</style></head><body><section class=\\\"sheet\\\">"
lite_repl = ".gm-v79-paper li{font-size:14px!important;line-height:1.18!important;padding:0 0 5px 4px!important;break-inside:avoid!important}" + bw + "</style></head><body><section class=\\\"sheet\\\">"
if s.count(lite_anchor) != 1:
    raise SystemExit(f'lite print style anchor count was {s.count(lite_anchor)}, expected 1')
s = s.replace(lite_anchor, lite_repl, 1)

# Guard against accidentally reintroducing the later Android print relay chain.
for forbidden in ('nativePrintHtml', 'gmNativePrintHtml', 'GreenmanAndroid.printHtml'):
    if forbidden in s:
        raise SystemExit(f'forbidden old print relay found after restore: {forbidden}')

# Ensure exactly one canonical fit marker and both B&W copies are present.
if s.count("data-gm-summary2-fit") != 2:
    raise SystemExit('Summary page-2 fit marker did not install exactly once')
if s.count("print-color-adjust:economy!important") != 4:
    raise SystemExit('B&W print rules were not installed in exactly two print documents')

out.write_text(s, encoding='utf-8')
print(f'Installed proven Summary page-2 containment and locked B&W print: {out}')
