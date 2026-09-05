package com.greenman.hedgewitchery;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.RandomAccessFile;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.Properties;

/**
 * Renders a gathered BoS package in an isolated Android process.
 *
 * Only one 794 x 1123 HTML page, one RGB_565 bitmap and one JPEG are alive at a
 * time. The PDF is streamed to disk, so a large illustrated book never becomes
 * one enormous JavaScript canvas or byte array.
 */
public final class ScribePdfService extends Service {
    public static final String ACTION_RENDER =
            "com.greenman.hedgewitchery.action.RENDER_SCRIBE_PDF";

    private static final String CHANNEL_ID = "greenman_bos_renderer";
    private static final int NOTIFICATION_ID = 46029;
    private static final int CSS_WIDTH = 794;
    private static final int CSS_HEIGHT = 1123;
    private static final int IMAGE_WIDTH = 1191;
    private static final int IMAGE_HEIGHT = 1685;
    private static final long PAGE_READY_TIMEOUT_MS = 8000L;

    private final Handler main = new Handler(Looper.getMainLooper());
    private WebView webView;
    private File activeDirectory;
    private File outputPart;
    private FlatPdfWriter pdfWriter;
    private Properties meta;
    private String css = "";
    private String jobId = "";
    private String storageKey = "";
    private String title = "Book of Shadows";
    private String scriptName = "Original English";
    private String fileName = "Greenman_Book_of_Shadows.pdf";
    private String kind = "bind";
    private int pageCount;
    private int pageIndex;
    private long pageLoadStarted;
    private long jobStarted;
    private boolean running;
    private boolean finishing;
    private boolean pageScheduled;

    @Override
    public void onCreate() {
        super.onCreate();
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            try {
                WebView.setDataDirectorySuffix("bosrender");
            } catch (Throwable ignored) {
            }
        }
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        startForeground(NOTIFICATION_ID, notification("Starting Book of Shadows PDF", 0, 1));
        if (intent == null || !ACTION_RENDER.equals(intent.getAction())) {
            stopSelf(startId);
            return START_NOT_STICKY;
        }
        if (!running) {
            running = true;
            main.post(this::beginRender);
        }
        return START_REDELIVER_INTENT;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        destroyWebView();
        closeWriter();
        super.onDestroy();
    }

    private void beginRender() {
        try {
            activeDirectory = new File(
                    BoundBookStore.rootDirectory(this), BoundBookStore.ACTIVE_DIRECTORY);
            File metaFile = new File(activeDirectory, BoundBookStore.META_NAME);
            File styleFile = new File(activeDirectory, BoundBookStore.STYLE_NAME);
            if (!metaFile.isFile() || !styleFile.isFile()) {
                throw new IllegalStateException("The gathered BoS package is incomplete");
            }
            meta = new Properties();
            try (FileInputStream in = new FileInputStream(metaFile)) {
                meta.load(in);
            }
            jobId = meta.getProperty("jobId", "job");
            storageKey = meta.getProperty("storageKey", "bound-original");
            title = meta.getProperty("title", "Book of Shadows");
            scriptName = meta.getProperty("scriptName", "Original English");
            fileName = meta.getProperty("fileName", "Greenman_Book_of_Shadows.pdf");
            kind = meta.getProperty("kind", "bind");
            pageCount = Integer.parseInt(meta.getProperty("pageCount", "0"));
            if (pageCount < 1 || pageCount > 2000) {
                throw new IllegalStateException("The BoS page count is invalid");
            }
            css = readUtf8(styleFile);
            if (css.isEmpty()) throw new IllegalStateException("The BoS page style is empty");
            if (cancelRequested()) {
                cancelRender();
                return;
            }
            for (int i = 0; i < pageCount; i++) {
                if (!BoundBookStore.pageFile(activeDirectory, i).isFile()) {
                    throw new IllegalStateException("A gathered BoS page is missing");
                }
            }

            outputPart = new File(BoundBookStore.rootDirectory(this),
                    "render-" + BoundBookStore.safeToken(jobId, "job") + ".pdf.part");
            if (outputPart.exists() && !outputPart.delete()) {
                throw new IllegalStateException("The temporary PDF could not be replaced");
            }
            pdfWriter = new FlatPdfWriter(outputPart, pageCount);
            jobStarted = System.currentTimeMillis();
            pageIndex = 0;
            createWebView();
            updateStatus("rendering", 0, "Preparing page 1 of " + pageCount, 0L);
            updateNotification("Preparing page 1 of " + pageCount, 0, pageCount);
            renderNextPage();
        } catch (Throwable error) {
            fail(error);
        }
    }

    private void createWebView() {
        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(244, 236, 216));
        webView.setLayerType(WebView.LAYER_TYPE_SOFTWARE, null);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(false);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(false);
        settings.setBlockNetworkLoads(true);
        settings.setLoadsImagesAutomatically(true);
        settings.setDefaultTextEncodingName("utf-8");
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setTextZoom(100);
        settings.setUseWideViewPort(true);
        settings.setLoadWithOverviewMode(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setBuiltInZoomControls(false);
        settings.setSupportZoom(false);
        webView.setHorizontalScrollBarEnabled(false);
        webView.setVerticalScrollBarEnabled(false);
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(
                    WebView view, WebResourceRequest request) {
                String scheme = request.getUrl() == null ? "" : request.getUrl().getScheme();
                if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
                    return new WebResourceResponse("text/plain", "utf-8",
                            new ByteArrayInputStream(new byte[0]));
                }
                return super.shouldInterceptRequest(view, request);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                main.postDelayed(ScribePdfService.this::checkPageReady, 80L);
            }
        });
    }

    private void renderNextPage() {
        if (cancelRequested()) {
            cancelRender();
            return;
        }
        if (pageIndex >= pageCount) {
            completeRender();
            return;
        }
        try {
            File pageFile = BoundBookStore.pageFile(activeDirectory, pageIndex);
            String fragment = readUtf8(pageFile);
            if (fragment.isEmpty()) throw new IllegalStateException(
                    "A4 page " + (pageIndex + 1) + " is empty");
            pageLoadStarted = System.currentTimeMillis();
            pageScheduled = false;
            String document = "<!doctype html><html><head><meta charset=\"utf-8\">"
                    + "<meta name=\"viewport\" content=\"width=" + CSS_WIDTH
                    + ",initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no\">"
                    + "<style>" + css + "</style></head><body>" + fragment
                    + "<script>(function(){var done=function(){document.documentElement.setAttribute('data-gm-ready','1')};"
                    + "var waits=Array.prototype.map.call(document.images,function(i){if(i.complete)return Promise.resolve();return new Promise(function(r){i.onload=r;i.onerror=r})});"
                    + "try{if(document.fonts&&document.fonts.ready)waits.push(document.fonts.ready)}catch(e){}"
                    + "Promise.race([Promise.all(waits),new Promise(function(r){setTimeout(r,5000)})]).then(function(){requestAnimationFrame(function(){requestAnimationFrame(done)})},done)})();</script>"
                    + "</body></html>";
            webView.loadDataWithBaseURL("file:///android_asset/", document,
                    "text/html", "utf-8", null);
        } catch (Throwable error) {
            fail(error);
        }
    }

    private void checkPageReady() {
        if (finishing || webView == null || pageScheduled) return;
        if (cancelRequested()) {
            cancelRender();
            return;
        }
        webView.evaluateJavascript(
                "document.documentElement.getAttribute('data-gm-ready')||''",
                value -> {
                    if (finishing) return;
                    boolean ready = value != null && value.contains("1");
                    boolean timedOut = System.currentTimeMillis() - pageLoadStarted
                            >= PAGE_READY_TIMEOUT_MS;
                    if (ready || timedOut) {
                        if (pageScheduled) return;
                        pageScheduled = true;
                        main.postDelayed(this::drawCurrentPage, 55L);
                    } else {
                        main.postDelayed(this::checkPageReady, 100L);
                    }
                });
    }

    private void drawCurrentPage() {
        if (finishing || webView == null) return;
        if (cancelRequested()) {
            cancelRender();
            return;
        }
        Bitmap bitmap = null;
        File jpeg = null;
        try {
            int widthSpec = android.view.View.MeasureSpec.makeMeasureSpec(
                    CSS_WIDTH, android.view.View.MeasureSpec.EXACTLY);
            int heightSpec = android.view.View.MeasureSpec.makeMeasureSpec(
                    CSS_HEIGHT, android.view.View.MeasureSpec.EXACTLY);
            webView.measure(widthSpec, heightSpec);
            webView.layout(0, 0, CSS_WIDTH, CSS_HEIGHT);
            bitmap = Bitmap.createBitmap(
                    IMAGE_WIDTH, IMAGE_HEIGHT, Bitmap.Config.RGB_565);
            Canvas canvas = new Canvas(bitmap);
            canvas.drawColor(Color.rgb(244, 236, 216));
            canvas.scale((float) IMAGE_WIDTH / CSS_WIDTH,
                    (float) IMAGE_HEIGHT / CSS_HEIGHT);
            webView.draw(canvas);

            jpeg = new File(activeDirectory,
                    String.format(Locale.US, "page-%04d.jpg", pageIndex));
            int quality = pageCount > 300 ? 72 : (pageCount > 120 ? 74 : 77);
            try (FileOutputStream out = new FileOutputStream(jpeg, false)) {
                if (!bitmap.compress(Bitmap.CompressFormat.JPEG, quality, out)) {
                    throw new IllegalStateException(
                            "A4 page " + (pageIndex + 1) + " could not be compressed");
                }
                out.flush();
            }
            bitmap.recycle();
            bitmap = null;
            pdfWriter.addJpegPage(jpeg, IMAGE_WIDTH, IMAGE_HEIGHT);
            jpeg.delete();
            jpeg = null;

            pageIndex++;
            long elapsed = System.currentTimeMillis() - jobStarted;
            String message = pageIndex >= pageCount
                    ? "Finishing the PDF"
                    : "Rendered page " + pageIndex + " of " + pageCount;
            updateStatus("rendering", pageIndex, message, 0L);
            updateNotification(message, pageIndex, pageCount);
            main.postDelayed(this::renderNextPage, 30L);
        } catch (Throwable error) {
            if (bitmap != null && !bitmap.isRecycled()) bitmap.recycle();
            if (jpeg != null && jpeg.exists()) jpeg.delete();
            fail(error);
        }
    }

    private void completeRender() {
        if (finishing) return;
        finishing = true;
        try {
            pdfWriter.finish();
            pdfWriter = null;
            BoundBookStore.atomicReplace(outputPart,
                    BoundBookStore.bookFile(this, storageKey));
            File stable = BoundBookStore.bookFile(this, storageKey);
            updateStatus("ready", pageCount,
                    scriptName + " Book of Shadows is ready", stable.length());
            updateNotification(scriptName + " Book of Shadows is ready",
                    pageCount, pageCount);
            BoundBookStore.deleteRecursively(activeDirectory);
            destroyWebView();
            stopForeground(false);
            main.postDelayed(this::stopSelf, 4500L);
        } catch (Throwable error) {
            finishing = false;
            fail(error);
        }
    }

    private void cancelRender() {
        if (finishing) return;
        finishing = true;
        closeWriter();
        if (outputPart != null && outputPart.exists()) outputPart.delete();
        updateStatus("cancelled", pageIndex,
                "The unfinished conversion was discarded", 0L);
        updateNotification("Book of Shadows conversion cancelled", pageIndex, pageCount);
        BoundBookStore.deleteRecursively(activeDirectory);
        destroyWebView();
        stopForeground(true);
        stopSelf();
    }

    private void fail(Throwable error) {
        if (finishing) return;
        finishing = true;
        closeWriter();
        if (outputPart != null && outputPart.exists()) outputPart.delete();
        String message = error == null || error.getMessage() == null
                ? "The background PDF renderer stopped"
                : error.getMessage();
        updateStatus("error", pageIndex, message, 0L);
        updateNotification("Book of Shadows PDF could not be completed",
                pageIndex, Math.max(1, pageCount));
        BoundBookStore.deleteRecursively(activeDirectory);
        destroyWebView();
        stopForeground(true);
        stopSelf();
    }

    private boolean cancelRequested() {
        return activeDirectory != null
                && new File(activeDirectory, BoundBookStore.CANCEL_NAME).exists();
    }

    private void updateStatus(String state, int done, String message, long pdfBytes) {
        BoundBookStore.writeStatus(this, state, done, pageCount, jobId,
                storageKey, title, scriptName, fileName, kind, message, pdfBytes);
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "Book of Shadows PDF", NotificationManager.IMPORTANCE_LOW);
        channel.setDescription("Background binding and Scribe text conversion progress");
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) manager.createNotificationChannel(channel);
    }

    private Notification notification(String text, int done, int total) {
        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);
        builder.setContentTitle("Greenman Book of Shadows")
                .setContentText(text)
                .setSmallIcon(getApplicationInfo().icon)
                .setOnlyAlertOnce(true)
                .setOngoing(done < total)
                .setProgress(Math.max(1, total), Math.max(0, done), total <= 1);
        return builder.build();
    }

    private void updateNotification(String text, int done, int total) {
        NotificationManager manager =
                (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (manager != null) manager.notify(
                NOTIFICATION_ID, notification(text, done, Math.max(1, total)));
    }

    private void destroyWebView() {
        if (webView == null) return;
        try {
            webView.stopLoading();
            webView.loadUrl("about:blank");
            webView.clearHistory();
            webView.removeAllViews();
            webView.destroy();
        } catch (Throwable ignored) {
        }
        webView = null;
    }

    private void closeWriter() {
        if (pdfWriter == null) return;
        try {
            pdfWriter.close();
        } catch (Throwable ignored) {
        }
        pdfWriter = null;
    }

    private static String readUtf8(File file) throws Exception {
        long length = file.length();
        if (length < 0L || length > 80L * 1024L * 1024L) {
            throw new IllegalStateException("A gathered BoS page is too large");
        }
        byte[] bytes = new byte[(int) length];
        int offset = 0;
        try (FileInputStream in = new FileInputStream(file)) {
            while (offset < bytes.length) {
                int count = in.read(bytes, offset, bytes.length - offset);
                if (count < 0) break;
                offset += count;
            }
        }
        if (offset != bytes.length) throw new IllegalStateException("A BoS page was incomplete");
        return new String(bytes, StandardCharsets.UTF_8);
    }

    /** Minimal streaming image-only A4 PDF writer. */
    private static final class FlatPdfWriter implements AutoCloseable {
        private final RandomAccessFile file;
        private final long[] offsets;
        private final int totalPages;
        private int pagesWritten;
        private boolean closed;

        FlatPdfWriter(File target, int pageCount) throws Exception {
            totalPages = pageCount;
            offsets = new long[3 + pageCount * 3];
            file = new RandomAccessFile(target, "rw");
            file.setLength(0L);
            ascii("%PDF-1.4\n%Greenman Flat A4\n");
            object(1, "<< /Type /Catalog /Pages 2 0 R >>");
            StringBuilder kids = new StringBuilder();
            for (int i = 0; i < pageCount; i++) {
                if (i > 0) kids.append(' ');
                kids.append(3 + i * 3).append(" 0 R");
            }
            object(2, "<< /Type /Pages /Count " + pageCount
                    + " /Kids [" + kids + "] >>");
        }

        void addJpegPage(File jpeg, int width, int height) throws Exception {
            if (closed || pagesWritten >= totalPages) {
                throw new IllegalStateException("Too many PDF pages");
            }
            int pageId = 3 + pagesWritten * 3;
            int imageId = pageId + 1;
            int contentId = pageId + 2;
            String imageName = "Im" + (pagesWritten + 1);
            object(pageId, "<< /Type /Page /Parent 2 0 R "
                    + "/MediaBox [0 0 595.276 841.890] "
                    + "/Resources << /ProcSet [/PDF /ImageC] /XObject << /"
                    + imageName + " " + imageId + " 0 R >> >> "
                    + "/Contents " + contentId + " 0 R >>");

            offsets[imageId] = file.getFilePointer();
            ascii(imageId + " 0 obj\n<< /Type /XObject /Subtype /Image /Width "
                    + width + " /Height " + height
                    + " /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length "
                    + jpeg.length() + " >>\nstream\n");
            try (FileInputStream in = new FileInputStream(jpeg)) {
                byte[] buffer = new byte[65536];
                int count;
                while ((count = in.read(buffer)) >= 0) file.write(buffer, 0, count);
            }
            ascii("\nendstream\nendobj\n");

            String stream = "q\n595.276 0 0 841.890 0 0 cm\n/"
                    + imageName + " Do\nQ\n";
            byte[] bytes = stream.getBytes(StandardCharsets.ISO_8859_1);
            offsets[contentId] = file.getFilePointer();
            ascii(contentId + " 0 obj\n<< /Length " + bytes.length + " >>\nstream\n");
            file.write(bytes);
            ascii("endstream\nendobj\n");
            pagesWritten++;
        }

        void finish() throws Exception {
            if (pagesWritten != totalPages) {
                throw new IllegalStateException("The PDF page set is incomplete");
            }
            long xref = file.getFilePointer();
            int size = offsets.length;
            ascii("xref\n0 " + size + "\n0000000000 65535 f \n");
            for (int i = 1; i < size; i++) {
                ascii(String.format(Locale.US, "%010d 00000 n \n", offsets[i]));
            }
            ascii("trailer\n<< /Size " + size + " /Root 1 0 R >>\nstartxref\n"
                    + xref + "\n%%EOF\n");
            file.getFD().sync();
            close();
        }

        private void object(int id, String body) throws Exception {
            offsets[id] = file.getFilePointer();
            ascii(id + " 0 obj\n" + body + "\nendobj\n");
        }

        private void ascii(String text) throws Exception {
            file.write(text.getBytes(StandardCharsets.ISO_8859_1));
        }

        @Override
        public void close() throws Exception {
            if (closed) return;
            closed = true;
            file.close();
        }
    }
}
