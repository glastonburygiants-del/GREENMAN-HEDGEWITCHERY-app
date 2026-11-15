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
# JOURNAL / BOS SAVED-PAGE RECOVERY
# ---------------------------------------------------------------------------
# Preserve authored layout. Remove only known runtime fit residue. In particular,
# --summary-fit-scale is a runtime value and was the surviving cause of miniature
# saved Summary pages. The 2.7.7 fitFlatPages owner remains in control afterwards,
# so a page can reduce just enough to stay inside A4 but can never collapse tiny.
helper=r'''
function gmRecoverBosSnapshotPage(root){
  if(!root)return root;
  var nodes=[root].concat(qsa('*',root));
  nodes.forEach(function(el){
    if(!el||el.nodeType!==1)return;
    if(el.dataset&&el.dataset.gmFullText!=null){
      el.textContent=String(el.dataset.gmFullText||'');
      el.removeAttribute('data-gm-full-text');
      if(el.style){el.style.removeProperty('font-size');el.style.removeProperty('line-height');}
    }
    if(el.style){
      el.style.removeProperty('--summary-fit-scale');
      el.style.removeProperty('--grimoire-fit-scale');
    }
  });
  var fitted=[];
  if(root.matches&&root.matches('.true-page,.true-content,[data-gm-summary2-fit],[data-gm-instruction-fit],[data-gm-print-fit],[data-gm-scale],[data-gm-fit-scale]'))fitted.push(root);
  if(root.querySelectorAll)fitted=fitted.concat(qsa('.true-page,.true-content,[data-gm-summary2-fit],[data-gm-instruction-fit],[data-gm-print-fit],[data-gm-scale],[data-gm-fit-scale]',root));
  fitted.forEach(function(el){
    if(!el||!el.style)return;
    ['zoom','transform','transform-origin','width','min-width','max-width','height','min-height','max-height']
      .forEach(function(p){el.style.removeProperty(p);});
    ['data-gm-summary2-fit','data-gm-instruction-fit','data-gm-print-fit','data-gm-scale','data-gm-fit-scale']
      .forEach(function(a){el.removeAttribute(a);});
  });
  var page=root.matches&&root.matches('.true-page')?root:root.querySelector&&root.querySelector('.true-page');
  if(page){
    page.hidden=false;page.removeAttribute('hidden');
    page.style.setProperty('display','block','important');
    page.style.setProperty('visibility','visible','important');
    page.style.setProperty('opacity','1','important');
    /* Initial marker only. The 2.7.7 fitter replaces this with the measured scale. */
    page.setAttribute('data-gm-print-fit','1.0000');
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

# Keep the safer 2.7.7 A4 fitter. Add recovery immediately before it measures.
fit_anchor="qsa('.gm-flat .true-page',root).forEach(function(pg){\n    var c=pg.querySelector(':scope > .true-content')||pg.querySelector('.true-content')||pg.firstElementChild;if(!c)return;"
fit_repl="qsa('.gm-flat .true-page',root).forEach(function(pg){\n    gmRecoverBosSnapshotPage(pg);\n    var c=pg.querySelector(':scope > .true-content')||pg.querySelector('.true-content')||pg.firstElementChild;if(!c)return;"
journal=replace_once(journal,fit_anchor,fit_repl,'Journal safe A4 fitter recovery hook')

# ---------------------------------------------------------------------------
# SPELL BUILDER FUTURE SNAPSHOT CLEANUP
# ---------------------------------------------------------------------------
# Future captures preserve authored inline geometry and typography. Only known fit
# residue is removed before the snapshot enters localStorage.
spell_helper=r'''
  function gmCleanBosSnapshotClone(clone){
    if(!clone)return clone;
    const nodes=[clone].concat(qa('*',clone));
    nodes.forEach(function(el){
      if(!el||el.nodeType!==1)return;
      if(el.dataset&&el.dataset.gmFullText!=null){
        el.textContent=String(el.dataset.gmFullText||'');
        el.removeAttribute('data-gm-full-text');
        if(el.style){el.style.removeProperty('font-size');el.style.removeProperty('line-height');}
      }
      if(el.style){
        el.style.removeProperty('--summary-fit-scale');
        el.style.removeProperty('--grimoire-fit-scale');
      }
    });
    let fitted=[];
    if(clone.matches&&clone.matches('.true-page,.true-content,[data-gm-summary2-fit],[data-gm-instruction-fit],[data-gm-print-fit],[data-gm-scale],[data-gm-fit-scale]'))fitted.push(clone);
    fitted=fitted.concat(qa('.true-page,.true-content,[data-gm-summary2-fit],[data-gm-instruction-fit],[data-gm-print-fit],[data-gm-scale],[data-gm-fit-scale]',clone));
    fitted.forEach(function(el){
      if(!el||!el.style)return;
      ['zoom','transform','transform-origin','width','min-width','max-width','height','min-height','max-height']
        .forEach(function(p){el.style.removeProperty(p);});
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

for term in ('gmRecoverBosSnapshotPage','gm-bos-native','gmCleanBosSnapshotClone','--summary-fit-scale',"data-gm-print-fit','1.0000"):
    if term not in s: raise SystemExit('missing BoS recovery guard '+term)
out.write_text(s,encoding='utf-8')
print('Installed safe BoS snapshot recovery: remove only runtime fit residue, preserve authored layout, keep 2.7.7 A4 containment')
