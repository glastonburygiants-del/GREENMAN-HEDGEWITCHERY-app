#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_wildwood_stock_bridge_html.py input.html output.html")

src=Path(sys.argv[1]); dst=Path(sys.argv[2])
text=src.read_text(encoding="utf-8")
marker="gm-wildwood-stock-bridge-v1"
if marker in text:
    raise SystemExit("Wildwood bridge HTML patch already present")

script=r'''
<script id="gm-wildwood-stock-bridge-v1">
(function(){
'use strict';
const STOCK='gm_admin_stock_v1';
const LOG='gm_stock_deduction_log';
const MODE='gm_app_mode';
const MASTER='gm_master_mode';
const APPLIED='gm_wildwood_bridge_revision_v1';

function nativeBridge(){
  try{return window.GMStockBridge&&typeof window.GMStockBridge.publish==='function'?window.GMStockBridge:null}catch(_e){return null}
}
function ls(k,fallback){
  try{const v=localStorage.getItem(k);return v==null?fallback:v}catch(_e){return fallback}
}
function applyPending(){
  const b=nativeBridge(); if(!b||typeof b.pending!=='function')return;
  try{
    const p=JSON.parse(String(b.pending()||'{}'));
    const revision=Number(p&&p.revision||0);
    const stock=String(p&&p.stock_json||'');
    const applied=Number(ls(APPLIED,'0')||0);
    if(!revision||revision<=applied||!stock)return;
    const parsed=JSON.parse(stock);
    if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))return;
    localStorage.setItem(STOCK,JSON.stringify(parsed));
    localStorage.setItem(APPLIED,String(revision));
    try{if(typeof b.acknowledge==='function')b.acknowledge(revision)}catch(_e){}
    try{window.dispatchEvent(new CustomEvent('gm-wildwood-stock-bridge-update',{detail:{revision:revision}}))}catch(_e){}
  }catch(_e){}
}
function publish(){
  const b=nativeBridge();if(!b)return;
  applyPending();
  try{
    b.publish(
      ls(STOCK,'{}'),
      ls(LOG,'[]'),
      ls(MODE,''),
      ls(MASTER,'0')
    );
  }catch(_e){}
}
window.GM_WILDWOOD_STOCK_BRIDGE_REFRESH=publish;
setInterval(publish,1000);
window.addEventListener('focus',publish);
document.addEventListener('visibilitychange',function(){if(!document.hidden)publish()});
window.addEventListener('storage',function(e){
  if(!e||[STOCK,LOG,MODE,MASTER].indexOf(e.key)>=0)publish();
});
setTimeout(publish,50);
setTimeout(publish,500);
})();
</script>
'''
pos=text.rfind("</body>")
if pos<0:
    raise SystemExit("outer </body> not found")
text=text[:pos]+script+"\n"+text[pos:]

for required in (
    marker,
    "gm_admin_stock_v1",
    "gm_stock_deduction_log",
    "GMStockBridge",
    "gm-wildwood-stock-bridge-update",
):
    if required not in text:
        raise SystemExit("missing bridge marker: "+required)

dst.write_text(text,encoding="utf-8")
print("patched main app Wildwood stock bridge HTML")
