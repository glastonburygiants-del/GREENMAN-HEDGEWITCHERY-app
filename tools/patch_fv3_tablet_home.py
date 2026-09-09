#!/usr/bin/env python3
"""Start the FV3 line with tablet proportion and approved Home-page changes."""

import json
import sys
from pathlib import Path


if len(sys.argv) != 3:
    raise SystemExit("usage: patch_fv3_tablet_home.py INPUT.html OUTPUT.html")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_json_string(text, marker, transform):
    pos = text.index(marker) + len(marker)
    value, used = json.JSONDecoder().raw_decode(text[pos:])
    if not isinstance(value, str):
        raise RuntimeError(f"{marker!r} does not contain an HTML string")
    updated = transform(value)
    encoded = (json.dumps(updated, ensure_ascii=True, separators=(",", ":"))
               .replace("</script", "<\\/script")
               .replace("</SCRIPT", "<\\/SCRIPT"))
    return text[:pos] + encoded + text[pos + used:]


source = Path(sys.argv[1]).read_text(encoding="utf-8")

if "gm-fv3-tablet-proportions" in source or "FV3 HOME" in source:
    raise RuntimeError("FV3 tablet/Home patch is already present")


tablet_head = r'''
<style id="gm-fv3-tablet-proportions">
/* FV3 TABLET PROPORTIONS
   Tablets keep the intended portrait app ratio. Spare width becomes side
   margin instead of stretching every fixed-height room short and fat. */
html.gm-fv3-tablet #gmShell{
  width:var(--gm-fv3-app-width)!important;
  max-width:var(--gm-fv3-app-width)!important;
  min-width:0!important;
  left:50%!important;
  right:auto!important;
  transform:translateX(-50%)!important;
}
html.gm-fv3-tablet #frameWrap,
html.gm-fv3-tablet #pageFrame,
html.gm-fv3-tablet #gmBottomTabs{
  width:100%!important;
  max-width:100%!important;
  min-width:0!important;
  left:0!important;
  right:0!important;
  transform:none!important;
}
html.gm-fv3-tablet #gmCupboardKey{
  right:max(10px,calc((100vw - var(--gm-fv3-app-width))/2 + 10px))!important;
}
html.gm-fv3-tablet #gmOpenFullFloat{
  width:calc(var(--gm-fv3-app-width) - 20px)!important;
  left:50%!important;
  right:auto!important;
  transform:translateX(-50%)!important;
}
#gmCupboardKey{
  width:88px!important;
  height:88px!important;
  padding:7px 6px 6px!important;
}
#gmCupboardKey svg{width:39px!important;height:39px!important}
#gmCupboardKey span{font-size:9.5px!important;line-height:1.05!important;letter-spacing:.01em!important}
@media(max-width:520px){
  #gmCupboardKey{width:84px!important;height:84px!important;right:8px!important;bottom:66px!important}
  #gmCupboardKey svg{width:37px!important;height:37px!important}
  #gmCupboardKey span{font-size:9px!important}
}
@media print{
  html.gm-fv3-tablet #gmShell{width:100%!important;max-width:none!important;left:auto!important;transform:none!important}
}
</style>
<script id="gm-fv3-tablet-proportions-script">
(function(){
  var stableHeight=0,orientation='';
  function apply(){
    var key=window.innerWidth>window.innerHeight?'landscape':'portrait';
    if(key!==orientation){orientation=key;stableHeight=window.innerHeight||1}
    else stableHeight=Math.max(stableHeight,window.innerHeight||1);
    var sw=window.screen&&screen.width||window.innerWidth;
    var sh=window.screen&&screen.height||window.innerHeight;
    var tablet=Math.min(sw,sh)>=600;
    var width=tablet?Math.min(window.innerWidth,Math.round(stableHeight*9/16)):window.innerWidth;
    document.documentElement.classList.toggle('gm-fv3-tablet',tablet);
    document.documentElement.style.setProperty('--gm-fv3-app-width',width+'px');
    return tablet;
  }
  window.gmFv3ApplyTabletRatio=apply;
  window.addEventListener('resize',apply,{passive:true});
  window.addEventListener('orientationchange',function(){orientation='';setTimeout(apply,80)},{passive:true});
  apply();
})();
</script>
'''

head_pos = source.find("</head>")
body_pos = source.find("<body", 0, head_pos + 1)
if head_pos < 0 or body_pos >= 0:
    raise RuntimeError("outer document head boundary not found")
source = source[:head_pos] + tablet_head + source[head_pos:]


old_reset = """      var shell=document.getElementById('gmShell');
      var tabs=document.getElementById('gmBottomTabs');
      var frame=document.getElementById('pageFrame');
      [shell,tabs,frame].forEach(function(el){
        if(!el) return;
        el.style.left='0px'; el.style.right='0px'; el.style.width='100vw'; el.style.maxWidth='100vw';
        el.style.transform='none'; el.style.zoom='1';
      });"""
new_reset = """      var shell=document.getElementById('gmShell');
      var tabs=document.getElementById('gmBottomTabs');
      var frame=document.getElementById('pageFrame');
      var tablet=window.gmFv3ApplyTabletRatio&&window.gmFv3ApplyTabletRatio();
      var appWidth=getComputedStyle(document.documentElement).getPropertyValue('--gm-fv3-app-width').trim()||'100vw';
      [shell,tabs,frame].forEach(function(el){
        if(!el) return;
        var outer=el===shell;
        el.style.left=outer&&tablet?'50%':'0px';
        el.style.right=outer&&tablet?'auto':'0px';
        el.style.width=outer&&tablet?appWidth:'100%';
        el.style.maxWidth=outer&&tablet?appWidth:'100%';
        el.style.transform=outer&&tablet?'translateX(-50%)':'none';
        el.style.zoom='1';
      });"""
source = replace_once(source, old_reset, new_reset, "outer pan reset")


old_viewport_loop = """    ['gmShell','frameWrap','pageFrame','gmBottomTabs'].forEach(function(id){
      const el=document.getElementById(id);if(!el)return;
      el.style.setProperty('left','0px','important');
      el.style.setProperty('right','0px','important');
      el.style.setProperty('width','100%','important');
      el.style.setProperty('max-width','100%','important');
      el.style.setProperty('min-width','0','important');
      el.style.setProperty('transform','none','important');
      el.style.setProperty('zoom','1','important');
      el.scrollLeft=0;
    });"""
new_viewport_loop = """    const gmFv3Tablet=window.gmFv3ApplyTabletRatio&&window.gmFv3ApplyTabletRatio();
    const gmFv3Width=getComputedStyle(document.documentElement).getPropertyValue('--gm-fv3-app-width').trim()||'100%';
    ['gmShell','frameWrap','pageFrame','gmBottomTabs'].forEach(function(id){
      const el=document.getElementById(id);if(!el)return;
      const outer=id==='gmShell';
      el.style.setProperty('left',outer&&gmFv3Tablet?'50%':'0px','important');
      el.style.setProperty('right',outer&&gmFv3Tablet?'auto':'0px','important');
      el.style.setProperty('width',outer&&gmFv3Tablet?gmFv3Width:'100%','important');
      el.style.setProperty('max-width',outer&&gmFv3Tablet?gmFv3Width:'100%','important');
      el.style.setProperty('min-width','0','important');
      el.style.setProperty('transform',outer&&gmFv3Tablet?'translateX(-50%)':'none','important');
      el.style.setProperty('zoom','1','important');
      el.scrollLeft=0;
    });"""
source = replace_once(source, old_viewport_loop, new_viewport_loop, "cupboard return viewport reset")


def patch_home(home):
    home = replace_once(
        home,
        '<button aria-label="Begin Your Spell" class="begin-btn" onclick="handleBeginSpell()">\n      ✦ Begin<br/>Your<br/>Spell ✦\n    </button>',
        '<button aria-label="Open Spells" class="begin-btn" onclick="handleBeginSpell()">SPELLS</button>',
        "Home SPELLS button",
    )

    clear_start = home.index("<!-- CLEAR SPELL BLOCK")
    footer_start = home.index("<!-- FOOTER -->", clear_start)
    footer_close = home.index("\n</div>\n</div>\n<!-- BOTTOM TAB BAR -->", footer_start) + len("\n</div>")
    clear_block = home[clear_start:footer_start]
    footer_block = home[footer_start:footer_close]
    home = home[:clear_start] + footer_block + "\n" + clear_block + home[footer_close:]

    home = replace_once(
        home,
        "Continue with the spell already underway, or clear it and begin a new one.<br/><br/>\n      Your saved Journal and Book of Shadows entries will stay safe.",
        "Continue with the spell already underway, or clear it and begin a new one.<br/>\n      Your saved Journal and Book of Shadows entries will stay safe.",
        "compact progress wording",
    )

    home_css = r'''
<style id="gm-home-fv3">
/* FV3 HOME: agreed large SPELLS action, centred steps and lower compact progress panel. */
.begin-btn{
  width:clamp(210px,58vw,240px)!important;
  height:clamp(210px,58vw,240px)!important;
  padding:0 18px!important;
  font-size:30px!important;
  line-height:1!important;
  letter-spacing:.11em!important;
}
.steps-list li{
  display:flex!important;
  flex-direction:column!important;
  align-items:center!important;
  justify-content:center!important;
  gap:4px!important;
  padding:10px 8px!important;
  text-align:center!important;
}
.step-num{min-width:0!important;font-size:19px!important;line-height:1.05!important}
.step-text{width:100%!important;text-align:center!important}
.clear-block{
  padding:14px 14px 13px!important;
  margin:14px 0 12px!important;
}
.clear-heading{margin-bottom:7px!important}
.clear-body{font-size:15px!important;line-height:1.32!important;margin-bottom:11px!important}
.btn-continue{padding:11px 14px!important;margin-bottom:8px!important}
.btn-clear{
  padding:10px 14px!important;
  background:linear-gradient(#89643a,#51351d)!important;
  border-color:#d0a75d!important;
}
@media(min-width:600px){
  .begin-btn{width:240px!important;height:240px!important;font-size:32px!important}
}
</style>
<!-- FV3 HOME -->
'''
    hp = home.find("</head>")
    if hp < 0:
        raise RuntimeError("Home </head> not found")
    home = home[:hp] + home_css + home[hp:]

    required = [
        '>SPELLS</button>',
        'gm-home-fv3',
        'Magical traditions can vary, use this Greenman Apothecary as a guide and continue your own research.',
        'Its recommendations are created by matching that stored data to your intention.',
    ]
    for item in required:
        if item not in home:
            raise RuntimeError(f"Home requirement missing: {item}")
    if home.index("<!-- FOOTER -->") > home.index("<!-- CLEAR SPELL BLOCK"):
        raise RuntimeError("Spell-progress panel was not moved beneath the footer")
    return home


source = replace_json_string(source, 'const PAGES = {"home":', patch_home)

for required in [
    "gm-fv3-tablet-proportions",
    "gmFv3ApplyTabletRatio",
    "gm-home-fv3",
    "FV3 HOME",
]:
    if required not in source:
        raise RuntimeError(f"final output missing {required}")

Path(sys.argv[2]).write_text(source, encoding="utf-8")
payload = Path(sys.argv[2]).read_bytes()
print("bytes", len(payload))
