#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_main_wildwood_same_device.py input.html output.html")

src=Path(sys.argv[1]); dst=Path(sys.argv[2])
text=src.read_text(encoding="utf-8")
if "gm-wildwood-native-bridge-v1" in text:
    raise SystemExit("Wildwood same-device bridge already present")

script=r'''
<script id="gm-wildwood-native-bridge-v1">
(function(){
  'use strict';
  if(window.__gmWildwoodNativeBridgeV1)return;
  window.__gmWildwoodNativeBridgeV1=true;
  var STOCK='gm_admin_stock_v1', LOG='gm_stock_deduction_log', REV='gm_wildwood_bridge_rev_v1';
  var lastCanon='';

  function canon(){
    var s='{}',l='[]';
    try{s=localStorage.getItem(STOCK)||'{}'}catch(_e){}
    try{l=localStorage.getItem(LOG)||'[]'}catch(_e){}
    return {stock:s,log:l,key:s+'\n'+l};
  }
  function nativeSnapshot(){
    try{
      if(!window.GreenmanWildwood||!window.GreenmanWildwood.getSnapshot)return null;
      return JSON.parse(String(window.GreenmanWildwood.getSnapshot()||'{}'));
    }catch(_e){return null}
  }
  function saveNative(c){
    try{
      var r=JSON.parse(String(window.GreenmanWildwood.saveSnapshot(c.stock,c.log)||'{}'));
      if(r&&r.ok){
        localStorage.setItem(REV,String(Number(r.revision||0)));
        lastCanon=c.key;
        return true;
      }
    }catch(_e){}
    return false;
  }
  function applyNative(n){
    try{
      JSON.parse(n.stock_json||'{}');
      JSON.parse(n.log_json||'[]');
      localStorage.setItem(STOCK,n.stock_json||'{}');
      localStorage.setItem(LOG,n.log_json||'[]');
      localStorage.setItem(REV,String(Number(n.revision||0)));
      lastCanon=(n.stock_json||'{}')+'\n'+(n.log_json||'[]');
      try{window.dispatchEvent(new CustomEvent('gm:wildwood-stock-bridge-update',{detail:{revision:Number(n.revision||0)}}))}catch(_e){}
      return true;
    }catch(_e){return false}
  }
  function tick(){
    try{
      if(!window.GreenmanWildwood)return;
      var n=nativeSnapshot(),c=canon(),seen=Number(localStorage.getItem(REV)||0);
      if(n&&n.ready&&Number(n.revision||0)>seen){
        applyNative(n);
        return;
      }
      if(!n||!n.ready||c.key!==lastCanon){
        saveNative(c);
      }
    }catch(_e){}
  }
  window.gmOpenStocktake=function(){
    try{return !!(window.GreenmanWildwood&&window.GreenmanWildwood.openStocktake&&window.GreenmanWildwood.openStocktake())}catch(_e){return false}
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(tick,250)});
  else setTimeout(tick,250);
  setInterval(tick,1200);
})();
</script>
'''
anchor='</body></html>'
pos=text.rfind(anchor)
if pos<0:
    raise SystemExit("closing body/html anchor not found")
text=text[:pos]+script+'\n'+text[pos:]
for marker in ['gm-wildwood-native-bridge-v1','gm_admin_stock_v1','gm_stock_deduction_log','GreenmanWildwood','gmOpenStocktake']:
    if marker not in text:
        raise SystemExit('missing '+marker)
dst.write_text(text,encoding='utf-8')
print('added same-device Wildwood bridge sync to main app')
