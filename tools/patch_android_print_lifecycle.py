#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)


SUMMARY_OLD = (
    "try{printFrame.contentWindow.document.title=title;"
    "printFrame.contentWindow.focus();"
    "printFrame.contentWindow.print()}catch(e){console.error(e)}"
)

SUMMARY_NEW = (
    "try{printFrame.contentWindow.document.title=title;"
    "var html='<!doctype html>'+d.documentElement.outerHTML;"
    "if(window.GreenmanAndroid&&typeof window.GreenmanAndroid.printHtml==='function'){"
    "window.__GM_SUMMARY_NATIVE_PRINT_WIRED__=1;"
    "window.GreenmanAndroid.printHtml(html,title);removeFrame()}else{"
    "printFrame.contentWindow.focus();printFrame.contentWindow.print()}}"
    "catch(e){busy=false;console.error(e)}"
)

SNAPSHOT_RENDER_OLD = (
    "function renderBosSnapshotInto(container,e,activeOnly){"
    "container.innerHTML='';appendBosSnapshotInto(container,e,activeOnly);}"
)

SNAPSHOT_RENDER_NEW = (
    "function renderBosSnapshotInto(container,e,activeOnly){"
    "container.innerHTML='';appendFlatSnapshot(container,e,activeOnly);"
    "qsa('.a4-page',container).forEach(function(pg){pg.classList.add('active')});"
    "fitFlatPages(container);}"
)

JOURNAL_RENDER_OLD = (
    "function renderActiveEntry(){const e=activeEntry();if(!e)return;gmResetZoom();"
    "const stage=qs('#viewerStage');if(hasBosSnapshot(e))"
    "renderBosSnapshotInto(stage,e,activePageIndex);else stage.innerHTML=buildEntryPages(e);"
    "fitSummaryPages(stage);updateEntryPages();fitVisibleA4();fitInstructionText();}"
)

JOURNAL_RENDER_NEW = (
    "function renderActiveEntry(){const e=activeEntry();if(!e)return;gmResetZoom();"
    "const stage=qs('#viewerStage');if(!hasBosSnapshot(e))stage.innerHTML=buildEntryPages(e);"
    "updateEntryPages();fitSummaryPages(stage);fitVisibleA4();fitInstructionText();}"
)

BOS_RENDER_OLD = (
    "function renderReader(){applyBosLiteMode();const e=activeEntry();if(!e)return showHome();"
    "const stage=qs('#stage');if(hasBosSnapshot(e))renderBosSnapshotInto(stage,e,activePageIndex);"
    "else stage.innerHTML=buildEntryPages(e);updatePages();requestAnimationFrame(()=>{"
    "fitSummaryPages(stage);fitGrimoirePages(stage);setTimeout(()=>{fitAllGrimoireInfoBoxes(stage);"
    "fitGrimoirePages(stage);fitStage();},80);});}"
)

BOS_RENDER_NEW = (
    "function renderReader(){applyBosLiteMode();const e=activeEntry();if(!e)return showHome();"
    "const stage=qs('#stage');if(!hasBosSnapshot(e))stage.innerHTML=buildEntryPages(e);"
    "updatePages();requestAnimationFrame(()=>{fitSummaryPages(stage);fitGrimoirePages(stage);"
    "setTimeout(()=>{fitAllGrimoireInfoBoxes(stage);fitGrimoirePages(stage);fitStage();},80);});}"
)

PRINT_HELPER = r'''function gmNativePrintArea(area,title){
  if(!area)return;
  var styles=Array.prototype.map.call(document.querySelectorAll('style'),function(s){return s.outerHTML}).join('');
  var bodyClass=String(document.body.className||'').replace(/[<>"&]/g,' ');
  var html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=794,initial-scale=1,maximum-scale=1,user-scalable=no">'+styles+'<style>@page{size:A4 portrait;margin:0}html,body{margin:0!important;padding:0!important;background:#fff!important}</style></head><body class="'+bodyClass+'">'+area.outerHTML+'</body></html>';
  if(window.GreenmanAndroid&&typeof window.GreenmanAndroid.printHtml==='function'){
    window.__GM_JOURNAL_BOS_NATIVE_PRINT_WIRED__=1;
    window.GreenmanAndroid.printHtml(html,title||document.title||'Greenman HedgeWitchery');
    setTimeout(function(){try{area.innerHTML=''}catch(_e){}},80);
  }else{
    window.print();
    setTimeout(function(){try{area.innerHTML=''}catch(_e){}},1800);
  }
}
'''


def patch_spellbuilder(page: str) -> str:
    page = replace_once(
        page,
        SUMMARY_OLD,
        SUMMARY_NEW,
        "wire both Summary print routes to Android",
    )
    required = [
        "__GM_SUMMARY_NATIVE_PRINT_WIRED__",
        "GreenmanAndroid.printHtml(html,title)",
        "data-gm-a4-page",
        "data-gm-a4-pack",
        "PRINT LITE PACK",
    ]
    missing = [item for item in required if item not in page]
    if missing:
        raise SystemExit("Summary print requirements missing: " + ", ".join(missing))
    return page


def patch_snapshot_display(page: str, page_name: str) -> str:
    page = replace_once(
        page,
        SNAPSHOT_RENDER_OLD,
        SNAPSHOT_RENDER_NEW,
        f"{page_name}: replace fragile display iframe with flat page",
    )
    if page_name == "journal":
        page = replace_once(
            page,
            JOURNAL_RENDER_OLD,
            JOURNAL_RENDER_NEW,
            "journal: remove duplicate saved-page render",
        )
    else:
        page = replace_once(
            page,
            BOS_RENDER_OLD,
            BOS_RENDER_NEW,
            "bos: remove duplicate saved-page render",
        )
    return page


def patch_journal_print(page: str) -> str:
    page = replace_once(
        page,
        "function gmFlatPrint(area){",
        PRINT_HELPER + "function gmFlatPrint(area){",
        "journal: add compact native print document builder",
    )
    page = replace_once(
        page,
        "setTimeout(function(){window.print();},140);",
        "setTimeout(function(){gmNativePrintArea(area,document.title||'Greenman Journal');},40);",
        "journal: print flat snapshots through Android",
    )
    old_print_html = (
        "function printHtml(html){const area=qs('#printArea'); area.innerHTML=html; "
        "fitSummaryPages(area); fitInstructionText(); fitFlatPages(area); "
        "setTimeout(()=>window.print(),120);}"
    )
    new_print_html = (
        "function printHtml(html){const area=qs('#printArea');area.innerHTML=html;"
        "fitSummaryPages(area);fitInstructionText();fitFlatPages(area);"
        "setTimeout(function(){gmNativePrintArea(area,document.title||'Greenman Journal');},40);}"
    )
    page = replace_once(
        page,
        old_print_html,
        new_print_html,
        "journal: print generated entry through Android",
    )
    page = replace_once(
        page,
        "setTimeout(()=>window.print(),180);",
        "setTimeout(function(){gmNativePrintArea(area,'Greenman Book of Shadows');},60);",
        "journal: print whole BoS through Android",
    )
    return page


def patch_bos_print(page: str) -> str:
    page = replace_once(
        page,
        "function gmFlatPrint(area){",
        PRINT_HELPER + "function gmFlatPrint(area){",
        "bos: add compact native print document builder",
    )
    page = replace_once(
        page,
        "setTimeout(function(){window.print();},140);",
        "setTimeout(function(){gmNativePrintArea(area,document.title||'Greenman Book of Shadows');},40);",
        "bos: print flat snapshots through Android",
    )
    old_generated = """      setTimeout(function(){
        document.body.classList.remove('gm-bos-fitting');
        window.print();
      },120);"""
    new_generated = """      setTimeout(function(){
        document.body.classList.remove('gm-bos-fitting');
        gmNativePrintArea(pa,document.title||'Greenman Book of Shadows');
      },40);"""
    page = replace_once(
        page,
        old_generated,
        new_generated,
        "bos: print generated entry through Android",
    )
    old_all = """      fitBosFrames(area,function(){
        document.body.classList.remove('gm-bos-fitting');
        window.print();
      });"""
    new_all = """      fitBosFrames(area,function(){
        document.body.classList.remove('gm-bos-fitting');
        gmNativePrintArea(area,'Greenman Book of Shadows');
      });"""
    page = replace_once(
        page,
        old_all,
        new_all,
        "bos: print complete book through Android",
    )
    return page


def patch_html(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    marker = "const PAGES = "
    start = text.index(marker) + len(marker)
    pages, used = json.JSONDecoder().raw_decode(text[start:])
    end = start + used

    pages["spellBuilder"] = patch_spellbuilder(pages["spellBuilder"])
    pages["journal"] = patch_journal_print(
        patch_snapshot_display(pages["journal"], "journal")
    )
    pages["bos"] = patch_bos_print(
        patch_snapshot_display(pages["bos"], "bos")
    )

    encoded = json.dumps(pages, ensure_ascii=False, separators=(",", ":"))
    encoded = re.sub(r"</script", r"<\\/script", encoded, flags=re.IGNORECASE)
    dst.write_text(text[:start] + encoded + text[end:], encoding="utf-8")


def patch_java(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    old = "printManager.print(jobName, target.createPrintDocumentAdapter(jobName), null);"
    new = """android.print.PrintAttributes attributes = new android.print.PrintAttributes.Builder()
                    .setMediaSize(android.print.PrintAttributes.MediaSize.ISO_A4)
                    .setMinMargins(android.print.PrintAttributes.Margins.NO_MARGINS)
                    .setColorMode(android.print.PrintAttributes.COLOR_MODE_COLOR)
                    .build();
            printManager.print(jobName, target.createPrintDocumentAdapter(jobName), attributes);"""
    text = replace_once(text, old, new, "java: request ISO A4 for native print")
    dst.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) not in (3, 5):
        raise SystemExit(
            "Usage: patch_android_print_lifecycle.py INPUT.html OUTPUT.html "
            "[INPUT.java OUTPUT.java]"
        )
    patch_html(Path(sys.argv[1]), Path(sys.argv[2]))
    if len(sys.argv) == 5:
        patch_java(Path(sys.argv[3]), Path(sys.argv[4]))
    print(
        "Android print lifecycle passed: Summary uses native print, Journal and BoS "
        "use flat stable pages, print documents are compact and cleared after handoff, "
        "and native output requests ISO A4."
    )


if __name__ == "__main__":
    main()
