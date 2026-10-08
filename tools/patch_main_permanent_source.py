#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 6:
    raise SystemExit("usage: patch_main_permanent_source.py MainActivity.java AndroidManifest.xml app/build.gradle strings.xml run_number")

java_path = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
gradle_path = Path(sys.argv[3])
strings_path = Path(sys.argv[4])
run_number = int(sys.argv[5])

java = java_path.read_text(encoding="utf-8")
manifest = manifest_path.read_text(encoding="utf-8")
gradle = gradle_path.read_text(encoding="utf-8")
strings = strings_path.read_text(encoding="utf-8")

def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)

# Permanent, side-by-side package for the clean source-built app.
gradle = re.sub(
    r'applicationId\s+"[^"]+"',
    'applicationId "com.greenman.hedgewitchery"',
    gradle,
    count=1,
)
gradle = re.sub(r'versionCode\s+\d+', f'versionCode {20000 + run_number}', gradle, count=1)
gradle = re.sub(r'versionName\s+"[^"]+"', f'versionName "PERMANENT-{run_number}"', gradle, count=1)

# Keep the Java namespace untouched while the install package gets a permanent identity.
manifest = once(
    manifest,
    'android:name=".MainActivity"',
    'android:name="com.greenman.hedgewitchery.MainActivity"',
    "MainActivity manifest name",
)
if 'android.permission.INTERNET' not in manifest:
    manifest = once(
        manifest,
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">',
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n\n    <uses-permission android:name="android.permission.INTERNET" />',
        "INTERNET permission",
    )

if 'com.greenman.hedgewitchery.apothecary.permission.WILDWOOD_BRIDGE' not in manifest:
    manifest = once(
        manifest,
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">',
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n\n    <permission android:name="com.greenman.hedgewitchery.apothecary.permission.WILDWOOD_BRIDGE" android:protectionLevel="signature" />\n    <queries><package android:name="com.greenman.hedgewitchery.stocktake" /></queries>',
        "Wildwood signature permission",
    )
if 'android:name="com.greenman.hedgewitchery.WildwoodBridgeProvider"' not in manifest:
    manifest = once(
        manifest,
        '    </application>',
        '        <provider android:name="com.greenman.hedgewitchery.WildwoodBridgeProvider" android:authorities="com.greenman.hedgewitchery.apothecary.wildwoodbridge" android:exported="true" android:readPermission="com.greenman.hedgewitchery.apothecary.permission.WILDWOOD_BRIDGE" android:writePermission="com.greenman.hedgewitchery.apothecary.permission.WILDWOOD_BRIDGE" />\n    </application>',
        "Wildwood provider",
    )

# Use the exact established Greenman app artwork, not the placeholder source-shell icon.
manifest, icon_n = re.subn(r'android:icon="[^"]+"', 'android:icon="@drawable/greenman_launcher_art"', manifest, count=1)
if icon_n != 1:
    raise SystemExit("launcher icon manifest attribute not found exactly once")
if 'android:roundIcon=' in manifest:
    manifest = re.sub(r'android:roundIcon="[^"]+"', 'android:roundIcon="@drawable/greenman_launcher_art"', manifest, count=1)

strings, n = re.subn(
    r'(<string\s+name="app_name"[^>]*>).*?(</string>)',
    r'\1Greenman HedgeWitchery Apothecary\2',
    strings,
    count=1,
    flags=re.S,
)
if n != 1:
    raise SystemExit("app_name string not found exactly once")

# Acer/Android 13 safety: only enter immersive mode after a content view exists.
java = once(
    java,
    '''        requestWindowFeature(Window.FEATURE_NO_TITLE);
        enterImmersiveMode();

        root = new FrameLayout(this);''',
    '''        requestWindowFeature(Window.FEATURE_NO_TITLE);

        root = new FrameLayout(this);''',
    "early immersive call",
)
java = once(
    java,
    '''        setContentView(root);

        webView = new WebView(this);''',
    '''        setContentView(root);
        enterImmersiveMode();

        webView = new WebView(this);''',
    "post-content immersive call",
)

# Current Book of Shadows native PDF owner.
java = once(
    java,
    '''        webView.addJavascriptInterface(new AndroidBridge(), "GreenmanAndroid");
        webView.setWebViewClient(new LocalAssetWebViewClient());''',
    '''        webView.addJavascriptInterface(new AndroidBridge(), "GreenmanAndroid");
        webView.addJavascriptInterface(new BoundBookStore(this), "GreenmanFiles");
        webView.addJavascriptInterface(new WildwoodBridge(this), "GreenmanWildwood");
        webView.setWebViewClient(new LocalAssetWebViewClient());''',
    "GreenmanFiles bridge",
)

# Let the WebView make the app's Supabase fetch/XHR calls. Everything else stays blocked.
java = once(
    java,
    '''            Uri uri = request.getUrl();
            if (!LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {
                return blockedResponse();
            }

            String path = uri.getPath();''',
    '''            Uri uri = request.getUrl();
            String requestHost = uri.getHost();
            if (requestHost != null && (
                    requestHost.equalsIgnoreCase("zzfgufuyetybxaeidcxu.supabase.co")
                            || requestHost.toLowerCase(Locale.ROOT).endsWith(".supabase.co"))) {
                return super.shouldInterceptRequest(view, request);
            }
            if (!LOCAL_HOST.equalsIgnoreCase(requestHost)) {
                return blockedResponse();
            }

            String path = uri.getPath();''',
    "Supabase request allowlist",
)

# Checkout and PayPal deliberately leave the embedded app and open in the device browser.
java = once(
    java,
    '''            if (LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {
                return false;
            }
            return true;''',
    '''            String host = uri.getHost();
            if (LOCAL_HOST.equalsIgnoreCase(host)) {
                return false;
            }
            if (host != null && (
                    host.equalsIgnoreCase("greenmanhedgewitchery.co.uk")
                            || host.equalsIgnoreCase("www.greenmanhedgewitchery.co.uk")
                            || host.equalsIgnoreCase("paypal.com")
                            || host.toLowerCase(Locale.ROOT).endsWith(".paypal.com"))) {
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception ignored) {
                    Toast.makeText(MainActivity.this, "The secure payment page could not be opened.", Toast.LENGTH_LONG).show();
                }
                return true;
            }
            return true;''',
    "external checkout browser",
)

java = once(
    java,
    '''            webView.removeJavascriptInterface("GreenmanAndroid");
            webView.destroy();''',
    '''            webView.removeJavascriptInterface("GreenmanAndroid");
            webView.removeJavascriptInterface("GreenmanFiles");
            webView.removeJavascriptInterface("GreenmanWildwood");
            webView.destroy();''',
    "bridge cleanup",
)

# Hard checks: do not emit a partially patched native shell.
for marker in [
    'new BoundBookStore(this), "GreenmanFiles"',
    'new WildwoodBridge(this), "GreenmanWildwood"',
    'zzfgufuyetybxaeidcxu.supabase.co',
    'greenmanhedgewitchery.co.uk',
    'endsWith(".paypal.com")',
    'setContentView(root);\n        enterImmersiveMode();',
]:
    if marker not in java:
        raise SystemExit("missing Java marker: " + marker)

if 'android.permission.INTERNET' not in manifest:
    raise SystemExit("INTERNET permission missing after patch")
if 'WildwoodBridgeProvider' not in manifest or 'permission.WILDWOOD_BRIDGE' not in manifest:
    raise SystemExit("Wildwood bridge manifest wiring missing after patch")
if 'android:icon="@drawable/greenman_launcher_art"' not in manifest:
    raise SystemExit("Greenman launcher art is not wired as the app icon")
if 'applicationId "com.greenman.hedgewitchery"' not in gradle:
    raise SystemExit("existing-package applicationId missing after patch")

manifest, n_icon = re.subn(r'android:icon="[^"]+"', 'android:icon="@drawable/greenman_launcher_art"', manifest, count=1)
if n_icon != 1:
    raise SystemExit("launcher icon manifest field missing")
manifest, n_round = re.subn(r'android:roundIcon="[^"]+"', 'android:roundIcon="@drawable/greenman_launcher_art"', manifest, count=1)
if n_round != 1:
    raise SystemExit("round launcher icon manifest field missing")

java_path.write_text(java, encoding="utf-8")
manifest_path.write_text(manifest, encoding="utf-8")
gradle_path.write_text(gradle, encoding="utf-8")
strings_path.write_text(strings, encoding="utf-8")
print(f"Patched permanent clean-source main app version PERMANENT-{run_number}.")
