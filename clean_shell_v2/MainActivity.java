package com.greenman.hedgewitchery;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.webkit.JavascriptInterface;
import android.webkit.MimeTypeMap;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;

import java.io.ByteArrayInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URLConnection;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final String LOCAL_HOST = "greenman.local";
    private static final String START_URL = "https://" + LOCAL_HOST + "/index.html";
    private static final int FILE_CHOOSER_REQUEST = 4107;

    private FrameLayout root;
    private WebView webView;
    private GreenmanChromeClient chromeClient;
    private ValueCallback<Uri[]> fileChooserCallback;
    private View customView;
    private WebChromeClient.CustomViewCallback customViewCallback;
    private WebView printWebView;
    private int printSerial;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        enterImmersiveMode();

        root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(42, 26, 8));
        setContentView(root);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(42, 26, 8));
        root.addView(webView, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        configureWebView();

        if (savedInstanceState == null) {
            webView.loadUrl(START_URL);
        } else {
            webView.restoreState(savedInstanceState);
        }
    }

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    private void configureWebView() {
        WebView.setWebContentsDebuggingEnabled(false);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccess(true);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setSupportZoom(false);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);

        webView.addJavascriptInterface(new AndroidBridge(), "GreenmanAndroid");
        webView.setWebViewClient(new LocalAssetWebViewClient());
        chromeClient = new GreenmanChromeClient();
        webView.setWebChromeClient(chromeClient);
        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) ->
                handleDownload(url, contentDisposition, mimeType));
    }

    private final class LocalAssetWebViewClient extends WebViewClient {
        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            if (!LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {
                return blockedResponse();
            }

            String path = uri.getPath();
            if (path == null || path.isEmpty() || "/".equals(path)) {
                path = "/index.html";
            }
            if (path.contains("..")) {
                return blockedResponse();
            }

            String assetPath = path.startsWith("/") ? path.substring(1) : path;
            try {
                InputStream stream = getAssets().open(assetPath);
                String mime = guessMimeType(assetPath);
                String encoding = isTextMime(mime) ? "UTF-8" : null;
                WebResourceResponse response = new WebResourceResponse(mime, encoding, stream);
                response.setStatusCodeAndReasonPhrase(200, "OK");
                return response;
            } catch (IOException missing) {
                return blockedResponse();
            }
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            if (LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {
                return false;
            }
            return true;
        }

        @Override
        public void onPageStarted(WebView view, String url, Bitmap favicon) {
            super.onPageStarted(view, url, favicon);
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            installRuntimeBridge();
        }
    }

    private final class GreenmanChromeClient extends WebChromeClient {
        @Override
        public boolean onShowFileChooser(
                WebView webView,
                ValueCallback<Uri[]> filePathCallback,
                FileChooserParams fileChooserParams) {
            if (fileChooserCallback != null) {
                fileChooserCallback.onReceiveValue(null);
            }
            fileChooserCallback = filePathCallback;

            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("*/*");
            intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{
                    "application/json",
                    "text/plain",
                    "text/html",
                    "text/csv",
                    "application/zip",
                    "application/pdf",
                    "image/*"
            });
            try {
                startActivityForResult(intent, FILE_CHOOSER_REQUEST);
                return true;
            } catch (Exception error) {
                fileChooserCallback = null;
                Toast.makeText(MainActivity.this, "No file picker is available.", Toast.LENGTH_LONG).show();
                return false;
            }
        }

        @Override
        public void onShowCustomView(View view, CustomViewCallback callback) {
            if (customView != null) {
                callback.onCustomViewHidden();
                return;
            }
            customView = view;
            customViewCallback = callback;
            webView.setVisibility(View.GONE);
            root.addView(view, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT));
            enterImmersiveMode();
        }

        @Override
        public void onHideCustomView() {
            if (customView == null) {
                return;
            }
            root.removeView(customView);
            customView = null;
            webView.setVisibility(View.VISIBLE);
            if (customViewCallback != null) {
                customViewCallback.onCustomViewHidden();
                customViewCallback = null;
            }
            enterImmersiveMode();
        }
    }

    private void installRuntimeBridge() {
        /*
         * ONE PRINT OWNER ONLY.
         *
         * The HTML app keeps complete ownership of page/pack construction and fitting.
         * This bridge only catches the browser print() call from whichever same-origin
         * document actually issued it, freezes that live document, and hands it once to
         * Android. No A4 builder, scale, page break or pack logic lives in this shell.
         */
        String script = "(function(){"
                + "if(window.__greenmanSingleNativeOwnerInstalled)return;"
                + "window.__greenmanSingleNativeOwnerInstalled=true;"
                + "var nativeBridge=window.GreenmanAndroid;"
                + "function safeName(n){return n||('greenman-export-'+Date.now());}"
                + "function copyFormState(src,dst){"
                + "try{var a=src.querySelectorAll('input,textarea,select'),b=dst.querySelectorAll('input,textarea,select');"
                + "for(var i=0;i<a.length&&i<b.length;i++){var x=a[i],y=b[i],tag=(x.tagName||'').toLowerCase();"
                + "if(tag==='textarea'){y.textContent=x.value||'';}"
                + "else if(tag==='select'){for(var j=0;j<x.options.length&&j<y.options.length;j++){if(x.options[j].selected)y.options[j].setAttribute('selected','selected');else y.options[j].removeAttribute('selected');}}"
                + "else{y.setAttribute('value',x.value||'');if(x.checked)y.setAttribute('checked','checked');else y.removeAttribute('checked');}}}catch(_e){}"
                + "}"
                + "function freezeFrames(srcDoc,cloneRoot){"
                + "try{var src=srcDoc.querySelectorAll('iframe'),dst=cloneRoot.querySelectorAll('iframe');"
                + "for(var i=0;i<src.length&&i<dst.length;i++){try{var idoc=src[i].contentDocument;"
                + "if(!idoc||!idoc.documentElement)continue;var ic=idoc.documentElement.cloneNode(true);copyFormState(idoc,ic);freezeFrames(idoc,ic);"
                + "var ih=ic.querySelector('head');if(ih&&!ih.querySelector('base')){var ib=ic.ownerDocument.createElement('base');ib.setAttribute('href',idoc.baseURI||srcDoc.baseURI||'https://greenman.local/index.html');ih.insertBefore(ib,ih.firstChild);}"
                + "dst[i].removeAttribute('src');dst[i].setAttribute('srcdoc','<!doctype html>'+ic.outerHTML);"
                + "}catch(_e){}}}catch(_e){}"
                + "}"
                + "function freeze(doc){"
                + "var clone=doc.documentElement.cloneNode(true);copyFormState(doc,clone);freezeFrames(doc,clone);"
                + "var head=clone.querySelector('head');if(head&&!head.querySelector('base')){var base=clone.ownerDocument.createElement('base');base.setAttribute('href',doc.baseURI||'https://greenman.local/index.html');head.insertBefore(base,head.firstChild);}"
                + "return '<!doctype html>'+clone.outerHTML;"
                + "}"
                + "function install(win,doc){"
                + "if(!win||!doc||!doc.documentElement)return;"
                + "if(!doc.__greenmanDownloadBridge){doc.__greenmanDownloadBridge=true;"
                + "doc.addEventListener('click',function(e){var a=e.target&&e.target.closest?e.target.closest('a[download]'):null;if(!a)return;"
                + "var u=a.href||'';if(!(u.indexOf('blob:')===0||u.indexOf('data:')===0))return;e.preventDefault();"
                + "fetch(u).then(function(r){return r.blob();}).then(function(b){var fr=new FileReader();fr.onloadend=function(){var z=String(fr.result||'');var k=z.indexOf(',');nativeBridge.saveBase64(safeName(a.download),b.type||'application/octet-stream',k>=0?z.slice(k+1):z);};fr.readAsDataURL(b);})"
                + ".catch(function(){nativeBridge.showMessage('The export could not be saved.');});},true);}"
                + "function hookFrame(f){try{if(!f.__greenmanLoadHook){f.__greenmanLoadHook=true;f.addEventListener('load',function(){try{install(f.contentWindow,f.contentDocument);}catch(_e){}});}}catch(_e){}try{install(f.contentWindow,f.contentDocument);}catch(_e){}}"
                + "if(!doc.__greenmanCreateElementHook){doc.__greenmanCreateElementHook=true;var create=doc.createElement.bind(doc);doc.createElement=function(){var el=create.apply(doc,arguments);try{if(String(arguments[0]||'').toLowerCase()==='iframe')hookFrame(el);}catch(_e){}return el;};}"
                + "if(!win.__greenmanNativePrintOwner){win.__greenmanNativePrintOwner=true;try{win.__greenmanOriginalPrint=win.print;"
                + "win.print=function(){if(win.__greenmanNativePrintBusy)return;win.__greenmanNativePrintBusy=true;"
                + "try{var ev;try{ev=new Event('beforeprint');}catch(_e){ev=doc.createEvent('Event');ev.initEvent('beforeprint',true,true);}win.dispatchEvent(ev);}catch(_e){}"
                + "var send=function(){try{nativeBridge.printDocument(freeze(doc),doc.title||'Greenman HedgeWitchery');}catch(err){nativeBridge.showMessage('The print document could not be sent to Android.');}"
                + "setTimeout(function(){try{var ev2;try{ev2=new Event('afterprint');}catch(_e){ev2=doc.createEvent('Event');ev2.initEvent('afterprint',true,true);}win.dispatchEvent(ev2);}catch(_e){}win.__greenmanNativePrintBusy=false;},120);};"
                + "try{win.requestAnimationFrame(function(){win.requestAnimationFrame(function(){setTimeout(send,20);});});}catch(_e){setTimeout(send,70);}" 
                + "};}catch(_e){}}"
                + "function scan(){try{Array.prototype.forEach.call(doc.querySelectorAll('iframe'),hookFrame);}catch(_e){}}scan();"
                + "if(!doc.__greenmanFrameObserver){try{doc.__greenmanFrameObserver=new MutationObserver(scan);doc.__greenmanFrameObserver.observe(doc.documentElement,{childList:true,subtree:true});}catch(_e){}}"
                + "}"
                + "install(window,document);"
                + "})();";
        webView.evaluateJavascript(script, null);
    }

    private final class AndroidBridge {
        @JavascriptInterface
        public void saveBase64(String requestedName, String mimeType, String base64Data) {
            runOnUiThread(() -> saveDecodedDownload(requestedName, mimeType, base64Data));
        }

        @JavascriptInterface
        public void showMessage(String message) {
            runOnUiThread(() -> Toast.makeText(MainActivity.this, message, Toast.LENGTH_LONG).show());
        }

        @JavascriptInterface
        public void printDocument(String html, String requestedJobName) {
            runOnUiThread(() -> openPrintDocument(html, requestedJobName));
        }
    }

    private final class PrintAssetWebViewClient extends WebViewClient {
        private final int serial;
        private boolean sent;

        PrintAssetWebViewClient(int serial) {
            this.serial = serial;
        }

        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            String scheme = uri.getScheme();
            if ("data".equalsIgnoreCase(scheme) || "about".equalsIgnoreCase(scheme) || "blob".equalsIgnoreCase(scheme)) {
                return null;
            }
            if (!LOCAL_HOST.equalsIgnoreCase(uri.getHost())) {
                return blockedResponse();
            }
            String path = uri.getPath();
            if (path == null || path.isEmpty() || "/".equals(path)) {
                path = "/index.html";
            }
            if (path.contains("..")) {
                return blockedResponse();
            }
            String assetPath = path.startsWith("/") ? path.substring(1) : path;
            try {
                InputStream stream = getAssets().open(assetPath);
                String mime = guessMimeType(assetPath);
                String encoding = isTextMime(mime) ? "UTF-8" : null;
                WebResourceResponse response = new WebResourceResponse(mime, encoding, stream);
                response.setStatusCodeAndReasonPhrase(200, "OK");
                return response;
            } catch (IOException missing) {
                return blockedResponse();
            }
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            String scheme = uri.getScheme();
            if ("data".equalsIgnoreCase(scheme) || "about".equalsIgnoreCase(scheme) || "blob".equalsIgnoreCase(scheme)) {
                return false;
            }
            return !LOCAL_HOST.equalsIgnoreCase(uri.getHost());
        }

        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            if (sent || view != printWebView || serial != printSerial) {
                return;
            }
            sent = true;
            view.postDelayed(() -> {
                if (view == printWebView && serial == printSerial) {
                    printWebViewDocument(view, "Greenman HedgeWitchery");
                }
            }, 850L);
        }
    }

    private void openPrintDocument(String html, String requestedJobName) {
        if (html == null || html.trim().length() < 80) {
            Toast.makeText(this, "The print document was empty.", Toast.LENGTH_LONG).show();
            return;
        }

        destroyPrintWebView();
        final int serial = ++printSerial;
        final String jobName = sanitizePrintJobName(requestedJobName);
        final WebView target = new WebView(this);
        printWebView = target;

        target.setTag(jobName);
        target.setBackgroundColor(Color.WHITE);
        target.setAlpha(1.0f);
        target.setVisibility(View.VISIBLE);
        target.setFocusable(false);
        target.setClickable(false);

        WebSettings settings = target.getSettings();
        settings.setJavaScriptEnabled(false);
        settings.setDomStorageEnabled(false);
        settings.setDatabaseEnabled(false);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setSupportZoom(false);
        settings.setUseWideViewPort(false);
        settings.setLoadWithOverviewMode(false);
        settings.setTextZoom(100);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);

        target.setWebViewClient(new PrintAssetWebViewClient(serial));
        target.setWebChromeClient(new WebChromeClient());

        FrameLayout.LayoutParams layout = new FrameLayout.LayoutParams(820, 1120);
        layout.leftMargin = 0;
        layout.topMargin = 0;
        root.addView(target, 0, layout);

        target.loadDataWithBaseURL(START_URL, ensurePrintViewport(html), "text/html", "UTF-8", null);
    }

    private static String ensurePrintViewport(String html) {
        String lower = html.toLowerCase(Locale.ROOT);
        if (lower.contains("name=\"viewport\"") || lower.contains("name='viewport'")) {
            return html;
        }
        String meta = "<meta name=\"viewport\" content=\"width=820, initial-scale=1.0, maximum-scale=1.0, user-scalable=no\">";
        int head = lower.indexOf("<head>");
        if (head >= 0) {
            int at = head + 6;
            return html.substring(0, at) + meta + html.substring(at);
        }
        return meta + html;
    }

    private void printWebViewDocument(WebView target, String fallbackJobName) {
        try {
            android.print.PrintManager printManager =
                    (android.print.PrintManager) getSystemService(PRINT_SERVICE);
            Object tag = target.getTag();
            String jobName = sanitizePrintJobName(tag instanceof String ? (String) tag : fallbackJobName);
            android.print.PrintAttributes attributes = new android.print.PrintAttributes.Builder()
                    .setMediaSize(android.print.PrintAttributes.MediaSize.ISO_A4)
                    .setMinMargins(android.print.PrintAttributes.Margins.NO_MARGINS)
                    .setColorMode(android.print.PrintAttributes.COLOR_MODE_COLOR)
                    .build();
            printManager.print(jobName, target.createPrintDocumentAdapter(jobName), attributes);
            target.postDelayed(() -> {
                if (printWebView == target) {
                    destroyPrintWebView();
                }
            }, 120000L);
        } catch (Exception error) {
            Toast.makeText(this, "Printing could not be opened.", Toast.LENGTH_LONG).show();
        }
    }

    private static String sanitizePrintJobName(String requestedJobName) {
        String name = requestedJobName == null ? "Greenman HedgeWitchery" : requestedJobName.trim();
        name = name.replaceAll("[\\r\\n\\t\\p{Cntrl}]", " ").replaceAll("\\s+", " ");
        if (name.isEmpty()) {
            name = "Greenman HedgeWitchery";
        }
        return name.length() > 80 ? name.substring(0, 80) : name;
    }

    private void destroyPrintWebView() {
        WebView target = printWebView;
        printWebView = null;
        if (target == null) {
            return;
        }
        try {
            if (target.getParent() instanceof ViewGroup) {
                ((ViewGroup) target.getParent()).removeView(target);
            }
            target.stopLoading();
            target.setWebChromeClient(null);
            target.setWebViewClient(null);
            target.destroy();
        } catch (Exception ignored) {
        }
    }

    private void handleDownload(String url, String contentDisposition, String mimeType) {
        String name = extractDownloadName(contentDisposition, mimeType);
        if (url == null) {
            return;
        }
        if (url.startsWith("data:")) {
            int comma = url.indexOf(',');
            if (comma < 0) {
                return;
            }
            String header = url.substring(5, comma);
            String data = url.substring(comma + 1);
            boolean base64 = header.contains(";base64");
            String detectedMime = header.split(";", 2)[0];
            if (detectedMime.isEmpty()) {
                detectedMime = mimeType;
            }
            if (base64) {
                saveDecodedDownload(name, detectedMime, data);
            } else {
                byte[] bytes = Uri.decode(data).getBytes(StandardCharsets.UTF_8);
                saveBytesToDownloads(name, detectedMime, bytes);
            }
        } else if (url.startsWith("blob:")) {
            String js = "fetch(" + quoteJs(url) + ").then(r=>r.blob()).then(b=>{const f=new FileReader();"
                    + "f.onloadend=()=>{const s=String(f.result||'');GreenmanAndroid.saveBase64("
                    + quoteJs(name) + ",b.type||" + quoteJs(mimeType) + ",s.substring(s.indexOf(',')+1));};"
                    + "f.readAsDataURL(b);});";
            webView.evaluateJavascript(js, null);
        } else {
            Toast.makeText(this, "Only offline Greenman files can be downloaded in this app.", Toast.LENGTH_LONG).show();
        }
    }

    private void saveDecodedDownload(String requestedName, String mimeType, String base64Data) {
        try {
            byte[] bytes = Base64.decode(base64Data, Base64.DEFAULT);
            saveBytesToDownloads(requestedName, mimeType, bytes);
        } catch (Exception error) {
            Toast.makeText(this, "The export could not be decoded.", Toast.LENGTH_LONG).show();
        }
    }

    private void saveBytesToDownloads(String requestedName, String mimeType, byte[] bytes) {
        String safeName = sanitizeFileName(requestedName, mimeType);
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, safeName);
        values.put(MediaStore.Downloads.MIME_TYPE,
                mimeType == null || mimeType.isEmpty() ? "application/octet-stream" : mimeType);
        values.put(MediaStore.Downloads.RELATIVE_PATH,
                Environment.DIRECTORY_DOWNLOADS + "/Greenman HedgeWitchery");
        values.put(MediaStore.Downloads.IS_PENDING, 1);

        Uri uri = null;
        try {
            uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) {
                throw new IOException("Download destination was unavailable.");
            }
            try (OutputStream output = getContentResolver().openOutputStream(uri)) {
                if (output == null) {
                    throw new IOException("Download stream was unavailable.");
                }
                output.write(bytes);
                output.flush();
            }
            ContentValues complete = new ContentValues();
            complete.put(MediaStore.Downloads.IS_PENDING, 0);
            getContentResolver().update(uri, complete, null, null);
            Toast.makeText(this, "Saved to Downloads/Greenman HedgeWitchery/" + safeName,
                    Toast.LENGTH_LONG).show();
        } catch (Exception error) {
            if (uri != null) {
                getContentResolver().delete(uri, null, null);
            }
            Toast.makeText(this, "The file could not be saved.", Toast.LENGTH_LONG).show();
        }
    }

    private static String extractDownloadName(String contentDisposition, String mimeType) {
        if (contentDisposition != null) {
            String lower = contentDisposition.toLowerCase(Locale.ROOT);
            int index = lower.indexOf("filename=");
            if (index >= 0) {
                String name = contentDisposition.substring(index + 9).trim();
                if (name.startsWith("\"") && name.endsWith("\"") && name.length() > 1) {
                    name = name.substring(1, name.length() - 1);
                }
                if (!name.isEmpty()) {
                    return name;
                }
            }
        }
        return "greenman-export-" + new SimpleDateFormat("yyyyMMdd-HHmmss", Locale.UK).format(new Date())
                + extensionForMime(mimeType);
    }

    private static String sanitizeFileName(String requestedName, String mimeType) {
        String name = requestedName == null ? "greenman-export" : requestedName.trim();
        name = name.replaceAll("[\\\\/:*?\"<>|\\p{Cntrl}]", "_");
        if (name.isEmpty()) {
            name = "greenman-export";
        }
        if (!name.contains(".")) {
            name += extensionForMime(mimeType);
        }
        return name;
    }

    private static String extensionForMime(String mimeType) {
        if (mimeType == null) {
            return ".bin";
        }
        String ext = MimeTypeMap.getSingleton().getExtensionFromMimeType(mimeType);
        return ext == null || ext.isEmpty() ? ".bin" : "." + ext;
    }

    private static String quoteJs(String value) {
        if (value == null) {
            return "''";
        }
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'")
                .replace("\r", "\\r").replace("\n", "\\n") + "'";
    }

    private WebResourceResponse blockedResponse() {
        return new WebResourceResponse(
                "text/plain",
                "UTF-8",
                403,
                "Blocked",
                java.util.Collections.emptyMap(),
                new ByteArrayInputStream(new byte[0]));
    }

    private static String guessMimeType(String path) {
        String guessed = URLConnection.guessContentTypeFromName(path);
        if (guessed != null) {
            return guessed;
        }
        String extension = MimeTypeMap.getFileExtensionFromUrl(path);
        String mapped = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension);
        return mapped == null ? "application/octet-stream" : mapped;
    }

    private static boolean isTextMime(String mime) {
        return mime.startsWith("text/") || mime.contains("javascript") || mime.contains("json")
                || mime.contains("xml") || mime.contains("svg");
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != FILE_CHOOSER_REQUEST || fileChooserCallback == null) {
            return;
        }
        Uri[] result = null;
        if (resultCode == RESULT_OK && data != null && data.getData() != null) {
            result = new Uri[]{data.getData()};
        }
        fileChooserCallback.onReceiveValue(result);
        fileChooserCallback = null;
    }

    @Override
    public void onBackPressed() {
        if (customView != null) {
            chromeClient.onHideCustomView();
            return;
        }
        webView.evaluateJavascript(
                "(function(){try{if(typeof window.gmAndroidBack==='function')return String(!!window.gmAndroidBack());}catch(e){}return 'false';})()",
                value -> {
                    boolean handled = value != null && (value.contains("true") || value.contains("\\\"true\\\""));
                    if (handled) {
                        return;
                    }
                    if (webView.canGoBack()) {
                        webView.goBack();
                    } else {
                        finish();
                    }
                });
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }

    @Override
    protected void onResume() {
        super.onResume();
        webView.onResume();
        enterImmersiveMode();
    }

    @Override
    protected void onPause() {
        webView.onPause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        destroyPrintWebView();
        if (webView != null) {
            webView.loadUrl("about:blank");
            webView.stopLoading();
            webView.setWebChromeClient(null);
            webView.setWebViewClient(null);
            webView.removeJavascriptInterface("GreenmanAndroid");
            webView.destroy();
        }
        super.onDestroy();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            enterImmersiveMode();
        }
    }

    private void enterImmersiveMode() {
        if (android.os.Build.VERSION.SDK_INT >= 30) {
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.hide(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                controller.setSystemBarsBehavior(
                        WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                            | View.SYSTEM_UI_FLAG_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
        }
    }
}
