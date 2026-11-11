package com.greenman.hedgewitchery.stocktake;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

public final class MainActivity extends Activity {
    private static final int EXPORT_DOCUMENT_REQUEST = 7011;
    private WebView webView;
    private byte[] pendingExportBytes;
    private String pendingExportMime;

    // Only exports CSV and JSON after Android's own save-file picker is shown.
    // No storage permission, external JavaScript, or access to arbitrary files.
    private final class StocktakeExportBridge {
        @JavascriptInterface
        public void saveFile(String filename, String contents, String mime) {
            if (filename == null || contents == null || mime == null) return;
            boolean csv = "text/csv".equals(mime) && filename.endsWith(".csv");
            boolean json = "application/json".equals(mime) && filename.endsWith(".json");
            if (!csv && !json) return;
            if (!filename.startsWith("GREENMAN_") || filename.length() > 128) return;

            final byte[] bytes = contents.getBytes(StandardCharsets.UTF_8);
            if (bytes.length > 2_000_000) return;
            final String safeFilename = filename.replaceAll("[^A-Za-z0-9._-]", "_");

            runOnUiThread(() -> {
                // The WebView loads only our packaged stocktake document.
                String page = webView == null ? null : webView.getUrl();
                if (page == null || !page.startsWith("file:///android_asset/")) return;
                if (pendingExportBytes != null) {
                    Toast.makeText(MainActivity.this, "Finish the current save first.", Toast.LENGTH_SHORT).show();
                    return;
                }
                pendingExportBytes = bytes;
                pendingExportMime = mime;
                Intent picker = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                picker.addCategory(Intent.CATEGORY_OPENABLE);
                picker.setType(mime);
                picker.putExtra(Intent.EXTRA_TITLE, safeFilename);
                try {
                    startActivityForResult(picker, EXPORT_DOCUMENT_REQUEST);
                } catch (Exception ex) {
                    pendingExportBytes = null;
                    pendingExportMime = null;
                    Toast.makeText(MainActivity.this, "Cannot open the save-file picker.", Toast.LENGTH_LONG).show();
                }
            });
        }
    }

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
        s.setAllowContentAccess(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setSupportZoom(false);

        // The name is versioned to avoid collisions with the app's stock-sync bridges.
        webView.addJavascriptInterface(new StocktakeExportBridge(), "GreenmanStocktakeExportV1");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, android.webkit.WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme();
                if ("file".equalsIgnoreCase(scheme)) return false;
                if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
                    try {
                        startActivity(new Intent(Intent.ACTION_VIEW, uri));
                    } catch (Exception ignored) {}
                    return true;
                }
                return false;
            }
        });

        webView.loadUrl("file:///android_asset/index.html");
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != EXPORT_DOCUMENT_REQUEST) return;

        byte[] bytes = pendingExportBytes;
        String mime = pendingExportMime;
        pendingExportBytes = null;
        pendingExportMime = null;
        if (resultCode != RESULT_OK || data == null || data.getData() == null || bytes == null) return;

        try (OutputStream output = getContentResolver().openOutputStream(data.getData())) {
            if (output == null) throw new IllegalStateException("No writable document stream");
            // Excel and other spreadsheet viewers can recognise UTF-8 stock names.
            if ("text/csv".equals(mime)) output.write(new byte[]{(byte)0xEF, (byte)0xBB, (byte)0xBF});
            output.write(bytes);
            output.flush();
            Toast.makeText(this, "Stocktake file saved.", Toast.LENGTH_LONG).show();
        } catch (Exception ex) {
            Toast.makeText(this, "File save failed. Your stocktake data is unchanged.", Toast.LENGTH_LONG).show();
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
