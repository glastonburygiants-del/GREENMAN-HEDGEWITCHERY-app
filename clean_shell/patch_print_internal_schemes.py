#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_print_internal_schemes.py MainActivity.java")

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
marker = "private final class PrintAssetWebViewClient extends WebViewClient {"
if marker not in text:
    raise SystemExit("PrintAssetWebViewClient marker missing")

head, tail = text.split(marker, 1)

old_request = '''            Uri uri = request.getUrl();
            if (!LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {'''
new_request = '''            Uri uri = request.getUrl();
            String scheme = uri.getScheme();
            if ("data".equalsIgnoreCase(scheme) || "about".equalsIgnoreCase(scheme) || "blob".equalsIgnoreCase(scheme)) {
                return null;
            }
            if (!LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {'''

if tail.count(old_request) != 1:
    raise SystemExit(f"expected exactly one print request gate, found {tail.count(old_request)}")
tail = tail.replace(old_request, new_request, 1)

old_navigation = '''        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            return !LOCAL_HOST.equalsIgnoreCase(request.getUrl().getHost());
        }'''
new_navigation = '''        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            String scheme = uri.getScheme();
            if ("data".equalsIgnoreCase(scheme) || "about".equalsIgnoreCase(scheme) || "blob".equalsIgnoreCase(scheme)) {
                return false;
            }
            return !LOCAL_HOST.equalsIgnoreCase(uri.getHost());
        }'''

if tail.count(old_navigation) != 1:
    raise SystemExit(f"expected exactly one print navigation gate, found {tail.count(old_navigation)}")
tail = tail.replace(old_navigation, new_navigation, 1)

patched = head + marker + tail

# Guardrails: the edit must live only after the print-client marker.
if '"data".equalsIgnoreCase(scheme)' in head:
    raise SystemExit("internal-scheme allowance leaked into main app WebView client")
if patched.count('"data".equalsIgnoreCase(scheme)') != 2:
    raise SystemExit("unexpected data: allowance count")
if patched.count('"about".equalsIgnoreCase(scheme)') != 2:
    raise SystemExit("unexpected about: allowance count")
if patched.count('"blob".equalsIgnoreCase(scheme)') != 2:
    raise SystemExit("unexpected blob: allowance count")

path.write_text(patched, encoding="utf-8")
print("Patched PrintAssetWebViewClient only: allowed data:, about:, blob: internal print documents.")
