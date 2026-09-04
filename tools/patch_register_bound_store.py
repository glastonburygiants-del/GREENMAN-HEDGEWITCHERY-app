#!/usr/bin/env python3
from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_register_bound_store.py MainActivity.smali")
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    anchor = """    invoke-virtual {v0, v2, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    .line 105
"""
    addition = """    invoke-virtual {v0, v2, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    iget-object v0, p0, Lcom/greenman/hedgewitchery/MainActivity;->webView:Landroid/webkit/WebView;

    new-instance v2, Lcom/greenman/hedgewitchery/BoundBookStore;

    invoke-direct {v2, p0}, Lcom/greenman/hedgewitchery/BoundBookStore;-><init>(Landroid/content/Context;)V

    const-string v4, "GreenmanFiles"

    invoke-virtual {v0, v2, v4}, Landroid/webkit/WebView;->addJavascriptInterface(Ljava/lang/Object;Ljava/lang/String;)V

    .line 105
"""
    if text.count(anchor) != 1:
        raise SystemExit(f"GreenmanAndroid registration anchor count: {text.count(anchor)}")
    text = text.replace(anchor, addition, 1)
    if text.count('const-string v4, "GreenmanFiles"') != 1:
        raise SystemExit("GreenmanFiles was not registered exactly once")
    path.write_text(text, encoding="utf-8")
    print("Registered native GreenmanFiles bridge without changing other APK bytecode.")


if __name__ == "__main__":
    main()
