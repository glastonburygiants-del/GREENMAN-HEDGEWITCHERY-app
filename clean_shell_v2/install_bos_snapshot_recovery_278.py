#!/usr/bin/env python3
from pathlib import Path
import json, sys

if len(sys.argv)!=3:
    raise SystemExit('usage: install_bos_snapshot_recovery_278.py INPUT OUTPUT')

src=Path(sys.argv[1]); out=Path(sys.argv[2])
s=src.read_text(encoding='utf-8')
marker='const PAGES = '
st=s.index(marker)+len(marker)
obj,end=json.JSONDecoder().raw_decode(s[st:])
for k in ('journal','spellBuilder'):
    if k not in obj: raise SystemExit(f'missing PAGES.{k}')
journal=obj['journal']; spell=obj['spellBuilder']


def replace_once(text,old,new,label):
    n=text.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 anchor, got {n}')
    return text.replace(old,new,1)

# ---------------------------------------------------------------------------
# JOURNAL / BOS PRINT RECOVERY
# ---------------------------------------------------------------------------
# The saved GM-BOS-PAGES-2 record already contains each canonical page's own CSS.
# Older records may also contain runtime fitting residue in inline styles and in the
# captured global head CSS. The tell-tale failure is a full-width page whose type
# and rows are only a fraction of their intended height. For these four A4 source
# pages there are no authored inline geometry/font styles, so geometry/font inline
# values are runtime residue and can be safely removed while preserving dynamic
# visibility and grid-column values.
helper=r'''
function gmRecoverBosSnapshotPage(root){
  if(!root)return root;
  var nodes=[root].concat(qsa('*',root));
  nodes.forEach(function(el){
    if(!el||el.nodeType!==1)return;
    var tag=String(el.nodeName||'').toLowerCase();
    if(tag==='svg'||tag==='path'||tag==='circle'||tag==='ellipse'||tag==='line'||tag==='polyline'||tag==='polygon'||tag==='g')return;
    /* Older fitters could shorten a text leaf after saving its full value here. */
    if(el.dataset&&el.dataset.gmFullText!=null){el.textContent=String(el.dataset.gmFullText||'');el.removeAttribute('data-gm-full-text');}
    var st=el.style;if(!st)return;
    ['zoom','transform','transform-origin','width','min-width','max-width','height','min-height','max-height',
     'font-size','line-height','padding','padding-top','padding-right','padding-bottom','padding-left','overflow','box-sizing']
      .forEach(function(p){st.removeProperty(p);});
    ['data-gm-summary2-fit','data-gm-instruction-fit','data-gm-print-fit','data-gm-scale','data-gm-fit-scale']
      .forEach(function(a){el.removeAttribute(a);});
  });
  var page=root.matches&&root.matches('.true-page')?root:root.querySelector&&root.querySelector('.true-page');
  if(page){
    page.hidden=false;page.removeAttribute('hidden');
    page.style.setProperty('display','block','important');
    page.style.setProperty('visibility','visible','important');
    page.style.setProperty('opacity','1','important');
  }
  return root;
}
'''
anchor='function appendFlatSnapshot(container,e,activeOnly){'
if helper.strip() not in journal:
    if journal.count(anchor)!=1: raise SystemExit('Journal appendFlatSnapshot anchor missing')
    journal=journal.replace(anchor,helper+'\n'+anchor,1)

old_append=r'''function appendFlatSnapshot(container,e,activeOnly){
  var snap=e.bosSnapshot||{},pages=snap.pages||[],css='';
  pages.forEach(function(pg,i){
    if(activeOnly!=null&&i!==activeOnly)return;
    var cls='gm-flat-'+(++GM_FLAT_SEQ);
    css+=gmScopeCss(String(snap.css||'')+' '+String(pg.css||''),'.'+cls);
    var sec=document.createElement('section');
    sec.className='a4-page gm-flat gm-v55-fit '+cls;
    var cv=document.createElement('div');
    cv.className='gm-flat-canvas';
    cv.innerHTML=String(pg.html||'');
    sec.appendChild(cv);
    container.appendChild(sec);
  });
  if(css){var st=document.createElement('style');st.textContent=css;container.appendChild(st);}
}'''
new_append=r'''function appendFlatSnapshot(container,e,activeOnly){
  var snap=e.bosSnapshot||{},pages=snap.pages||[],css='';
  pages.forEach(function(pg,i){
    if(activeOnly!=null&&i!==activeOnly)return;
    var cls='gm-flat-'+(++GM_FLAT_SEQ);
    /* The page-local CSS is the canonical A4 design. Captured global head CSS can
       contain old phone/print fitters, so never replay it when local page CSS exists. */
    var pageCss=String(pg.css||'').trim()||String(snap.css||'');
    css+=gmScopeCss(pageCss,'.'+cls);
    var sec=document.createElement('section');
    sec.className='a4-page gm-flat gm-v55-fit gm-bos-native '+cls;
    sec.setAttribute('data-gm-bos-native','1');
    var cv=document.createElement('div');
    cv.className='gm-flat-canvas';
    cv.innerHTML=String(pg.html||'');
    gmRecoverBosSnapshotPage(cv);
    sec.appendChild(cv);
    container.appendChild(sec);
  });
  if(css){var st=document.createElement('style');st.id='gm-bos-recovered-page-css';st.textContent=css;container.appendChild(st);}
}'''
journal=replace_once(journal,old_append,new_append,'Journal flat snapshot recovery owner')

# Saved pages are already fixed 756 x 1058 design canvases. Never apply another
# whole-page scale in Journal printing. That extra fit was the remaining path that
# could turn a good A4 snapshot into a miniature page.
fit_start=journal.index('function fitFlatPages(root){')
fit_end=journal.index('\nfunction gmEnsureJournalPrintFonts',fit_start)
new_fit=r'''function fitFlatPages(root){
  qsa('.gm-flat .true-page',root).forEach(function(pg){
    gmRecoverBosSnapshotPage(pg);
    pg.style.setProperty('width','756px','important');
    pg.style.setProperty('min-width','756px','important');
    pg.style.setProperty('max-width','756px','important');
    pg.style.setProperty('height','1058px','important');
    pg.style.setProperty('min-height','1058px','important');
    pg.style.setProperty('max-height','1058px','important');
    pg.style.setProperty('zoom','1','important');
    pg.style.setProperty('transform','none','important');
    pg.style.setProperty('overflow','hidden','important');
    var c=pg.querySelector(':scope > .true-content')||pg.querySelector('.true-content');
    if(c){
      c.style.setProperty('zoom','1','important');
      c.style.setProperty('transform','none','important');
      c.style.setProperty('transform-origin','top left','important');
      c.style.removeProperty('width');c.style.removeProperty('height');
      c.style.removeProperty('min-width');c.style.removeProperty('max-width');
      c.style.removeProperty('min-height');c.style.removeProperty('max-height');
    }
    pg.setAttribute('data-gm-print-fit','1.0000');
  });
}
'''
journal=journal[:fit_start]+new_fit+journal[fit_end:]

# Strong print-only geometry guard. Page-local CSS continues to own all typography,
# grids and decoration; this only prevents a stored runtime scale from returning.
css_anchor='.gm-flat .true-page>.true-content{transform-origin:top left!important;}'
css_repl=css_anchor+".gm-flat.gm-bos-native .true-page>.true-content{zoom:1!important;transform:none!important;transform-origin:top left!important;width:auto!important;max-width:none!important;height:auto!important;min-height:0!important;}.gm-flat.gm-bos-native .true-page{zoom:1!important;transform:none!important;}"
journal=replace_once(journal,css_anchor,css_repl,'Journal native BoS print geometry guard')

# ---------------------------------------------------------------------------
# SPELL BUILDER FUTURE SNAPSHOT CLEANUP
# ---------------------------------------------------------------------------
# Clean future captures before they enter localStorage, so device/display fit state
# can never become part of a BoS page again.
spell_helper=r'''
  function gmCleanBosSnapshotClone(clone){
    if(!clone)return clone;
    const nodes=[clone].concat(qa('*',clone));
    nodes.forEach(function(el){
      if(!el||el.nodeType!==1)return;
      const tag=String(el.nodeName||'').toLowerCase();
      if(tag==='svg'||tag==='path'||tag==='circle'||tag==='ellipse'||tag==='line'||tag==='polyline'||tag==='polygon'||tag==='g')return;
      if(el.dataset&&el.dataset.gmFullText!=null){el.textContent=String(el.dataset.gmFullText||'');el.removeAttribute('data-gm-full-text');}
      const st=el.style;if(!st)return;
      ['zoom','transform','transform-origin','width','min-width','max-width','height','min-height','max-height',
       'font-size','line-height','padding','padding-top','padding-right','padding-bottom','padding-left','overflow','box-sizing']
        .forEach(function(p){st.removeProperty(p);});
      ['data-gm-summary2-fit','data-gm-instruction-fit','data-gm-print-fit','data-gm-scale','data-gm-fit-scale']
        .forEach(function(a){el.removeAttribute(a);});
    });
    clone.hidden=false;clone.removeAttribute('hidden');clone.classList.remove('active');
    clone.style.setProperty('display','block','important');
    clone.style.setProperty('visibility','visible','important');
    clone.style.setProperty('opacity','1','important');
    return clone;
  }
'''
spell_anchor='  window.GM_BUILD_BOS_SNAPSHOT=function(done){'
if spell.count(spell_anchor)!=1: raise SystemExit('Spell Builder BoS snapshot owner anchor missing')
spell=spell.replace(spell_anchor,spell_helper+'\n'+spell_anchor,1)

old_capture=r'''            clone.hidden=false; clone.removeAttribute('hidden'); clone.classList.remove('active');
            clone.style.setProperty('display','block','important');
            clone.style.setProperty('visibility','visible','important');
            clone.style.setProperty('opacity','1','important');
            clone.style.removeProperty('zoom'); clone.style.removeProperty('transform');
            snap.pages.push({file:file,index:index,css:localCss,html:clone.outerHTML});'''
new_capture=r'''            gmCleanBosSnapshotClone(clone);
            snap.pages.push({file:file,index:index,css:localCss,html:clone.outerHTML});'''
spell=replace_once(spell,old_capture,new_capture,'Future BoS snapshot runtime-fit cleanup')

obj['journal']=journal;obj['spellBuilder']=spell
new_json=json.dumps(obj,ensure_ascii=False,separators=(',',':'))
s=s[:st]+new_json+s[st+end:]

for term in ('gmRecoverBosSnapshotPage','gm-bos-native','gmCleanBosSnapshotClone',"data-gm-print-fit','1.0000"):
    if term not in s: raise SystemExit('missing 2.7.8 guard '+term)
out.write_text(s,encoding='utf-8')
print('Installed 2.7.8 BoS snapshot scale recovery: discard captured global fit CSS, restore canonical page geometry, clean future snapshots')
