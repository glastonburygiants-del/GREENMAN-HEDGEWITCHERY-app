#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: install_phone_friendly_pdf_adapter.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')

# This experiment deliberately changes only the final Android PDF representation.
# The Greenman HTML, A4 builders, print content, fitting code and databases stay intact.
# The print WebView is allowed to finish layout first. We then force its existing
# @media print rules into the capture view, capture the completed page drawing once,
# and emit simple image-backed A4 pages through a native PrintDocumentAdapter.

imports = {
    'import android.graphics.Bitmap;\n': 'import android.graphics.Bitmap;\nimport android.graphics.Canvas;\nimport android.graphics.Paint;\nimport android.graphics.Picture;\nimport android.graphics.Rect;\n',
    'import android.os.Environment;\n': 'import android.os.Environment;\nimport android.os.CancellationSignal;\nimport android.os.ParcelFileDescriptor;\n',
    'import android.provider.MediaStore;\n': 'import android.provider.MediaStore;\nimport android.print.PageRange;\nimport android.print.PrintAttributes;\nimport android.print.PrintDocumentAdapter;\nimport android.print.PrintDocumentInfo;\nimport android.print.pdf.PrintedPdfDocument;\n',
    'import java.io.ByteArrayInputStream;\n': 'import java.io.ByteArrayInputStream;\nimport java.io.FileOutputStream;\n',
    'import java.util.Locale;\n': 'import java.util.Locale;\n\nimport org.json.JSONArray;\nimport org.json.JSONObject;\nimport org.json.JSONTokener;\n',
}
for old,new in imports.items():
    if s.count(old) != 1:
        raise SystemExit(f'import anchor count for {old!r}: {s.count(old)}')
    s=s.replace(old,new,1)

start=s.index('    private void printWebViewDocument(WebView target, String fallbackJobName) {')
end=s.index('\n    private static String sanitizePrintJobName',start)

block=r'''    private static final String PHONE_CAPTURE_SCRIPT =
            "(function(){try{"
                    + "var force=document.getElementById('__gm_phone_print_css');"
                    + "if(!force){var css='';"
                    + "function walk(rules){if(!rules)return;for(var i=0;i<rules.length;i++){var r=rules[i];"
                    + "try{if(r.type===4&&/print/i.test(String(r.conditionText||''))){for(var j=0;j<r.cssRules.length;j++)css+=r.cssRules[j].cssText+'\\n';}"
                    + "else if(r.cssRules)walk(r.cssRules);}catch(_e){}}}"
                    + "for(var s=0;s<document.styleSheets.length;s++){try{walk(document.styleSheets[s].cssRules);}catch(_e){}}"
                    + "force=document.createElement('style');force.id='__gm_phone_print_css';"
                    + "force.textContent=css+'\\n*{animation:none!important;transition:none!important;}';document.head.appendChild(force);}"
                    + "try{window.dispatchEvent(new Event('beforeprint'));}catch(_e){}"
                    + "document.documentElement.style.background='#fff';document.body.style.background='#fff';"
                    + "var selectors=['#printArea .a4-page','#printArea .a4-shell','#printArea .true-page',"
                    + "'#gmAdminBookPrintArea .a4-shell','#root>.true-page','#root>.pack-page','#root>.pp-page',"
                    + "'.a4-page','.a4-shell','.true-page','.pack-page','.pp-page','body>.sheet'];"
                    + "var raw=[];for(var si=0;si<selectors.length;si++){var els=document.querySelectorAll(selectors[si]);"
                    + "for(var ei=0;ei<els.length;ei++){var e=els[ei],st=getComputedStyle(e);if(st.display==='none'||st.visibility==='hidden')continue;"
                    + "var r=e.getBoundingClientRect(),w=r.width,h=r.height;if(w<420||h<600)continue;"
                    + "raw.push({l:r.left+window.scrollX,t:r.top+window.scrollY,w:w,h:h,rank:selectors.length-si});}}"
                    + "raw.sort(function(a,b){return a.t-b.t||b.rank-a.rank||b.w*b.h-a.w*a.h;});"
                    + "var out=[];for(var k=0;k<raw.length;k++){var a=raw[k],dup=false;for(var q=0;q<out.length;q++){var b=out[q];"
                    + "var ix=Math.max(0,Math.min(a.l+a.w,b.l+b.w)-Math.max(a.l,b.l));"
                    + "var iy=Math.max(0,Math.min(a.t+a.h,b.t+b.h)-Math.max(a.t,b.t));"
                    + "var overlap=ix*iy/Math.max(1,Math.min(a.w*a.h,b.w*b.h));if(overlap>.82){dup=true;break;}}"
                    + "if(!dup)out.push(a);}"
                    + "if(!out.length){var d=document.documentElement,b=document.body;var w=Math.max(d.scrollWidth,b?b.scrollWidth:0,794);"
                    + "var h=Math.max(d.scrollHeight,b?b.scrollHeight:0,1123);var ph=w*1.4142857;for(var y=0;y<h;y+=ph)out.push({l:0,t:y,w:w,h:Math.min(ph,h-y),rank:0});}"
                    + "return JSON.stringify(out);}catch(err){return JSON.stringify({error:String(err)});}})();";

    private static final class PageSlice {
        final float left;
        final float top;
        final float width;
        final float height;

        PageSlice(float left, float top, float width, float height) {
            this.left = left;
            this.top = top;
            this.width = width;
            this.height = height;
        }
    }

    @SuppressWarnings("deprecation")
    private void printWebViewDocument(WebView target, String fallbackJobName) {
        try {
            android.print.PrintManager printManager =
                    (android.print.PrintManager) getSystemService(PRINT_SERVICE);
            Object tag = target.getTag();
            String jobName = sanitizePrintJobName(tag instanceof String ? (String) tag : fallbackJobName);
            PrintAttributes attributes = new PrintAttributes.Builder()
                    .setMediaSize(PrintAttributes.MediaSize.ISO_A4)
                    .setMinMargins(PrintAttributes.Margins.NO_MARGINS)
                    .setColorMode(PrintAttributes.COLOR_MODE_COLOR)
                    .build();

            target.evaluateJavascript(PHONE_CAPTURE_SCRIPT, value -> {
                try {
                    Object decoded = new JSONTokener(value == null ? "null" : value).nextValue();
                    String json = decoded instanceof String ? (String) decoded : String.valueOf(decoded);
                    if (json.startsWith("{")) {
                        throw new IllegalStateException("Page capture script failed: " + json);
                    }
                    JSONArray array = new JSONArray(json);
                    java.util.ArrayList<PageSlice> slices = new java.util.ArrayList<>();
                    for (int i = 0; i < array.length(); i++) {
                        JSONObject o = array.getJSONObject(i);
                        float w = (float) o.optDouble("w", 0);
                        float h = (float) o.optDouble("h", 0);
                        if (w < 100 || h < 100) continue;
                        slices.add(new PageSlice(
                                (float) o.optDouble("l", 0),
                                (float) o.optDouble("t", 0),
                                w,
                                h));
                    }
                    if (slices.isEmpty()) {
                        throw new IllegalStateException("No A4 pages were found.");
                    }
                    target.postDelayed(() -> {
                        try {
                            Picture picture = target.capturePicture();
                            if (picture == null || picture.getWidth() < 100 || picture.getHeight() < 100) {
                                throw new IllegalStateException("The print drawing was empty.");
                            }
                            printManager.print(jobName,
                                    new PhoneFriendlyPictureAdapter(picture, slices, jobName),
                                    attributes);
                            target.postDelayed(() -> {
                                if (printWebView == target) destroyPrintWebView();
                            }, 120000L);
                        } catch (Exception error) {
                            Toast.makeText(MainActivity.this,
                                    "The phone PDF could not be prepared.", Toast.LENGTH_LONG).show();
                        }
                    }, 220L);
                } catch (Exception error) {
                    Toast.makeText(MainActivity.this,
                            "The A4 pages could not be prepared for PDF.", Toast.LENGTH_LONG).show();
                }
            });
        } catch (Exception error) {
            Toast.makeText(this, "Printing could not be opened.", Toast.LENGTH_LONG).show();
        }
    }

    private final class PhoneFriendlyPictureAdapter extends PrintDocumentAdapter {
        private static final int RASTER_WIDTH = 1190; // A4 at 144 dpi.
        private static final int RASTER_HEIGHT = 1684;
        private final Picture picture;
        private final java.util.ArrayList<PageSlice> slices;
        private final String jobName;
        private PrintAttributes attributes;

        PhoneFriendlyPictureAdapter(Picture picture, java.util.ArrayList<PageSlice> slices, String jobName) {
            this.picture = picture;
            this.slices = slices;
            this.jobName = jobName;
        }

        @Override
        public void onLayout(
                PrintAttributes oldAttributes,
                PrintAttributes newAttributes,
                CancellationSignal cancellationSignal,
                LayoutResultCallback callback,
                Bundle extras) {
            attributes = newAttributes;
            if (cancellationSignal != null && cancellationSignal.isCanceled()) {
                callback.onLayoutCancelled();
                return;
            }
            PrintDocumentInfo info = new PrintDocumentInfo.Builder(jobName)
                    .setContentType(PrintDocumentInfo.CONTENT_TYPE_DOCUMENT)
                    .setPageCount(slices.size())
                    .build();
            callback.onLayoutFinished(info, true);
        }

        @Override
        public void onWrite(
                PageRange[] pages,
                ParcelFileDescriptor destination,
                CancellationSignal cancellationSignal,
                WriteResultCallback callback) {
            final PrintAttributes usedAttributes = attributes;
            new Thread(() -> writeFlattenedPages(
                    usedAttributes, pages, destination, cancellationSignal, callback),
                    "GreenmanPhonePdf").start();
        }

        private void writeFlattenedPages(
                PrintAttributes attrs,
                PageRange[] requested,
                ParcelFileDescriptor destination,
                CancellationSignal cancellationSignal,
                WriteResultCallback callback) {
            PrintedPdfDocument document = null;
            FileOutputStream stream = null;
            try {
                if (attrs == null) throw new IllegalStateException("Print layout was unavailable.");
                document = new PrintedPdfDocument(MainActivity.this, attrs);
                Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
                for (int i = 0; i < slices.size(); i++) {
                    if (!pageRequested(requested, i)) continue;
                    if (cancellationSignal != null && cancellationSignal.isCanceled()) {
                        callback.onWriteCancelled();
                        return;
                    }
                    PageSlice slice = slices.get(i);
                    Bitmap bitmap = Bitmap.createBitmap(
                            RASTER_WIDTH, RASTER_HEIGHT, Bitmap.Config.RGB_565);
                    try {
                        Canvas bitmapCanvas = new Canvas(bitmap);
                        bitmapCanvas.drawColor(Color.WHITE);
                        float scale = Math.min(
                                RASTER_WIDTH / Math.max(1f, slice.width),
                                RASTER_HEIGHT / Math.max(1f, slice.height));
                        float dx = (RASTER_WIDTH - slice.width * scale) / 2f;
                        float dy = (RASTER_HEIGHT - slice.height * scale) / 2f;
                        bitmapCanvas.save();
                        bitmapCanvas.translate(dx, dy);
                        bitmapCanvas.scale(scale, scale);
                        bitmapCanvas.translate(-slice.left, -slice.top);
                        picture.draw(bitmapCanvas);
                        bitmapCanvas.restore();

                        android.graphics.pdf.PdfDocument.Page page = document.startPage(i);
                        Rect content = document.getPageContentRect();
                        page.getCanvas().drawColor(Color.WHITE);
                        page.getCanvas().drawBitmap(bitmap, null, content, paint);
                        document.finishPage(page);
                    } finally {
                        bitmap.recycle();
                    }
                }
                stream = new FileOutputStream(destination.getFileDescriptor());
                document.writeTo(stream);
                stream.flush();
                callback.onWriteFinished(requested == null || requested.length == 0
                        ? new PageRange[]{PageRange.ALL_PAGES}
                        : requested);
            } catch (Exception error) {
                callback.onWriteFailed("The phone-friendly PDF could not be written.");
            } finally {
                try {
                    if (stream != null) stream.close();
                } catch (IOException ignored) {
                }
                if (document != null) document.close();
            }
        }

        private boolean pageRequested(PageRange[] requested, int page) {
            if (requested == null || requested.length == 0) return true;
            for (PageRange range : requested) {
                if (range == null) continue;
                if (range == PageRange.ALL_PAGES) return true;
                if (page >= range.getStart() && page <= range.getEnd()) return true;
            }
            return false;
        }
    }
'''

s=s[:start]+block+s[end:]

for required in (
    'PHONE_CAPTURE_SCRIPT',
    'class PhoneFriendlyPictureAdapter extends PrintDocumentAdapter',
    'new PrintedPdfDocument(MainActivity.this, attrs)',
    'target.capturePicture()',
    'RASTER_WIDTH = 1190',
):
    if required not in s:
        raise SystemExit(f'missing phone-friendly PDF marker: {required}')
if 'new PhoneFriendlyPrintAdapter' in s or 'PdfRenderer' in s:
    raise SystemExit('obsolete failed PDF-wrapper experiment remains')
if s.count('private void printWebViewDocument') != 1:
    raise SystemExit('printWebViewDocument owner count changed')

out.write_text(s, encoding='utf-8')
print('Installed native flattened A4 PDF adapter; Greenman HTML/page builders unchanged')
