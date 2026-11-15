#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: install_fullscreen_bridge.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')

anchor = '''        @JavascriptInterface
        public void printDocument(String html, String requestedJobName) {
            runOnUiThread(() -> openPrintDocument(html, requestedJobName));
        }
'''
replacement = '''        @JavascriptInterface
        public void refreshImmersive() {
            runOnUiThread(() -> {
                enterImmersiveMode();
                if (webView != null) {
                    webView.postDelayed(MainActivity.this::enterImmersiveMode, 140L);
                    webView.postDelayed(MainActivity.this::enterImmersiveMode, 420L);
                }
            });
        }

        @JavascriptInterface
        public void printDocument(String html, String requestedJobName) {
            runOnUiThread(() -> openPrintDocument(html, requestedJobName));
        }
'''

count = s.count(anchor)
if count != 1:
    raise SystemExit(f'AndroidBridge printDocument anchor count was {count}, expected 1')

s = s.replace(anchor, replacement, 1)

if s.count('public void refreshImmersive()') != 1:
    raise SystemExit('refreshImmersive bridge was not installed exactly once')
if s.count('public void printDocument') != 1:
    raise SystemExit('printDocument owner count changed')
if 'nativePrintHtml' in s or 'gmNativePrintHtml' in s:
    raise SystemExit('old print relay found after fullscreen bridge install')

out.write_text(s, encoding='utf-8')
print('Installed fullscreen refresh bridge without changing the print owner')
