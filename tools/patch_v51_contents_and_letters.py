#!/usr/bin/env python3
"""V51: apply the approved Contents opener and add the Scribe's Letters chapter.

The V43 PDF renderer and all existing saved-book records remain unchanged.
The user's 19-folio Scribe chapter is added to the Book of Shadows page pool.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ANCHORS = ("function __gmLazyScribeSrc(){return ", "PAGES.scribe = ")
MARK = "gm-bos-folio-v51-contents-letters"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one anchor, found {count}")
    return source.replace(old, new, 1)


def replace_function(source: str, start: str, end: str, replacement: str) -> str:
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError(f"Expected unique function anchors: {start} / {end}")
    a = source.index(start)
    b = source.index(end, a + len(start))
    return source[:a] + replacement.rstrip() + "\n" + source[b:]


def patch(source: str, chapter_html: str, runtime: str, css: str) -> str:
    if MARK in source:
        raise ValueError("V51 patch is already present")
    active = [anchor for anchor in ANCHORS if source.count(anchor)]
    if len(active) != 1 or source.count(active[0]) != 1:
        raise ValueError("Expected one embedded Scribe HTML document")
    pos = source.index(active[0]) + len(active[0])
    scribe, consumed = json.JSONDecoder().raw_decode(source[pos:])
    if not isinstance(scribe, str):
        raise ValueError("Embedded Scribe document is not a string")
    if "gm-bos-folio-v47-clean" not in scribe:
        raise ValueError("V51 must be applied to the V47/V50 manuscript baseline")
    if "GM_INK_A4_SVG_PAINT_PAGINATION_V43" not in scribe:
        raise ValueError("The proven V43 PDF renderer is missing")
    for token in ("const W=794,H=1123;", "const CHAPTERS=[", "function addContents(){",
                  "function addSpellContents(){", "function addChapterContentsPages(){",
                  "addRefs('tools','ritual');\n addChapterContentsPages();",
                  "function gmBosTocSections(){", "function bindChapterContentsNavigation(){"):
        if scribe.count(token) != 1:
            raise ValueError(f"Expected one V50 Scribe anchor: {token}")
    if chapter_html.count("id=\"greenman-bos-scribe-chapter\"") != 1:
        raise ValueError("Scribe's Letters source document is missing its chapter root")
    if chapter_html.count('class="sheet') < 20 or chapter_html.count('data-script-notes=') != 19:
        raise ValueError("Scribe's Letters must contain its cover, 19 folios and 19 note areas")

    # Keep all lettering and notes self-contained and offline in the app.
    encoded_chapter = json.dumps(chapter_html, ensure_ascii=False, separators=(",", ":"))
    encoded_chapter = re.sub(r"</script", r"<\/script", encoded_chapter, flags=re.I)
    runtime_blob = "const GM_BOS_SCRIBE_LETTERS_HTML=" + encoded_chapter + ";\n" + runtime
    scribe = replace_once(scribe, "const W=794,H=1123;", "const W=794,H=1123;\n" + runtime_blob,
                          "offline chapter payload and V51 runtime")

    chapter_tail = " {id:'index',num:'17',title:'Reference Index',sub:'Items, moons, Sabbats, tools and other references with their page numbers.'}\n];"
    chapter_new = " {id:'index',num:'17',title:'Reference Index',sub:'Items, moons, Sabbats, tools and other references with their page numbers.'},\n {id:'scribe-letters',num:'18',title:'The Scribe’s Letters',sub:'Nineteen illustrated reference leaves for the Scribe’s writing hands.'}\n];"
    scribe = replace_once(scribe, chapter_tail, chapter_new, "chapter 18 definition")

    toc_anchor = " const spellCh=['spell-list','altars','summaries','timings','instructions'];\n return TOC_CHAPTERS.map(c=>{"
    toc_new = " const spellCh=['spell-list','altars','summaries','timings','instructions'];\n return TOC_CHAPTERS.map(c=>{\n  if(c.id==='scribe-letters')return sec(c.id,[range(c.id,'The Lettered Leaves · 19 scripts')]);"
    scribe = replace_once(scribe, toc_anchor, toc_new, "Scribe's Letters contents entry")

    contents = r'''function addContents(){
 GM_BOS_TOC_PACKS=gmBosTocPackSections(gmBosTocSections(),15);
 GM_BOS_TOC_PACKS.forEach((pack,i)=>{
  const sub='Page '+(i+1)+' of '+GM_BOS_TOC_PACKS.length;
  const p=page('contents','Contents',sub,'gmBosContentsPage gmBosV47Page gmV51ContentsPage');
  const h=p.querySelector('.gmBosChapterHead');if(h)h.innerHTML='';
  const filter=i===0?'<div class="gmBosContentsActions gmV47ContentsFilter"><button type="button" id="gmBosSelectAll">All chapters</button><button type="button" id="gmBosSelectSpell">Spell chapters</button><button type="button" id="gmBosSelectReference">Lore chapters</button></div>':'';
  body(p).innerHTML='<div class="gmV51ContentsBody"><div class="gmV51NameRegion"><button type="button" class="gmV51NameAdd">Add magical name</button><form class="gmV51NameEditor" hidden><input type="text" class="gmV51NameInput" maxlength="36" placeholder="Magical name" aria-label="Magical name" autocomplete="off" spellcheck="false"><button type="submit" class="gmV51NameSave">Save</button><button type="button" class="gmV51NameCancel">Cancel</button></form><div class="gmV51NameRender" role="button" tabindex="0" title="Double-tap to edit magical name" aria-label="Magical name. Double-tap to edit." aria-live="polite"><div class="gmV51NameArt" role="img" aria-label="Magical name"></div></div></div><div class="gmV51BookHeading"><h1 class="gmV51AccessibleTitle">Book of Shadows</h1><svg class="gmV51BookTitle" role="img" aria-label="Book of Shadows"></svg></div><svg class="gmV51TitleOrnament" viewBox="0 0 660 30" aria-hidden="true"><path d="M3 15 H205 Q227 15 241 9 Q259 1 268 14 Q278 26 289 16 Q303 5 316 15 Q333 30 347 15 Q362 2 376 15 Q389 28 402 15 Q415 2 429 10 Q449 15 466 15 H657" fill="none" stroke="#99733e" stroke-width="1.5"/><path d="M249 13 Q233 2 220 5 Q224 18 249 13 Z M405 15 Q420 2 439 5 Q436 16 405 15 Z" fill="#49664f" stroke="#bc9e64" stroke-width="1.1"/><circle cx="329" cy="15" r="3.5" fill="#843c40" stroke="#d6aa4e" stroke-width="1.5"/><circle cx="329" cy="15" r="1" fill="#efcb75"/></svg><div class="gmV51ContentsHeading">'+gmV47Initial('C')+'<div class="gmV51ContentsWords"><h1>Contents</h1><div class="gmV51PageMark">'+esc(sub)+'</div></div></div><svg class="gmV51Rule" viewBox="0 0 650 12" aria-hidden="true"><path d="M2 6 H648" stroke="#b49c74" stroke-width="1"/><path d="M322 6 l4 -4 4 4 -4 4 Z" fill="#aa7c3e"/><circle cx="16" cy="6" r="2" fill="#a65b49"/><circle cx="634" cy="6" r="2" fill="#a65b49"/></svg>'+filter+'<div class="gmBosContentsRows gmV47Register" data-gm-contents-pack="'+i+'"></div><div class="gmV51BrandFooter">Greenman HedgeWitchery Apothecary</div></div>';
  gmV51IlluminatedLettering('BOOK OF SHADOWS',p.querySelector('.gmV51BookTitle'));
  gmV51BindNameRegion(p.querySelector('.gmV51NameRegion'));
 });
}'''
    scribe = replace_function(scribe, "function addContents(){", "function addSpellContents(){", contents)

    scribe = replace_once(scribe, "addRefs('tools','ritual');\n addChapterContentsPages();",
                          "addRefs('tools','ritual');\n gmV51AddScribeLettersPages();\n addChapterContentsPages();",
                          "chapter build order")

    style = '<style id="' + MARK + '">' + css + "</style>"
    if "</head>" not in scribe:
        raise ValueError("Expected an Scribe head boundary")
    scribe = scribe.replace("</head>", style + "</head>", 1)
    if scribe.count(MARK) != 1 or scribe.count("function gmV51IlluminatedLettering") != 1:
        raise ValueError("V51 style/runtime postcondition failed")
    if scribe.count("function gmV51AddScribeLettersPages()") != 1:
        raise ValueError("V51 Scribe chapter function postcondition failed")

    encoded_scribe = json.dumps(scribe, ensure_ascii=False, separators=(",", ":"))
    encoded_scribe = re.sub(r"</script", r"<\/script", encoded_scribe, flags=re.I)
    result = source[:pos] + encoded_scribe + source[pos + consumed:]
    if result[:pos] != source[:pos] or result[pos + len(encoded_scribe):] != source[pos + consumed:]:
        raise ValueError("V51 changed outer app content outside embedded Scribe")
    return result


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: patch_v51_contents_and_letters.py INPUT.html OUTPUT.html")
    root = Path(__file__).parent
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    result = patch(
        source.read_text(encoding="utf-8"),
        (root / "scribe_letters_chapter.html").read_text(encoding="utf-8"),
        (root / "gm_v51_runtime.js").read_text(encoding="utf-8"),
        (root / "bos_folio_v51.css").read_text(encoding="utf-8"),
    )
    output.write_text(result, encoding="utf-8")
    print("V51 Contents title, optional magical name and Scribe's 19-folio chapter integrated")


if __name__ == "__main__":
    main()
