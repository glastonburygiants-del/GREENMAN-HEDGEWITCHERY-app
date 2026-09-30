# Greenman HedgeWitchery Apothecary - HedgeWitchery Key Maker

Standalone private Android Key Maker.

- Separate package: `com.greenman.hedgewitchery.keymaker`
- Does not modify or replace the main HedgeWitchery app.
- Opens directly into the Key Maker. There is no password screen.
- Creates Web and Android access keys through the existing Supabase key service.
- Full generated codes are retained locally on the Key Maker device; Supabase stores hashes/masked records.

## Private build credential

The repository is public, so the Key Maker credential is deliberately **not committed to source**.

GitHub Actions expects a repository secret named:

`GREENMAN_KEYMAKER_DEVICE_TOKEN`

The secret is compiled into the private APK at build time and exposed only to the app's internal WebView bridge.
