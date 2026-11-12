#!/usr/bin/env python3
"""V45: typeset Contents/chapter folios on the proven V43 binder baseline.

Only one JSON-embedded Scribe document changes: its presentation stylesheet,
its visible chapter heading, its one-spell chapter title fallback, and a label.
No Android shell, PDF renderer, storage key, handler, or signing changes.
"""
import json
import re
import sys
from pathlib import Path

ANCHORS=('function __gmLazyScribeSrc(){return ','PAGES.scribe = ')
MARK='gm-bos-compositor-folio-v45'
TITLE="page(c.id,c.num+' · '+c.title,c.sub,'gmBosChapterContentsPage')"
NEW_TITLE="page(c.id,c.title,c.sub,'gmBosChapterContentsPage')"
FALLBACK="if(names.length)return gmBosUniqueNames(names).join(' · ')\n }\n const ids="
NEW_FALLBACK="if(names.length)return gmBosUniqueNames(names).join(' · ')\n }\n if(spells.length===1 && ['spell-list','altars','summaries','timings','instructions'].includes(ch))return spellName(spells[0])+' · '+spellMadeDate(spells[0]);\n const ids="
DEST="' · '+count+' destination'+(count===1?'':'s')"
ENTRY="' · '+count+' '+(count===1?'entry':'entries')"

def one(text,old,new,label):
    n=text.count(old)
    if n!=1:raise ValueError(f'{label}: expected one anchor, found {n}')
    return text.replace(old,new,1)

def patch(src,css):
    active=[a for a in ANCHORS if src.count(a)]
    if len(active)!=1 or src.count(active[0])!=1:
        raise ValueError('Scribe embedding missing or ambiguous')
    pos=src.index(active[0])+len(active[0])
    page,consumed=json.JSONDecoder().raw_decode(src[pos:])
    if not isinstance(page,str) or MARK in page:
        raise ValueError('Expected unmodified embedded Scribe document')
    for token in ('gmBosChapterContentsPage','gmBosTocChapterText','gmChapterOpening','gmChapterCardGrid',
                  'gmChapterCardName','gmBosTocItemLabelBtn','gm-bos-manuscript-v39',
                  'GM_INK_A4_SVG_PAINT_PAGINATION_V43'):
        if token not in page:raise ValueError('V43 book contract missing: '+token)
    if any(token in css.lower() for token in ('@import','url(', '<script', 'javascript:')):
        raise ValueError('CSS must not fetch external resources or run scripts')
    head=page.find('</head>')
    if head<0 or head>page.find('<body'):
        raise ValueError('Outer Scribe head not found')
    page=one(page,TITLE,NEW_TITLE,'Chapter title')
    page=one(page,FALLBACK,NEW_FALLBACK,'Single-spell chapter entry fallback')
    page=one(page,DEST,ENTRY,'Chapter entry-count label')
    page=page[:head]+f'<style id="{MARK}">{css.strip()}</style>'+page[head:]
    if page.count(MARK)!=1:raise ValueError('V45 stylesheet not unique')
    encoded=json.dumps(page,ensure_ascii=False,separators=(',',':'))
    encoded=re.sub(r'</script',r'<\/script',encoded,flags=re.I)
    out=src[:pos]+encoded+src[pos+consumed:]
    if out[:pos]!=src[:pos] or out[pos+len(encoded):]!=src[pos+consumed:]:
        raise ValueError('Outer app changed unexpectedly')
    return out

if __name__=='__main__':
    if len(sys.argv)!=3:
        raise SystemExit('Usage: patch_v45_bos_manuscript.py INPUT.html OUTPUT.html')
    css=Path(__file__).with_name('bos_manuscript_v45.css').read_text(encoding='utf-8')
    result=patch(Path(sys.argv[1]).read_text(encoding='utf-8'),css)
    Path(sys.argv[2]).write_text(result,encoding='utf-8')
    print('V45: manuscript Contents and chapter folios, proven V43 binder untouched.')
