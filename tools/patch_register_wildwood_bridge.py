#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit("usage: patch_register_wildwood_bridge.py MainActivity.smali")
p=Path(sys.argv[1])
s=p.read_text(encoding="utf-8")

if 'const-string v4, "GMStockBridge"' in s:
    raise SystemExit("GMStockBridge already registered")

# Register beside the existing GreenmanFiles interface when present.
anchor='''    const-string v4, "GreenmanFiles"

    invoke-virtual {v0, v2, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V
'''
if s.count(anchor)!=1:
    raise SystemExit(f"GreenmanFiles registration anchor count: {s.count(anchor)}")
addition=anchor+'''
    iget-object v0, p0, Lcom/greenman/hedgewitchery/MainActivity;->webView:Landroid/webkit/WebView;

    new-instance v2, Lcom/greenman/hedgewitchery/WildwoodWebBridge;

    invoke-direct {v2, p0}, Lcom/greenman/hedgewitchery/WildwoodWebBridge;-><init>(Landroid/content/Context;)V

    const-string v4, "GMStockBridge"

    invoke-virtual {v0, v2, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V
'''
s=s.replace(anchor,addition,1)
if s.count('const-string v4, "GMStockBridge"')!=1:
    raise SystemExit("GMStockBridge registration failed")
p.write_text(s,encoding="utf-8")
print("registered GMStockBridge JavaScript interface")
