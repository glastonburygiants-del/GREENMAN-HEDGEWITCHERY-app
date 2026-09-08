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
import java.io.RandomAccessFile;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;

/** V28-safe native owner for the current bound BoS and Ink Pot PDF copies. */
public final class BoundBookStore {
    private static final String DIRECTORY = "bound-book";
    private static final String FILE_NAME = "Greenman_Last_Bound_Book.pdf";
    private static final String PART_NAME = "Greenman_Last_Bound_Book.pdf.part";
    private static final String COPY_PART_NAME = "Greenman_Ink_Pot_Copy.pdf.part";

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

    @JavascriptInterface
    public synchronized boolean exportLastBoundPdfAs(String displayName) {
        File source = finalFile();
        if (!source.isFile() || source.length() <= 0L) return false;
        return exportFileToDownloads(source, safePdfName(displayName, FILE_NAME));
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
        if (source == null || !source.isFile() || source.length() <= 0L) return false;
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, displayName);
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