#!/usr/bin/env python3
"""V58: Apply all five item-specific lunar grids to Greenman Grimoire.
Source: Greenman_Golden_Master_ALL_ITEMS_LUNAR_REVIEW.xlsx.
Only Moon filter associations and the Dark/New transition are modified.
"""
import base64,json,sys,zlib
from pathlib import Path
MARK='gm-curated-all-moon-v58'
B64='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'
PHASES=['Dark Moon','New Moon','Waxing Crescent','First Quarter','Waxing Gibbous','Full Moon','Waning Gibbous','Last Quarter','Waning Crescent']
CATEGORIES={'Herb':'Herbs','Crystal':'Crystals','Oil':'Oils','Rune':'Runes','Deity':'Deities'}


def apply_home_moon_selection_fix(html):
    """Selecting Moon from the Grimoire home page must set the card filter too."""
    marker="gm-home-moon-active-v58b"
    if marker in html:raise ValueError("Home Moon fix already applied")
    def enc(value):return json.dumps(value,ensure_ascii=False)[1:-1]
    substitutions=[
        ("function showMoonInfo(index){\n  const m=GM_MOON_PHASE_DATA[index];\n  if(!m)return;",
         "function showMoonInfo(index){\n  const m=GM_MOON_PHASE_DATA[index];\n  if(!m)return;\n  // "+marker+": apply the selected phase to Grimoire card filters.\n  filters.moon=m.name;\n  renderFilters();\n  gmUpdatePills();\n  renderCards();"),
        ("'<div class=\"gm-popup-kicker\">'+(m.name===gmCurrentMoonPhase()?'Current live phase estimate':'Moon phase information')+'</div>'+",
         "'<div class=\"gm-popup-kicker\">'+esc(m.name)+' filter active · choose a Grimoire category</div>'+"),
        ("'<div class=\"gm-popup-actions\"><button class=\"gm-popup-action\" onclick=\"openMoonPicker(&quot;home&quot;)\">Choose another phase</button></div>'+",
         "'<div class=\"gm-popup-actions\"><button class=\"gm-popup-action\" onclick=\"closeRef();openCategory(&quot;Herb&quot;)\">Show filtered Herbs</button><button class=\"gm-popup-action\" onclick=\"openMoonPicker(&quot;home&quot;)\">Choose another phase</button></div>'+"),
    ]
    for before,after in substitutions:
        a,b=enc(before),enc(after)
        if html.count(a)!=1:raise ValueError("Moon home UI source mismatch: "+repr(before[:40]))
        html=html.replace(a,b,1)
    assert html.count(marker)==1
    return html

def patch(html):
    if MARK in html:raise ValueError("V58 already applied")
    payload=json.loads(zlib.decompress(base64.b64decode(B64)))
    assert set(payload)==set(CATEGORIES)
    a_key='const EDITOR_DATA = '
    st=html.index(a_key)+len(a_key)
    en=html.index('};',st)+1
    catalog=json.loads(json.loads('"'+html[st:en]+'"'))
    for cat,src in CATEGORIES.items():
        valid={x['_name'] for x in catalog[src]}
        for phase,names in payload[cat].items():
            assert phase in PHASES
            assert len(names)==len(set(names))
            unknown=set(names)-valid
            if unknown:raise ValueError("Unknown "+cat+" names: "+repr(sorted(unknown)))
    a_key='const GM_MOON_PHASE_DATA = '
    a=html.index(a_key)+len(a_key)
    b=html.index('];',a)+1
    old=json.loads(html[a:b].replace(r'\"','"'))
    if len(old)!=9 or {p['name'] for p in old}!=set(PHASES):raise ValueError("Unexpected phase records")
    new=json.loads(json.dumps(old))
    for p in new:
        for cat in CATEGORIES:p['items'][cat]=payload[cat][p['name']]
    for before,after in zip(old,new):
        x={k:v for k,v in before.items() if k!='items'}
        y={k:v for k,v in after.items() if k!='items'}
        assert x==y
    encoded=json.dumps(new,ensure_ascii=False,separators=(',',':')).replace('"',r'\"')
    html=html[:a]+encoded+html[b:]
    old_new=r'if(age<1.3 || age>28.3)return \"New Moon\";'
    new_new=r'if(age<1.3)return \"New Moon\";'
    old_waning=r'if(age<27.8)return \"Waning Crescent\";'
    new_waning=r'if(age<synodic-1.3)return \"Waning Crescent\";'
    if html.count(old_new)!=1 or html.count(old_waning)!=1:raise ValueError("Old timing rules not present")
    html=html.replace(old_new,new_new,1).replace(old_waning,new_waning,1)
    html=html.replace('const GM_NAMED_MOON_DATA = ','/* '+MARK+' */\\nconst GM_NAMED_MOON_DATA = ',1)
    assert html.count(MARK)==1
    html=apply_home_moon_selection_fix(html)
    print("V58 moon filters:",{k:sum(len(v) for v in payload[k].values()) for k in CATEGORIES})
    return html

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: patch_v58_all_moon_items.py INPUT OUTPUT')
    Path(sys.argv[2]).write_text(patch(Path(sys.argv[1]).read_text(encoding='utf-8')),encoding='utf-8')
