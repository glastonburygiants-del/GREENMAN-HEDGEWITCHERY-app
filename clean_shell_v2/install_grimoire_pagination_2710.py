#!/usr/bin/env python3
from pathlib import Path
import json, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: install_grimoire_pagination_2710.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')
marker = 'const PAGES = '
st = s.index(marker) + len(marker)
pages, end = json.JSONDecoder().raw_decode(s[st:])
if 'bos' not in pages:
    raise SystemExit('missing PAGES.bos')
bos = pages['bos']

# Preserve the proven 2.7.9 rule directly in the generated app: Grimoire and
# Summary pages keep their specialist fitters and are never scaled a second time
# by the generic whole-book fitter.
old_selector = ".a4-page:not(.gm-flat):not(.gm-book-front):not(.gm-book-frontmatter)"
new_selector = ".a4-page:not(.gm-flat):not(.gm-book-front):not(.gm-book-frontmatter):not(.grimoire-page):not(.summary-page)"
if new_selector not in bos:
    if bos.count(old_selector) != 1:
        raise SystemExit('2.7.10: whole-book fitter selector anchor changed')
    bos = bos.replace(old_selector, new_selector, 1)

start = bos.index('function buildGrimoirePages(e){')
stop = bos.index('\n\nfunction fitTextInsideBox', start)
new_builder = r'''function buildGrimoirePages(e){
  const item=e.grimoireItem||e.item||{},title=item.Name||item.name||e.spellName||'Grimoire Entry';
  const magicalUses=item['Magical Uses']||item.magicalUses||'';
  const powers=item.Powers||item.powers||'';
  const green=item['Greenman Energy']||item.greenmanEnergy||item.green||'';
  const correspondences=[item.Element,item.Planet,item.Day,item.Number,item.Gender].filter(Boolean).join(' · ');
  const associated=associatedText(item);
  const description=item.Description||item.description||'';
  const folklore=item['Folk Lore']||item.folklore||'';
  const geology=item.Geology||item.Origin||'';
  const warning=item.Warning||item.warning||'';
  const identity=`<div class="parch-box"><div class="pp-section-title">Identity</div>${infoRow('Category',e.category)}${infoRow('Name',item.Name||item.name)}${infoRow('Ye Olde Name',item['Ye Olde Name']||item.old||item.yeOlde)}${infoRow('Latin',item.Latin||item['Latin Name']||item.latin)}</div>`;
  const magicalBox=`<div class="grimoire-info"><div class="grimoire-info-label">Magical Uses</div><div class="grimoire-info-text">${esc(magicalUses)}</div></div>`;
  const textWeight=[magicalUses,powers,green,associated,description,folklore,geology,warning].join(' ').length;
  const split=textWeight>900 || String(magicalUses).length>520 || String(description).length>420 || String(folklore).length>360;

  if(!split){
    const one=pageHead(title,'Grimoire Entry','1 of 1')+
    `<main class="grimoire-layout">
      <div class="grimoire-identity-notes">${identity}${hedgeNotesBox(e)}</div>
      <div class="grimoire-magical-full">${magicalBox}</div>
      <div class="grimoire-grid">
        ${gBlock('Powers',powers)}
        ${gBlock('Greenman Energy',green,'green')}
        ${gBlock('Correspondences',correspondences,'wide')}
        ${gBlock('Associated Items',associated,'wide')}
        ${gBlock('Description',description,'wide')}
        ${gBlock('Folk Lore',folklore,'wide')}
        ${gBlock('Geology / Origin',geology,'wide')}
        ${gBlock('Warning',warning,'wide')}
      </div>
    </main>`;
    return pageFrame(one,true,'grimoire-page gm-grimoire-native gm-grimoire-single');
  }

  const first=pageHead(title,'Grimoire Entry','1 of 2')+
  `<main class="grimoire-layout">
    <div class="grimoire-identity-notes">${identity}${hedgeNotesBox(e)}</div>
    <div class="grimoire-magical-full">${magicalBox}</div>
    <div class="grimoire-grid">
      ${gBlock('Powers',powers)}
      ${gBlock('Greenman Energy',green,'green')}
      ${gBlock('Correspondences',correspondences,'wide')}
    </div>
  </main>`;
  const second=pageHead(title,'Grimoire Entry','2 of 2')+
  `<main class="grimoire-layout gm-grimoire-continuation">
    <div class="grimoire-grid">
      ${gBlock('Associated Items',associated,'wide')}
      ${gBlock('Description',description,'wide')}
      ${gBlock('Folk Lore',folklore,'wide')}
      ${gBlock('Geology / Origin',geology,'wide')}
      ${gBlock('Warning',warning,'wide')}
    </div>
  </main>`;
  return pageFrame(first,true,'grimoire-page gm-grimoire-native gm-grimoire-split gm-grimoire-split-1')+
         pageFrame(second,false,'grimoire-page gm-grimoire-native gm-grimoire-split gm-grimoire-split-2');
}'''
bos = bos[:start] + new_builder + bos[stop:]

old_fit = """function fitGrimoirePages(root=document){\n  qsa('.grimoire-page',root).forEach(page=>{\n    page.style.setProperty('--grimoire-fit-scale','1');\n    fitAllGrimoireInfoBoxes(page);"""
new_fit = """function fitGrimoirePages(root=document){\n  qsa('.grimoire-page',root).forEach(page=>{\n    page.style.setProperty('--grimoire-fit-scale','1');\n    fitAllGrimoireInfoBoxes(page);\n    if(page.classList.contains('gm-grimoire-native')){\n      requestAnimationFrame(()=>fitAllGrimoireInfoBoxes(page));\n      return;\n    }"""
if bos.count(old_fit) != 1:
    raise SystemExit('2.7.10: Grimoire fitter anchor changed')
bos = bos.replace(old_fit, new_fit, 1)

css = r'''
<style id="gm-grimoire-pagination-v1">
.gm-grimoire-native .a4-content{transform:none!important;width:100%!important;height:100%!important;}
.gm-grimoire-native .grimoire-layout{display:flex!important;flex-direction:column!important;height:auto!important;gap:8px!important;overflow:hidden!important;}
.gm-grimoire-native .grimoire-grid{flex:0 0 auto!important;overflow:visible!important;}
.gm-grimoire-native .grimoire-grid>.grimoire-info{height:auto!important;}
.gm-grimoire-single .grimoire-magical-full .grimoire-info{height:auto!important;min-height:112px!important;max-height:170px!important;}
.gm-grimoire-single .grimoire-grid>.grimoire-info:nth-child(1),.gm-grimoire-single .grimoire-grid>.grimoire-info:nth-child(2){height:72px!important;}
.gm-grimoire-single .grimoire-grid>.grimoire-info:nth-child(n+3){height:62px!important;}
.gm-grimoire-split-1 .grimoire-magical-full .grimoire-info{height:230px!important;min-height:230px!important;max-height:230px!important;}
.gm-grimoire-split-1 .grimoire-grid>.grimoire-info:nth-child(1),.gm-grimoire-split-1 .grimoire-grid>.grimoire-info:nth-child(2){height:118px!important;}
.gm-grimoire-split-1 .grimoire-grid>.grimoire-info:nth-child(3){height:84px!important;}
.gm-grimoire-split-2 .grimoire-grid{grid-template-columns:1fr!important;}
.gm-grimoire-split-2 .grimoire-grid>.grimoire-info{grid-column:1!important;}
.gm-grimoire-split-2 .grimoire-grid>.grimoire-info:nth-child(1){height:104px!important;}
.gm-grimoire-split-2 .grimoire-grid>.grimoire-info:nth-child(2){height:190px!important;}
.gm-grimoire-split-2 .grimoire-grid>.grimoire-info:nth-child(3){height:150px!important;}
.gm-grimoire-split-2 .grimoire-grid>.grimoire-info:nth-child(4){height:104px!important;}
.gm-grimoire-split-2 .grimoire-grid>.grimoire-info:nth-child(5){height:128px!important;}
</style>
'''
bos = bos.replace('</head>', css + '</head>', 1)

pages['bos'] = bos
new_json = json.dumps(pages, ensure_ascii=False, separators=(',', ':'))
s = s[:st] + new_json + s[st+end:]

for term in ('gm-grimoire-pagination-v1','gm-grimoire-native','gm-grimoire-split-1','gm-grimoire-split-2',"textWeight>900"):
    if term not in s:
        raise SystemExit('missing 2.7.10 pagination guard: ' + term)
out.write_text(s, encoding='utf-8')
print('Installed 2.7.10 Grimoire pagination: short entries remain one A4 page; long entries split cleanly across two A4 pages without whole-page shrinking')
