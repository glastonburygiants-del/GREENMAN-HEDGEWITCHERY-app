package com.greenman.hedgewitchery;

import android.content.ContentValues;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.pdf.PdfDocument;
import android.graphics.pdf.PdfRenderer;
import android.net.Uri;
import android.os.Environment;
import android.os.ParcelFileDescriptor;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.JavascriptInterface;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.RandomAccessFile;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/** V28-safe native owner for the current bound BoS and Ink Pot PDF copies. */
public final class BoundBookStore {
    private static final String DIRECTORY = "bound-book";
    private static final String FILE_NAME = "Greenman_Last_Bound_Book.pdf";
    private static final String PART_NAME = "Greenman_Last_Bound_Book.pdf.part";
    private static final String COPY_PART_NAME = "Greenman_Ink_Pot_Copy.pdf.part";
    private static final String SELECTED_PART_NAME = "Greenman_Ink_Pot_Selected.pdf.part";

    private final Context context;
    private FileOutputStream pendingStream;
    private File pendingFile;
    private long expectedBytes;
    private long writtenBytes;

    private FileOutputStream copyStream;
    private File copyFile;
    private long copyExpectedBytes;
    private long copyWrittenBytes;
    private String copyDisplayName;
    private String lastError = "";

    public BoundBookStore(Context context) {
        this.context = context.getApplicationContext();
    }

    private void clearError() {
        lastError = "";
    }

    private void rememberError(Throwable error) {
        if (error == null) {
            lastError = "Unknown Android PDF error";
            return;
        }
        String message = error.getMessage();
        lastError = error.getClass().getSimpleName()
                + (message == null || message.trim().length() == 0 ? "" : ": " + message.trim());
    }

    private void rememberError(String message) {
        lastError = message == null ? "Unknown Android PDF error" : message;
    }

    @JavascriptInterface
    public synchronized String lastError() {
        return lastError == null ? "" : lastError;
    }

    @JavascriptInterface
    public synchronized boolean beginLastBoundPdf(long size) {
        abortLastBoundPdf();
        if (size <= 0L) return false;
        try {
            File directory = directory();
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
            try {
                Files.move(
                        pendingFile.toPath(),
                        finalFile().toPath(),
                        StandardCopyOption.REPLACE_EXISTING,
                        StandardCopyOption.ATOMIC_MOVE);
            } catch (java.nio.file.AtomicMoveNotSupportedException unsupported) {
                Files.move(
                        pendingFile.toPath(),
                        finalFile().toPath(),
                        StandardCopyOption.REPLACE_EXISTING);
            }
            clearPending();
            return true;
        } catch (Exception error) {
            abortLastBoundPdf();
            return false;
        }
    }

    @JavascriptInterface
    public synchronized void abortLastBoundPdf() {
        try {
            if (pendingStream != null) pendingStream.close();
        } catch (Exception ignored) {
        }
        pendingStream = null;
        if (pendingFile != null && pendingFile.exists()) pendingFile.delete();
        clearPending();
    }

    @JavascriptInterface
    public synchronized boolean hasLastBoundPdf() {
        File file = finalFile();
        return file.isFile() && file.length() > 0L;
    }

    @JavascriptInterface
    public synchronized String lastBoundPdfInfo() {
        File file = finalFile();
        if (!file.isFile()) return "";
        return file.length() + "|" + file.lastModified();
    }

    @JavascriptInterface
    public synchronized long lastBoundPdfSize() {
        File file = finalFile();
        return file.isFile() ? file.length() : 0L;
    }

    /** Read the current bound PDF in bounded chunks so the Ink Pot can filter it after an app restart. */
    @JavascriptInterface
    public synchronized String readLastBoundPdfChunk(long offset, int length) {
        File file = finalFile();
        if (!file.isFile() || offset < 0L || length <= 0 || offset >= file.length()) return "";
        int wanted = (int)Math.min((long)Math.min(length, 524288), file.length() - offset);
        byte[] bytes = new byte[wanted];
        try (RandomAccessFile input = new RandomAccessFile(file, "r")) {
            input.seek(offset);
            int read = input.read(bytes);
            if (read <= 0) return "";
            if (read != bytes.length) {
                byte[] exact = new byte[read];
                System.arraycopy(bytes, 0, exact, 0, read);
                bytes = exact;
            }
            return Base64.encodeToString(bytes, Base64.NO_WRAP);
        } catch (Exception error) {
            return "";
        }
    }

    @JavascriptInterface
    public synchronized boolean exportLastBoundPdf() {
        return exportLastBoundPdfAs(FILE_NAME);
    }

    /** Whole-book export is a byte-for-byte copy of the completed bound original. */
    @JavascriptInterface
    public synchronized boolean exportLastBoundPdfAs(String displayName) {
        clearError();
        File source = finalFile();
        if (!source.isFile() || source.length() <= 0L) {
            rememberError("The completed bound PDF is missing from Greenman storage");
            return false;
        }
        boolean ok = exportFileToDownloads(source, safePdfName(displayName, FILE_NAME));
        if (!ok && lastError.length() == 0) rememberError("Android Downloads could not save the whole bound PDF");
        if (ok) clearError();
        return ok;
    }

    /**
     * Cut chapter/page/spell selections directly from the already-bound PDF inside Android.
     * Nothing is round-tripped through the WebView. Pages are rendered one at a time at 2x,
     * keeping memory bounded on older phones.
     */
    @JavascriptInterface
    public synchronized boolean exportSelectedPagesAs(String displayName, String pageIndexesCsv) {
        clearError();
        File source = finalFile();
        if (!source.isFile() || source.length() <= 0L) {
            rememberError("The completed bound PDF is missing from Greenman storage");
            return false;
        }

        List<Integer> indexes;
        try {
            indexes = parsePageIndexes(pageIndexesCsv);
        } catch (Exception error) {
            rememberError(error);
            return false;
        }
        if (indexes.isEmpty()) {
            rememberError("No bound PDF pages were selected");
            return false;
        }

        File directory = directory();
        if (!directory.exists() && !directory.mkdirs()) {
            rememberError("Could not create Greenman bound-book storage");
            return false;
        }
        File selected = new File(directory, SELECTED_PART_NAME);
        if (selected.exists() && !selected.delete()) {
            rememberError("Could not replace the unfinished selected-page PDF");
            return false;
        }

        ParcelFileDescriptor descriptor = null;
        PdfRenderer renderer = null;
        PdfDocument output = null;
        FileOutputStream stream = null;
        try {
            descriptor = ParcelFileDescriptor.open(source, ParcelFileDescriptor.MODE_READ_ONLY);
            renderer = new PdfRenderer(descriptor);
            final int pageCount = renderer.getPageCount();
            for (Integer index : indexes) {
                if (index == null || index < 0 || index >= pageCount) {
                    throw new IllegalArgumentException(
                            "Selected page " + (index == null ? "?" : (index + 1))
                                    + " is outside the bound PDF");
                }
            }

            output = new PdfDocument();
            final Paint paint = new Paint(
                    Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG | Paint.DITHER_FLAG);
            int outputPageNumber = 1;
            for (Integer index : indexes) {
                PdfRenderer.Page sourcePage = renderer.openPage(index);
                Bitmap bitmap = null;
                try {
                    int width = Math.max(1, sourcePage.getWidth());
                    int height = Math.max(1, sourcePage.getHeight());
                    bitmap = Bitmap.createBitmap(width * 2, height * 2, Bitmap.Config.ARGB_8888);
                    bitmap.eraseColor(Color.WHITE);
                    Matrix matrix = new Matrix();
                    matrix.setScale(2f, 2f);
                    sourcePage.render(bitmap, null, matrix, PdfRenderer.Page.RENDER_MODE_FOR_PRINT);

                    PdfDocument.PageInfo info =
                            new PdfDocument.PageInfo.Builder(width, height, outputPageNumber++).create();
                    PdfDocument.Page targetPage = output.startPage(info);
                    targetPage.getCanvas().drawColor(Color.WHITE);
                    targetPage.getCanvas().drawBitmap(
                            bitmap, null, new Rect(0, 0, width, height), paint);
                    output.finishPage(targetPage);
                } finally {
                    if (bitmap != null) bitmap.recycle();
                    sourcePage.close();
                }
            }

            stream = new FileOutputStream(selected, false);
            output.writeTo(stream);
            stream.flush();
            stream.getFD().sync();
            stream.close();
            stream = null;
            output.close();
            output = null;
            renderer.close();
            renderer = null;
            descriptor.close();
            descriptor = null;

            if (!selected.isFile() || selected.length() <= 0L) {
                rememberError("Android created an empty selected-page PDF");
                selected.delete();
                return false;
            }

            boolean ok = exportFileToDownloads(
                    selected,
                    safePdfName(displayName, "Greenman_Book_of_Shadows_Selection.pdf"));
            selected.delete();
            if (!ok && lastError.length() == 0) rememberError("Android Downloads could not save the selected-page PDF");
            if (ok) clearError();
            return ok;
        } catch (Exception error) {
            rememberError(error);
            if (selected.exists()) selected.delete();
            return false;
        } finally {
            try { if (stream != null) stream.close(); } catch (Exception ignored) {}
            try { if (output != null) output.close(); } catch (Exception ignored) {}
            try { if (renderer != null) renderer.close(); } catch (Exception ignored) {}
            try { if (descriptor != null) descriptor.close(); } catch (Exception ignored) {}
        }
    }

    private List<Integer> parsePageIndexes(String csv) {
        Set<Integer> ordered = new LinkedHashSet<>();
        String value = csv == null ? "" : csv.trim();
        if (value.length() == 0) return new ArrayList<>();
        String[] parts = value.split(",");
        for (String part : parts) {
            String clean = part == null ? "" : part.trim();
            if (clean.length() == 0) continue;
            int index = Integer.parseInt(clean);
            if (index < 0) throw new IllegalArgumentException("Negative PDF page index");
            ordered.add(index);
        }
        return new ArrayList<>(ordered);
    }

    /** Begin a separate Ink Pot PDF copy. This never replaces the bound original. */
    @JavascriptInterface
    public synchronized boolean beginPdfCopy(String displayName, long size) {
        abortPdfCopy();
        if (size <= 0L) return false;
        try {
            File directory = directory();
            if (!directory.exists() && !directory.mkdirs()) return false;
            copyFile = new File(directory, COPY_PART_NAME);
            if (copyFile.exists() && !copyFile.delete()) return false;
            copyStream = new FileOutputStream(copyFile, false);
            copyExpectedBytes = size;
            copyWrittenBytes = 0L;
            copyDisplayName = safePdfName(displayName, "Greenman_Book_of_Shadows_Copy.pdf");
            return true;
        } catch (Exception error) {
            abortPdfCopy();
            return false;
        }
    }

    /** Finish the Ink Pot copy and place it directly in Downloads / Greenman HedgeWitchery. */
    @JavascriptInterface
    public synchronized boolean appendPdfCopyChunk(String encoded, boolean last) {
        if (copyStream == null || copyFile == null || encoded == null) return false;
        try {
            byte[] bytes = Base64.decode(encoded, Base64.NO_WRAP);
            copyStream.write(bytes);
            copyWrittenBytes += bytes.length;
            if (!last) return copyWrittenBytes <= copyExpectedBytes;

            copyStream.flush();
            copyStream.getFD().sync();
            copyStream.close();
            copyStream = null;
            if (copyWrittenBytes != copyExpectedBytes) {
                copyFile.delete();
                clearCopy();
                return false;
            }
            boolean ok = exportFileToDownloads(copyFile, copyDisplayName);
            copyFile.delete();
            clearCopy();
            return ok;
        } catch (Exception error) {
            abortPdfCopy();
            return false;
        }
    }

    @JavascriptInterface
    public synchronized void abortPdfCopy() {
        try {
            if (copyStream != null) copyStream.close();
        } catch (Exception ignored) {
        }
        copyStream = null;
        if (copyFile != null && copyFile.exists()) copyFile.delete();
        clearCopy();
    }

    private boolean exportFileToDownloads(File source, String displayName) {
        if (source == null || !source.isFile() || source.length() <= 0L) {
            rememberError("The PDF file to export is empty");
            return false;
        }
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, displayName);
        values.put(MediaStore.Downloads.MIME_TYPE, "application/pdf");
        values.put(MediaStore.Downloads.RELATIVE_PATH,
                Environment.DIRECTORY_DOWNLOADS + "/Greenman HedgeWitchery");
        values.put(MediaStore.Downloads.IS_PENDING, 1);
        Uri destination = null;
        try {
            destination = context.getContentResolver().insert(
                    MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (destination == null) {
                rememberError("Android Downloads did not create a PDF destination");
                return false;
            }
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
            clearError();
            return true;
        } catch (Exception error) {
            rememberError(error);
            if (destination != null) context.getContentResolver().delete(destination, null, null);
            return false;
        }
    }

    private String safePdfName(String value, String fallback) {
        String name = value == null ? "" : value.trim();
        if (name.length() == 0) name = fallback;
        name = name.replaceAll("[\\\\/:*?\"<>|\\p{Cntrl}]", "_");
        if (!name.toLowerCase().endsWith(".pdf")) name += ".pdf";
        if (name.length() > 180) name = name.substring(0, 176) + ".pdf";
        return name;
    }

    private File directory() {
        return new File(context.getFilesDir(), DIRECTORY);
    }

    private File finalFile() {
        return new File(directory(), FILE_NAME);
    }

    private void clearPending() {
        pendingFile = null;
        expectedBytes = 0L;
        writtenBytes = 0L;
    }

    private void clearCopy() {
        copyFile = null;
        copyExpectedBytes = 0L;
        copyWrittenBytes = 0L;
        copyDisplayName = null;
    }
}