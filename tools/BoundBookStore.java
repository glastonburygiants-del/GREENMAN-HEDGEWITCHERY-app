package com.greenman.hedgewitchery;

import android.content.ContentUris;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.Properties;

/** Native owner for the current bound BoS and one current PDF per Scribe hand. */
public final class BoundBookStore {
    static final String ROOT_DIRECTORY = "bound-book";
    static final String BOOK_DIRECTORY = "scribe-books";
    static final String STAGING_DIRECTORY = "render-staging";
    static final String ACTIVE_DIRECTORY = "render-active";
    static final String STATUS_NAME = "render-status.json";
    static final String META_NAME = "meta.properties";
    static final String STYLE_NAME = "book-style.css";
    static final String CANCEL_NAME = "cancel.request";

    private static final String LAST_KEY = "bound-original";
    private static final String FILE_NAME = "Greenman_Last_Bound_Book.pdf";
    private static final String PART_NAME = "Greenman_Last_Bound_Book.pdf.part";

    private final Context context;
    private FileOutputStream pendingStream;
    private File pendingFile;
    private long expectedBytes;
    private long writtenBytes;

    private File submissionDirectory;
    private FileOutputStream submissionStream;
    private File submissionPart;
    private File submissionFinal;
    private long submissionExpected;
    private long submissionWritten;
    private int submissionPages;
    private String submissionJobId = "";
    private String submissionKey = "";
    private String submissionTitle = "";
    private String submissionScript = "";
    private String submissionFileName = "";
    private String submissionKind = "";
    private boolean exportBusy;

    public BoundBookStore(Context context) {
        this.context = context.getApplicationContext();
    }

    /* V28 compatibility route. */
    @JavascriptInterface
    public synchronized boolean beginLastBoundPdf(long size) {
        abortLastBoundPdf();
        if (size <= 0L) return false;
        try {
            File directory = rootDirectory(context);
            if (!directory.exists() && !directory.mkdirs()) return false;
            pendingFile = new File(directory, PART_NAME);
            if (pendingFile.exists() && !pendingFile.delete()) return false;
            pendingStream = new FileOutputStream(pendingFile, false);
            expectedBytes = size;
            writtenBytes = 0L;
            return true;
        } catch (Exception error) {
            abortLastBoundPdf();
            return false;
        }
    }

    @JavascriptInterface
    public synchronized boolean appendLastBoundPdfChunk(String encoded, boolean last) {
        if (pendingStream == null || pendingFile == null || encoded == null) return false;
        try {
            byte[] bytes = Base64.decode(encoded, Base64.NO_WRAP);
            pendingStream.write(bytes);
            writtenBytes += bytes.length;
            if (!last) return writtenBytes <= expectedBytes;
            pendingStream.flush();
            pendingStream.getFD().sync();
            pendingStream.close();
            pendingStream = null;
            if (writtenBytes != expectedBytes) {
                pendingFile.delete();
                clearPending();
                return false;
            }
            atomicReplace(pendingFile, bookFile(context, LAST_KEY));
            clearPending();
            return true;
        } catch (Exception error) {
            abortLastBoundPdf();
            return false;
        }
    }

    @JavascriptInterface
    public synchronized void abortLastBoundPdf() {
        closeQuietly(pendingStream);
        pendingStream = null;
        if (pendingFile != null && pendingFile.exists()) pendingFile.delete();
        clearPending();
    }

    @JavascriptInterface
    public synchronized boolean hasLastBoundPdf() {
        return hasPdf(bookFile(context, LAST_KEY));
    }

    @JavascriptInterface
    public synchronized String lastBoundPdfInfo() {
        return pdfInfo(bookFile(context, LAST_KEY));
    }

    @JavascriptInterface
    public synchronized boolean exportLastBoundPdf() {
        String date = new SimpleDateFormat("yyyy-MM-dd", Locale.UK).format(new Date());
        return exportBookPdf(LAST_KEY, "Greenman_Book_of_Shadows_" + date + ".pdf", false);
    }

    /** Begin receiving a temporary CSS plus one self-contained HTML fragment per page. */
    @JavascriptInterface
    public synchronized boolean beginPdfJob(
            String jobId, String storageKey, String title, String scriptName,
            String requestedFileName, int pageCount, String kind) {
        if (pageCount < 1 || pageCount > 2000) return false;
        String priorStatus = readStatus(context);
        String state = statusState(priorStatus);
        if ("receiving".equals(state) || "queued".equals(state)
                || "rendering".equals(state) || "cancelling".equals(state)) {
            long age = System.currentTimeMillis() - statusLong(priorStatus, "updatedAt", 0L);
            if (age < 10L * 60L * 1000L) return false;
            deleteRecursively(new File(rootDirectory(context), STAGING_DIRECTORY));
            deleteRecursively(new File(rootDirectory(context), ACTIVE_DIRECTORY));
        }
        abortSubmission(false);
        try {
            File root = rootDirectory(context);
            if (!root.exists() && !root.mkdirs()) return false;
            File staging = new File(root, STAGING_DIRECTORY);
            deleteRecursively(staging);
            if (!staging.mkdirs()) return false;
            submissionDirectory = staging;
            submissionPages = pageCount;
            submissionJobId = safeToken(jobId, "job-" + System.currentTimeMillis());
            submissionKey = safeToken(storageKey, LAST_KEY);
            submissionTitle = cleanText(title, "Book of Shadows");
            submissionScript = cleanText(scriptName, "Original English");
            submissionFileName = safePdfName(requestedFileName);
            submissionKind = safeToken(kind, "export");
            writeMeta(staging);
            writeStatus(context, "receiving", 0, pageCount, submissionJobId,
                    submissionKey, submissionTitle, submissionScript,
                    submissionFileName, submissionKind,
                    "Gathering the selected A4 pages", 0L);
            return true;
        } catch (Exception error) {
            deleteRecursively(new File(rootDirectory(context), ACTIVE_DIRECTORY));
            abortSubmission(true);
            return false;
        }
    }

    @JavascriptInterface
    public synchronized boolean beginPdfStyle(long size) {
        return submissionDirectory != null
                && beginSubmissionFile(new File(submissionDirectory, STYLE_NAME), size);
    }

    @JavascriptInterface
    public synchronized boolean appendPdfStyleChunk(String encoded, boolean last) {
        return appendSubmissionChunk(encoded, last);
    }

    @JavascriptInterface
    public synchronized boolean beginPdfPage(int index, long size) {
        return submissionDirectory != null && index >= 0 && index < submissionPages
                && beginSubmissionFile(pageFile(submissionDirectory, index), size);
    }

    @JavascriptInterface
    public synchronized boolean appendPdfPageChunk(String encoded, boolean last) {
        return appendSubmissionChunk(encoded, last);
    }

    @JavascriptInterface
    public synchronized boolean startPdfJob() {
        if (submissionDirectory == null || submissionStream != null) return false;
        try {
            File style = new File(submissionDirectory, STYLE_NAME);
            if (!style.isFile() || style.length() < 1L) return false;
            for (int i = 0; i < submissionPages; i++) {
                File page = pageFile(submissionDirectory, i);
                if (!page.isFile() || page.length() < 1L) return false;
            }
            File active = new File(rootDirectory(context), ACTIVE_DIRECTORY);
            deleteRecursively(active);
            atomicReplace(submissionDirectory, active);
            writeStatus(context, "queued", 0, submissionPages, submissionJobId,
                    submissionKey, submissionTitle, submissionScript,
                    submissionFileName, submissionKind,
                    "The background renderer is starting", 0L);
            Intent intent = new Intent(context, ScribePdfService.class);
            intent.setAction(ScribePdfService.ACTION_RENDER);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent);
            } else {
                context.startService(intent);
            }
            clearSubmission();
            return true;
        } catch (Exception error) {
            deleteRecursively(new File(rootDirectory(context), ACTIVE_DIRECTORY));
            abortSubmission(true);
            return false;
        }
    }

    @JavascriptInterface
    public synchronized void abortPdfJobSubmission() {
        abortSubmission(true);
    }

    @JavascriptInterface
    public synchronized boolean cancelPdfJob() {
        String status = readStatus(context);
        String state = statusState(status);
        if ("receiving".equals(state)) {
            String jobId = statusString(status, "jobId", submissionJobId);
            String key = statusString(status, "storageKey", submissionKey);
            String title = statusString(status, "title", submissionTitle);
            String script = statusString(status, "scriptName", submissionScript);
            String fileName = statusString(status, "fileName", submissionFileName);
            String kind = statusString(status, "kind", submissionKind);
            int total = statusInt(status, "total", submissionPages);
            abortSubmission(false);
            deleteRecursively(new File(rootDirectory(context), STAGING_DIRECTORY));
            writeStatus(context, "cancelled", 0, total, jobId, key, title, script,
                    fileName, kind, "The unfinished page package was discarded", 0L);
            return true;
        }
        if ("cancelling".equals(state)) return true;
        if (!"queued".equals(state) && !"rendering".equals(state)) return false;
        try {
            File active = new File(rootDirectory(context), ACTIVE_DIRECTORY);
            if (!active.isDirectory()) return false;
            File marker = new File(active, CANCEL_NAME);
            try (FileOutputStream out = new FileOutputStream(marker, false)) {
                out.write("cancel".getBytes(StandardCharsets.UTF_8));
                out.flush();
                out.getFD().sync();
            }
            writeStatus(context, "cancelling", statusInt(status, "done", 0),
                    statusInt(status, "total", 0),
                    statusString(status, "jobId", ""),
                    statusString(status, "storageKey", ""),
                    statusString(status, "title", "Book of Shadows"),
                    statusString(status, "scriptName", ""),
                    statusString(status, "fileName", ""),
                    statusString(status, "kind", ""),
                    "Stopping safely after the current page", 0L);
            Intent intent = new Intent(context, ScribePdfService.class);
            intent.setAction(ScribePdfService.ACTION_RENDER);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent);
            } else {
                context.startService(intent);
            }
            return true;
        } catch (Exception error) {
            return false;
        }
    }

    @JavascriptInterface
    public synchronized String pdfJobStatus() {
        return readStatus(context);
    }

    @JavascriptInterface
    public synchronized boolean hasBookPdf(String storageKey) {
        return hasPdf(bookFile(context, storageKey));
    }

    @JavascriptInterface
    public synchronized String bookPdfInfo(String storageKey) {
        return pdfInfo(bookFile(context, storageKey));
    }

    @JavascriptInterface
    public synchronized boolean deleteBookPdf(String storageKey) {
        File file = bookFile(context, storageKey);
        return !file.exists() || file.delete();
    }

    /** Save one dated copy to Downloads. Repeating the same export replaces it. */
    @JavascriptInterface
    public synchronized boolean exportBookPdf(
            String storageKey, String requestedFileName, boolean openAfterSave) {
        File source = bookFile(context, storageKey);
        if (!hasPdf(source)) return false;
        if (exportBusy) return true;
        exportBusy = true;
        String displayName = safePdfName(requestedFileName);
        context.getMainExecutor().execute(() -> Toast.makeText(context,
                "Saving " + displayName + " to Downloads…", Toast.LENGTH_SHORT).show());
        new Thread(() -> {
            try {
                boolean saved = exportBookPdfNow(source, displayName, openAfterSave);
                if (!saved) context.getMainExecutor().execute(() -> Toast.makeText(context,
                        "The PDF could not be copied to Downloads.", Toast.LENGTH_LONG).show());
            } finally {
                synchronized (BoundBookStore.this) {
                    exportBusy = false;
                }
            }
        }, "GreenmanPdfExport").start();
        return true;
    }

    private boolean exportBookPdfNow(
            File source, String displayName, boolean openAfterSave) {
        String relativePath = Environment.DIRECTORY_DOWNLOADS + "/Greenman HedgeWitchery/";
        removePriorDownload(displayName, relativePath);
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, displayName);
        values.put(MediaStore.Downloads.MIME_TYPE, "application/pdf");
        values.put(MediaStore.Downloads.RELATIVE_PATH, relativePath);
        values.put(MediaStore.Downloads.IS_PENDING, 1);
        Uri destination = null;
        try {
            destination = context.getContentResolver().insert(
                    MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (destination == null) return false;
            try (InputStream input = new FileInputStream(source);
                 OutputStream output = context.getContentResolver().openOutputStream(destination)) {
                if (output == null) throw new IllegalStateException("No PDF output stream");
                byte[] buffer = new byte[65536];
                int count;
                while ((count = input.read(buffer)) >= 0) output.write(buffer, 0, count);
                output.flush();
            }
            ContentValues complete = new ContentValues();
            complete.put(MediaStore.Downloads.IS_PENDING, 0);
            context.getContentResolver().update(destination, complete, null, null);
            if (openAfterSave) openPdf(destination);
            return true;
        } catch (Exception error) {
            if (destination != null) context.getContentResolver().delete(destination, null, null);
            return false;
        }
    }

    private boolean beginSubmissionFile(File target, long size) {
        closeSubmissionStream();
        if (size < 1L || size > 80L * 1024L * 1024L) return false;
        try {
            submissionFinal = target;
            submissionPart = new File(target.getParentFile(), target.getName() + ".part");
            if (submissionPart.exists() && !submissionPart.delete()) return false;
            submissionStream = new FileOutputStream(submissionPart, false);
            submissionExpected = size;
            submissionWritten = 0L;
            return true;
        } catch (Exception error) {
            closeSubmissionStream();
            return false;
        }
    }

    private boolean appendSubmissionChunk(String encoded, boolean last) {
        if (submissionStream == null || submissionPart == null || encoded == null) return false;
        try {
            byte[] bytes = Base64.decode(encoded, Base64.NO_WRAP);
            submissionStream.write(bytes);
            submissionWritten += bytes.length;
            if (!last) return submissionWritten <= submissionExpected;
            submissionStream.flush();
            submissionStream.getFD().sync();
            submissionStream.close();
            submissionStream = null;
            if (submissionWritten != submissionExpected) {
                submissionPart.delete();
                clearSubmissionFile();
                return false;
            }
            atomicReplace(submissionPart, submissionFinal);
            clearSubmissionFile();
            return true;
        } catch (Exception error) {
            closeSubmissionStream();
            if (submissionPart != null) submissionPart.delete();
            clearSubmissionFile();
            return false;
        }
    }

    private void writeMeta(File directory) throws Exception {
        Properties meta = new Properties();
        meta.setProperty("jobId", submissionJobId);
        meta.setProperty("storageKey", submissionKey);
        meta.setProperty("title", submissionTitle);
        meta.setProperty("scriptName", submissionScript);
        meta.setProperty("fileName", submissionFileName);
        meta.setProperty("kind", submissionKind);
        meta.setProperty("pageCount", String.valueOf(submissionPages));
        File part = new File(directory, META_NAME + ".part");
        try (FileOutputStream out = new FileOutputStream(part, false)) {
            meta.store(out, "Greenman BoS PDF render job");
            out.flush();
            out.getFD().sync();
        }
        atomicReplace(part, new File(directory, META_NAME));
    }

    private void abortSubmission(boolean updateStatus) {
        closeSubmissionStream();
        if (submissionPart != null) submissionPart.delete();
        if (submissionDirectory != null) deleteRecursively(submissionDirectory);
        if (updateStatus && !submissionJobId.isEmpty()) {
            writeStatus(context, "cancelled", 0, submissionPages, submissionJobId,
                    submissionKey, submissionTitle, submissionScript,
                    submissionFileName, submissionKind,
                    "The unfinished page package was discarded", 0L);
        }
        clearSubmission();
    }

    private void removePriorDownload(String displayName, String relativePath) {
        String[] projection = {MediaStore.Downloads._ID};
        String selection = MediaStore.Downloads.DISPLAY_NAME + "=? AND "
                + MediaStore.Downloads.RELATIVE_PATH + "=?";
        String[] args = {displayName, relativePath};
        try (Cursor cursor = context.getContentResolver().query(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                projection, selection, args, null)) {
            if (cursor == null) return;
            int idColumn = cursor.getColumnIndexOrThrow(MediaStore.Downloads._ID);
            while (cursor.moveToNext()) {
                Uri uri = ContentUris.withAppendedId(
                        MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                        cursor.getLong(idColumn));
                context.getContentResolver().delete(uri, null, null);
            }
        } catch (Exception ignored) {
        }
    }

    private void openPdf(Uri uri) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "application/pdf");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
        } catch (Exception error) {
            Toast.makeText(context,
                    "PDF saved in Downloads / Greenman HedgeWitchery.",
                    Toast.LENGTH_LONG).show();
        }
    }

    private void closeSubmissionStream() {
        closeQuietly(submissionStream);
        submissionStream = null;
    }

    private void clearSubmissionFile() {
        submissionPart = null;
        submissionFinal = null;
        submissionExpected = 0L;
        submissionWritten = 0L;
    }

    private void clearSubmission() {
        closeSubmissionStream();
        clearSubmissionFile();
        submissionDirectory = null;
        submissionPages = 0;
        submissionJobId = "";
        submissionKey = "";
        submissionTitle = "";
        submissionScript = "";
        submissionFileName = "";
        submissionKind = "";
    }

    private void clearPending() {
        pendingFile = null;
        expectedBytes = 0L;
        writtenBytes = 0L;
    }

    static File rootDirectory(Context context) {
        return new File(context.getFilesDir(), ROOT_DIRECTORY);
    }

    static File bookFile(Context context, String storageKey) {
        String key = safeToken(storageKey, LAST_KEY);
        if (LAST_KEY.equals(key)) return new File(rootDirectory(context), FILE_NAME);
        File books = new File(rootDirectory(context), BOOK_DIRECTORY);
        if (!books.exists()) books.mkdirs();
        return new File(books, key + ".pdf");
    }

    static File pageFile(File directory, int index) {
        return new File(directory, String.format(Locale.US, "page-%04d.html", index));
    }

    static void writeStatus(
            Context context, String state, int done, int total, String jobId,
            String storageKey, String title, String scriptName, String fileName,
            String kind, String message, long pdfBytes) {
        try {
            File root = rootDirectory(context);
            if (!root.exists() && !root.mkdirs()) return;
            String text = "{" +
                    "\"state\":\"" + json(state) + "\"," +
                    "\"done\":" + Math.max(0, done) + "," +
                    "\"total\":" + Math.max(0, total) + "," +
                    "\"jobId\":\"" + json(jobId) + "\"," +
                    "\"storageKey\":\"" + json(storageKey) + "\"," +
                    "\"title\":\"" + json(title) + "\"," +
                    "\"scriptName\":\"" + json(scriptName) + "\"," +
                    "\"fileName\":\"" + json(fileName) + "\"," +
                    "\"kind\":\"" + json(kind) + "\"," +
                    "\"message\":\"" + json(message) + "\"," +
                    "\"pdfBytes\":" + Math.max(0L, pdfBytes) + "," +
                    "\"updatedAt\":" + System.currentTimeMillis() + "}";
            File part = new File(root, STATUS_NAME + ".part");
            try (FileOutputStream out = new FileOutputStream(part, false)) {
                out.write(text.getBytes(StandardCharsets.UTF_8));
                out.flush();
                out.getFD().sync();
            }
            atomicReplace(part, new File(root, STATUS_NAME));
        } catch (Exception ignored) {
        }
    }

    static String readStatus(Context context) {
        File file = new File(rootDirectory(context), STATUS_NAME);
        if (!file.isFile()) return "{\"state\":\"idle\"}";
        try {
            return new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8);
        } catch (Exception error) {
            return "{\"state\":\"idle\"}";
        }
    }

    private static String statusState(String text) {
        if (text == null) return "idle";
        int marker = text.indexOf("\"state\":\"");
        if (marker < 0) return "idle";
        int start = marker + 9;
        int end = text.indexOf('"', start);
        return end > start ? text.substring(start, end) : "idle";
    }

    private static String statusString(String text, String name, String fallback) {
        try {
            return new JSONObject(text).optString(name, fallback == null ? "" : fallback);
        } catch (Exception error) {
            return fallback == null ? "" : fallback;
        }
    }

    private static int statusInt(String text, String name, int fallback) {
        try {
            return new JSONObject(text).optInt(name, fallback);
        } catch (Exception error) {
            return fallback;
        }
    }

    private static long statusLong(String text, String name, long fallback) {
        try {
            return new JSONObject(text).optLong(name, fallback);
        } catch (Exception error) {
            return fallback;
        }
    }

    static void atomicReplace(File source, File destination) throws Exception {
        File parent = destination.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IllegalStateException("Could not create PDF directory");
        }
        try {
            Files.move(source.toPath(), destination.toPath(),
                    StandardCopyOption.REPLACE_EXISTING,
                    StandardCopyOption.ATOMIC_MOVE);
        } catch (java.nio.file.AtomicMoveNotSupportedException unsupported) {
            Files.move(source.toPath(), destination.toPath(),
                    StandardCopyOption.REPLACE_EXISTING);
        }
    }

    static void deleteRecursively(File file) {
        if (file == null || !file.exists()) return;
        File[] children = file.listFiles();
        if (children != null) for (File child : children) deleteRecursively(child);
        file.delete();
    }

    private static boolean hasPdf(File file) {
        return file.isFile() && file.length() > 0L;
    }

    private static String pdfInfo(File file) {
        return file.isFile() ? file.length() + "|" + file.lastModified() : "";
    }

    static String safeToken(String value, String fallback) {
        String clean = value == null ? "" : value.replaceAll("[^A-Za-z0-9_-]+", "-")
                .replaceAll("-+", "-").replaceAll("^-|-$", "");
        return clean.isEmpty() ? fallback : clean.substring(0, Math.min(80, clean.length()));
    }

    private static String safePdfName(String value) {
        String clean = value == null ? "" : value.replaceAll("[\\\\/:*?\"<>|\\r\\n\\t]+", " ")
                .replaceAll("\\s+", " ").trim().replace(' ', '_')
                .replaceAll("_+", "_").replaceAll("^_+|_+$", "");
        if (clean.toLowerCase(Locale.ROOT).endsWith(".pdf")) {
            clean = clean.substring(0, clean.length() - 4);
        }
        if (clean.isEmpty()) clean = "Greenman_Book_of_Shadows";
        clean = clean.substring(0, Math.min(176, clean.length()));
        return clean + ".pdf";
    }

    private static String cleanText(String value, String fallback) {
        String clean = value == null ? "" : value.replaceAll("[\\r\\n\\t]+", " ")
                .replaceAll("\\s+", " ").trim();
        return clean.isEmpty() ? fallback : clean.substring(0, Math.min(180, clean.length()));
    }

    private static String json(String value) {
        if (value == null) return "";
        return value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\r", "\\r").replace("\n", "\\n");
    }

    private static void closeQuietly(OutputStream stream) {
        if (stream == null) return;
        try {
            stream.close();
        } catch (Exception ignored) {
        }
    }
}
