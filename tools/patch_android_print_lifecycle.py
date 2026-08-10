#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys
from pathlib import Path


def replace_once(text, old, new, label):
    c=text.count(old)
    if c!=1: raise SystemExit(f'{label}: expected 1, found {c}')
    return text.replace(old,new,1)

PAGE_SEND_HELPER = r'''window.gmSendNativePrintHtml=window.gmSendNativePrintHtml||function(html,title){
  try{
    parent.postMessage({source:'greenman-new-shell-v1',cmd:'nativePrintHtml',html:String(html||''),title:String(title||'Greenman HedgeWitchery')},'*');
    return true;
  }catch(e){try{console.error(e)}catch(_e){}return false;}
};
'''

OUTER_HELPER = r'''window.gmNativePrintHtml=function(html,title){
  try{
    html=String(html||'');
    if(!html||html.length<80){
      if(window.GreenmanAndroid&&typeof window.GreenmanAndroid.showMessage==='function')window.GreenmanAndroid.showMessage('The print page was empty.');
      return false;
    }
    if(window.GreenmanAndroid&&typeof window.GreenmanAndroid.printHtml==='function'){
      window.GreenmanAndroid.printHtml(html,String(title||'Greenman HedgeWitchery'));
      return true;
    }
  }catch(e){try{console.error(e)}catch(_e){}}
  return false;
};
'''

COMPACT_PRINT_HELPER = r'''function gmSendPreparedPrintArea(area,title){
  if(!area)return false;
  var pageNodes=Array.prototype.filter.call(area.children,function(el){return el.classList&&el.classList.contains('a4-page')});
  var flat=pageNodes.length>0&&pageNodes.every(function(el){return el.classList.contains('gm-flat')});
  var extraStyles='';
  if(!flat){extraStyles=Array.prototype.map.call(document.querySelectorAll('style'),function(s){return s.textContent||'';}).join('\n');}
  var content=area.innerHTML;
  var base='@page{size:A4 portrait;margin:0}*{box-sizing:border-box}html,body{margin:0!important;padding:0!important;background:#fff!important;width:210mm!important;height:auto!important;overflow:visible!important}.gm-native-print-root{display:block!important;width:210mm!important;margin:0!important;padding:0!important}.gm-native-print-root>.a4-page,.gm-native-print-root .gm-flat{display:block!important;position:relative!important;left:auto!important;top:auto!important;width:210mm!important;height:297mm!important;min-height:297mm!important;max-height:297mm!important;margin:0!important;padding:0!important;overflow:hidden!important;visibility:visible!important;opacity:1!important;transform:none!important;page-break-after:always!important;break-after:page!important;box-shadow:none!important}.gm-native-print-root>.a4-page:last-of-type,.gm-native-print-root .gm-flat:last-of-type{page-break-after:auto!important;break-after:auto!important}.gm-flat{background:#fff!important;background-image:none!important}.gm-flat-canvas{position:relative!important;width:756px!important;height:1058px!important;overflow:hidden!important;margin:32px auto!important;background:transparent!important}.gm-flat .true-page{display:block!important;position:relative!important;left:auto!important;top:auto!important;width:756px!important;max-width:756px!important;min-width:756px!important;height:1058px!important;min-height:1058px!important;max-height:1058px!important;margin:0!important;overflow:hidden!important;box-shadow:none!important;visibility:visible!important;opacity:1!important;zoom:1!important}.gm-flat .true-page>.true-content{transform-origin:top left!important}.gm-flat .item-row{display:grid!important;grid-template-columns:165px 1fr 1fr 1fr!important}.gm-flat .summary-row{display:grid!important;grid-template-columns:190px 1fr!important;gap:10px!important}button,.bottom-btns,.tabbar,.bottom-tabbar,#gm-print-nav,[id*=print-nav],[id*=gather],.gather-btn,.gather-spell{display:none!important}';
  var html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=794,initial-scale=1,maximum-scale=1,user-scalable=no"><style>'+extraStyles+'\n'+base+'</style></head><body><main class="gm-native-print-root">'+content+'</main></body></html>';
  if(typeof window.gmSendNativePrintHtml==='function'&&window.gmSendNativePrintHtml(html,title||document.title||'Greenman HedgeWitchery')){
    window.__GM_COMPACT_PRINT_SENT__=1;
    setTimeout(function(){try{area.innerHTML=''}catch(_e){}},1200);
    return true;
  }
  return false;
}
'''

APPEND_OLD="""function appendFlatSnapshot(container,e,activeOnly){
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
}"""
APPEND_NEW="""function appendFlatSnapshot(container,e,activeOnly){
  var snap=e.bosSnapshot||{},pages=snap.pages||[],css='',common='gm-flat-common-'+(++GM_FLAT_SEQ);
  css+=gmScopeCss(String(snap.css||''),'.'+common);
  pages.forEach(function(pg,i){
    if(activeOnly!=null&&i!==activeOnly)return;
    if(i===3||i===4){
      container.appendChild(makeBosSnapshotPage(e,pg,false));
      return;
    }
    var cls='gm-flat-'+(++GM_FLAT_SEQ);
    css+=gmScopeCss(String(pg.css||''),'.'+cls);
    var sec=document.createElement('section');
    sec.className='a4-page gm-flat gm-v55-fit '+common+' '+cls;
    var cv=document.createElement('div');
    cv.className='gm-flat-canvas';
    cv.innerHTML=String(pg.html||'');
    sec.appendChild(cv);
    container.appendChild(sec);
  });
  if(css){var st=document.createElement('style');st.textContent=css;container.appendChild(st);}
}"""


def patch_spellbuilder(p):
    anchor='function renderPrint(pages,kind){'
    if 'window.gmSendNativePrintHtml=' not in p:
        p=replace_once(p,anchor,PAGE_SEND_HELPER+anchor,'spell helper')
    old="printFrame.contentWindow.document.title=title;printFrame.contentWindow.focus();printFrame.contentWindow.print()"
    new="printFrame.contentWindow.document.title=title;var html='<!doctype html>'+d.documentElement.outerHTML;if(window.gmSendNativePrintHtml(html,title)){window.__GM_NORMAL_SUMMARY_PRINT_SENT__=1;removeFrame()}else{printFrame.contentWindow.focus();printFrame.contentWindow.print()}"
    p=replace_once(p,old,new,'normal summary handoff')
    old_lite="""if(window.GreenmanAndroid&&typeof window.GreenmanAndroid.printHtml==='function'){
   window.__GM_LITE_PRINT_NATIVE_WIRED__=1;
   window.GreenmanAndroid.printHtml(liteHtml,liteTitle);
   setTimeout(function(){try{f.remove();}catch(_e){}},1200);
  }else{
   try{f.contentWindow.focus();f.contentWindow.print();}finally{setTimeout(function(){f.remove();},1800);}
  }"""
    new_lite="""if(typeof window.gmSendNativePrintHtml==='function'&&window.gmSendNativePrintHtml(liteHtml,liteTitle)){
   window.__GM_LITE_PRINT_NATIVE_WIRED__=1;
   window.__GM_LITE_PRINT_SENT__=1;
   setTimeout(function(){try{f.remove();}catch(_e){}},1200);
  }else{
   try{f.contentWindow.focus();f.contentWindow.print();}finally{setTimeout(function(){f.remove();},1800);}
  }"""
    p=replace_once(p,old_lite,new_lite,'lite summary handoff')
    p=replace_once(p,"  closeKb();\n  render();\n  jumpTo('timing');\n}","  closeKb();\n  render();\n}",'planet timing item no jump')
    p=replace_once(p,"    closeKb();\n    render();\n    jumpTo('timing');\n    return;","    closeKb();\n    render();\n    return;",'planet first match no jump')
    p=replace_once(p,"      showP(key, btn);\n      // Scroll to phase detail\n      document.getElementById('pd-icon').parentElement.scrollIntoView({behavior:'smooth', block:'start'});","      showP(key, btn);",'moon item no jump')
    return p


def patch_journal(p,name):
    if 'window.gmSendNativePrintHtml=' not in p:
        p=replace_once(p,'function gmFlatPrint(area){',PAGE_SEND_HELPER+COMPACT_PRINT_HELPER+'function gmFlatPrint(area){',name+' helpers')
    p=replace_once(p,APPEND_OLD,APPEND_NEW,name+' common CSS dedupe')
    old_gm="""function gmFlatPrint(area){
  document.body.classList.add('gm-bos-fitting');
  void document.body.offsetHeight;
  try{fitFlatPages(area);}catch(_e){}
  document.body.classList.remove('gm-bos-fitting');
  setTimeout(function(){window.print();},140);
}"""
    new_gm="""function gmFlatPrint(area){
  document.body.classList.add('gm-bos-fitting');
  void document.body.offsetHeight;
  try{fitFlatPages(area);}catch(_e){}
  document.body.classList.remove('gm-bos-fitting');
  setTimeout(function(){if(!gmSendPreparedPrintArea(area,document.title||'Greenman HedgeWitchery'))window.print();},80);
}"""
    p=replace_once(p,old_gm,new_gm,name+' snapshot print')
    if name=='journal':
        p=replace_once(p,"setTimeout(()=>window.print(),120);","setTimeout(function(){if(!gmSendPreparedPrintArea(area,document.title||'Greenman Journal'))window.print();},80);",'journal generic print')
        p=replace_once(p,"setTimeout(()=>window.print(),180);","setTimeout(function(){if(!gmSendPreparedPrintArea(area,'Greenman Book of Shadows'))window.print();},100);",'journal whole print')
    else:
        p=replace_once(p,"""      setTimeout(function(){
        document.body.classList.remove('gm-bos-fitting');
        window.print();
      },120);""","""      setTimeout(function(){
        document.body.classList.remove('gm-bos-fitting');
        if(!gmSendPreparedPrintArea(pa,document.title||'Greenman Book of Shadows'))window.print();
      },80);""",'bos generic print')
        p=replace_once(p,"""      fitBosFrames(area,function(){
        document.body.classList.remove('gm-bos-fitting');
        window.print();
      });""","""      fitBosFrames(area,function(){
        document.body.classList.remove('gm-bos-fitting');
        if(!gmSendPreparedPrintArea(area,'Greenman Book of Shadows'))window.print();
      });""",'bos whole print')
    return p


def patch_html(src,dst):
    text=src.read_text(encoding='utf-8')
    marker='const PAGES = '; start=text.index(marker)+len(marker)
    pages,used=json.JSONDecoder().raw_decode(text[start:]); end=start+used
    pages['spellBuilder']=patch_spellbuilder(pages['spellBuilder'])
    pages['journal']=patch_journal(pages['journal'],'journal')
    pages['bos']=patch_journal(pages['bos'],'bos')
    enc=json.dumps(pages,ensure_ascii=False,separators=(',',':'))
    enc=re.sub(r'</script',r'<\/script',enc,flags=re.I)
    tail=text[end:]
    listener="window.addEventListener('message', ev=>{"
    if 'window.gmNativePrintHtml=function' not in tail:
        pos=tail.find(listener)
        if pos<0: raise SystemExit('outer listener missing')
        tail=tail[:pos]+OUTER_HELPER+tail[pos:]
    gate="if(m.source!=='greenman-new-shell-v1') return;"
    handler="if(m.source!=='greenman-new-shell-v1') return;\n  if(m.cmd==='nativePrintHtml'){gmNativePrintHtml(m.html,m.title);return;}"
    if "m.cmd==='nativePrintHtml'" not in tail:
        tail=replace_once(tail,gate,handler,'outer print handler')
    out=text[:start]+enc+tail
    for req in ['__GM_NORMAL_SUMMARY_PRINT_SENT__','__GM_LITE_PRINT_SENT__','__GM_COMPACT_PRINT_SENT__',"m.cmd==='nativePrintHtml'",'window.gmNativePrintHtml=function']:
        if req not in out: raise SystemExit('missing '+req)
    dst.write_text(out,encoding='utf-8')


def extract_method(text, signature):
    i=text.find(signature)
    if i<0: return None
    b=text.find('{',i); depth=0; quote=None; esc=False; line=False; block=False; k=b
    while k<len(text):
        ch=text[k]; nx=text[k+1] if k+1<len(text) else ''
        if line:
            if ch=='\n': line=False
        elif block:
            if ch=='*' and nx=='/': block=False;k+=1
        elif quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
        else:
            if ch=='/' and nx=='/': line=True;k+=1
            elif ch=='/' and nx=='*': block=True;k+=1
            elif ch in "'\"": quote=ch
            elif ch=='{': depth+=1
            elif ch=='}':
                depth-=1
                if depth==0: return text[i:k+1]
        k+=1
    raise SystemExit('unclosed '+signature)

OPEN_NEW=r'''private void openPrintDocument(String html, String requestedJobName) {
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
        settings.setDomStorageEnabled(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setBuiltInZoomControls(false);
        settings.setSupportZoom(false);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(false);
        FrameLayout.LayoutParams layout = new FrameLayout.LayoutParams(794, 1123);
        layout.leftMargin = 0;
        layout.topMargin = 0;
        root.addView(target, 0, layout);
        target.setWebViewClient(new WebViewClient() {
            private boolean printed;
            @Override
            public void onPageFinished(WebView view, String url) {
                if (printed) return;
                printed = true;
                view.postDelayed(() -> {
                    if (printWebView != view) return;
                    view.evaluateJavascript("(function(){try{return String((document.body&&document.body.innerHTML||'').length)}catch(e){return '0'}})()", value -> {
                        if (printWebView != view) return;
                        printWebViewDocument(view, jobName);
                        view.postDelayed(MainActivity.this::destroyPrintWebView, 120000L);
                    });
                }, 900L);
            }
        });
        target.loadDataWithBaseURL("https://greenman.local/print/", html, "text/html", "UTF-8", null);
    }'''

PRINT_NEW=r'''private void printWebViewDocument(WebView target, String requestedJobName) {
        try {
            android.print.PrintManager printManager =
                    (android.print.PrintManager) getSystemService(PRINT_SERVICE);
            String jobName = sanitizePrintJobName(requestedJobName);
            android.print.PrintAttributes attributes = new android.print.PrintAttributes.Builder()
                    .setMediaSize(android.print.PrintAttributes.MediaSize.ISO_A4)
                    .setMinMargins(android.print.PrintAttributes.Margins.NO_MARGINS)
                    .setColorMode(android.print.PrintAttributes.COLOR_MODE_COLOR)
                    .build();
            printManager.print(jobName, target.createPrintDocumentAdapter(jobName), attributes);
        } catch (Exception error) {
            Toast.makeText(this, "Printing could not be opened.", Toast.LENGTH_LONG).show();
        }
    }'''

def patch_java(src,dst):
    text=src.read_text(encoding='utf-8')
    old=extract_method(text,'private void openPrintDocument(')
    if not old: raise SystemExit('openPrintDocument missing; customer patch not applied')
    text=text.replace(old,OPEN_NEW,1)
    oldp=extract_method(text,'private void printWebViewDocument(')
    if not oldp: raise SystemExit('printWebViewDocument missing')
    text=text.replace(oldp,PRINT_NEW,1)
    dst.write_text(text,encoding='utf-8')


def main():
    if len(sys.argv) not in (3,5): raise SystemExit('usage IN.html OUT.html [IN.java OUT.java]')
    patch_html(Path(sys.argv[1]),Path(sys.argv[2]))
    if len(sys.argv)==5: patch_java(Path(sys.argv[3]),Path(sys.argv[4]))
    print('final print owner patched')
if __name__=='__main__': main()
