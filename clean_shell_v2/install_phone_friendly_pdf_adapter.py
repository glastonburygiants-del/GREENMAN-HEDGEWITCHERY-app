#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: install_phone_friendly_pdf_adapter.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')

# Keep the live app and all HTML page builders untouched. This patch changes only
# the final Android PrintDocumentAdapter handed to PrintManager. Chromium still
# performs the authoritative A4 layout first; its temporary PDF is then rendered
# once into simple image-backed PDF pages that low-memory phone viewers can browse.

imports_anchor = '''import android.graphics.Color;\nimport android.net.Uri;\nimport android.os.Bundle;'''
imports_repl = '''import android.graphics.Color;\nimport android.graphics.Matrix;\nimport android.graphics.Rect;\nimport android.graphics.pdf.PdfDocument;\nimport android.graphics.pdf.PdfRenderer;\nimport android.net.Uri;\nimport android.os.Bundle;\nimport android.os.CancellationSignal;\nimport android.os.ParcelFileDescriptor;\nimport android.os.Bundle;'''
if s.count(imports_anchor) != 1:
    raise SystemExit(f'graphics import anchor count {s.count(imports_anchor)}')
s = s.replace(imports_anchor, imports_repl, 1)
# Remove the duplicate Bundle introduced above while keeping import placement easy to audit.
s = s.replace('import android.os.Bundle;\nimport android.os.CancellationSignal;\nimport android.os.ParcelFileDescriptor;\nimport android.os.Bundle;',
              'import android.os.Bundle;\nimport android.os.CancellationSignal;\nimport android.os.ParcelFileDescriptor;', 1)

print_import_anchor = '''import android.provider.MediaStore;\nimport android.util.Base64;'''
print_import_repl = '''import android.provider.MediaStore;\nimport android.print.PageRange;\nimport android.print.PrintAttributes;\nimport android.print.PrintDocumentAdapter;\nimport android.print.PrintDocumentInfo;\nimport android.util.Base64;'''
if s.count(print_import_anchor) != 1:
    raise SystemExit('print import anchor missing')
s = s.replace(print_import_anchor, print_import_repl, 1)

io_anchor = '''import java.io.ByteArrayInputStream;\nimport java.io.FileNotFoundException;\nimport java.io.IOException;'''
io_repl = '''import java.io.ByteArrayInputStream;\nimport java.io.File;\nimport java.io.FileNotFoundException;\nimport java.io.FileOutputStream;\nimport java.io.IOException;'''
if s.count(io_anchor) != 1:
    raise SystemExit('io import anchor missing')
s = s.replace(io_anchor, io_repl, 1)

call_old = '''            printManager.print(jobName, target.createPrintDocumentAdapter(jobName), attributes);'''
call_new = '''            printManager.print(jobName, new PhoneFriendlyPrintAdapter(target, jobName), attributes);'''
if s.count(call_old) != 1:
    raise SystemExit(f'PrintManager adapter anchor count {s.count(call_old)}')
s = s.replace(call_old, call_new, 1)

class_anchor = '''    private static String sanitizePrintJobName(String requestedJobName) {'''
if s.count(class_anchor) != 1:
    raise SystemExit('sanitizePrintJobName anchor missing')

adapter = r'''    /*
     * PHONE-FRIENDLY PDF OWNER
     *
     * The WebView print adapter remains the source of truth for A4 layout. We first
     * let it write its normal Chromium/Skia PDF to a private temporary file. We then
     * render each completed PDF page at 144 dpi and write a very simple image-backed
     * PDF to Android's requested destination. The visual page is unchanged, but the
     * saved PDF no longer contains the deep web/vector/font structure that caused
     * Samsung phone PDF viewers to stall or show blank pages while scrolling.
     */
    private final class PhoneFriendlyPrintAdapter extends PrintDocumentAdapter {
        private static final float RASTER_SCALE = 2.0f; // 144 dpi from PDF's 72 dpi page space.
        private final PrintDocumentAdapter chromium;
        private final String jobName;
        private PrintDocumentInfo documentInfo;
        private File tempPdf;

        PhoneFriendlyPrintAdapter(WebView source, String jobName) {
            this.chromium = source.createPrintDocumentAdapter(jobName);
            this.jobName = jobName;
        }

        @Override
        public void onLayout(
                PrintAttributes oldAttributes,
                PrintAttributes newAttributes,
                CancellationSignal cancellationSignal,
                LayoutResultCallback callback,
                Bundle extras) {
            chromium.onLayout(oldAttributes, newAttributes, cancellationSignal,
                    new LayoutResultCallback() {
                        @Override
                        public void onLayoutFinished(PrintDocumentInfo info, boolean changed) {
                            documentInfo = info;
                            callback.onLayoutFinished(info, changed);
                        }

                        @Override
                        public void onLayoutFailed(CharSequence error) {
                            callback.onLayoutFailed(error);
                        }

                        @Override
                        public void onLayoutCancelled() {
                            callback.onLayoutCancelled();
                        }
                    }, extras);
        }

        @Override
        public void onWrite(
                PageRange[] pages,
                ParcelFileDescriptor destination,
                CancellationSignal cancellationSignal,
                WriteResultCallback callback) {
            try {
                cleanupTempPdf();
                tempPdf = File.createTempFile("greenman-print-", ".pdf", getCacheDir());
                final ParcelFileDescriptor tempDestination = ParcelFileDescriptor.open(
                        tempPdf,
                        ParcelFileDescriptor.MODE_CREATE
                                | ParcelFileDescriptor.MODE_TRUNCATE
                                | ParcelFileDescriptor.MODE_READ_WRITE);

                chromium.onWrite(new PageRange[]{PageRange.ALL_PAGES}, tempDestination,
                        cancellationSignal, new WriteResultCallback() {
                            @Override
                            public void onWriteFinished(PageRange[] writtenPages) {
                                try {
                                    tempDestination.close();
                                } catch (IOException ignored) {
                                }
                                new Thread(() -> flattenAndWrite(
                                        destination, cancellationSignal, callback),
                                        "GreenmanPdfFlatten").start();
                            }

                            @Override
                            public void onWriteFailed(CharSequence error) {
                                try {
                                    tempDestination.close();
                                } catch (IOException ignored) {
                                }
                                callback.onWriteFailed(error);
                                cleanupTempPdf();
                            }

                            @Override
                            public void onWriteCancelled() {
                                try {
                                    tempDestination.close();
                                } catch (IOException ignored) {
                                }
                                callback.onWriteCancelled();
                                cleanupTempPdf();
                            }
                        });
            } catch (Exception error) {
                callback.onWriteFailed("The phone-friendly PDF could not be prepared.");
                cleanupTempPdf();
            }
        }

        private void flattenAndWrite(
                ParcelFileDescriptor destination,
                CancellationSignal cancellationSignal,
                WriteResultCallback callback) {
            PdfDocument output = null;
            ParcelFileDescriptor input = null;
            PdfRenderer renderer = null;
            FileOutputStream stream = null;
            try {
                if (tempPdf == null || !tempPdf.isFile() || tempPdf.length() < 100) {
                    throw new IOException("Temporary print PDF was empty.");
                }
                input = ParcelFileDescriptor.open(tempPdf, ParcelFileDescriptor.MODE_READ_ONLY);
                renderer = new PdfRenderer(input);
                output = new PdfDocument();

                final int pageCount = renderer.getPageCount();
                for (int index = 0; index < pageCount; index++) {
                    if (cancellationSignal != null && cancellationSignal.isCanceled()) {
                        callback.onWriteCancelled();
                        return;
                    }
                    PdfRenderer.Page sourcePage = renderer.openPage(index);
                    Bitmap bitmap = null;
                    try {
                        final int pointWidth = sourcePage.getWidth();
                        final int pointHeight = sourcePage.getHeight();
                        final int pixelWidth = Math.max(1, Math.round(pointWidth * RASTER_SCALE));
                        final int pixelHeight = Math.max(1, Math.round(pointHeight * RASTER_SCALE));
                        bitmap = Bitmap.createBitmap(pixelWidth, pixelHeight, Bitmap.Config.ARGB_8888);
                        bitmap.eraseColor(Color.WHITE);
                        Matrix matrix = new Matrix();
                        matrix.setScale(RASTER_SCALE, RASTER_SCALE);
                        sourcePage.render(bitmap, null, matrix, PdfRenderer.Page.RENDER_MODE_FOR_PRINT);

                        PdfDocument.PageInfo pageInfo = new PdfDocument.PageInfo.Builder(
                                pointWidth, pointHeight, index + 1).create();
                        PdfDocument.Page targetPage = output.startPage(pageInfo);
                        targetPage.getCanvas().drawColor(Color.WHITE);
                        targetPage.getCanvas().drawBitmap(
                                bitmap,
                                new Rect(0, 0, bitmap.getWidth(), bitmap.getHeight()),
                                new Rect(0, 0, pointWidth, pointHeight),
                                null);
                        output.finishPage(targetPage);
                    } finally {
                        if (bitmap != null) {
                            bitmap.recycle();
                        }
                        sourcePage.close();
                    }
                }

                stream = new FileOutputStream(destination.getFileDescriptor());
                output.writeTo(stream);
                stream.flush();
                callback.onWriteFinished(new PageRange[]{PageRange.ALL_PAGES});
            } catch (Exception error) {
                callback.onWriteFailed("The phone-friendly PDF could not be written.");
            } finally {
                try {
                    if (stream != null) stream.close();
                } catch (IOException ignored) {
                }
                if (output != null) output.close();
                if (renderer != null) renderer.close();
                try {
                    if (input != null) input.close();
                } catch (IOException ignored) {
                }
                cleanupTempPdf();
            }
        }

        private void cleanupTempPdf() {
            File f = tempPdf;
            tempPdf = null;
            if (f != null && f.exists()) {
                //noinspection ResultOfMethodCallIgnored
                f.delete();
            }
        }

        @Override
        public void onFinish() {
            try {
                chromium.onFinish();
            } finally {
                cleanupTempPdf();
            }
        }
    }

'''
s = s.replace(class_anchor, adapter + class_anchor, 1)

# Build guards.
for required in (
    'new PhoneFriendlyPrintAdapter(target, jobName)',
    'class PhoneFriendlyPrintAdapter extends PrintDocumentAdapter',
    'new PdfRenderer(input)',
    'RENDER_MODE_FOR_PRINT',
    'RASTER_SCALE = 2.0f',
):
    if required not in s:
        raise SystemExit(f'missing phone-friendly PDF marker: {required}')

if s.count('target.createPrintDocumentAdapter(jobName)') != 1:
    # Exactly one call is retained inside PhoneFriendlyPrintAdapter's constructor.
    raise SystemExit('unexpected Chromium adapter owner count')

out.write_text(s, encoding='utf-8')
print('Installed isolated phone-friendly PDF adapter; HTML/page builders unchanged')
