#!/usr/bin/env python3
import json,re,sys
from pathlib import Path

if len(sys.argv)!=3:
    raise SystemExit('usage: patch_fv3_followup_home_childsafe_fullwidth.py INPUT.html OUTPUT.html')


def replace_once(text, old, new, label):
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f'{label}: expected 1 match, found {n}')
    return text.replace(old,new,1)


def replace_json_string(text, marker, transform):
    pos=text.index(marker)+len(marker)
    value,used=json.JSONDecoder().raw_decode(text[pos:])
    if not isinstance(value,str):
        raise RuntimeError(f'{marker!r} does not point to JSON string')
    updated=transform(value)
    encoded=(json.dumps(updated,ensure_ascii=True,separators=(',',':'))
             .replace('</script','<\\/script').replace('</SCRIPT','<\\/SCRIPT'))
    return text[:pos]+encoded+text[pos+used:]

source=Path(sys.argv[1]).read_text('utf-8')
if 'gm-fv3-child-safe-master-v2' in source:
    raise RuntimeError('follow-up patch already applied')

# 1) Remove the FV3 narrow 9:16 centred strip. Keep tablet detection only so
#    later targeted tablet tweaks can be made without side gutters.
new_tablet=r'''<style id="gm-fv3-tablet-proportions">
/* FV3 FOLLOW-UP: tablets use the full available width. No artificial side gutters. */
html.gm-fv3-tablet #gmShell,
html.gm-fv3-tablet #frameWrap,
html.gm-fv3-tablet #pageFrame,
html.gm-fv3-tablet #gmBottomTabs{
  width:100vw!important;max-width:100vw!important;min-width:0!important;
  left:0!important;right:0!important;transform:none!important;
}
html.gm-fv3-tablet #gmCupboardKey{right:10px!important}
html.gm-fv3-tablet #gmOpenFullFloat{
  width:calc(100vw - 20px)!important;left:10px!important;right:10px!important;transform:none!important;
}
#gmCupboardKey{width:88px!important;height:88px!important;padding:7px 6px 6px!important}
#gmCupboardKey svg{width:39px!important;height:39px!important}
#gmCupboardKey span{font-size:9.5px!important;line-height:1.05!important;letter-spacing:.01em!important}
@media(max-width:520px){
  #gmCupboardKey{width:84px!important;height:84px!important;right:8px!important;bottom:66px!important}
  #gmCupboardKey svg{width:37px!important;height:37px!important}
  #gmCupboardKey span{font-size:9px!important}
}
@media print{html.gm-fv3-tablet #gmShell{width:100%!important;max-width:none!important;left:auto!important;transform:none!important}}
</style>
<script id="gm-fv3-tablet-proportions-script">
(function(){
  function apply(){
    var sw=window.screen&&screen.width||window.innerWidth;
    var sh=window.screen&&screen.height||window.innerHeight;
    var tablet=Math.min(sw,sh)>=600;
    document.documentElement.classList.toggle('gm-fv3-tablet',tablet);
    document.documentElement.style.setProperty('--gm-fv3-app-width','100vw');
    /* Existing reset owners narrow only when this returns true. Returning false
       deliberately restores their original full-width path while retaining the
       tablet class for targeted CSS. */
    return false;
  }
  window.gmFv3ApplyTabletRatio=apply;
  window.addEventListener('resize',apply,{passive:true});
  window.addEventListener('orientationchange',function(){setTimeout(apply,80)},{passive:true});
  apply();
})();
</script>'''
pat=re.compile(r'<style id="gm-fv3-tablet-proportions">.*?</style>\s*<script id="gm-fv3-tablet-proportions-script">.*?</script>',re.S)
source,n=pat.subn(new_tablet,source,count=1)
if n!=1: raise RuntimeError(f'tablet block: expected 1, found {n}')

# 2) The approved reference wording belongs in the Home content directly
#    UNDER the Clear Spell box and BEFORE the Home bottom tab bar.
def patch_home(home):
    note_pat=re.compile(
        r'\\n?<!-- (?:FOOTER|HOME REFERENCE NOTE) -->\\s*(<div class="footer-note gm-home-source-note">.*?</div>)',
        re.S,
    )
    m=note_pat.search(home)
    if not m:
        raise RuntimeError('Home source note not found')
    note=m.group(1)
    home=home[:m.start()]+home[m.end():]

    clear_anchor='<button class="btn-clear" onclick="showClearPopup()">Clear &amp; Begin New Spell</button>\\n</div>'
    if home.count(clear_anchor)!=1:
        raise RuntimeError('Clear Spell box closing boundary not found exactly once')
    home=home.replace(
        clear_anchor,
        clear_anchor+'\\n<!-- FOOTER -->\\n'+note,
        1,
    )

    if not (
        home.index('<!-- CLEAR SPELL BLOCK')
        < home.index('<!-- FOOTER -->')
        < home.index('<!-- BOTTOM TAB BAR -->')
    ):
        raise RuntimeError('Home footer is not directly below Clear Spell and above bottom tabs')
    return home

source=replace_json_string(source,'const PAGES = {"home":',patch_home)

# Shared child-facing vocabulary. This deliberately does NOT alter Grimoire data.
MASTER_REGEX=(
 r'(?:\\bsex(?:ual|uality|ually)?\\b|sex[- ]?magic|sexual[- ]?energy|sexual[- ]?arousal|'
 r'\\blust(?:ful)?\\b|aphrodisiac|love[- ]?making|lovemaking|\\bvirility\\b|'
 r'\\bfertilit(?:y|ies)\\b|\\bfertile\\b|\\bpotenc(?:y|ies)\\b|\\berect(?:ion|ile|ions)?\\b|'
 r'\\bimpoten(?:ce|t)\\b|\\borgasm(?:ic|s)?\\b|\\bgenital(?:s)?\\b|\\berotic(?:ism)?\\b|'
 r'\\bseduction\\b|\\bseductive\\b|physical[- ]?desire|sexual[- ]?desire|opposite[- ]?sex|'
 r'sacred[- ]?sexuality|sacred[- ]?union|marital[- ]?problems?|'
 r'\\bgambl(?:e|ing|er|ers)\\b|casino[- ]?luck|\\bcasino\\b|shape[- ]?shift(?:ing|er|ers)?|'
 r'\\bbinding\\b|\\bbanish(?:ing|ment|ed|es)?\\b|\\bcurse(?:s|d|ing)?\\b|\\bjinx(?:es|ed)?\\b|'
 r'\\bhex(?:es|ed|ing)?\\b|\\bevil\\b|evil[- ]?eye|exorcis(?:m|ms|e|ed|ing|t)?|'
 r'\\bdemon(?:s|ic)?\\b|ju[- ]?ju|gris[- ]?gris|\\bwrath\\b|\\brevenge\\b|'
 r'\\baggression\\b|causing[- ]?bad[- ]?luck[- ]?to[- ]?enemies|inhibiting[- ]?enemies)'
)

# 3) Spell Builder: define the missing master hook, retain the older BAD guard,
#    and let popup/card/summary paths all use the same vocabulary.
def patch_spell(spell):
    old_bad=r"var BAD=/(?:\bsex(?:ual|uality)?\b|\blust\b|aphrodisiac|love[- ]?making|lovemaking|\bvirility\b|\bfertility\b|\bfertile\b|\bhex(?:es)?\b|\bevil\b|exorcis|ju[- ]?ju|gris[- ]?gris|erect|impoten|orgasm)/i;"
    new_bad='var BAD=/' + MASTER_REGEX + '/i;'
    spell=replace_once(spell,old_bad,new_bad,'Spell Builder legacy BAD regex')
    spell=spell.replace(".forEach(function(box){if(inPopup(box))return;var lab=box.querySelector('.box-label,b');",
                        ".forEach(function(box){var lab=box.querySelector('.box-label,b');",1)

    hook=f'''<script id="gm-fv3-child-safe-master-v2">
(function(){{
'use strict';
if(window.__GM_FV3_CHILD_SAFE_MASTER_V2)return;
window.__GM_FV3_CHILD_SAFE_MASTER_V2=true;
var STORE='gm_current_spell_v11';
var MASTER=/{MASTER_REGEX}/i;
function txt(v){{return v==null?'':String(v).trim();}}
function state(){{try{{return JSON.parse(localStorage.getItem(STORE)||'{{}}')||{{}};}}catch(e){{return{{}};}}}}
function adultSpell(){{var s=state(),sd=s.sd||{{}},sp=s.spell||{{}};return /over\\s*[- ]?18|18\\+|adult(?:\\s+only)?|🔞/i.test([s.category,s.spellName,s.selectedSpell,sp.Name,sp.name,sp.Category,sp.category,sd.Category,sd['Spell/Charm Type']].join(' '));}}
function splitClean(v,mode){{
  v=txt(v); if(!v||adultSpell())return v;
  var parts=(mode==='list'?v.split(/[,;|\\n]+/):v.split(/(?<=[.!?])\\s+|[;|\\n]+/)).map(txt).filter(Boolean);
  var kept=parts.filter(function(x){{return !MASTER.test(x);}});
  if(kept.length)return mode==='list'?kept.join(', '):kept.join(' ');
  return 'Traditional adult material is hidden in this child-friendly view.';
}}
window.GM_CHILD_SAFE_BAD=MASTER;
window.GM_CHILD_SAFE_TEXT=splitClean;
window.GM_CHILD_SAFE_IS_ADULT=adultSpell;
function scrub(root){{
  if(adultSpell())return;
  (root||document).querySelectorAll('.square-box,.gm-v36-box,#gm-v67-info section,.item-row:not(.header)').forEach(function(box){{
    var label=box.querySelector&&box.querySelector('.box-label,b,.scroll-energy-label');
    var lt=txt(label&&label.textContent);
    if(/greenman\\s+energy.*over\\s*18|over\\s*18|18\\+/i.test(lt)){{box.style.display='none';return;}}
    var bodies=box.querySelectorAll?box.querySelectorAll('.box-text,p,.item-text span,.item-text,.item-green span,.item-green,.scroll-energy-text'):[];
    Array.prototype.forEach.call(bodies,function(el){{var mode=/uses|powers/i.test(lt)?'list':'prose';var cleaned=splitClean(el.textContent,mode);if(cleaned!==el.textContent)el.textContent=cleaned;}});
  }});
}}
var timer=0;function schedule(){{clearTimeout(timer);timer=setTimeout(function(){{scrub(document);}},25);}}
var app=document.getElementById('gm-app');if(app)new MutationObserver(schedule).observe(app,{{childList:true,subtree:true,characterData:true}});
document.addEventListener('DOMContentLoaded',schedule);schedule();
}})();
</script>
'''
    anchor='<script id="gm-v67-repair-owner">'
    if anchor not in spell: raise RuntimeError('Spell Builder V67 anchor not found')
    spell=spell.replace(anchor,hook+anchor,1)
    return spell
source=replace_json_string(source,',"spellBuilder":',patch_spell)

# 4) Hedgewitch/Supply Cupboards: always child-friendly. Saved Over-18 spells are
#    already excluded by isOver18SpellEntry(); this adds text-layer protection.
def patch_cupboard(cup):
    guard=f'''\n/* FV3 CHILD-SAFE CUPBOARD MASTER V2 */
const GM_CUPBOARD_CHILD_BAD=/{MASTER_REGEX}/i;
function gmCupboardChildSafeBad(v){{return GM_CUPBOARD_CHILD_BAD.test(String(v==null?'':v));}}
function gmCupboardChildSafeText(v,mode='prose'){{
  v=String(v==null?'':v).trim();if(!v)return '';
  const parts=(mode==='list'?v.split(/[,;|\\n]+/):v.split(/(?<=[.!?])\\s+|[;|\\n]+/)).map(x=>String(x||'').trim()).filter(Boolean);
  const kept=parts.filter(x=>!gmCupboardChildSafeBad(x));
  return kept.length?(mode==='list'?kept.join(', '):kept.join(' ')):'Traditional adult material is hidden in this child-friendly view.';
}}
'''
    anchor="function openItem(item,source='supply'){"
    if anchor not in cup: raise RuntimeError('Cupboard openItem anchor not found')
    cup=cup.replace(anchor,guard+anchor,1)
    cup=cup.replace('escapeHtml(item.powers)',"escapeHtml(gmCupboardChildSafeText(item.powers,'prose'))")
    cup=cup.replace('escapeHtml(item.voice)',"escapeHtml(gmCupboardChildSafeText(item.voice,'prose'))")
    cup=cup.replace("escapeHtml(item.voice||'No Greenman voice has been recorded for this item.')",
                    "escapeHtml(gmCupboardChildSafeText(item.voice||'No Greenman voice has been recorded for this item.','prose'))")
    old="${item.energies.map(en=>`<div class=\"scroll-energy-card\"><div class=\"scroll-energy-label\">${escapeHtml(en.label)}</div><div class=\"scroll-energy-text\">${escapeHtml(en.text)}</div></div>`).join('')}"
    new="${item.energies.filter(en=>!(/over\\s*18|18\\+|adult/i.test(String(en&&en.label||'')))).map(en=>`<div class=\"scroll-energy-card\"><div class=\"scroll-energy-label\">${escapeHtml(en.label)}</div><div class=\"scroll-energy-text\">${escapeHtml(gmCupboardChildSafeText(en.text,'prose'))}</div></div>`).join('')}"
    cup=replace_once(cup,old,new,'Cupboard Greenman Energy popup rendering')
    cup=cup.replace("escapeHtml(item.voice||'')","escapeHtml(gmCupboardChildSafeText(item.voice||'','prose'))")
    return cup
source=replace_json_string(source,'PAGES.cupboard = ',patch_cupboard)

required=[
 'gm-fv3-child-safe-master-v2','GM_CHILD_SAFE_TEXT','GM_CUPBOARD_CHILD_BAD',
 'Traditional adult material is hidden in this child-friendly view.',
 'isOver18SpellEntry(entry)','readSavedSpellEntries()',
 'gm-home-source-note','<!-- FOOTER -->',
 'Greenman HedgeWitchery Apothecary · Woods Witch &amp; RuneSmith',
 'HedgeWitchery uses its own curated reference data stored on your device.',
 'gm-fv3-tablet-proportions'
]
for x in required:
    if x not in source: raise RuntimeError('final output missing '+x)
if 'Math.min(window.innerWidth,Math.round(stableHeight*9/16))' in source:
    raise RuntimeError('old tablet side-gutter width calculation still present')

Path(sys.argv[2]).write_text(source,'utf-8')
print('bytes',Path(sys.argv[2]).stat().st_size)
