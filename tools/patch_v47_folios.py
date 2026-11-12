#!/usr/bin/env python3
"""Fresh Contents/chapter HTML on the validated V43 PDF baseline.
Never modifies the spell binder, signing, stored data or Android permissions.
"""
import json,re,sys
from pathlib import Path
ANCHORS=('function __gmLazyScribeSrc(){return ','PAGES.scribe = ')
MARK='gm-bos-folio-v47-clean'
def replace_function(s,head,next_token,replacement):
    if s.count(head)!=1 or s.count(next_token)!=1:
        raise ValueError(f'V43 function anchors not unique: {head} / {next_token}')
    a=s.index(head);b=s.index(next_token,a+len(head))
    return s[:a]+replacement+'\n'+s[b:]
def patch(src,css,logic):
    active=[a for a in ANCHORS if src.count(a)]
    if len(active)!=1 or src.count(active[0])!=1:raise ValueError('Scribe embedded source ambiguous')
    pos=src.index(active[0])+len(active[0])
    page,n=json.JSONDecoder().raw_decode(src[pos:])
    if not isinstance(page,str) or MARK in page or 'gm-bos-compositor-folio-v45' in page:
        raise ValueError('Expected untouched V43 manuscript layout')
    for marker in ('GM_INK_A4_SVG_PAINT_PAGINATION_V43','gmBosTocItemHTML','gmBosTocChapterHTML','addContents','addChapterContentsPages'):
        if marker not in page:raise ValueError('Missing V43 baseline: '+marker)
    if any(x in css.lower() for x in ('@import','url(', '<script','javascript:')):raise ValueError('No remote assets permitted')
    points=['function gmV47Initial(','function gmBosTocItemHTML(','function gmBosTocChapterHTML(','function addContents(','function addChapterContentsPages(']
    pieces={}
    for i,start in enumerate(points):
        if logic.count(start)!=1:raise ValueError('New function missing/duplicated: '+start)
        begin=logic.index(start);finish=logic.index(points[i+1],begin+len(start)) if i+1<len(points) else len(logic)
        pieces[start]=logic[begin:finish].strip()
    page=replace_function(page,'function gmBosTocItemHTML(','function gmBosTocChapterHTML(',pieces['function gmBosTocItemHTML('])
    page=replace_function(page,'function gmBosTocChapterHTML(','function addContents(',pieces['function gmBosTocChapterHTML('])
    page=replace_function(page,'function addContents(','function addSpellContents(',pieces['function addContents('])
    page=replace_function(page,'function addChapterContentsPages(','const GM_BOS_MOON_CHARGE_STATE_KEY=',pieces['function addChapterContentsPages('])
    page=page.replace('function gmBosTocItemHTML(',pieces['function gmV47Initial(']+'\nfunction gmBosTocItemHTML(',1)
    close=page.index('</head>')
    page=page[:close]+'<style id="'+MARK+'">'+css+'</style>'+page[close:]
    if page.count(MARK)!=1:raise ValueError('Missing unique V47 stylesheet')
    out_json=json.dumps(page,ensure_ascii=False,separators=(',',':'))
    out_json=re.sub(r'</script',r'<\/script',out_json,flags=re.I)
    out=src[:pos]+out_json+src[pos+n:]
    if out[:pos]!=src[:pos] or out[pos+len(out_json):]!=src[pos+n:]:raise ValueError('Outer app altered')
    return out
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: patch_v47_folios.py IN.html OUT.html')
    root=Path(__file__).parent
    css=(root/'bos_folio_v47.css').read_text(encoding='utf-8')
    logic=(root/'gm_v47_runtime.js').read_text(encoding='utf-8')
    Path(sys.argv[2]).write_text(patch(Path(sys.argv[1]).read_text(encoding='utf-8'),css,logic),encoding='utf-8')
    print('V47 new manuscript folios installed: V43 PDF renderer untouched')
