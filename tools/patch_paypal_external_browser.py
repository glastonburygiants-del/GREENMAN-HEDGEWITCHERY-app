#!/usr/bin/env python3
"""Fix: PayPal checkout silently does nothing.

Real-code confirmed cause: MainActivity$LocalAssetWebViewClient.shouldOverrideUrlLoading()
allows navigation only when the URL's host is exactly "greenman.local" (the
local-asset origin); every other host, including paypal.com, returns true
("I'm handling this navigation myself") but takes no further action at all.
So even with android.permission.INTERNET now present, the JS checkout code's
`window.top.location.href = approvalUrl` silently does nothing on-device -
no error, no navigation, nothing visible happens.

This also happens to be the right fix for the Play Protect "harmful app"
classification: Google's scanner treats an app that quietly redirects its
own embedded WebView to a payment page as a phishing-pattern red flag.
The recommended, safer pattern is to hand payment URLs to the device's own
browser via a normal external Intent instead of navigating in-app.

Fix: when the navigation host isn't greenman.local, allow only known payment
hosts to leave the app through Intent.ACTION_VIEW:
- *.paypal.com
- this project's exact Supabase host, zzfgufuyetybxaeidcxu.supabase.co\n- the public checkout host, greenmanhedgewitchery.co.uk

This lets the new Greenman card checkout page open in the device's real browser
without weakening the WebView allowlist generally. Every other external host
remains silently blocked exactly as before.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_paypal_external_browser.py MainActivity$LocalAssetWebViewClient.smali')

target = Path(sys.argv[1])
text = target.read_text(encoding='utf-8')
original = text

anchor = (
    ".method public shouldOverrideUrlLoading(Landroid/webkit/WebView;Landroid/webkit/WebResourceRequest;)Z\n"
    "    .locals 3\n"
    "    .param p1, \"view\"    # Landroid/webkit/WebView;\n"
    "    .param p2, \"request\"    # Landroid/webkit/WebResourceRequest;\n"
    "\n"
    "    .line 143\n"
    "    invoke-interface {p2}, Landroid/webkit/WebResourceRequest;->getUrl()Landroid/net/Uri;\n"
    "\n"
    "    move-result-object v0\n"
    "\n"
    "    .line 144\n"
    "    .local v0, \"uri\":Landroid/net/Uri;\n"
    "    const-string v1, \"greenman.local\"\n"
    "\n"
    "    invoke-virtual {v0}, Landroid/net/Uri;->getHost()Ljava/lang/String;\n"
    "\n"
    "    move-result-object v2\n"
    "\n"
    "    invoke-virtual {v1, v2}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z\n"
    "\n"
    "    move-result v1\n"
    "\n"
    "    if-eqz v1, :cond_0\n"
    "\n"
    "    .line 145\n"
    "    const/4 v1, 0x0\n"
    "\n"
    "    return v1\n"
    "\n"
    "    .line 147\n"
    "    :cond_0\n"
    "    const/4 v1, 0x1\n"
    "\n"
    "    return v1\n"
    ".end method\n"
)

replacement = (
    ".method public shouldOverrideUrlLoading(Landroid/webkit/WebView;Landroid/webkit/WebResourceRequest;)Z\n"
    "    .locals 5\n"
    "    .param p1, \"view\"    # Landroid/webkit/WebView;\n"
    "    .param p2, \"request\"    # Landroid/webkit/WebResourceRequest;\n"
    "\n"
    "    .line 143\n"
    "    invoke-interface {p2}, Landroid/webkit/WebResourceRequest;->getUrl()Landroid/net/Uri;\n"
    "\n"
    "    move-result-object v0\n"
    "\n"
    "    .line 144\n"
    "    .local v0, \"uri\":Landroid/net/Uri;\n"
    "    const-string v1, \"greenman.local\"\n"
    "\n"
    "    invoke-virtual {v0}, Landroid/net/Uri;->getHost()Ljava/lang/String;\n"
    "\n"
    "    move-result-object v2\n"
    "\n"
    "    invoke-virtual {v1, v2}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z\n"
    "\n"
    "    move-result v1\n"
    "\n"
    "    if-eqz v1, :cond_0\n"
    "\n"
    "    .line 145\n"
    "    const/4 v1, 0x0\n"
    "\n"
    "    return v1\n"
    "\n"
    "    .line 147\n"
    "    :cond_0\n"
    "    if-eqz v2, :cond_1\n"
    "\n"
    "    const-string v3, \"paypal.com\"\n"
    "\n"
    "    invoke-virtual {v2}, Ljava/lang/String;->toLowerCase()Ljava/lang/String;\n"
    "\n"
    "    move-result-object v4\n"
    "\n"
    "    invoke-virtual {v4, v3}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z\n"
    "\n"
    "    move-result v3\n"
    "\n"
    "    if-nez v3, :launch_external\n"
    "\n"
    "    const-string v3, \"zzfgufuyetybxaeidcxu.supabase.co\"\n"
    "\n"
    "    invoke-virtual {v3, v2}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z\n"
    "\n"
    "    move-result v3\n"
    "\n"
    "    if-nez v3, :launch_external\n"
    "\n"
    "    const-string v3, \"greenmanhedgewitchery.co.uk\"\n"
    "\n"
    "    invoke-virtual {v3, v2}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z\n"
    "\n"
    "    move-result v3\n"
    "\n"
    "    if-eqz v3, :cond_1\n"
    "\n"
    "    :launch_external\n"
    "    new-instance v3, Landroid/content/Intent;\n"
    "\n"
    "    const-string v4, \"android.intent.action.VIEW\"\n"
    "\n"
    "    invoke-direct {v3, v4, v0}, Landroid/content/Intent;-><init>(Ljava/lang/String;Landroid/net/Uri;)V\n"
    "\n"
    "    iget-object v4, p0, Lcom/greenman/hedgewitchery/MainActivity$LocalAssetWebViewClient;->this$0:Lcom/greenman/hedgewitchery/MainActivity;\n"
    "\n"
    "    invoke-virtual {v4, v3}, Lcom/greenman/hedgewitchery/MainActivity;->startActivity(Landroid/content/Intent;)V\n"
    "\n"
    "    :cond_1\n"
    "    const/4 v1, 0x1\n"
    "\n"
    "    return v1\n"
    ".end method\n"
)

count = text.count(anchor)
if count != 1:
    raise SystemExit(f'shouldOverrideUrlLoading anchor: expected exactly 1 occurrence, found {count}')
text = text.replace(anchor, replacement, 1)

if text == original:
    raise SystemExit('no change applied')

target.write_text(text, encoding='utf-8')
print('shouldOverrideUrlLoading now routes *.paypal.com, the exact Greenman Supabase project host, and greenmanhedgewitchery.co.uk to the external browser; all other external hosts remain blocked')
