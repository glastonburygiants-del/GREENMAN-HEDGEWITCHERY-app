package com.greenman.hedgewitchery;

import android.content.Context;
import android.content.SharedPreferences;
import android.webkit.JavascriptInterface;

import org.json.JSONObject;

public final class WildwoodWebBridge {
    private static final String PREFS = "gm_wildwood_stock_bridge_v1";
    private final Context context;
    private final SharedPreferences prefs;

    public WildwoodWebBridge(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = this.context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static String safe(String s, int max, String fallback) {
        if (s == null) return fallback;
        if (s.length() > max) return fallback;
        return s;
    }

    @JavascriptInterface
    public synchronized boolean publish(String stockJson, String logJson, String appMode, String masterMode) {
        String stock = safe(stockJson, 2_000_000, "{}");
        String logs = safe(logJson, 2_000_000, "[]");
        String mode = safe(appMode, 40, "");
        String master = "1".equals(masterMode) ? "1" : "0";
        SharedPreferences.Editor e = prefs.edit()
                .putString("stock_json", stock)
                .putString("log_json", logs)
                .putString("app_mode", mode)
                .putString("master_mode", master)
                .putLong("updated_at", System.currentTimeMillis());
        String pending = prefs.getString("pending_stock_json", "");
        if (pending != null && pending.equals(stock)) {
            e.remove("pending_stock_json");
        }
        e.apply();
        return true;
    }

    @JavascriptInterface
    public synchronized String pending() {
        try {
            JSONObject o = new JSONObject();
            String pending = prefs.getString("pending_stock_json", "");
            o.put("revision", prefs.getLong("pending_revision", 0L));
            o.put("stock_json", pending == null ? "" : pending);
            return o.toString();
        } catch (Exception e) {
            return "{\"revision\":0,\"stock_json\":\"\"}";
        }
    }

    @JavascriptInterface
    public synchronized boolean acknowledge(long revision) {
        long current = prefs.getLong("pending_revision", 0L);
        if (revision <= 0L || current != revision) return false;
        prefs.edit().remove("pending_stock_json").apply();
        return true;
    }

    @JavascriptInterface
    public synchronized String state() {
        try {
            JSONObject o = new JSONObject();
            o.put("stock_json", prefs.getString("stock_json", "{}"));
            o.put("log_json", prefs.getString("log_json", "[]"));
            o.put("app_mode", prefs.getString("app_mode", ""));
            o.put("master_mode", prefs.getString("master_mode", "0"));
            o.put("updated_at", prefs.getLong("updated_at", 0L));
            o.put("pending_revision", prefs.getLong("pending_revision", 0L));
            return o.toString();
        } catch (Exception e) {
            return "{}";
        }
    }
}