package com.greenman.hedgewitchery;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;

import org.json.JSONArray;
import org.json.JSONObject;

public final class WildwoodBridgeProvider extends ContentProvider {
    public static final String AUTHORITY = "com.greenman.hedgewitchery.apothecary.wildwoodbridge";
    public static final Uri URI = Uri.parse("content://" + AUTHORITY);
    private static final String PREFS = "greenman_wildwood_bridge_v1";
    private static final String STOCK = "stock_json";
    private static final String LOG = "log_json";
    private static final String READY = "ready";
    private static final String REVISION = "revision";
    private static final String UPDATED = "updated_at";

    private SharedPreferences prefs() {
        Context c = getContext();
        if (c == null) throw new IllegalStateException("Context unavailable");
        return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static Bundle read(Context context) {
        SharedPreferences p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        Bundle b = new Bundle();
        b.putBoolean("ready", p.getBoolean(READY, false));
        b.putLong("revision", p.getLong(REVISION, 0));
        b.putLong("updated_at", p.getLong(UPDATED, 0));
        b.putString("stock_json", p.getString(STOCK, "{}"));
        b.putString("log_json", p.getString(LOG, "[]"));
        return b;
    }

    public static Bundle write(Context context, String stockJson, String logJson) {
        try {
            new JSONObject(stockJson == null ? "{}" : stockJson);
            new JSONArray(logJson == null ? "[]" : logJson);
        } catch (Exception invalid) {
            Bundle b = new Bundle();
            b.putBoolean("ok", false);
            b.putString("error", "Invalid Wildwood JSON");
            return b;
        }

        SharedPreferences p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        long rev = p.getLong(REVISION, 0) + 1;
        long now = System.currentTimeMillis();
        p.edit()
                .putString(STOCK, stockJson == null ? "{}" : stockJson)
                .putString(LOG, logJson == null ? "[]" : logJson)
                .putBoolean(READY, true)
                .putLong(REVISION, rev)
                .putLong(UPDATED, now)
                .apply();

        Bundle b = new Bundle();
        b.putBoolean("ok", true);
        b.putLong("revision", rev);
        b.putLong("updated_at", now);
        return b;
    }

    @Override
    public boolean onCreate() {
        return true;
    }

    @Override
    public Bundle call(String method, String arg, Bundle extras) {
        Context c = getContext();
        if (c == null) return Bundle.EMPTY;
        if ("read".equals(method)) return read(c);
        if ("write".equals(method)) {
            String stock = extras == null ? "{}" : extras.getString("stock_json", "{}");
            String log = extras == null ? "[]" : extras.getString("log_json", "[]");
            return write(c, stock, log);
        }
        return super.call(method, arg, extras);
    }

    @Override public String getType(Uri uri) { return null; }
    @Override public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs, String sortOrder) { return null; }
    @Override public Uri insert(Uri uri, ContentValues values) { return null; }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) { return 0; }
    @Override public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) { return 0; }
}
