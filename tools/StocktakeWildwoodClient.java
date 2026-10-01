package com.greenman.hedgewitchery;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.webkit.JavascriptInterface;

import org.json.JSONObject;

public final class StocktakeWildwoodClient {
    private static final Uri URI = Uri.parse("content://com.greenman.hedgewitchery.stockbridge/state");
    private final Context context;

    public StocktakeWildwoodClient(Context context) {
        this.context = context.getApplicationContext();
    }

    @JavascriptInterface
    public synchronized boolean available() {
        Cursor c = null;
        try {
            c = context.getContentResolver().query(URI, null, null, null, null);
            return c != null && c.moveToFirst();
        } catch (Throwable e) {
            return false;
        } finally {
            if (c != null) c.close();
        }
    }

    @JavascriptInterface
    public synchronized String readState() {
        Cursor c = null;
        try {
            c = context.getContentResolver().query(URI, null, null, null, null);
            if (c == null || !c.moveToFirst()) return "{}";
            JSONObject o = new JSONObject();
            for (String name : new String[]{"stock_json","log_json","app_mode","master_mode","pending_stock_json"}) {
                int i = c.getColumnIndex(name);
                if (i >= 0) o.put(name, c.getString(i));
            }
            int r = c.getColumnIndex("pending_revision");
            if (r >= 0) o.put("pending_revision", c.getLong(r));
            int u = c.getColumnIndex("updated_at");
            if (u >= 0) o.put("updated_at", c.getLong(u));
            return o.toString();
        } catch (Throwable e) {
            return "{}";
        } finally {
            if (c != null) c.close();
        }
    }

    @JavascriptInterface
    public synchronized boolean writeStock(String stockJson) {
        if (stockJson == null || stockJson.length() == 0 || stockJson.length() > 2_000_000) return false;
        try {
            ContentValues v = new ContentValues();
            v.put("stock_json", stockJson);
            return context.getContentResolver().update(URI, v, null, null) == 1;
        } catch (Throwable e) {
            return false;
        }
    }
}