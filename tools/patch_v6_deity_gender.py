#!/usr/bin/env python3
from pathlib import Path
import json, sys


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_spell(sp):
    old = """function deityPolarity(item){return norm([item&&item.Polarity,item&&item.Energy,item&&item['Deity Gender'],item&&item.Gender,item&&item.Deity].join(' '));}\n  function isDual(item){const p=deityPolarity(item);return /dual|both|all|balance|god and goddess/.test(p);}\n  function isFem(item){const p=deityPolarity(item);return /feminine|female|goddess/.test(p)||isDual(item);}\n  function isMasc(item){const p=deityPolarity(item);return !isDual(item)&&(/masculine|male/.test(p)||(/\\bgod\\b/.test(p)&&!/goddess|feminine|female/.test(p)));}"""
    new = """function deityPolarity(item){\n    const primary=norm([item&&item.Polarity,item&&item.Energy].join(' '));\n    return primary||norm([item&&item['Deity Gender'],item&&item.Gender,item&&item.Deity].join(' '));\n  }\n  function deityRole(item){\n    const p=deityPolarity(item);\n    if(/\\bdual\\b|\\bboth\\b|\\ball\\b|balance|god and goddess/.test(p))return 'dual';\n    if(/feminine|female/.test(p)&&!/masculine|male/.test(p))return 'goddess';\n    if(/masculine|male/.test(p)&&!/feminine|female/.test(p))return 'god';\n    if(/goddess/.test(p)&&!/\\bgod\\b/.test(p.replace(/goddess/g,'')))return 'goddess';\n    if(/\\bgod\\b/.test(p)&&!/goddess/.test(p))return 'god';\n    return '';\n  }\n  function isDual(item){return deityRole(item)==='dual';}\n  function isFem(item){const r=deityRole(item);return r==='goddess'||r==='dual';}\n  function isMasc(item){return deityRole(item)==='god';}"""
    sp = replace_once(sp, old, new, 'V36 deity classification')

    old = """      const g=lc(first(row['Deity Gender'],row.Polarity));\n      const isG=/goddess|feminine|female/.test(g)&&!/both/.test(g);\n      const isM=(/\\bgod\\b/.test(g)||/masculine|male/.test(g))&&!/goddess|feminine|female/.test(g);\n      const both=/both|dual|all/.test(g);\n      const chosen=load().goddess||{};\n      const chosenGender=lc(first(chosen['Deity Gender'],chosen.Polarity,chosen.Energy,chosen.Gender));"""
    new = """      const g=lc(first(row.Polarity,row.Energy,row['Deity Gender'],row.Gender));\n      const isG=/goddess|feminine|female/.test(g)&&!/both|dual|all/.test(g);\n      const isM=(/\\bgod\\b/.test(g)||/masculine|male/.test(g))&&!/goddess|feminine|female/.test(g)&&!/both|dual|all/.test(g);\n      const both=/both|dual|all/.test(g);\n      const chosen=load().goddess||{};\n      const chosenGender=lc(first(chosen.Polarity,chosen.Energy,chosen['Deity Gender'],chosen.Gender));"""
    sp = replace_once(sp, old, new, 'V55 deity visibility')

    old = "function gender(r){return norm([r&&r['Deity Gender'],r&&r.Polarity,r&&r.Energy,r&&r.Gender,r&&r.Type].join(' '));}"
    new = "function gender(r){var p=norm([r&&r.Polarity,r&&r.Energy].join(' '));return p||norm([r&&r['Deity Gender'],r&&r.Gender,r&&r.Type].join(' '));}"
    if sp.count(old) != 2:
        raise SystemExit(f"V67/V69 gender authority: expected 2 matches, found {sp.count(old)}")
    sp = sp.replace(old, new, 2)

    sp = replace_once(
        sp,
        "/* V69 FINAL DEITY OWNER\n   Keeps the ranked seven-card V36 deity page in control.",
        "/* V69 FINAL DEITY OWNER\n   V6 gender rule: Polarity/Energy outrank contradictory legacy Deity Gender values.\n   Keeps the ranked seven-card V36 deity page in control.",
        'V69 audit marker')

    old = """  function render(){\n    if(!/14_goddess|15_god/.test(file()))return;\n    var page=document.querySelector('#gm-app .page-scroll')||document.querySelector('#gm-app main')||document.querySelector('#gm-app .page');if(!page)return;"""
    new = """  function render(){\n    if(!/14_goddess|15_god/.test(file()))return;\n    var repaired=state(), dirty=false;\n    if(repaired.goddess&&!feminine(repaired.goddess)){delete repaired.goddess;delete repaired.god;dirty=true;}\n    if(repaired.god){var dualFirst=repaired.goddess&&dual(repaired.goddess);var godOk=dualFirst?dual(repaired.god):masculine(repaired.god);if(!godOk){delete repaired.god;dirty=true;}}\n    if(dirty)save(repaired);\n    var page=document.querySelector('#gm-app .page-scroll')||document.querySelector('#gm-app main')||document.querySelector('#gm-app .page');if(!page)return;"""
    sp = replace_once(sp, old, new, 'V69 stored deity cleanup')
    return sp


def patch_index(path):
    text = Path(path).read_text(encoding='utf-8')
    key = '"spellBuilder"'
    k = text.find(key)
    if k < 0:
        raise SystemExit('spellBuilder key not found')
    colon = text.find(':', k + len(key))
    start = colon + 1
    while text[start].isspace():
        start += 1
    spell, end = json.JSONDecoder().raw_decode(text[start:])
    patched = patch_spell(spell)
    encoded = json.dumps(patched, ensure_ascii=False, separators=(',', ':')).replace('</script>', '<\\/script>')
    Path(path).write_text(text[:start] + encoded + text[start + end:], encoding='utf-8')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: patch_v6_deity_gender.py assets/index.html')
    patch_index(sys.argv[1])
    print('V6 deity gender repair applied')
