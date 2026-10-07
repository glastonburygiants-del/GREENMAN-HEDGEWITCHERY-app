package com.greenman.hedgewitchery.stocktake;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import org.json.JSONObject;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private static final String MAIN_APP_PACKAGE = "com.greenman.hedgewitchery.apothecary";
    private static final Uri MAIN_WILDWOOD_URI = Uri.parse("content://com.greenman.hedgewitchery.apothecary.wildwoodbridge");
    private WebView webView;
    private WebView printWebView;

    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        setContentView(webView);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setAllowUniversalAccessFromFileURLs(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);

        webView.addJavascriptInterface(new StocktakeBridge(), "GreenmanStocktake");
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme() == null ? "" : uri.getScheme();
                if ("file".equalsIgnoreCase(scheme)) return false;
                if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
                    try {
                        startActivity(new Intent(Intent.ACTION_VIEW, uri));
                        return true;
                    } catch (Exception ignored) {
                        return false;
                    }
                }
                return false;
            }
        });

        webView.loadUrl("file:///android_asset/index.html");
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    private final class StocktakeBridge {
        @JavascriptInterface
        public boolean mainAppInstalled() {
            try {
                return getPackageManager().getLaunchIntentForPackage(MAIN_APP_PACKAGE) != null;
            } catch (Exception ignored) {
                return false;
            }
        }

        @JavascriptInterface
        public String readMainWildwood() {
            try {
                Bundle b = getContentResolver().call(MAIN_WILDWOOD_URI, "read", null, null);
                JSONObject o = new JSONObject();
                o.put("installed", true);
                o.put("ready", b != null && b.getBoolean("ready", false));
                o.put("revision", b == null ? 0 : b.getLong("revision", 0));
                o.put("stock_json", b == null ? "{}" : b.getString("stock_json", "{}"));
                o.put("log_json", b == null ? "[]" : b.getString("log_json", "[]"));
                o.put("updated_at", b == null ? 0 : b.getLong("updated_at", 0));
                return o.toString();
            } catch (Exception error) {
                try {
                    JSONObject o = new JSONObject();
                    o.put("installed", mainAppInstalled());
                    o.put("ready", false);
                    o.put("error", error.getClass().getSimpleName());
                    return o.toString();
                } catch (Exception ignored) {
                    return "{\"installed\":false,\"ready\":false}";
                }
            }
        }

        @JavascriptInterface
        public String writeMainWildwood(String stockJson, String logJson) {
            try {
                Bundle in = new Bundle();
                in.putString("stock_json", stockJson == null ? "{}" : stockJson);
                in.putString("log_json", logJson == null ? "[]" : logJson);
                Bundle b = getContentResolver().call(MAIN_WILDWOOD_URI, "write", null, in);
                JSONObject o = new JSONObject();
                o.put("ok", b != null && b.getBoolean("ok", false));
                o.put("revision", b == null ? 0 : b.getLong("revision", 0));
                return o.toString();
            } catch (Exception error) {
                try {
                    JSONObject o = new JSONObject();
                    o.put("ok", false);
                    o.put("error", error.getClass().getSimpleName());
                    return o.toString();
                } catch (Exception ignored) {
                    return "{\"ok\":false}";
                }
            }
        }

        @JavascriptInterface
        public boolean openMainApp() {
            try {
                Intent launch = getPackageManager().getLaunchIntentForPackage(MAIN_APP_PACKAGE);
                if (launch == null) return false;
                launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(launch);
                return true;
            } catch (Exception ignored) {
                return false;
            }
        }

        @JavascriptInterface
        public void printHtml(final String html, final String jobName) {
            runOnUiThread(() -> {
                printWebView = new WebView(MainActivity.this);
                printWebView.getSettings().setJavaScriptEnabled(false);
                printWebView.setWebViewClient(new WebViewClient() {
                    @Override
                    public void onPageFinished(WebView view, String url) {
                        PrintManager pm = (PrintManager) getSystemService(Context.PRINT_SERVICE);
                        PrintDocumentAdapter adapter = view.createPrintDocumentAdapter(
                                jobName == null || jobName.trim().isEmpty() ? "Greenman Stocktake" : jobName
                        );
                        PrintAttributes attrs = new PrintAttributes.Builder()
                                .setMediaSize(new PrintAttributes.MediaSize(
                                        "GREENMAN_57MM_90MM",
                                        "57 mm x 90 mm",
                                        2244,
                                        3543))
                                .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                                .build();
                        pm.print("Greenman Stocktake", adapter, attrs);
                    }
                });
                printWebView.loadDataWithBaseURL(
                        "file:///android_asset/",
                        html,
                        "text/html",
                        "UTF-8",
                        null
                );
            });
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) webView.destroy();
        if (printWebView != null) printWebView.destroy();
        super.onDestroy();
    }
}
