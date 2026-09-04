package com.greenman.hedgewitchery;

import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.JavascriptInterface;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;

/** Native, non-localStorage owner for the single most recently bound BoS PDF. */
public final class BoundBookStore {
    private static final String DIRECTORY = "bound-book";
    private static final String FILE_NAME = "Greenman_Last_Bound_Book.pdf";
    private static final String PART_NAME = "Greenman_Last_Bound_Book.pdf.part";

    private final Context context;
    private FileOutputStream pendingStream;
    private File pendingFile;
    private long expectedBytes;
    private long writtenBytes;

    public BoundBookStore(Context context) {
        this.context = context.getApplicationContext();
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
    public synchronized boolean exportLastBoundPdf() {
        File source = finalFile();
        if (!source.isFile() || source.length() <= 0L) return false;
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, FILE_NAME);
        values.put(MediaStore.Downloads.MIME_TYPE, "application/pdf");
        values.put(
                MediaStore.Downloads.RELATIVE_PATH,
                Environment.DIRECTORY_DOWNLOADS + "/Greenman HedgeWitchery");
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
            return true;
        } catch (Exception error) {
            if (destination != null) context.getContentResolver().delete(destination, null, null);
            return false;
        }
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
}
