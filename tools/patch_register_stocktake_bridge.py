#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv)!=2:
    raise SystemExit("usage: patch_register_stocktake_bridge.py MainActivity.smali")
p=Path(sys.argv[1]); s=p.read_text(encoding="utf-8")
if 'const-string v4, "WildwoodBridge"' in s:
    raise SystemExit("WildwoodBridge already registered")

anchor='''    invoke-virtual {v0, v2, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    .line 105
'''
if s.count(anchor)!=1:
    raise SystemExit(f"base JavaScript-interface anchor count: {s.count(anchor)}")
addition='''    invoke-virtual {v0, v2, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    iget-object v0, p0, Lcom/greenman/hedgewitchery/MainActivity;->webView:Landroid/webkit/WebView;

    new-instance v2, Lcom/greenman/hedgewitchery/StocktakeWildwoodClient;

    invoke-direct {v2, p0}, Lcom/greenman/hedgewitchery/StocktakeWildwoodClient;-><init>(Landroid/content/Context;)V

    const-string v4, "WildwoodBridge"

    invoke-virtual {v0, v2, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    .line 105
'''
s=s.replace(anchor,addition,1)
if s.count('const-string v4, "WildwoodBridge"')!=1:
    raise SystemExit("WildwoodBridge registration failed")
p.write_text(s,encoding="utf-8")
print("registered Stocktake WildwoodBridge JavaScript interface")
