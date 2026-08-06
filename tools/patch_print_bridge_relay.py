#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


HELPER = r'''<script id="gm-native-print-relay-v1">
(function(){
  if(window.gmAppPrintHtml)return;
  window.gmAppPrintHtml=function(html,title){
    try{
      if(parent&&typeof parent.gmNativePrintHtml==='function'){
        return !!parent.gmNativePrintHtml(String(html||''),String(title||'Greenman HedgeWitchery'));
      }
    }catch(_e){}
    try{
      parent.postMessage({source:'greenman-new-shell-v1',cmd:'nativePrintHtml',html:String(html||''),title:String(title||'Greenman HedgeWitchery')},'*');
      return true;
    }catch(_e2){}
    return false;
  };
})();
<\/script>
'''

OUTER_RELAY = r'''window.gmNativePrintHtml=function(html,title){
  try{
    if(window.GreenmanAndroid&&typeof window.GreenmanAndroid.printHtml==='function'){
      window.GreenmanAndroid.printHtml(String(html||''),String(title||'Greenman HedgeWitchery'));
      return true;
    }
  }catch(e){try{console.error(e)}catch(_e){}}
  return false;
};
'''


def patch_page(page: str, page_name: str) -> str:
    if 'gm-native-print-relay-v1' not in page:
        if '</head>' not in page:
            raise SystemExit(f'{page_name}: head closing tag missing')
        page = page.replace('</head>', HELPER + '</head>', 1)

    page = page.replace(
        "window.GreenmanAndroid&&typeof window.GreenmanAndroid.printHtml==='function'",
        "typeof window.gmAppPrintHtml==='function'",
    )
    page = page.replace(
        'window.GreenmanAndroid.printHtml(',
        'window.gmAppPrintHtml(',
    )

    if 'window.GreenmanAndroid.printHtml(' in page:
        raise SystemExit(f'{page_name}: direct iframe Android call remains')
    return page


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit('Usage: patch_print_bridge_relay.py INPUT.html OUTPUT.html')

    src, dst = map(Path, sys.argv[1:])
    text = src.read_text(encoding='utf-8')
    marker = 'const PAGES = '
    start = text.index(marker) + len(marker)
    pages, used = json.JSONDecoder().raw_decode(text[start:])
    end = start + used

    for page_name in ('spellBuilder', 'journal', 'bos'):
        pages[page_name] = patch_page(pages[page_name], page_name)

    encoded = json.dumps(pages, ensure_ascii=False, separators=(',', ':'))
    encoded = re.sub(r'</script', r'<\\/script', encoded, flags=re.IGNORECASE)

    tail = text[end:]
    listener_anchor = "window.addEventListener('message', ev=>{"
    if 'window.gmNativePrintHtml=function' not in tail:
        position = tail.find(listener_anchor)
        if position < 0:
            raise SystemExit('Outer app message listener missing')
        tail = tail[:position] + OUTER_RELAY + tail[position:]

    old_gate = "if(m.source!=='greenman-new-shell-v1') return;"
    new_gate = (
        "if(m.source!=='greenman-new-shell-v1') return;\n"
        "  if(m.cmd==='nativePrintHtml'){gmNativePrintHtml(m.html,m.title);return;}"
    )
    if "m.cmd==='nativePrintHtml'" not in tail:
        if tail.count(old_gate) != 1:
            raise SystemExit(f'Outer source gate count was {tail.count(old_gate)}')
        tail = tail.replace(old_gate, new_gate, 1)

    output = text[:start] + encoded + tail

    required = [
        'gm-native-print-relay-v1',
        'window.gmNativePrintHtml=function',
        "m.cmd==='nativePrintHtml'",
        'window.gmAppPrintHtml(',
    ]
    missing = [item for item in required if item not in output]
    if missing:
        raise SystemExit('Print relay requirements missing: ' + ', '.join(missing))

    dst.write_text(output, encoding='utf-8')
    print(
        'Print relay passed: embedded Summary, Lite, Journal and BoS pages now hand '
        'completed HTML to the outer Android bridge.'
    )


if __name__ == '__main__':
    main()
