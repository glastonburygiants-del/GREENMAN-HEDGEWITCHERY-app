#!/usr/bin/env python3
"""Carry each Scribe glyph into its page so shadow roots and print need no shared defs."""
import json,re,sys
from pathlib import Path

RUNTIME=r'''
const GM_V56_GLYPH_CSS='.sheet .hand-sample svg.hand-glyph{fill:currentColor!important;stroke:currentColor!important;stroke-width:8!important;stroke-linejoin:round!important}.sheet .letter-art svg.ref-glyph{fill:currentColor;stroke:currentColor;stroke-width:6;stroke-linejoin:round}.sheet .roman-sample,.sheet .hand-punct{font-weight:700}';
function gmV56InlineGlyphs(sheet,source){
 let pass=0;
 while(sheet.querySelector('use')){
  if(++pass>8)throw new Error('Nested Scribe glyph reference limit');
  sheet.querySelectorAll('use').forEach(use=>{
   const href=use.getAttribute('href')||use.getAttribute('xlink:href')||'';
   const target=href.startsWith('#')?source.getElementById(href.slice(1)):null;
   if(!target)throw new Error('Missing Scribe symbol '+href);
   const svg=use.closest('svg');const group=source.createElementNS('http://www.w3.org/2000/svg','g');
   for(const attr of target.attributes){if(!['id','viewBox','viewbox'].includes(attr.name))group.setAttribute(attr.name,attr.value)}
   if(use.getAttribute('transform'))group.setAttribute('transform',use.getAttribute('transform'));
   if(target.tagName.toLowerCase()==='symbol'){
    const viewBox=target.getAttribute('viewBox')||target.getAttribute('viewbox');if(viewBox&&svg)svg.setAttribute('viewBox',viewBox);
    for(const child of target.childNodes)group.append(child.cloneNode(true));
   }else{const copy=target.cloneNode(true);copy.removeAttribute('id');group.append(copy)}
   group.dataset.gmScribeGlyph=href.slice(1);use.replaceWith(group);
  });
 }
}
'''

def once(s,a,b):
 if s.count(a)!=1:raise ValueError('Expected one anchor: '+a[:100])
 return s.replace(a,b,1)

def patch(s):
 a='function __gmLazyScribeSrc(){return ';pos=s.index(a)+len(a);doc,n=json.JSONDecoder().raw_decode(s[pos:])
 if 'gm-bos-scribe-opener-v55' not in doc:raise ValueError('V55 base required')
 doc=once(doc,'const W=794,H=1123;','const W=794,H=1123;\n'+RUNTIME)
 doc=once(doc,"const styles=qa('style',doc).map(x=>x.textContent||'').join('\\n'),sheets=", "const styles=qa('style',doc).map(x=>x.textContent||'').join('\\n')+GM_V56_GLYPH_CSS,sheets=")
 doc=once(doc,'const getHtml=()=>{const copy=sheet.cloneNode(true);if(i===0)', 'const getHtml=()=>{const copy=sheet.cloneNode(true);gmV56InlineGlyphs(copy,doc);if(i===0)')
 doc=doc.replace('</head>','<!-- gm-bos-scribe-glyphs-v56 --></head>',1)
 enc=re.sub(r'</script',r'<\/script',json.dumps(doc,ensure_ascii=False,separators=(',',':')),flags=re.I)
 return s[:pos]+enc+s[pos+n:]

if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('Usage: patch_v56_scribe_glyphs.py INPUT OUTPUT')
 Path(sys.argv[2]).write_text(patch(Path(sys.argv[1]).read_text()),encoding='utf-8')
 print('V56: Scribe chart and description symbols made self-contained and bold')
