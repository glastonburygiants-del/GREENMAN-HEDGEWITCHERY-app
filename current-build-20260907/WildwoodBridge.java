package com.greenman.hedgewitchery;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.webkit.JavascriptInterface;

import org.json.JSONObject;

public final class WildwoodBridge {
    private static final String STOCKTAKE_PACKAGE = "com.greenman.hedgewitchery.stocktake";
    private final Context context;

    public WildwoodBridge(Context context) {
        this.context = context.getApplicationContext();
    }

    @JavascriptInterface
    public String getSnapshot() {
        try {
            Bundle b = WildwoodBridgeProvider.read(context);
            JSONObject o = new JSONObject();
            o.put("ready", b.getBoolean("ready", false));
            o.put("revision", b.getLong("revision", 0));
            o.put("updated_at", b.getLong("updated_at", 0));
            o.put("stock_json", b.getString("stock_json", "{}"));
            o.put("log_json", b.getString("log_json", "[]"));
            return o.toString();
        } catch (Exception e) {
            return "{\"ready\":false,\"revision\":0}";
        }
    }

    @JavascriptInterface
    public String saveSnapshot(String stockJson, String logJson) {
        try {
            Bundle b = WildwoodBridgeProvider.write(context, stockJson, logJson);
            JSONObject o = new JSONObject();
            o.put("ok", b.getBoolean("ok", false));
            o.put("revision", b.getLong("revision", 0));
            o.put("updated_at", b.getLong("updated_at", 0));
            o.put("error", b.getString("error", ""));
            return o.toString();
        } catch (Exception e) {
            return "{\"ok\":false}";
        }
    }

    @JavascriptInterface
    public boolean openStocktake() {
        try {
            Intent i = context.getPackageManager().getLaunchIntentForPackage(STOCKTAKE_PACKAGE);
            if (i == null) return false;
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(i);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
