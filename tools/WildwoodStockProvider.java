package com.greenman.hedgewitchery;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;

public final class WildwoodStockProvider extends ContentProvider {
    public static final String AUTHORITY = "com.greenman.hedgewitchery.stockbridge";
    public static final String PERMISSION = "com.greenman.hedgewitchery.permission.WILDWOOD_STOCK_BRIDGE";
    private static final String PREFS = "gm_wildwood_stock_bridge_v1";
    private SharedPreferences prefs;

    private SharedPreferences prefs() {
        if (prefs == null) {
            Context c = getContext();
            if (c != null) prefs = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        }
        return prefs;
    }

    @Override public boolean onCreate() {
        prefs();
        return true;
    }

    private static String safe(String s, int max, String fallback) {
        if (s == null) return fallback;
        if (s.length() > max) return fallback;
        return s;
    }

    @Override public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs, String sortOrder) {
        MatrixCursor c = new MatrixCursor(new String[]{
                "stock_json","log_json","app_mode","master_mode","updated_at",
                "pending_revision","pending_stock_json"
        });
        SharedPreferences p = prefs();
        if (p == null) return c;
        String published = p.getString("stock_json", "{}");
        String pending = p.getString("pending_stock_json", "");
        long revision = p.getLong("pending_revision", 0L);
        String effective = pending != null && pending.length() > 0 ? pending : published;
        c.addRow(new Object[]{
                effective == null ? "{}" : effective,
                p.getString("log_json", "[]"),
                p.getString("app_mode", ""),
                p.getString("master_mode", "0"),
                p.getLong("updated_at", 0L),
                revision,
                pending == null ? "" : pending
        });
        return c;
    }

    @Override public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        if (values == null || !values.containsKey("stock_json")) return 0;
        String stock = safe(values.getAsString("stock_json"), 2_000_000, null);
        if (stock == null || stock.trim().length() == 0) return 0;
        SharedPreferences p = prefs();
        if (p == null) return 0;
        long revision = Math.max(1L, p.getLong("pending_revision", 0L) + 1L);
        p.edit()
                .putString("pending_stock_json", stock)
                .putLong("pending_revision", revision)
                .putLong("external_requested_at", System.currentTimeMillis())
                .apply();
        Context c = getContext();
        if (c != null) c.getContentResolver().notifyChange(uri, null);
        return 1;
    }

    @Override public String getType(Uri uri) { return "vnd.android.cursor.item/vnd.greenman.wildwood-stock"; }
    @Override public Uri insert(Uri uri, ContentValues values) { throw new UnsupportedOperationException("insert"); }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) { throw new UnsupportedOperationException("delete"); }
}