#!/usr/bin/env python3
"""Fix: sale checkout fetch() to Supabase silently fails ("Failed to fetch").

Real-device report: tapping Checkout in the Journal sales basket showed
"Failed to fetch" under a clean Wi-Fi connection (confirmed capable of
streaming video at the same time), and a direct Supabase log query for
that exact time window showed the request never arrived at the edge
function at all - not even as an error. That rules out a network or
backend-side problem entirely: the request was blocked before it ever
left the device.

Root cause confirmed by reading MainActivity$LocalAssetWebViewClient
directly: shouldInterceptRequest() runs for every resource request the
page makes - not just top-level page navigation (that's
shouldOverrideUrlLoading, already patched separately for the PayPal
redirect) - and it unconditionally returns blockedResponse() for any
host that isn't exactly "greenman.local". That includes fetch()/XHR
calls, so the sales code's fetch() to
https://zzfgufuyetybxaeidcxu.supabase.co/functions/v1/shop-create-order
was being silently blocked by the app's own request filter, before any
network layer ever saw it - exactly matching "Failed to fetch" with
nothing in Supabase's own logs.

Fix: when the request host isn't greenman.local, check whether it ends
with "supabase.co" (case-insensitive); if so, return null so the
WebView handles the request normally over the real network instead of
blocking it. Every other external host keeps the original behavior:
blocked exactly as before. This is the same pass-through pattern
already used for paypal.com in shouldOverrideUrlLoading, applied here
to the resource-request filter that governs fetch()/XHR.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_supabase_fetch_allowlist.py MainActivity$LocalAssetWebViewClient.smali')

target = Path(sys.argv[1])
text = target.read_text(encoding='utf-8')
original = text

anchor = (
    '.method public shouldInterceptRequest(Landroid/webkit/WebView;Landroid/webkit/WebResourceRequest;)Landroid/webkit/WebResourceResponse;\n'
    '    .locals 9\n'
    '    .param p1, "view"    # Landroid/webkit/WebView;\n'
    '    .param p2, "request"    # Landroid/webkit/WebResourceRequest;\n'
    '\n'
    '    .line 115\n'
    '    invoke-interface {p2}, Landroid/webkit/WebResourceRequest;->getUrl()Landroid/net/Uri;\n'
    '\n'
    '    move-result-object v0\n'
    '\n'
    '    .line 116\n'
    '    .local v0, "uri":Landroid/net/Uri;\n'
    '    const-string v1, "greenman.local"\n'
    '\n'
    '    invoke-virtual {v0}, Landroid/net/Uri;->getHost()Ljava/lang/String;\n'
    '\n'
    '    move-result-object v2\n'
    '\n'
    '    invoke-virtual {v1, v2}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z\n'
    '\n'
    '    move-result v1\n'
    '\n'
    '    if-nez v1, :cond_0'
)

replacement = (
    anchor + '\n'
    '\n'
    '    if-eqz v2, :cond_supabase_blocked\n'
    '\n'
    '    const-string v3, "supabase.co"\n'
    '\n'
    '    invoke-virtual {v2}, Ljava/lang/String;->toLowerCase()Ljava/lang/String;\n'
    '\n'
    '    move-result-object v4\n'
    '\n'
    '    invoke-virtual {v4, v3}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z\n'
    '\n'
    '    move-result v3\n'
    '\n'
    '    if-eqz v3, :cond_supabase_blocked\n'
    '\n'
    '    const/4 v5, 0x0\n'
    '\n'
    '    return-object v5\n'
    '\n'
    '    :cond_supabase_blocked'
)

count = text.count(anchor)
if count != 1:
    raise SystemExit(f'shouldInterceptRequest anchor: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

if text == original:
    raise SystemExit('no change applied')

target.write_text(text, encoding='utf-8')
print('shouldInterceptRequest now lets *.supabase.co resource requests (fetch/XHR) through to the real network; every other external host remains blocked exactly as before')
