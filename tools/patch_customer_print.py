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


def patch_spellbuilder(page: str) -> str:
    anchor = """  function setGatherStatus(show,message){
    var st=ensureGatherStatus();
    st.textContent=message||'Gathering your spell…';
    st.classList.toggle('show',!!show);
  }
"""
    addition = anchor + r"""  function ensureGatherCompleteDialog(){
    var overlay=document.getElementById('gm-gather-complete-overlay');
    if(overlay)return overlay;
    var css=document.createElement('style');
    css.id='gm-gather-complete-style';
    css.textContent='#gm-gather-complete-overlay{position:fixed;inset:0;z-index:950000;display:none;align-items:center;justify-content:center;padding:20px;background:rgba(0,0,0,.76)}#gm-gather-complete-overlay.show{display:flex}#gm-gather-complete-card{width:min(430px,100%);background:#f5ead0;color:#1a0e04;border:3px solid #c9a84c;border-radius:14px;padding:22px 20px;box-shadow:0 14px 38px rgba(0,0,0,.62);font-family:Georgia,serif}#gm-gather-complete-title{font-family:Cinzel,Georgia,serif;font-size:18px;line-height:1.2;letter-spacing:.06em;text-align:center;color:#2d4a1e;margin:0 0 12px}#gm-gather-complete-text{font-size:16px;line-height:1.48;color:#3a2010;margin:0 0 18px;text-align:left}#gm-gather-complete-actions{display:grid;grid-template-columns:1fr 1fr;gap:9px}#gm-gather-complete-actions button{min-height:48px;border-radius:8px;border:2px solid #8a6030;padding:9px 8px;font-family:Cinzel,Georgia,serif;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}#gm-gather-open-journal{background:#2d4a1e;color:#f5ead0;border-color:#c9a84c!important}#gm-gather-stay{background:#e8c040;color:#1a0e04}@media(max-width:420px){#gm-gather-complete-actions{grid-template-columns:1fr}#gm-gather-complete-card{padding:19px 16px}}@media print{#gm-gather-complete-overlay{display:none!important}}';
    document.head.appendChild(css);
    overlay=document.createElement('div');
    overlay.id='gm-gather-complete-overlay';
    overlay.setAttribute('role','dialog');
    overlay.setAttribute('aria-modal','true');
    overlay.innerHTML='<div id="gm-gather-complete-card"><h2 id="gm-gather-complete-title">✦ Your Spell Is Gathered ✦</h2><p id="gm-gather-complete-text">Your spell is gathered. The Greenman has laid a Quick List of every chosen item in your Journal, ready for the cupboard or a shopping trip. When you wish to keep the full working, open the Journal and choose <strong>Save &amp; Add to BoS</strong> to place it in your personal Book of Shadows on this device.</p><div id="gm-gather-complete-actions"><button id="gm-gather-open-journal" type="button">Open Journal</button><button id="gm-gather-stay" type="button">Begin Another Spell</button></div></div>';
    document.body.appendChild(overlay);
    overlay.querySelector('#gm-gather-open-journal').addEventListener('click',function(){
      overlay.classList.remove('show');
      try{parent.postMessage({source:'greenman-new-shell-v1',cmd:'nav',target:'journal'},'*');}catch(_e){}
    });
    overlay.querySelector('#gm-gather-stay').addEventListener('click',function(){overlay.classList.remove('show');});
    return overlay;
  }
  function showGatherCompleteDialog(){
    var overlay=ensureGatherCompleteDialog();
    overlay.classList.add('show');
    try{overlay.querySelector('#gm-gather-open-journal').focus();}catch(_e){}
  }
"""
    page = replace_once(page, anchor, addition, "insert gather customer dialog")
    page = replace_once(
        page,
        "alert('Spell gathered. Journal, shopping list, Admin capture and stock have been updated.');",
        "showGatherCompleteDialog();",
        "replace admin-facing gather alert",
    )

    old_build_page = """function buildPage(){if(busy)return;busy=true;var f=window.GM_CURRENT_FILE||'Page';var css=(window.GM_PAGE_DEFS&&window.GM_PAGE_DEFS[f]&&window.GM_PAGE_DEFS[f].css)||'';var pages=qa('#gm-app .true-page').map(function(p,i){return {file:f+'#'+(i+1),node:clonePage(p),css:css}});renderPrint(pages,'Page')}"""
    new_build_page = """function buildPage(){if(busy)return;busy=true;var f=window.GM_CURRENT_FILE||'Page';var css=(window.GM_PAGE_DEFS&&window.GM_PAGE_DEFS[f]&&window.GM_PAGE_DEFS[f].css)||'';var all=qa('#gm-app .true-page');var visible=all.filter(function(p){var cs=getComputedStyle(p);return cs.display!=='none'&&cs.visibility!=='hidden'&&(p.offsetWidth||p.offsetHeight||p.getClientRects().length)});var source=visible.length?visible:(all.length?[all[0]]:[]);var pages=source.map(function(p,i){return {file:f+'#'+(i+1),node:clonePage(p),css:css}});renderPrint(pages,'Page')}"""
    page = replace_once(page, old_build_page, new_build_page, "make A4 Page print visible sheet only")

    old_interval = "window.addEventListener('resize',function(){setTimeout(applyScreen,80)});document.addEventListener('DOMContentLoaded',function(){setTimeout(applyScreen,300)});setInterval(applyScreen,1000);"
    new_interval = """window.addEventListener('resize',function(){setTimeout(applyScreen,80)});document.addEventListener('DOMContentLoaded',function(){setTimeout(applyScreen,180);setTimeout(applyScreen,520);setTimeout(applyScreen,980)});var gmFitTimer=0;new MutationObserver(function(){clearTimeout(gmFitTimer);gmFitTimer=setTimeout(applyScreen,120)}).observe(document.getElementById('gm-app')||document.documentElement,{childList:true,subtree:true,characterData:true});"""
    page = replace_once(page, old_interval, new_interval, "remove repeated one-second page refit")

    old_num_interval = "setInterval(function(){if(/18_summary/.test(window.GM_CURRENT_FILE||'')||q('#gm-v40-print-stack'))repair()},700);"
    page = replace_once(page, old_num_interval, "", "remove repeated summary numerology refit")

    replacements = {
        "position:fixed;left:-12000px;top:0;width:900px;height:1250px;border:0;opacity:0;pointer-events:none":
        "position:fixed;left:0;top:0;width:900px;height:1250px;border:0;opacity:0;visibility:hidden;pointer-events:none;z-index:-2147483648;clip-path:inset(100%);contain:strict",
        "position:fixed;left:-12000px;top:0;width:820px;height:1120px;border:0;opacity:0;pointer-events:none":
        "position:fixed;left:0;top:0;width:820px;height:1120px;border:0;opacity:0;visibility:hidden;pointer-events:none;z-index:-2147483648;clip-path:inset(100%);contain:strict",
    }
    for old, new in replacements.items():
        count = page.count(old)
        if count < 1:
            raise SystemExit(f"print helper iframe style not found: {old[:40]}")
        page = page.replace(old, new)

    clip_style = r"""
<style id="gm-customer-summary-bleed-guard">
@media screen{
  body.gm-v65-canonical-pages #gm-app .true-page{
    overflow:hidden!important;
    contain:layout paint!important;
    isolation:isolate!important;
    clip-path:inset(0 round 14px)!important;
  }
  body.gm-v65-canonical-pages #gm-app .true-content{
    max-width:100%!important;
    min-width:0!important;
  }
}
</style>
"""
    if "</head>" not in page:
        raise SystemExit("spellbuilder head not found")
    page = page.replace("</head>", clip_style + "</head>", 1)
    return page


def patch_snapshot_page(page: str, page_name: str) -> str:
    old_return = "return '<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=794,initial-scale=1,maximum-scale=1,user-scalable=no\"><style>'+css+'\\n'+finalCss+'</style></head><body data-summary=\"'+(summary?'1':'0')+'\" data-summary-page2=\"'+(summaryPage2?'1':'0')+'\">'+(p.html||'')+fitter+'</body></html>';"
    new_return = "return '<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=794,initial-scale=1,maximum-scale=1,user-scalable=no\"><style>'+css+'\\n'+finalCss+'</style><script>window.applyBosLiteMode=window.applyBosLiteMode||function(){};<\\/script></head><body data-summary=\"'+(summary?'1':'0')+'\" data-summary-page2=\"'+(summaryPage2?'1':'0')+'\">'+(p.html||'')+fitter+'</body></html>';"
    page = replace_once(page, old_return, new_return, f"{page_name}: add saved-page compatibility guard")

    if page_name == "journal":
        old_render = "function renderActiveEntry(){const e=activeEntry(); if(!e)return; gmResetZoom(); const stage=qs('#viewerStage'); if(hasBosSnapshot(e))renderBosSnapshotInto(stage,e,null); else stage.innerHTML=buildEntryPages(e); fitSummaryPages(stage); updateEntryPages(); fitVisibleA4(); fitInstructionText();}\nfunction updateEntryPages(){const pages=qsa('.a4-page',qs('#viewerStage')); if(!pages.length)return; activePageIndex=Math.max(0,Math.min(activePageIndex,pages.length-1)); pages.forEach((p,i)=>p.classList.toggle('active',i===activePageIndex)); qs('#entryPageCount').textContent=(activePageIndex+1)+' of '+pages.length; fitSummaryPages(qs('#viewerStage')); fitVisibleA4(); const wrap=qs('.viewer-stage-wrap'); if(wrap)wrap.scrollTop=0;}"
        new_render = """function renderActiveEntry(){const e=activeEntry();if(!e)return;gmResetZoom();const stage=qs('#viewerStage');if(hasBosSnapshot(e))renderBosSnapshotInto(stage,e,activePageIndex);else stage.innerHTML=buildEntryPages(e);fitSummaryPages(stage);updateEntryPages();fitVisibleA4();fitInstructionText();}
function updateEntryPages(){const e=activeEntry(),stage=qs('#viewerStage');if(!e||!stage)return;let total=0;if(hasBosSnapshot(e)){total=e.bosSnapshot.pages.length;activePageIndex=Math.max(0,Math.min(activePageIndex,total-1));renderBosSnapshotInto(stage,e,activePageIndex);}else{const pages=qsa('.a4-page',stage);if(!pages.length)return;total=pages.length;activePageIndex=Math.max(0,Math.min(activePageIndex,total-1));pages.forEach((p,i)=>p.classList.toggle('active',i===activePageIndex));}qs('#entryPageCount').textContent=(activePageIndex+1)+' of '+total;fitSummaryPages(stage);fitVisibleA4();const wrap=qs('.viewer-stage-wrap');if(wrap){wrap.scrollTop=0;wrap.scrollLeft=0;}}"""
        page = replace_once(page, old_render, new_render, "journal: render one saved A4 iframe at a time")
    elif page_name == "bos":
        old_render = "function renderReader(){applyBosLiteMode();const e=activeEntry();if(!e)return showHome();const stage=qs('#stage');if(hasBosSnapshot(e))renderBosSnapshotInto(stage,e,null);else stage.innerHTML=buildEntryPages(e);updatePages();requestAnimationFrame(()=>{fitSummaryPages(stage);fitGrimoirePages(stage);setTimeout(()=>{fitAllGrimoireInfoBoxes(stage);fitGrimoirePages(stage);fitStage();},80);});}"
        new_render = "function renderReader(){applyBosLiteMode();const e=activeEntry();if(!e)return showHome();const stage=qs('#stage');if(hasBosSnapshot(e))renderBosSnapshotInto(stage,e,activePageIndex);else stage.innerHTML=buildEntryPages(e);updatePages();requestAnimationFrame(()=>{fitSummaryPages(stage);fitGrimoirePages(stage);setTimeout(()=>{fitAllGrimoireInfoBoxes(stage);fitGrimoirePages(stage);fitStage();},80);});}"
        page = replace_once(page, old_render, new_render, "bos: render one saved A4 iframe at a time")
        old_update = "function updatePages(){const pages=qsa('.a4-page',qs('#stage'));if(!pages.length)return;activePageIndex=Math.max(0,Math.min(activePageIndex,pages.length-1));pages.forEach((p,i)=>p.classList.toggle('active',i===activePageIndex));qs('#readerInfo').textContent=(activePageIndex+1)+' of '+pages.length+' · '+(activeEntry().spellName||'Book of Shadows');qs('#prevBtn').disabled=activePageIndex===0;qs('#nextBtn').disabled=activePageIndex>=pages.length-1;fitSummaryPages(qs('#stage'));fitStage();const sc=qs('.page-scroll');if(sc){sc.scrollTop=0;sc.scrollLeft=0;}}"
        new_update = "function updatePages(){const e=activeEntry(),stage=qs('#stage');if(!e||!stage)return;let total=0;if(hasBosSnapshot(e)){total=e.bosSnapshot.pages.length;activePageIndex=Math.max(0,Math.min(activePageIndex,total-1));renderBosSnapshotInto(stage,e,activePageIndex);}else{const pages=qsa('.a4-page',stage);if(!pages.length)return;total=pages.length;activePageIndex=Math.max(0,Math.min(activePageIndex,total-1));pages.forEach((p,i)=>p.classList.toggle('active',i===activePageIndex));}qs('#readerInfo').textContent=(activePageIndex+1)+' of '+total+' · '+(e.spellName||'Book of Shadows');qs('#prevBtn').disabled=activePageIndex===0;qs('#nextBtn').disabled=activePageIndex>=total-1;fitSummaryPages(stage);fitStage();const sc=qs('.page-scroll');if(sc){sc.scrollTop=0;sc.scrollLeft=0;}}"
        page = replace_once(page, old_update, new_update, "bos: preserve total page count with one iframe")
    return page


def patch_html(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    marker = "const PAGES = "
    start = text.index(marker) + len(marker)
    pages, consumed = json.JSONDecoder().raw_decode(text[start:])
    end = start + consumed
    pages["spellBuilder"] = patch_spellbuilder(pages["spellBuilder"])
    pages["journal"] = patch_snapshot_page(pages["journal"], "journal")
    pages["bos"] = patch_snapshot_page(pages["bos"], "bos")
    encoded = json.dumps(pages, ensure_ascii=False, separators=(",", ":"))
    encoded = re.sub(r"</script", r"<\\/script", encoded, flags=re.IGNORECASE)
    text = text[:start] + encoded + text[end:]
    dst.write_text(text, encoding="utf-8")


def patch_java(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    private View customView;\n    private WebChromeClient.CustomViewCallback customViewCallback;",
        "    private View customView;\n    private WebChromeClient.CustomViewCallback customViewCallback;\n    private WebView printWebView;",
        "java: add print WebView field",
    )
    old_bridge = '                + "try{var original=win.print;win.print=function(){GreenmanAndroid.printCurrentPage();};win.__greenmanOriginalPrint=original;}catch(_e){}"\n'
    new_bridge = '                + "try{var original=win.print;win.print=function(){var html=\'<!doctype html>\'+doc.documentElement.outerHTML;GreenmanAndroid.printHtml(html,doc.title||\'Greenman HedgeWitchery\');var fe=win.frameElement;if(fe&&fe.id!==\'pageFrame\'&&!(fe.classList&&fe.classList.contains(\'snapshot-frame\')))setTimeout(function(){try{fe.remove();}catch(_e){}},350);};win.__greenmanOriginalPrint=original;}catch(_e){}"\n'
    text = replace_once(text, old_bridge, new_bridge, "java: print the calling document, not outer app")

    old_interface = """        @JavascriptInterface
        public void printCurrentPage() {
            runOnUiThread(() -> {
                try {
                    android.print.PrintManager printManager =
                            (android.print.PrintManager) getSystemService(PRINT_SERVICE);
                    String jobName = "Greenman HedgeWitchery";
                    printManager.print(jobName, webView.createPrintDocumentAdapter(jobName), null);
                } catch (Exception error) {
                    Toast.makeText(MainActivity.this, "Printing could not be opened.", Toast.LENGTH_LONG).show();
                }
            });
        }
"""
    new_interface = """        @JavascriptInterface
        public void printCurrentPage() {
            runOnUiThread(() -> printWebViewDocument(webView, "Greenman HedgeWitchery"));
        }

        @JavascriptInterface
        public void printHtml(String html, String requestedJobName) {
            runOnUiThread(() -> openPrintDocument(html, requestedJobName));
        }
"""
    text = replace_once(text, old_interface, new_interface, "java: add HTML print bridge")

    insert_before = "    private void handleDownload(String url, String contentDisposition, String mimeType) {"
    methods = r'''    private void openPrintDocument(String html, String requestedJobName) {
        if (html == null || html.trim().isEmpty()) {
            Toast.makeText(this, "The A4 page was empty and could not be printed.", Toast.LENGTH_LONG).show();
            return;
        }
        destroyPrintWebView();
        final String jobName = sanitizePrintJobName(requestedJobName);
        final WebView target = new WebView(this);
        printWebView = target;
        target.setBackgroundColor(Color.WHITE);
        WebSettings settings = target.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setBuiltInZoomControls(false);
        settings.setSupportZoom(false);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(false);
        target.setAlpha(0.01f);
        FrameLayout.LayoutParams layout = new FrameLayout.LayoutParams(794, 1123);
        layout.leftMargin = -1800;
        layout.topMargin = 0;
        root.addView(target, layout);
        target.setWebViewClient(new WebViewClient() {
            private boolean printed;
            @Override
            public void onPageFinished(WebView view, String url) {
                if (printed) return;
                printed = true;
                view.postDelayed(() -> {
                    if (printWebView != view) return;
                    printWebViewDocument(view, jobName);
                    view.postDelayed(MainActivity.this::destroyPrintWebView, 120000L);
                }, 500L);
            }
        });
        target.loadDataWithBaseURL("https://greenman.local/print/", html, "text/html", "UTF-8", null);
    }

    private void printWebViewDocument(WebView target, String requestedJobName) {
        try {
            android.print.PrintManager printManager =
                    (android.print.PrintManager) getSystemService(PRINT_SERVICE);
            String jobName = sanitizePrintJobName(requestedJobName);
            printManager.print(jobName, target.createPrintDocumentAdapter(jobName), null);
        } catch (Exception error) {
            Toast.makeText(this, "Printing could not be opened.", Toast.LENGTH_LONG).show();
        }
    }

    private static String sanitizePrintJobName(String requestedJobName) {
        String name = requestedJobName == null ? "Greenman HedgeWitchery" : requestedJobName.trim();
        name = name.replaceAll("[\\r\\n\\t\\p{Cntrl}]", " ").replaceAll("\\s+", " ");
        if (name.isEmpty()) name = "Greenman HedgeWitchery";
        return name.length() > 80 ? name.substring(0, 80) : name;
    }

    private void destroyPrintWebView() {
        WebView target = printWebView;
        printWebView = null;
        if (target == null) return;
        try {
            if (target.getParent() instanceof ViewGroup) {
                ((ViewGroup) target.getParent()).removeView(target);
            }
            target.stopLoading();
            target.setWebChromeClient(null);
            target.setWebViewClient(null);
            target.destroy();
        } catch (Exception ignored) {}
    }

'''
    text = replace_once(text, insert_before, methods + insert_before, "java: add temporary print WebView")
    text = replace_once(
        text,
        "    protected void onDestroy() {\n        if (webView != null) {",
        "    protected void onDestroy() {\n        destroyPrintWebView();\n        if (webView != null) {",
        "java: clean print WebView",
    )
    dst.write_text(text, encoding="utf-8")


def main() -> None:
    if len(sys.argv) not in (3, 5):
        raise SystemExit("usage: patch_customer_print.py INPUT_HTML OUTPUT_HTML [INPUT_JAVA OUTPUT_JAVA]")
    patch_html(Path(sys.argv[1]), Path(sys.argv[2]))
    if len(sys.argv) == 5:
        patch_java(Path(sys.argv[3]), Path(sys.argv[4]))


if __name__ == "__main__":
    main()
