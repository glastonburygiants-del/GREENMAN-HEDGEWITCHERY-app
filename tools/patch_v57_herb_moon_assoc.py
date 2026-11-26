#!/usr/bin/env python3
"""V57: curated Grimoire Herbs Moon filter from the master item 'Used in magic for' text.
Changes only the nine Herb arrays and the Grimoire Dark/New transition; other families and features remain unchanged.
"""
import json,sys
from pathlib import Path

# Correspondences copied from Greenman_Golden_Master_Lunar_Used_In_Magic_Reviewed.xlsx
# These are editorial timing suggestions, not independently proven historical attributions.
PHASES={
 "Dark Moon":"APPLEWOOD CHIPS,CAMPHOR SYNTHETIC,MULLEIN,OAK MOSS,PARSLEY,PENNYROYAL,TANSY,THYME,WHEAT GRAINS,WILLOW BARK,BLACK SALT",
 "New Moon":"ACORN,JASMINE,PEPPERMINT,ROSEMARY,THYME,WHEAT GRAINS,WOODRUFF",
 "Waxing Crescent":"STAR ANISE,BLACKBERRY LEAVES,CLOVER RED,GARDENIA FRUIT,GOLDENROD,HIBISCUS,JUNIPER BERRIES,LADIES MANTLE,LEMON BALM,LINDEN,LINSEED,ORRIS ROOT POWDER,RASPBERRY LEAF,ROSE HIP,ROSE PETALS,RUE",
 "First Quarter":"ACORN,BLACK TEA,DILL,FENNEL (SEED),GARLIC POWDER,OAKBARK RED,PINE NUT,WOODRUFF",
 "Waxing Gibbous":"BENZOIN,CALAMUS ROOT,CEDARWOOD (HIMALAYAN),DRAGON'S BLOOD,DRAGON'S BLOOD RESIN,GOLDENSEAL ROOT,HOREHOUND,LADIES MANTLE,MARIGOLD",
 "Full Moon":"BAY LAUREL,CAMPHOR SYNTHETIC,CINNAMON STICKS,COLTSFOOT,EYEBRIGHT,GOLDENROD,JASMINE,LAVENDER FLOWERS,LINDEN,MARIGOLD,HONESTY,NUTMEG POWDER,ORRIS ROOT POWDER,PARSLEY,ROSE BUDS PINK,ROSE BUDS RED,ROSE PETALS,SAGE,SANDALWOOD RED,SANDALWOOD WHITE,VIOLET,WORMWOOD,YARROW",
 "Waning Gibbous":"EYEBRIGHT,MYRRH GUM,MYRRH GUM POWDER,SWEET MYRRH,VIOLET LEAVES",
 "Last Quarter":"AGRIMONY,BASIL,CHAMOMILE,CHIVE,CLOVES,COMFREY,COMFREY ROOT,DEVILS CLAW ROOT,FRANKINCENSE,GARLIC POWDER,HOREHOUND,HYSSOP,JUNIPER BERRIES,LEMON VERBENA,LEMONGRASS,MUSTARD SEED WHITE,MYRRH GUM,MYRRH GUM POWDER,NETTLE,OAKLEAF,PENNYROYAL,PINE NUT,RUE,SANDALWOOD WHITE,SEA SALT,ST JOHN'S WORT,VALERIAN ROOT,VERVAIN,VIOLET,WINTERGREEN,WITCH HAZEL BARK,WITCH HAZEL LEAVES,BLACK SALT,WORMWOOD",
 "Waning Crescent":"BLACK TEA,CHAMOMILE,DILL,LAVENDER FLOWERS,PEPPERMINT,ROSE BUDS RED,ROSEMARY,SEA SALT,VALERIAN ROOT",
}
MARK="gm-curated-herb-moon-v57"
START="const GM_MOON_PHASE_DATA = "
END="];\\nconst GM_NAMED_MOON_DATA"

def patch(html):
    if MARK in html: raise ValueError("Already patched")
    if html.count(START)!=1 or html.count(END)!=1: raise ValueError("Grimoire Moon record not unique")
    a=html.index(START)+len(START)
    b=html.index(END,a)+1
    old=json.loads(html[a:b].replace('\\"','"'))
    assert len(old)==9 and set(x['name'] for x in old)==set(PHASES)
    assert json.dumps(old,ensure_ascii=False,separators=(',',':')).replace('"','\\"')==html[a:b]
    original=set(v for p in old for v in p['items']['Herb'])
    current={name:[v.strip() for v in names.split(',') if v.strip()] for name,names in PHASES.items()}
    combined=set(v for names in current.values() for v in names)
    if combined!=original or len(combined)!=99:raise ValueError("Master 99-herb match failed")
    new=json.loads(json.dumps(old))
    for phase in new:phase['items']['Herb']=current[phase['name']]
    for before,after in zip(old,new):
        before_noherbs=json.loads(json.dumps(before));after_noherbs=json.loads(json.dumps(after))
        del before_noherbs['items']['Herb'];del after_noherbs['items']['Herb']
        assert before_noherbs==after_noherbs
    replacement=json.dumps(new,ensure_ascii=False,separators=(',',':')).replace('"','\\"')
    updated=html[:a]+replacement+html[b:]
    assert updated.count("const GM_NAMED_MOON_DATA = ")==1
    updated=updated.replace("const GM_NAMED_MOON_DATA = ","/* "+MARK+" - herbs only, sources in reviewed master */\\nconst GM_NAMED_MOON_DATA = ",1)
    # The old Grimoire labelled the final ~1.2 days BEFORE conjunction as
    # New Moon. Split the same brief transition around estimated conjunction:
    # Dark Moon before; New Moon after. Existing age calculation is approximate.
    old_new=r'if(age<1.3 || age>28.3)return \"New Moon\";'
    fix_new=r'if(age<1.3)return \"New Moon\";'
    old_waning=r'if(age<27.8)return \"Waning Crescent\";'
    fix_waning=r'if(age<synodic-1.3)return \"Waning Crescent\";'
    if updated.count(old_new)!=1 or updated.count(old_waning)!=1:
        raise ValueError("Could not identify original Grimoire Dark/New timing rule")
    updated=updated.replace(old_new,fix_new,1).replace(old_waning,fix_waning,1)
    print("V57 lunar timing: Dark 1.3 days before estimated conjunction; New 1.3 days after")
    print("V57 verified 99 source herbs, per-phase counts:",{p:len(ns) for p,ns in current.items()})
    return updated

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("Usage: patch_v57_herb_moon_assoc.py INPUT OUTPUT")
    Path(sys.argv[2]).write_text(patch(Path(sys.argv[1]).read_text(encoding="utf-8")),encoding="utf-8")
